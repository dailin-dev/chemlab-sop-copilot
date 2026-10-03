"""向量检索封装。"""
from __future__ import annotations

import os
import pathlib

from .embeddings import Embedder
from .vectorstore import CURRENT_COLLECTION, VectorStore

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_PERSIST = ROOT / "data" / "vectorstore" / "chroma"
PERSIST = pathlib.Path(os.getenv("CHEMLAB_PERSIST_DIR", str(DEFAULT_PERSIST)))


class Retriever:
    def __init__(self) -> None:
        self.embedder = Embedder()
        self.store = VectorStore(PERSIST)

    def search(self, query: str, k: int = 5, collection: str = CURRENT_COLLECTION):
        query_vector = self.embedder.encode([query])[0]
        raw = self.store.search(collection, query_vector, k)
        hits = []
        for cid, distance, meta, document in zip(
            raw["ids"][0],
            raw["distances"][0],
            raw["metadatas"][0],
            raw["documents"][0],
        ):
            hit = dict(meta)
            hit["chunk_id"] = cid
            hit["score"] = round(1 - float(distance), 4)
            hit["text"] = document
            hits.append(hit)
        return hits