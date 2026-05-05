import streamlit as st
import os
import time
from dotenv import load_dotenv
from rag_engine import RAGEngine

# Load .env automatically if it exists
load_dotenv()

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NotesMind · AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Root variables ── */
:root {
    --bg-primary:   #f5f7fb;
    --bg-secondary: #0f172a;
    --bg-card:      #ffffff;
    --accent:       #0f766e;
    --accent-2:     #f59e0b;
    --accent-dim:   rgba(15,118,110,0.10);
    --accent-glow:  rgba(15,118,110,0.20);
    --text-primary: #111827;
    --text-muted:   #64748b;
    --border:       #dbe3ef;
    --user-bubble:  #1e3a5f;
    --ai-bubble:    #ffffff;
    --success:      #059669;
    --error:        #dc2626;
}

/* ── Global reset ── */
html, body, .stApp, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

.stApp {
    background:
        radial-gradient(circle at 20% 0%, rgba(15,118,110,0.10), transparent 28rem),
        linear-gradient(180deg, #f8fafc 0%, #eef3f8 100%) !important;
}

p, div, span, label { color: inherit; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid rgba(255,255,255,0.10) !important;
}
[data-testid="stSidebar"] > div { padding: 1.5rem 1.2rem !important; }

/* ── Brand header ── */
.brand {
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 2rem;
}
.brand-icon {
    width: 38px; height: 38px; border-radius: 10px;
    background: linear-gradient(135deg, var(--accent), #14b8a6);
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; box-shadow: 0 0 18px var(--accent-glow);
}
.brand-name {
    font-family: 'Playfair Display', serif;
    font-size: 1.35rem; font-weight: 700;
    background: linear-gradient(135deg, #5eead4, #fbbf24);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.brand-tag { font-size: 0.68rem; color: #cbd5e1; letter-spacing: 1.5px; text-transform: uppercase; }

/* ── Section labels ── */
.sidebar-label {
    font-size: 0.7rem; letter-spacing: 1.8px; text-transform: uppercase;
    color: #cbd5e1; margin: 1.4rem 0 0.5rem;
    display: flex; align-items: center; gap: 6px;
}
.sidebar-label::after {
    content: ''; flex: 1; height: 1px; background: rgba(255,255,255,0.12);
}

/* ── Upload zone ── */
[data-testid="stFileUploader"] {
    border: 2px dashed rgba(15,118,110,0.35) !important;
    border-radius: 14px !important;
    background: var(--accent-dim) !important;
    transition: border-color 0.3s !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent) !important;
}
[data-testid="stFileUploader"] label { color: var(--text-muted) !important; }
[data-testid="stFileUploader"] section {
    background: #ffffff !important;
    border-radius: 12px !important;
    min-height: 92px !important;
}
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p {
    color: #334155 !important;
}
[data-testid="stTextInput"] input {
    background: #ffffff !important;
    color: var(--text-primary) !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 10px !important;
}
[data-testid="stTextInput"] input::placeholder {
    color: #64748b !important;
    opacity: 1 !important;
}

/* ── Buttons ── */
.stButton > button {
    width: 100%; border: none !important;
    background: linear-gradient(135deg, var(--accent), #14b8a6) !important;
    color: #ffffff !important; font-weight: 700 !important;
    font-size: 0.88rem !important; border-radius: 10px !important;
    padding: 0.55rem 1rem !important;
    box-shadow: 0 4px 20px var(--accent-glow) !important;
    transition: all 0.25s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 28px var(--accent-glow) !important;
}

/* ── Doc card ── */
.doc-card {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    display: flex; align-items: center; gap: 10px;
    animation: slideIn 0.3s ease;
}
.doc-card-icon { font-size: 1.1rem; }
.doc-card-info { flex: 1; }
.doc-card-name { font-size: 0.82rem; font-weight: 500; color: #e5eefb; }
.doc-card-meta { font-size: 0.7rem; color: #94a3b8; margin-top: 2px; }
.doc-status { font-size: 0.7rem; color: var(--success); font-weight: 600; }

/* ── Main chat area ── */
.chat-header {
    background: rgba(255,255,255,0.88);
    border-bottom: 1px solid var(--border);
    padding: 1.1rem 2rem;
    display: flex; align-items: center; justify-content: space-between;
    position: sticky; top: 0; z-index: 99;
    backdrop-filter: blur(12px);
}
.chat-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem; font-weight: 700;
    color: var(--text-primary);
}
.chat-subtitle { font-size: 0.75rem; color: var(--text-muted); }

/* ── Welcome screen ── */
.welcome-wrap {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    min-height: 44vh; text-align: center; gap: 1.2rem;
    padding: 3rem 3rem 1.5rem;
}
.welcome-icon {
    font-size: 4rem;
    animation: pulse 2s ease-in-out infinite;
}
.welcome-title {
    font-family: 'Playfair Display', serif;
    font-size: 2rem; font-weight: 700;
    background: linear-gradient(135deg, #0f766e, #2563eb);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.welcome-sub { color: var(--text-muted); font-size: 0.95rem; max-width: 420px; line-height: 1.7; }

/* ── Suggestion chips ── */
.chips { display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center; margin-top: 0.5rem; }
.chip {
    background: #ffffff; border: 1px solid var(--border);
    border-radius: 999px; padding: 0.4rem 1rem;
    font-size: 0.78rem; color: #334155; cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 8px 24px rgba(15,23,42,0.06);
}
.chip:hover { border-color: var(--accent); color: var(--accent); }

/* ── Messages ── */
.msg-wrap { padding: 1.25rem 2rem 7rem; }
.msg-row { display: flex; gap: 12px; margin-bottom: 1.4rem; animation: fadeUp 0.3s ease; }
.msg-row.user { flex-direction: row-reverse; }

.avatar {
    width: 34px; height: 34px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
}
.avatar.ai { background: linear-gradient(135deg, var(--accent), #14b8a6); color: #ffffff; }
.avatar.user { background: var(--user-bubble); border: 1px solid rgba(255,255,255,0.18); color: #ffffff; }

.bubble {
    max-width: 72%; padding: 0.9rem 1.2rem;
    border-radius: 14px; line-height: 1.7; font-size: 0.9rem;
    box-shadow: 0 14px 34px rgba(15,23,42,0.08);
    color: var(--text-primary);
}
.bubble.ai { background: var(--ai-bubble); border: 1px solid var(--border); border-top-left-radius: 4px; }
.bubble.user { background: var(--user-bubble); border: 1px solid rgba(30,58,95,0.15); border-top-right-radius: 4px; color: #ffffff; }
.bubble.user * { color: #ffffff !important; }
.bubble.ai * { color: var(--text-primary); }

.bubble-meta { font-size: 0.68rem; color: var(--text-muted); margin-top: 0.4rem; }
.sources { margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid var(--border); }
.sources-label { font-size: 0.7rem; color: #475569; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 0.4rem; }
.source-tag {
    display: inline-block; background: #ecfdf5;
    border: 1px solid rgba(15,118,110,0.25);
    border-radius: 6px; padding: 0.2rem 0.6rem;
    font-size: 0.72rem; color: var(--accent);
    margin-right: 0.4rem; margin-bottom: 0.3rem;
}

/* ── Input bar ── */
.input-bar {
    position: sticky; bottom: 0;
    background: rgba(245,247,251,0.92);
    border-top: 1px solid var(--border);
    padding: 1rem 2rem 1.25rem;
    backdrop-filter: blur(14px);
}
[data-testid="stChatInput"] textarea {
    background: #ffffff !important;
    color: var(--text-primary) !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
    box-shadow: 0 10px 26px rgba(15,23,42,0.08) !important;
}
[data-testid="stChatInput"] {
    background: transparent !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: rgba(15,118,110,0.65) !important;
    box-shadow: 0 0 0 3px rgba(15,118,110,0.14), 0 10px 26px rgba(15,23,42,0.08) !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #64748b !important; opacity: 1 !important; }
[data-testid="stChatInput"] button {
    background: var(--accent) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
}

/* ── Progress / spinner ── */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* ── Stat badge ── */
.stat-row { display: flex; gap: 0.5rem; margin-top: 0.8rem; }
.stat-badge {
    flex: 1; background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 10px; padding: 0.6rem 0.8rem; text-align: center;
}
.stat-num { font-size: 1.1rem; font-weight: 700; color: var(--accent); }
.stat-lbl { font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; }

.sidebar-footer {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255,255,255,0.10);
    text-align: center;
    font-size: 0.68rem;
    color: #94a3b8;
}

/* ── Animations ── */
@keyframes pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.06); } }
@keyframes fadeUp { from { opacity:0; transform: translateY(10px); } to { opacity:1; transform: translateY(0); } }
@keyframes slideIn { from { opacity:0; transform: translateX(-8px); } to { opacity:1; transform: translateX(0); } }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "rag" not in st.session_state:
    st.session_state.rag = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []
if "api_key_set" not in st.session_state:
    st.session_state.api_key_set = False

api_key = st.secrets.get("COHERE_API_KEY", "").strip()
st.session_state.api_key_set = bool(api_key)


def process_uploaded_pdfs(uploaded_files, api_key: str):
    """Build the RAG index from uploaded PDFs and update app state."""
    engine = RAGEngine(api_key=api_key)
    doc_info = engine.load_pdfs(uploaded_files)
    st.session_state.rag = engine
    st.session_state.uploaded_docs = doc_info
    st.session_state.messages = []
    st.session_state.api_key_set = bool(api_key)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="brand">
        <div class="brand-icon">🧠</div>
        <div>
            <div class="brand-name">NotesMind</div>
            <div class="brand-tag">Powered by Cohere</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.api_key_set:
        st.warning("Server API key is not configured. Add COHERE_API_KEY to .env.")

    # Upload
    st.markdown('<div class="sidebar-label">📄 Upload PDFs</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Drop PDFs here",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="Only PDF files are supported right now.",
    )

    if uploaded_files and st.session_state.api_key_set:
        if st.button("⚡ Process & Index PDFs"):
            with st.spinner("Extracting & embedding…"):
                try:
                    process_uploaded_pdfs(uploaded_files, api_key)
                    st.success(f"✅ {len(uploaded_files)} doc(s) indexed!")
                except Exception as e:
                    st.error(f"Error: {e}")
    elif uploaded_files and not st.session_state.api_key_set:
        st.warning("Server API key is not configured.")

    # Indexed docs
    if st.session_state.uploaded_docs:
        st.markdown('<div class="sidebar-label">📚 Indexed Documents</div>', unsafe_allow_html=True)
        total_chunks = sum(d["chunks"] for d in st.session_state.uploaded_docs)
        total_pages  = sum(d["pages"]  for d in st.session_state.uploaded_docs)

        for doc in st.session_state.uploaded_docs:
            st.markdown(f"""
            <div class="doc-card">
                <div class="doc-card-icon">📄</div>
                <div class="doc-card-info">
                    <div class="doc-card-name">{doc['name']}</div>
                    <div class="doc-card-meta">{doc['pages']} pages · {doc['chunks']} chunks</div>
                </div>
                <div class="doc-status">✓</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="stat-row">
            <div class="stat-badge"><div class="stat-num">{len(st.session_state.uploaded_docs)}</div><div class="stat-lbl">Docs</div></div>
            <div class="stat-badge"><div class="stat-num">{total_pages}</div><div class="stat-lbl">Pages</div></div>
            <div class="stat-badge"><div class="stat-num">{total_chunks}</div><div class="stat-lbl">Chunks</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="margin-top:1.5rem;"></div>', unsafe_allow_html=True)
        if st.button("🗑️ Clear All"):
            st.session_state.rag = None
            st.session_state.messages = []
            st.session_state.uploaded_docs = []
            st.rerun()

    # Footer
    st.markdown("""
    <div class="sidebar-footer">
        RAG · FAISS · Cohere<br>
        <span style="color:rgba(20,184,166,0.75);">● Cohere API</span>
    </div>
    """, unsafe_allow_html=True)

# ── Main content ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="chat-header">
    <div>
        <div class="chat-title">Chat with Your Notes</div>
        <div class="chat-subtitle">Ask anything — get answers grounded in your documents</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Welcome screen
if not st.session_state.uploaded_docs:
    st.markdown("""
    <div class="welcome-wrap">
        <div class="welcome-icon">🧠</div>
        <div class="welcome-title">Your Notes, Supercharged</div>
        <div class="welcome-sub">
            Upload your PDFs below and start asking questions.<br>
            NotesMind extracts, indexes, and reasons over your documents instantly.
        </div>
        <div class="chips">
            <div class="chip">📖 Study notes</div>
            <div class="chip">📑 Research papers</div>
            <div class="chip">📘 Textbooks</div>
            <div class="chip">📋 Reports</div>
            <div class="chip">🗒️ Lecture slides</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, upload_col, _ = st.columns([1, 1.25, 1])
    with upload_col:
        main_uploaded_files = st.file_uploader(
            "Upload your notes",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload one or more PDF notes.",
            key="main_pdf_uploader",
        )

        if main_uploaded_files:
            if api_key:
                if st.button("Process & Index PDFs", key="main_process_pdfs"):
                    with st.spinner("Extracting & embedding..."):
                        try:
                            process_uploaded_pdfs(main_uploaded_files, api_key)
                            st.success(f"{len(main_uploaded_files)} doc(s) indexed!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.warning("Server API key is not configured.")

else:
    # Chat messages
    st.markdown('<div class="msg-wrap">', unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown(f"""
        <div class="msg-row">
            <div class="avatar ai">🧠</div>
            <div>
                <div class="bubble ai">
                    Hey! I've indexed <strong>{len(st.session_state.uploaded_docs)} document(s)</strong> for you.
                    Ask me anything about your notes — I'll find the most relevant sections and explain them clearly. 🎯
                </div>
                <div class="bubble-meta">NotesMind · just now</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.messages:
        ts = msg.get("time", "")
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="msg-row user">
                <div class="avatar user">👤</div>
                <div>
                    <div class="bubble user">{msg["content"]}</div>
                    <div class="bubble-meta" style="text-align:right;">{ts}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            sources_html = ""
            if msg.get("sources"):
                tags = "".join(f'<span class="source-tag">📄 {s}</span>' for s in msg["sources"])
                sources_html = f'<div class="sources"><div class="sources-label">Sources</div>{tags}</div>'

            st.markdown(f"""
            <div class="msg-row">
                <div class="avatar ai">🧠</div>
                <div>
                    <div class="bubble ai">
                        {msg["content"]}
                        {sources_html}
                    </div>
                    <div class="bubble-meta">{ts}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Input
    st.markdown('<div class="input-bar">', unsafe_allow_html=True)
    prompt = st.chat_input("Ask anything about your notes…")
    st.markdown('</div>', unsafe_allow_html=True)

    if prompt:
        ts = time.strftime("%I:%M %p")
        st.session_state.messages.append({"role": "user", "content": prompt, "time": ts})

        with st.spinner("Thinking…"):
            try:
                answer, sources = st.session_state.rag.query(prompt)
            except Exception as e:
                answer  = f"⚠️ Error: {e}"
                sources = []

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "time": time.strftime("%I:%M %p"),
        })
        st.rerun()
