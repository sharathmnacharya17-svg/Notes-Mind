import re
import numpy as np
import requests
import faiss
import pdfplumber
from io import BytesIO


class RAGEngine:
    """RAG pipeline: PDF -> chunks -> Cohere embeddings -> FAISS -> Cohere chat."""

    API_BASE = "https://api.cohere.com/v2"
    EMBED_MODEL = "embed-v4.0"
    CHAT_MODEL  = "command-a-03-2025"
    CHUNK_SIZE  = 600    # characters
    CHUNK_OVERLAP = 100
    TOP_K       = 5

    def __init__(self, api_key: str):
        self.api_key     = api_key
        self.index       = None
        self.chunks      = []   # list of {"text": ..., "source": ..., "page": ...}

    # ── PDF processing ────────────────────────────────────────────────────────

    def load_pdfs(self, uploaded_files) -> list[dict]:
        """Extract text from uploaded PDFs, chunk, embed, and index."""
        all_chunks = []
        doc_info   = []

        for uf in uploaded_files:
            uf.seek(0)
            raw_bytes = uf.read()
            pages_text, n_pages = self._extract_pdf(raw_bytes, uf.name)
            doc_chunks = self._chunk_text(pages_text, source=uf.name)
            all_chunks.extend(doc_chunks)
            doc_info.append({
                "name":   uf.name,
                "pages":  n_pages,
                "chunks": len(doc_chunks),
            })

        if not all_chunks:
            raise ValueError("No text could be extracted from the uploaded PDFs.")

        self.chunks = all_chunks
        self._build_index(all_chunks)
        return doc_info

    def _extract_pdf(self, raw_bytes: bytes, name: str):
        """Return (list of page texts, page count) using pdfplumber."""
        pages_text = []
        with pdfplumber.open(BytesIO(raw_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                pages_text.append(text)
        return pages_text, len(pages_text)

    def _chunk_text(self, pages: list[str], source: str) -> list[dict]:
        """Split each page into overlapping chunks."""
        chunks = []
        for page_no, text in enumerate(pages, start=1):
            text = self._clean(text)
            if not text.strip():
                continue
            start = 0
            while start < len(text):
                end   = start + self.CHUNK_SIZE
                chunk = text[start:end].strip()
                if chunk:
                    chunks.append({
                        "text":   chunk,
                        "source": source,
                        "page":   page_no,
                    })
                start += self.CHUNK_SIZE - self.CHUNK_OVERLAP
        return chunks

    @staticmethod
    def _clean(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # ── Embedding & index ─────────────────────────────────────────────────────

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _post_json(self, path: str, payload: dict) -> dict:
        response = requests.post(
            f"{self.API_BASE}{path}",
            headers=self._headers(),
            json=payload,
            timeout=90,
        )
        if response.ok:
            return response.json()

        try:
            error = response.json()
            message = error.get("message") or error.get("error") or error
        except ValueError:
            message = response.text
        raise RuntimeError(f"Cohere API error {response.status_code}: {message}")

    def _embed(self, texts: list[str], input_type="search_document") -> np.ndarray:
        """Batch embed texts with Cohere Embed v4."""
        vectors = []
        BATCH = 96  # Cohere Embed v2 maximum texts per call
        for i in range(0, len(texts), BATCH):
            batch = texts[i : i + BATCH]
            result = self._post_json(
                "/embed",
                {
                    "model": self.EMBED_MODEL,
                    "texts": batch,
                    "input_type": input_type,
                    "embedding_types": ["float"],
                },
            )
            vectors.extend(result["embeddings"]["float"])
        return np.array(vectors, dtype="float32")

    def _build_index(self, chunks: list[dict]):
        texts = [c["text"] for c in chunks]
        vecs  = self._embed(texts, input_type="search_document")
        dim   = vecs.shape[1]
        # Normalize for cosine similarity
        faiss.normalize_L2(vecs)
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(vecs)

    # ── Query ─────────────────────────────────────────────────────────────────

    def query(self, question: str) -> tuple[str, list[str]]:
        """Retrieve relevant chunks and generate an answer."""
        if self.index is None:
            raise RuntimeError("No documents indexed yet.")

        # Embed query
        q_vec = self._embed([question], input_type="search_query")
        faiss.normalize_L2(q_vec)
        _, indices = self.index.search(q_vec, self.TOP_K)

        retrieved = [self.chunks[i] for i in indices[0] if i < len(self.chunks)]
        context   = "\n\n---\n\n".join(
            f"[Source: {c['source']} | Page {c['page']}]\n{c['text']}"
            for c in retrieved
        )
        sources = list({c["source"] for c in retrieved})

        # Build prompt
        prompt = f"""You are NotesMind, an intelligent study assistant.
Answer the user's question using ONLY the context below.
If the answer is not in the context, say so honestly.
Be clear, concise, and structured. Use markdown formatting when helpful.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

        result = self._post_json(
            "/chat",
            {
                "model": self.CHAT_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are NotesMind, a concise study assistant.",
                    },
                    {"role": "user", "content": prompt},
                ],
            },
        )
        answer = result["message"]["content"][0]["text"]
        return answer, sources
