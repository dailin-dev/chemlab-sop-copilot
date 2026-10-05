"""阶段 B：读 chunks.jsonl -> BGE 向量化 -> 写 Chroma（current/归档分集合）。可重复运行。"""
from __future__ import annotations

import json
import pathlib

from .embeddings import DEFAULT_MODEL, Embedder
from .vectorstore import ARCHIVE_COLLECTION, CURRENT_COLLECTION, VectorStore

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "data" / "processed" / "chunks.jsonl"
PERSIST = ROOT / "data" / "vectorstore" / "chroma"


def load_chunks() -> list[dict]:
    with open(CHUNKS, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main(model_name: str = DEFAULT_MODEL) -> None:
    chunks = load_chunks()
    if not chunks:
        raise SystemExit("chunks.jsonl 为空，请先运行 python -m src.run_chunking")

    embedder = Embedder(model_name)
    vectors = embedder.encode([c["text"] for c in chunks], show_progress=True)
    vector_by_id = {c["chunk_id"]: vectors[i] for i, c in enumerate(chunks)}

    store = VectorStore(PERSIST)
    store.reset()  # 先删后建，保证可重复运行、不产生脏数据

    current = [c for c in chunks if c["status"] == "current"]
    archived = [c for c in chunks if c["status"] != "current"]
    store.add(CURRENT_COLLECTION, current, vector_by_id)
    store.add(ARCHIVE_COLLECTION, archived, vector_by_id)

    print("=" * 60)
    print(f"模型: {embedder.name}")
    print(f"主集合 {CURRENT_COLLECTION}: {len(current)} 条（仅现行版本）")
    print(f"归档集合 {ARCHIVE_COLLECTION}: {len(archived)} 条（旧版本）")
    print("Chroma 已持久化:", PERSIST.relative_to(ROOT))


if __name__ == "__main__":
    main()