def reciprocal_rank_fusion(
    result_lists,
    weights=None,
    rrf_k=60,
    limit=20,
):
    if weights is None:
        weights = [1.0] * len(result_lists)

    fused = {}

    for results, weight in zip(result_lists, weights):
        for rank, (document, original_score) in enumerate(results, start=1):
            chunk_id = document.metadata["chunk_id"]

            if chunk_id not in fused:
                fused[chunk_id] = {
                    "document": document,
                    "rrf_score": 0.0,
                    "source_scores": [],
                }

            fused[chunk_id]["rrf_score"] += weight / (rrf_k + rank)
            fused[chunk_id]["source_scores"].append(original_score)

    ranked = sorted(
        fused.values(),
        key=lambda item: item["rrf_score"],
        reverse=True,
    )

    return ranked[:limit]

import json
import sys

from langchain_core.documents import Document
from langchain_pinecone import PineconeRerank

from bm25_retriever import KeywordRetriever
from retrieve import retrieve


def load_chunks(path="chunks.json"):
    with open(path, "r", encoding="utf-8") as file:
        records = json.load(file)

    return [
        Document(
            page_content=record["page_content"],
            metadata=record["metadata"],
        )
        for record in records
    ]


def reciprocal_rank_fusion(
    result_lists,
    weights=None,
    rrf_k=60,
    limit=20,
):
    if weights is None:
        weights = [1.0] * len(result_lists)

    fused = {}

    for results, weight in zip(result_lists, weights):
        for rank, (document, original_score) in enumerate(
            results,
            start=1,
        ):
            chunk_id = document.metadata["chunk_id"]

            if chunk_id not in fused:
                fused[chunk_id] = {
                    "document": document,
                    "rrf_score": 0.0,
                    "source_scores": [],
                }

            fused[chunk_id]["rrf_score"] += (
                weight / (rrf_k + rank)
            )
            fused[chunk_id]["source_scores"].append(
                original_score
            )

    ranked = sorted(
        fused.values(),
        key=lambda item: item["rrf_score"],
        reverse=True,
    )

    return ranked[:limit]


def hybrid_retrieve(question, k=20, rerank_top_n=5):
    # Semantic vector search
    dense_results = retrieve(question, k=k)

    # Keyword BM25 search
    chunks = load_chunks()
    keyword_retriever = KeywordRetriever(chunks)
    keyword_results = keyword_retriever.search(question, k=k)

    # Combine rankings instead of combining incompatible raw scores
    fused_results = reciprocal_rank_fusion(
        result_lists=[dense_results, keyword_results],
        weights=[1.0, 0.8],
        limit=k,
    )

    candidates = [
        result["document"]
        for result in fused_results
    ]

    # Rerank the hybrid candidates
    reranker = PineconeRerank(
        model="bge-reranker-v2-m3",
        top_n=rerank_top_n,
    )

    return list(
        reranker.compress_documents(
            documents=candidates,
            query=question,
        )
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(
            'Usage: python hybrid_retriever.py "question"'
        )

    question = " ".join(sys.argv[1:])
    results = hybrid_retrieve(question)

    for rank, document in enumerate(results, start=1):
        relevance = document.metadata.get(
            "relevance_score",
            0,
        )

        print(
            f"\n--- RESULT {rank} "
            f"| RERANK SCORE {relevance:.4f} ---"
        )
        print(f"Source: {document.metadata.get('source')}")
        print(f"Page: {document.metadata.get('page')}")
        print(document.page_content[:700])