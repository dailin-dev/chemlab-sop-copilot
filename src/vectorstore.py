"""Chroma 向量库：current 主集合 + superseded 归档集合，cosine 空间，可重建。"""
from __future__ import annotations

import pathlib

import chromadb

CURRENT_COLLECTION = "sop_current"
ARCHIVE_COLLECTION = "sop_archive"
_CHROMA_META_KEYS = [
    "doc_id", "title", "version", "status", "instrument_type",
    "category", "source_url", "file_path", "section", "page",
]


def meta_for_chroma(chunk: dict) -> dict:
    out = {}
    for key in _CHROMA_META_KEYS:
        value = chunk.get(key, "")
        out[key] = "" if value is None else str(value)
    return out


class VectorStore:
    def __init__(self, persist_dir: str | pathlib.Path) -> None:
        path = pathlib.Path(persist_dir)
        path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(path))

    def reset(self) -> None:
        for name in (CURRENT_COLLECTION, ARCHIVE_COLLECTION):
            try:
                self.client.delete_collection(name)
            except Exception:
                pass

    def _collection(self, name: str):
        return self.client.get_or_create_collection(
            name, metadata={"hnsw:space": "cosine"}
        )

    def add(self, name: str, chunks: list[dict], vectors) -> None:
        if not chunks:
            return
        collection = self._collection(name)
        collection.add(
            ids=[c["chunk_id"] for c in chunks],
            embeddings=[vectors[c["chunk_id"]] for c in chunks],
            documents=[c["text"] for c in chunks],
            metadatas=[meta_for_chroma(c) for c in chunks],
        )

    def search(self, name: str, query_vector, k: int = 5) -> dict:
        return self.client.get_collection(name).query(
            query_embeddings=[query_vector], n_results=k
        )