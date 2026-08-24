import json
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "evaluation_results.json"
OUTPUT = ROOT / "output" / "pdf" / "home_buying_rag_evaluation_report.pdf"

INK = colors.HexColor("#18332E")
GREEN = colors.HexColor("#245C50")
CORAL = colors.HexColor("#DF7358")
CREAM = colors.HexColor("#F7F4ED")
MINT = colors.HexColor("#DCEBE4")
PALE = colors.HexColor("#FFFDF8")
MUTED = colors.HexColor("#687874")
LINE = colors.HexColor("#D8DED8")
WHITE = colors.white


class EvaluationDocTemplate(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(
            filename,
            pagesize=letter,
            leftMargin=0.68 * inch,
            rightMargin=0.68 * inch,
            topMargin=0.84 * inch,
            bottomMargin=0.62 * inch,
            title="Home Buying RAG Retrieval Evaluation",
            author="Home Buying Assistant",
        )
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="main",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        self.addPageTemplates(PageTemplate(id="report", frames=frame, onPage=draw_page))


def draw_page(canvas, doc):
    canvas.saveState()
    width, height = letter
    page_number = canvas.getPageNumber()
    if page_number > 1:
        canvas.setStrokeColor(LINE)
        canvas.line(doc.leftMargin, height - 0.43 * inch, width - doc.rightMargin, height - 0.43 * inch)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(GREEN)
        canvas.drawString(doc.leftMargin, height - 0.31 * inch, "HAVEN  /  RETRIEVAL EVALUATION")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 0.32 * inch, "Home Buying RAG - clean recursive-v1 baseline")
    canvas.drawRightString(width - doc.rightMargin, 0.32 * inch, f"{page_number}")
    canvas.restoreState()


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=29,
            leading=33, textColor=INK, alignment=TA_LEFT, spaceAfter=13,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=base["BodyText"], fontName="Helvetica", fontSize=12,
            leading=18, textColor=MUTED, spaceAfter=18,
        ),
        "eyebrow": ParagraphStyle(
            "Eyebrow", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=8,
            leading=10, textColor=CORAL, spaceAfter=12, tracking=1.6,
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=19,
            leading=23, textColor=INK, spaceBefore=8, spaceAfter=11,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=13,
            leading=16, textColor=GREEN, spaceBefore=10, spaceAfter=7,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.2,
            leading=14, textColor=INK, spaceAfter=8,
        ),
        "small": ParagraphStyle(
            "Small", parent=base["BodyText"], fontName="Helvetica", fontSize=7.6,
            leading=10.5, textColor=MUTED,
        ),
        "table": ParagraphStyle(
            "Table", parent=base["BodyText"], fontName="Helvetica", fontSize=6.7,
            leading=8.5, textColor=INK,
        ),
        "table_head": ParagraphStyle(
            "TableHead", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=6.7,
            leading=8, textColor=WHITE, alignment=TA_LEFT,
        ),
        "metric": ParagraphStyle(
            "Metric", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=18,
            leading=20, textColor=GREEN, alignment=TA_CENTER,
        ),
        "metric_label": ParagraphStyle(
            "MetricLabel", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=6.6,
            leading=8, textColor=MUTED, alignment=TA_CENTER,
        ),
    }


