import sys

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from hybrid_retriever import hybrid_retrieve

load_dotenv()


def format_context(documents):
    blocks = []

    for number, document in enumerate(documents, start=1):
        source = document.metadata.get("source", "unknown")
        page = document.metadata.get("page", "unknown")

        blocks.append(
            f"[Source {number}: {source}, page {page}]\n"
            f"{document.page_content}"
        )

    return "\n\n---\n\n".join(blocks)


def answer(question):
    print("Running hybrid retrieval and reranking...")

    documents = hybrid_retrieve(
        question,
        k=20,
        rerank_top_n=5,
    )

    if not documents:
        return "No relevant documents were retrieved."

    context = format_context(documents)

    print("Generating answer...")

    model = ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=0,
    )

    system_prompt = f"""
You are a home-buying education assistant.

Answer using only the supplied context.

Rules:
- Do not make claims unsupported by the context.
- If the context is insufficient, clearly say so.
- Cite sources using [Source N].
- Explain terminology in plain language.
- Do not present general information as legal advice.

CONTEXT:

{context}
""".strip()

    response = model.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question),
        ]
    )

    return response.content


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(
            'Usage: python ask.py "Your question here"'
        )

    question = " ".join(sys.argv[1:])
    print(f"Question: {question}\n")

    result = answer(question)

    print("\nAnswer:\n")
    print(result)