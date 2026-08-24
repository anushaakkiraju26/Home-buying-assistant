import hashlib
import os
import sys
from pathlib import Path
import json
from bs4 import UnicodeDammit
from langchain_core.documents import Document

from dotenv import load_dotenv
from langchain_community.document_loaders import (
    BSHTMLLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_pinecone import PineconeEmbeddings, PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone

load_dotenv()

INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]


def stable_chunk_id(source: str, page: int, text: str) -> str:
    value = f"{source}:{page}:{text}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def load_document(path: Path):
    extension = path.suffix.lower()

    if extension == ".pdf":
        loader = PyPDFLoader(str(path))

    elif extension in {".txt", ".md"}:
        loader = TextLoader(
            str(path),
            encoding="utf-8",
            autodetect_encoding=True,
        )

    elif extension in {".html", ".htm"}:
        detected_encoding = (
            UnicodeDammit(path.read_bytes(), is_html=True).original_encoding
            or "utf-8"
        )
        loader = BSHTMLLoader(
            str(path),
            open_encoding=detected_encoding,
            get_text_separator="\n",
        )

    else:
        raise ValueError(
            f"Unsupported document type: {path}"
        )

    documents = loader.load()

    for document in documents:
        document.metadata.update(
            {
                "source": path.name,
                "file_path": str(path),
                "file_type": extension.removeprefix("."),
                "document_type": "home_buying_reference",
            }
        )

    return documents

def chunk_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    for position, chunk in enumerate(chunks):
        page = chunk.metadata.get("page", 0)

        chunk.metadata.update(
            {
                "chunk_strategy": "recursive",
                "chunk_position": position,
                "chunk_id": stable_chunk_id(
                    chunk.metadata["source"],
                    page,
                    chunk.page_content,
                ),
            }
        )

    return chunks

def save_chunks(chunks, output_path="chunks.json"):
    records = [
        {
            "page_content": chunk.page_content,
            "metadata": chunk.metadata,
        }
        for chunk in chunks
    ]

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)

    print(f"Saved {len(records)} chunks to {output_path}")



def find_document_files(input_path: Path):
    supported_extensions = {
    ".pdf",
    ".txt",
    ".md",
    ".html",
    ".htm",
}

    if input_path.is_file():
        if input_path.suffix.lower() not in supported_extensions:
            raise ValueError(
                f"Unsupported document type: {input_path}"
            )

        return [input_path]

    if input_path.is_dir():
        document_files = sorted(
            path
            for path in input_path.rglob("*")
            if (
                path.is_file()
                and path.suffix.lower() in supported_extensions
            )
        )

        if not document_files:
            raise ValueError(
                f"No supported documents found in: {input_path}"
            )

        return document_files

    raise FileNotFoundError(input_path)


def main(input_path: str):
    path = Path(input_path)
    document_files = find_document_files(path)

    all_documents = []

    for document_path in document_files:
        print(f"Loading {document_path.name}...")

        documents = load_document(document_path)
        all_documents.extend(documents)

        print(
            f"  Loaded {len(documents)} document units "
            f"from {document_path.name}"
        )
    chunks = chunk_documents(all_documents)
    save_chunks(chunks)

    embeddings = PineconeEmbeddings(
        model="multilingual-e5-large"
    )

    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index = pc.Index(INDEX_NAME)

    vector_store = PineconeVectorStore(
        index=index,
        embedding=embeddings,
        text_key="text",
        namespace="recursive-v1",
    )

    ids = [
        chunk.metadata["chunk_id"]
        for chunk in chunks
    ]

    print(f"Uploading {len(chunks)} chunks to Pinecone...")

    vector_store.add_documents(
        documents=chunks,
        ids=ids,
    )

    print(f"Loaded {len(document_files)} files")
    print(f"Loaded {len(all_documents)} total pages")
    print(f"Created and indexed {len(chunks)} chunks")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python ingest.py <PDF file or directory>"
        )

    main(sys.argv[1])
