import os
import sys

from dotenv import load_dotenv
from langchain_pinecone import PineconeEmbeddings, PineconeVectorStore
from pinecone import Pinecone

load_dotenv()

INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]


def build_vector_store():
    embeddings = PineconeEmbeddings(
        model="multilingual-e5-large"
    )

    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index = pc.Index(INDEX_NAME)

    return PineconeVectorStore(
        index=index,
        embedding=embeddings,
        text_key="text",
        namespace="recursive-v1",
    )


def retrieve(question: str, k: int = 10):
    vector_store = build_vector_store()

    return vector_store.similarity_search_with_score(
        query=question,
        k=k,
    )


if __name__ == "__main__":
    question = " ".join(sys.argv[1:])
    results = retrieve(question)

    for rank, (document, score) in enumerate(results, start=1):
        print(f"\n--- RESULT {rank} | SCORE {score:.4f} ---")
        print(f"Source: {document.metadata.get('source')}")
        print(f"Page: {document.metadata.get('page')}")
        print(document.page_content[:700])