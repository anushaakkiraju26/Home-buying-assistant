import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from hybrid_retriever import hybrid_retrieve


load_dotenv()

st.set_page_config(
    page_title="Haven — Home Buying Assistant",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)


def source_name(path: str) -> str:
    return Path(path).stem.replace("_", " ").replace("-", " ").title()


def format_context(documents) -> str:
    return "\n\n---\n\n".join(
        f"[Source {number}: {document.metadata.get('source', 'unknown')}, "
        f"page {document.metadata.get('page', 'unknown')}]\n{document.page_content}"
        for number, document in enumerate(documents, start=1)
    )


@st.cache_resource
def answer_model() -> ChatAnthropic:
    return ChatAnthropic(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        temperature=0,
    )


def answer_question(question: str) -> tuple[str, list]:
    documents = hybrid_retrieve(question, k=20, rerank_top_n=5)
    if not documents:
        return (
            "I couldn't find enough information in the reference library "
            "to answer that question.",
            [],
        )

    prompt = f"""
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

{format_context(documents)}
""".strip()

    response = answer_model().invoke(
        [SystemMessage(content=prompt), HumanMessage(content=question)]
    )
    content = response.content
    if isinstance(content, list):
        content = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return str(content), documents


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700&display=swap');
:root { --ink:#18332e; --cream:#f7f4ed; --green:#245c50; --coral:#df7358; }
.stApp { background:var(--cream); color:var(--ink); font-family:'DM Sans',sans-serif; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background:var(--cream) !important; }
footer, [data-testid="stStatusWidget"], #MainMenu { display:none !important; }
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"],
[data-testid="stChatInputContainer"] { background:var(--cream) !important; }
[data-testid="stBottomBlockContainer"] { border-top:0 !important; box-shadow:none !important; }
.stApp, .stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2,
.stApp h3, .stApp h4, .stApp h5, .stApp h6,
.stApp [data-testid="stMarkdownContainer"] { color:var(--ink); }
[data-testid="stSidebar"] { background:#153e35; border:0; }
[data-testid="stSidebar"], [data-testid="stSidebar"] p,
[data-testid="stSidebar"] li, [data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color:#f5f3ec !important; }
[data-testid="stSidebar"] hr { border-color:rgba(255,255,255,.14); }
.block-container { max-width:900px; padding-top:3.25rem; padding-bottom:7rem; }
.brand { font:700 1.45rem 'Manrope'; letter-spacing:-.03em; margin:.35rem 0 2rem; }
.brand span { color:#f4a27d; }
.eyebrow { font-size:.68rem; letter-spacing:.19em; font-weight:700; color:#7f918c; margin-bottom:1rem; }
.hero { font:600 clamp(2.6rem,6vw,4.2rem)/1.08 'Manrope'; letter-spacing:-.05em; margin:0 0 1.25rem; color:var(--ink); }
.hero em { font-family:Georgia,serif; font-weight:400; color:var(--coral); }
.subhead { max-width:670px; color:#697b76; line-height:1.7; font-size:1.02rem; margin-bottom:2rem; }
.trust { display:inline-flex; gap:.45rem; align-items:center; border:1px solid #d5dfda; border-radius:99px; padding:.35rem .7rem; font-size:.7rem; color:#557269; background:#fbfaf6; }
.trust i { width:6px; height:6px; border-radius:50%; background:#5da879; }
[data-testid="stChatMessage"] { background:transparent; padding:1rem 0; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li { color:#203d36 !important; line-height:1.72; }
[data-testid="stChatInput"], [data-testid="stChatInput"] > div,
[data-testid="stChatInput"] div:has(textarea) {
  background:#fffdf8 !important;
  color:#18332e !important;
}
[data-testid="stChatInput"] { border:1px solid #cbd5ce !important; border-radius:16px; box-shadow:0 10px 32px rgba(31,55,49,.1); overflow:hidden; }
[data-testid="stChatInput"]:focus-within { border-color:#648e82 !important; box-shadow:0 0 0 3px rgba(36,92,80,.1),0 10px 32px rgba(31,55,49,.1); }
[data-testid="stChatInput"] textarea {
  background:#fffdf8 !important;
  color:#18332e !important;
  -webkit-text-fill-color:#18332e !important;
  caret-color:#18332e !important;
  opacity:1 !important;
}
[data-testid="stChatInput"] textarea::placeholder { color:#71817c !important; opacity:1; }
[data-testid="stChatInput"] button { background:#245c50 !important; color:#ffffff !important; border-radius:10px !important; }
[data-testid="stChatInput"] button svg { fill:#ffffff !important; color:#ffffff !important; }
.source-meta { font-size:.72rem; color:#71827d; margin-bottom:.4rem; }
.source-text { color:#536762; font-size:.83rem; line-height:1.55; }
.fine-print { color:#8b9995; font-size:.68rem; text-align:center; margin-top:.8rem; }
.sidebar-note { color:#9cb2ac !important; font-size:.75rem; line-height:1.5; }
div[data-testid="stButton"] button { border-radius:11px; border:1px solid #dce1db; min-height:3.5rem; text-align:left; background:#fffdf8; color:#23443c; }
div[data-testid="stButton"] button p { color:#23443c !important; }
div[data-testid="stButton"] button:hover { border-color:#779c91; color:#153e35; transform:translateY(-1px); }
[data-testid="stSidebar"] div[data-testid="stButton"] button { background:rgba(255,255,255,.08); border-color:rgba(255,255,255,.2); color:white; min-height:2.7rem; }
[data-testid="stSidebar"] div[data-testid="stButton"] button p { color:white !important; }
[data-testid="stExpander"] { background:#fffdf8; border-color:#d9ded7; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p { color:#203d36 !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color:#61736e !important; }
[data-testid="stAlert"] p { color:inherit !important; }
</style>
""",
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown('<div class="brand">⌂ <span>haven</span></div>', unsafe_allow_html=True)
    if st.button("＋  New conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("#### Your conversations")
    if st.session_state.messages:
        for message in [m for m in st.session_state.messages if m["role"] == "user"][-6:][::-1]:
            st.caption("• " + message["content"][:54])
    else:
        st.markdown('<p class="sidebar-note">Your questions will appear here during this session.</p>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**● Reference library**")
    st.markdown('<p class="sidebar-note">Government guides, regulations, and trusted industry resources are ready.</p>', unsafe_allow_html=True)

st.markdown('<div class="trust"><i></i> SOURCE-GROUNDED</div>', unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown('<div class="eyebrow">YOUR HOME BUYING GUIDE</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="hero">Big decisions deserve<br><em>clear answers.</em></h1>', unsafe_allow_html=True)
    st.markdown('<p class="subhead">Ask about mortgages, inspections, disclosures, closing costs, and more. Haven searches trusted home-buying resources before it answers.</p>', unsafe_allow_html=True)

    suggestions = [
        ("🔎 Inspections", "What should I look for during a home inspection?"),
        ("📈 Mortgages", "How do I compare fixed-rate and adjustable-rate mortgages?"),
        ("◇ Closing", "What costs should I expect at closing?"),
        ("📄 Disclosures", "What does a seller have to disclose about a home?"),
    ]
    columns = st.columns(2)
    selected = None
    for index, (label, question) in enumerate(suggestions):
        with columns[index % 2]:
            if st.button(f"{label}\n\n{question}", key=f"suggestion-{index}", use_container_width=True):
                selected = question
else:
    selected = None

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🏡" if message["role"] == "assistant" else None):
        st.markdown(message["content"])
        if message.get("documents"):
            with st.expander(f"Sources used · {len(message['documents'])}"):
                for number, document in enumerate(message["documents"], start=1):
                    source = document.metadata.get("source", "Reference source")
                    page = document.metadata.get("page", "unknown")
                    st.markdown(f"**[{number}] {source_name(str(source))}** · Page {page}")
                    st.caption(document.page_content[:700] + ("…" if len(document.page_content) > 700 else ""))
                    if number != len(message["documents"]):
                        st.divider()

question = st.chat_input("Ask a home-buying question…")
question = selected or question

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant", avatar="🏡"):
        try:
            with st.spinner("Searching the reference library…"):
                answer, documents = answer_question(question)
            st.markdown(answer)
            if documents:
                with st.expander(f"Sources used · {len(documents)}"):
                    for number, document in enumerate(documents, start=1):
                        source = document.metadata.get("source", "Reference source")
                        page = document.metadata.get("page", "unknown")
                        st.markdown(f"**[{number}] {source_name(str(source))}** · Page {page}")
                        st.caption(document.page_content[:700] + ("…" if len(document.page_content) > 700 else ""))
                        if number != len(documents):
                            st.divider()
            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "documents": documents}
            )
        except Exception as error:
            st.error("I couldn't complete that answer. Check your API configuration and try again.")
            st.caption(str(error))

st.markdown('<p class="fine-print">Haven provides general educational information, not legal or financial advice.</p>', unsafe_allow_html=True)