def safe(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def metric_cards(results, style):
    n = len(results)
    hit1 = sum(x["hit_at_1"] for x in results) / n
    hit3 = sum(x["hit_at_3"] for x in results) / n
    hit5 = sum(x["hit_at_5"] for x in results) / n
    mrr = sum(x["reciprocal_rank"] for x in results) / n
    recall = sum(x["expected_source_recall_at_5"] for x in results) / n
    strict = sum(x.get("strict_pass", False) for x in results) / n
    values = [
        (f"{strict:.0%}", "STRICT PASS RATE"),
        (f"{hit1:.0%}", "HIT@1"),
        (f"{hit3:.0%}", "HIT@3"),
        (f"{hit5:.0%}", "HIT@5"),
        (f"{mrr:.3f}", "MEAN RECIPROCAL RANK"),
    ]
    cells = [
        [Paragraph(value, style["metric"]), Paragraph(label, style["metric_label"])]
        for value, label in values
    ]
    table = Table(
        [[Table([[cell[0]], [cell[1]]], colWidths=[1.22 * inch]) for cell in cells]],
        colWidths=[1.34 * inch] * 5,
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), 0.7, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return table


def question_table(results, style):
    data = [[
        Paragraph("ID", style["table_head"]),
        Paragraph("Verdict", style["table_head"]),
        Paragraph("Category", style["table_head"]),
        Paragraph("Expected source", style["table_head"]),
        Paragraph("Rank", style["table_head"]),
        Paragraph("Hit@5", style["table_head"]),
        Paragraph("Recall", style["table_head"]),
        Paragraph("Top score", style["table_head"]),
    ]]
    for item in results:
        expected = "<br/>".join(safe(x) for x in item["expected_sources"])
        rank = item["first_relevant_rank"] or "-"
        score = item["top_rerank_score"]
        data.append([
            Paragraph(item["id"], style["table"]),
            Paragraph("PASS" if item["strict_pass"] else "FAIL", style["table"]),
            Paragraph(safe(item["category"]), style["table"]),
            Paragraph(expected, style["table"]),
            Paragraph(str(rank), style["table"]),
            Paragraph("Yes" if item["hit_at_5"] else "No", style["table"]),
            Paragraph(f"{item['expected_source_recall_at_5']:.0%}", style["table"]),
            Paragraph(f"{score:.3f}" if score is not None else "-", style["table"]),
        ])
    table = Table(
        data,
        colWidths=[0.31 * inch, 0.43 * inch, 0.8 * inch, 2.17 * inch, 0.39 * inch, 0.45 * inch, 0.48 * inch, 0.52 * inch],
        repeatRows=1,
    )
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for row in range(1, len(data)):
        if row % 2 == 0:
            commands.append(("BACKGROUND", (0, row), (-1, row), CREAM))
    table.setStyle(TableStyle(commands))
    return table


def bullet(text, style):
    return Paragraph(f"<font color='#DF7358'>&bull;</font>&nbsp;&nbsp;{safe(text)}", style["body"])


def build():
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    results = payload["results"]
    generated = datetime.fromisoformat(payload["generated_at"]).strftime("%B %d, %Y at %H:%M UTC")
    style = styles()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    story = [
        Spacer(1, 0.48 * inch),
        Paragraph("RETRIEVAL QUALITY / EVALUATION REPORT", style["eyebrow"]),
        Paragraph("Home Buying RAG<br/><font color='#DF7358'>15-question evaluation</font>", style["title"]),
        Paragraph(
            "A source-level assessment of retrieval precision, recall, ranking quality, "
            "and observed failure patterns across the clean 33-document reference corpus.",
            style["subtitle"],
        ),
        Spacer(1, 0.08 * inch),
        metric_cards(results, style),
        Spacer(1, 0.28 * inch),
        HRFlowable(width="100%", thickness=1, color=LINE),
        Spacer(1, 0.2 * inch),
        Table(
            [
                [Paragraph("EVALUATED", style["metric_label"]), Paragraph("CORPUS", style["metric_label"]), Paragraph("VECTOR BASELINE", style["metric_label"])],
                [Paragraph(generated, style["body"]), Paragraph("33 documents / 604 pages", style["body"]), Paragraph("2,776 clean chunks", style["body"])],
            ],
            colWidths=[2.35 * inch, 2.25 * inch, 2.05 * inch],
            style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]),
        ),
        Spacer(1, 0.28 * inch),
        Paragraph("Overall assessment", style["h2"]),
        Paragraph(
            "Retrieval shows strong broad recall but moderate rank-one precision. Every test "
            "found an expected source within five unique sources, while five questions placed "
            "a different relevant or adjacent source first. The system is suitable for a "
            "multi-source RAG answer flow, but the first result should not be treated as independently authoritative.",
            style["body"],
        ),
        Paragraph(
            "Scope: judgments are binary at the source level. This report does not grade final "
            "answer writing, citation correctness, or whether each retrieved chunk contains every required fact.",
            style["small"],
        ),
        PageBreak(),
        Paragraph("Question-level results", style["h1"]),
        Paragraph(
            "Expected sources were selected manually from the curated corpus. Rank is measured "
            "after deduplicating returned chunks by source document.", style["body"],
        ),
        question_table(results, style),
        Spacer(1, 0.18 * inch),
        Paragraph("Metric definitions", style["h2"]),
        bullet("Strict pass: an expected source ranks first and all expected sources appear within the top five.", style),
        bullet("Hit@K: at least one expected source appears within the first K unique sources.", style),
        bullet("MRR: rewards placing the first expected source near rank one; 1.0 is perfect.", style),
        bullet("Source recall@5: fraction of all expected sources recovered in the top five.", style),
        bullet("Reranker scores are comparative relevance signals, not calibrated probabilities.", style),
        PageBreak(),
        Paragraph("Failure analysis", style["h1"]),
        Paragraph("Strict failures", style["h2"]),
    ]

    strict_failures = [x for x in results if not x.get("strict_pass", False)]
    story.append(Paragraph(
        f"<b>{len(strict_failures)} of {len(results)} questions failed</b> the strict criterion. "
        "A failure means the expected source was not ranked first or at least one manually "
        "expected source was absent from the top five.", style["body"]
    ))
    for item in strict_failures:
        story.append(bullet(
            f"{item['id']} / {item['category']}: FAIL - {'; '.join(item['failure_reasons'])}.", style
        ))

    story += [
        Spacer(1, 0.08 * inch),
        Paragraph("Expected source retrieved, but not ranked first", style["h2"]),
    ]

    weak = [x for x in results if x["hit_at_5"] and x["first_relevant_rank"] and x["first_relevant_rank"] > 1]
    for item in weak:
        story.append(bullet(
            f"{item['id']} / {item['category']}: expected source first appeared at rank "
            f"{item['first_relevant_rank']}; rank one was {item['ranking'][0]['source']}.", style
        ))

    partial = [x for x in results if 0 < x["expected_source_recall_at_5"] < 1]
    story += [Spacer(1, 0.08 * inch), Paragraph("Partial multi-source recovery", style["h2"])]
    for item in partial:
        story.append(bullet(
            f"{item['id']} / {item['category']}: missing {', '.join(item['missing_expected_sources'])} from the top five.", style
        ))

    story += [
        Spacer(1, 0.08 * inch),
        Paragraph("Cross-cutting observations", style["h2"]),
        bullet("Forms and sample disclosures may retrieve boilerplate instead of the exact field needed.", style),
        bullet("Jurisdiction terms are essential; vague questions may blend California, Texas, and federal sources.", style),
        bullet("Broad guides can outrank specialist documents because they cover many buyer topics in natural language.", style),
        bullet("Source relevance does not guarantee complete answer coverage at the chunk level.", style),
        PageBreak(),
        Spacer(1, 0.28 * inch),
        Paragraph("Recommended actions", style["h1"]),
        bullet("Preserve clean namespace rebuilds so obsolete chunk IDs do not accumulate.", style),
        bullet("Add title, publisher, jurisdiction, category, and source URL metadata during ingestion.", style),
        bullet("Introduce jurisdiction-aware filters or routing for state-specific questions.", style),
        bullet("Add chunk-level relevance judgments for ambiguous and form-based questions.", style),
        bullet("Track this suite after every corpus, embedding, chunking, or reranker change.", style),
        PageBreak(),
        Paragraph("Retrieved-source detail", style["h1"]),
        Paragraph("The first five unique source documents returned for each evaluation question.", style["body"]),
    ]

    for item in results:
        if item["id"] in {"Q06", "Q13"}:
            story.append(PageBreak())
            if item["id"] == "Q13":
                story.append(Spacer(1, 0.32 * inch))
        rows = []
        for rank, source in enumerate(item["ranking"][:5], start=1):
            score = f"{source['score']:.3f}" if source["score"] is not None else "n/a"
            rows.append([
                Paragraph(str(rank), style["table"]),
                Paragraph(safe(source["source"]), style["table"]),
                Paragraph(f"Page {safe(source['page'])}", style["table"]),
                Paragraph(score, style["table"]),
            ])
        detail = Table(rows, colWidths=[0.3 * inch, 4.65 * inch, 0.75 * inch, 0.6 * inch])
        detail.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PALE),
            ("GRID", (0, 0), (-1, -1), 0.35, LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(KeepTogether([
            Paragraph(f"{item['id']} / {safe(item['question'])}", style["h2"]),
            detail,
            Spacer(1, 0.08 * inch),
        ]))

    doc = EvaluationDocTemplate(str(OUTPUT))
    doc.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    build()
