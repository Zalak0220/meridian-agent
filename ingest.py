"""
ingest.py

Builds the local vector store from the document corpus in ./docs.

This is a hand-rolled retrieval pipeline (per the assignment's restriction
against LlamaIndex / LangChain pre-built RAG chains):
  1. Read each .txt file in docs/
  2. Chunk it ourselves with a simple sliding-window splitter
  3. Embed chunks locally with sentence-transformers
  4. Upsert into a persistent ChromaDB collection on disk

Run once (or any time docs/ changes):
    python ingest.py
"""
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

from src import config


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Simple character-based sliding-window chunker with overlap.
    Splits on paragraph boundaries where possible to keep chunks coherent.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}".strip()
        else:
            if current:
                chunks.append(current)
            # start new chunk, carrying overlap from the tail of the previous one
            overlap_text = current[-overlap:] if current else ""
            current = f"{overlap_text}\n\n{para}".strip()
    if current:
        chunks.append(current)

    # Fallback: if a single paragraph is longer than chunk_size, hard-split it
    final_chunks = []
    for c in chunks:
        if len(c) <= chunk_size * 1.3:
            final_chunks.append(c)
        else:
            for i in range(0, len(c), chunk_size - overlap):
                final_chunks.append(c[i:i + chunk_size])
    return final_chunks


def build_index():
    print(f"Loading embedding model '{config.EMBED_MODEL_NAME}' locally...")
    embedder = SentenceTransformer(config.EMBED_MODEL_NAME)

    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    # Fresh build each run so re-ingesting doesn't create duplicates.
    try:
        client.delete_collection(config.CHROMA_COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(
        name=config.CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    doc_files = sorted(Path(config.DOCS_DIR).glob("*.txt"))
    if not doc_files:
        raise RuntimeError(f"No .txt files found in {config.DOCS_DIR}")

    all_chunks, all_ids, all_metas = [], [], []
    for path in doc_files:
        text = path.read_text(encoding="utf-8")
        chunks = chunk_text(text, config.CHUNK_SIZE_CHARS, config.CHUNK_OVERLAP_CHARS)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"{path.stem}::chunk{i}")
            all_metas.append({"source": path.name, "chunk_index": i})
        print(f"  {path.name}: {len(chunks)} chunk(s)")

    print(f"Embedding {len(all_chunks)} chunks locally...")
    embeddings = embedder.encode(all_chunks, show_progress_bar=True).tolist()

    collection.add(
        ids=all_ids,
        embeddings=embeddings,
        documents=all_chunks,
        metadatas=all_metas,
    )
    print(f"Indexed {len(all_chunks)} chunks from {len(doc_files)} documents "
          f"into '{config.CHROMA_COLLECTION}' at {config.CHROMA_DIR}")


if __name__ == "__main__":
    build_index()
