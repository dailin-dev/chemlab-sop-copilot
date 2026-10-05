"""BGE Embedding：本地 sentence-transformers，输出归一化向量（配合 cosine）。"""
from __future__ import annotations

DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"


class Embedder:
    def __init__(self, model_name: str = DEFAULT_MODEL, device: str | None = None) -> None:
        from sentence_transformers import SentenceTransformer

        self.name = model_name
        self.model = SentenceTransformer(model_name, device=device)

    def encode(self, texts: list[str], batch_size: int = 32, show_progress: bool = False):
        return self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )