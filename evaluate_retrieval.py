import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from hybrid_retriever import hybrid_retrieve


QUESTIONS_PATH = Path("evaluation_questions.json")
RESULTS_PATH = Path("evaluation_results.json")
REPORT_PATH = Path("evaluation_report.md")


def unique_source_ranking(documents) -> list[dict]:
    ranking = []
    seen = set()
    for document in documents:
        source = str(document.metadata.get("source", "unknown"))
        if source in seen:
            continue
        seen.add(source)
        score = document.metadata.get("relevance_score")
        ranking.append(
            {
                "source": source,
                "page": document.metadata.get("page", "unknown"),
                "score": float(score) if score is not None else None,
                "excerpt": document.page_content[:240].replace("\n", " "),
            }
        )
    return ranking


def score_case(case: dict, ranking: list[dict]) -> dict:
    expected = set(case["expected_sources"])
    ranked_sources = [item["source"] for item in ranking]
    relevant_ranks = [
        rank
        for rank, source in enumerate(ranked_sources, start=1)
        if source in expected
    ]
    first_rank = min(relevant_ranks) if relevant_ranks else None
    found_at_5 = expected.intersection(ranked_sources[:5])
    top_score = ranking[0]["score"] if ranking else None

    return {
        **case,
        "ranking": ranking,
        "first_relevant_rank": first_rank,
        "hit_at_1": bool(first_rank == 1),
        "hit_at_3": bool(first_rank is not None and first_rank <= 3),
        "hit_at_5": bool(first_rank is not None and first_rank <= 5),
        "reciprocal_rank": 1 / first_rank if first_rank else 0.0,
        "expected_source_recall_at_5": len(found_at_5) / len(expected),
        "missing_expected_sources": sorted(expected - found_at_5),
        "top_rerank_score": top_score,
    }


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def build_report(results: list[dict], generated_at: str) -> str:
    count = len(results)
    hit_1 = sum(item["hit_at_1"] for item in results) / count
    hit_3 = sum(item["hit_at_3"] for item in results) / count
    hit_5 = sum(item["hit_at_5"] for item in results) / count
    mrr = statistics.mean(item["reciprocal_rank"] for item in results)
    recall = statistics.mean(item["expected_source_recall_at_5"] for item in results)
    scores = [item["top_rerank_score"] for item in results if item["top_rerank_score"] is not None]
    mean_score = statistics.mean(scores) if scores else 0.0

    misses = [item for item in results if not item["hit_at_5"]]
    weak = [
        item for item in results
        if item["hit_at_5"] and item["first_relevant_rank"] > 1
    ]
    partial = [
        item for item in results
        if 0 < item["expected_source_recall_at_5"] < 1
    ]

    lines = [
        "# Home Buying RAG Retrieval Evaluation",
        "",
        f"**Generated:** {generated_at}",
        "",
        "## Executive summary",
        "",
        "This evaluation measures whether the retriever surfaces the manually "
        "identified authoritative source for 15 representative home-buying questions. "
        "Judgments are source-level and binary; they do not grade answer style or factual completeness.",
        "",
        "| Metric | Score |",
        "| --- | ---: |",
        f"| Hit@1 | {pct(hit_1)} ({sum(x['hit_at_1'] for x in results)}/{count}) |",
        f"| Hit@3 | {pct(hit_3)} ({sum(x['hit_at_3'] for x in results)}/{count}) |",
        f"| Hit@5 | {pct(hit_5)} ({sum(x['hit_at_5'] for x in results)}/{count}) |",
        f"| Mean reciprocal rank | {mrr:.3f} |",
        f"| Mean expected-source recall@5 | {pct(recall)} |",
        f"| Mean top reranker score | {mean_score:.3f} |",
        "",
        "### Interpretation",
        "",
        "- **Hit@K**: percentage of questions with at least one expected source in the first K unique sources.",
        "- **MRR**: rewards placing the first expected source near rank 1; 1.0 is perfect.",
        "- **Expected-source recall@5**: fraction of all manually expected sources recovered in the top five.",
        "- **Reranker score**: model-provided relevance signal; it is useful for comparisons but is not a calibrated probability.",
        "",
        "## Question-level results",
        "",
        "| ID | Category | Expected source | First relevant rank | Hit@5 | Recall@5 | Top score |",
        "| --- | --- | --- | ---: | :---: | ---: | ---: |",
    ]

    for item in results:
        expected = "<br>".join(f"`{x}`" for x in item["expected_sources"])
        rank = item["first_relevant_rank"] or "—"
        top_score = item["top_rerank_score"]
        score_text = f"{top_score:.3f}" if top_score is not None else "—"
        lines.append(
            f"| {item['id']} | {item['category']} | {expected} | {rank} | "
            f"{'Yes' if item['hit_at_5'] else 'No'} | "
            f"{pct(item['expected_source_recall_at_5'])} | {score_text} |"
        )
    lines += ["", "## Failure analysis", ""]

    if not misses and not weak and not partial:
        lines.append("All expected sources ranked first; no source-level failures were observed.")
    else:
        if misses:
            lines += ["### Expected source absent from top five", ""]
            for item in misses:
                returned = ", ".join(x["source"] for x in item["ranking"][:5]) or "No results"
                missing = ", ".join(item["missing_expected_sources"])
                lines.append(
                    f"- **{item['id']} — {item['question']}** Missing: `{missing}`. "
                    f"Returned: {returned}."
                )
            lines.append("")
        if weak:
            lines += ["### Expected source retrieved but not ranked first", ""]
            for item in weak:
                lines.append(
                    f"- **{item['id']} — {item['category']}** Expected source first appeared "
                    f"at rank {item['first_relevant_rank']}; rank 1 was "
                    f"`{item['ranking'][0]['source']}`."
                )
            lines.append("")
        if partial:
            lines += ["### Partial recovery for multi-source questions", ""]
            for item in partial:
                lines.append(
                    f"- **{item['id']} — {item['category']}** Missing expected source(s): "
                    f"`{', '.join(item['missing_expected_sources'])}`."
                )
            lines.append("")

    lines += [
        "### Cross-cutting risks",
        "",
        "- Source-level relevance does not guarantee that the retrieved chunk contains every fact needed for a complete answer.",
        "- Forms and sample disclosures can retrieve visually repetitive or boilerplate chunks rather than the field that answers the question.",
        "- Jurisdiction terms are essential. Omitting California or Texas may blend state-specific sources.",
        "- The live namespace may contain stale vectors from earlier ingestions unless it is cleared before rebuilding.",
        "- Reranker scores vary by query and should not be treated as confidence probabilities without calibration.",
        "",
        "## Recommendations",
        "",
        "1. Preserve the clean rebuild procedure for `recursive-v1` so obsolete chunk IDs do not accumulate.",
        "2. Add title, publisher, jurisdiction, category, and source URL metadata during ingestion.",
        "3. Apply jurisdiction-aware metadata filters or query routing for state-specific questions.",
        "4. Add chunk-level relevance judgments for misses and ambiguous form-based questions.",
        "5. Run this suite after every corpus, chunking, embedding, or reranker change and track metric deltas.",
        "6. Add adversarial questions for unsupported jurisdictions and verify the assistant abstains.",
        "",
        "## Per-question retrieved sources",
        "",
    ]

    for item in results:
        lines += [f"### {item['id']} — {item['question']}", ""]
        for rank, source in enumerate(item["ranking"][:5], start=1):
            score = f"{source['score']:.3f}" if source["score"] is not None else "n/a"
            lines.append(
                f"{rank}. `{source['source']}` — page {source['page']}, score {score}"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    load_dotenv(".env")
    cases = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    results = []

    for position, case in enumerate(cases, start=1):
        print(f"[{position}/{len(cases)}] {case['id']}: {case['question']}", flush=True)
        documents = hybrid_retrieve(case["question"], k=20, rerank_top_n=10)
        results.append(score_case(case, unique_source_ranking(documents)))

    generated_at = datetime.now(timezone.utc).isoformat()
    payload = {"generated_at": generated_at, "results": results}
    RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(build_report(results, generated_at), encoding="utf-8")
    print(f"Wrote {RESULTS_PATH} and {REPORT_PATH}")


if __name__ == "__main__":
    main()
