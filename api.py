import os
from pathlib import Path
from typing import Any, Optional, Union

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from hybrid_retriever import hybrid_retrieve


app = FastAPI(
    title="Home Buying RAG API",
    version="1.0.0",
    description="Hybrid retrieval API for the home-buying reference library.",
)


class RetrieveRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    k: int = Field(default=20, ge=1, le=50)
    rerank_top_n: int = Field(default=5, ge=1, le=20)


class RetrievedDocument(BaseModel):
    content: str
    source: str
    page: Union[int, str]
    relevance_score: Optional[float] = None
    metadata: dict[str, Any]


class RetrieveResponse(BaseModel):
    question: str
    context: str
    documents: list[RetrievedDocument]


class AskResponse(BaseModel):
    question: str
    answer: str
    documents: list[RetrievedDocument]


def require_api_key(
    authorization: Optional[str] = Header(default=None),
) -> None:
    expected = os.getenv("RAG_SERVICE_API_KEY")
    if not expected:
        return

    if authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/retrieve",
    response_model=RetrieveResponse,
    dependencies=[Depends(require_api_key)],
)
def retrieve(request: RetrieveRequest) -> RetrieveResponse:
    documents = hybrid_retrieve(
        request.question,
        k=request.k,
        rerank_top_n=request.rerank_top_n,
    )

    results = []
    context_blocks = []

    for number, document in enumerate(documents, start=1):
        metadata = dict(document.metadata)
        source = str(metadata.get("source", "unknown"))
        page = metadata.get("page", "unknown")
        relevance = metadata.get("relevance_score")

        results.append(
            RetrievedDocument(
                content=document.page_content,
                source=source,
                page=page,
                relevance_score=(
                    float(relevance) if relevance is not None else None
                ),
                metadata=metadata,
            )
        )
        context_blocks.append(
            f"[Source {number}: {source}, page {page}]\n"
            f"{document.page_content}"
        )

    return RetrieveResponse(
        question=request.question,
        context="\n\n---\n\n".join(context_blocks),
        documents=results,
    )


@app.post(
    "/tool",
    response_class=PlainTextResponse,
    dependencies=[Depends(require_api_key)],
)
def retrieve_for_agent(request: RetrieveRequest) -> str:
    result = retrieve(request)
    if not result.context:
        return "No relevant documents were retrieved."
    return result.context


@app.post(
    "/ask",
    response_model=AskResponse,
    dependencies=[Depends(require_api_key)],
)
def ask(request: RetrieveRequest) -> AskResponse:
    """Retrieve evidence and generate a grounded, citation-ready answer."""
    result = retrieve(request)
    if not result.documents:
        return AskResponse(
            question=request.question,
            answer="I couldn't find enough information in the reference library to answer that question.",
            documents=[],
        )

    system_prompt = f"""
You are Haven, a calm and practical home-buying education assistant.
Answer using only the supplied context.

Rules:
- Lead with a direct, useful answer, then explain the important details.
- Cite factual claims inline using [Source N].
- Use short paragraphs and bullets where they improve clarity.
- Explain unfamiliar terms in plain language.
- If the context is insufficient, say exactly what is missing.
- Never present general information as legal, tax, or financial advice.

CONTEXT:

{result.context}
""".strip()

    try:
        response = ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            temperature=0,
        ).invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=request.question),
            ]
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="The answer service is temporarily unavailable. Please try again.",
        ) from exc

    answer_text = response.content
    if isinstance(answer_text, list):
        answer_text = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in answer_text
        )

    return AskResponse(
        question=request.question,
        answer=str(answer_text),
        documents=result.documents,
    )


UI_DIR = Path(__file__).parent / "ui"

if UI_DIR.exists():
    app.mount("/assets", StaticFiles(directory=UI_DIR), name="assets")

    @app.get("/", include_in_schema=False)
    def home() -> FileResponse:
        return FileResponse(UI_DIR / "index.html")
