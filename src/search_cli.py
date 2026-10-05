"""命令行检索：输入问题，返回 Top-K 块。默认查 current，加 --archive 查旧版。"""
from __future__ import annotations

import argparse

from .embeddings import DEFAULT_MODEL, Embedder
from .vectorstore import ARCHIVE_COLLECTION, CURRENT_COLLECTION, VectorStore
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PERSIST = ROOT / "data" / "vectorstore" / "chroma"


def main() -> None:
    parser = argparse.ArgumentParser(description="SOP 向量检索 CLI")
    parser.add_argument("query", help="检索问题（建议与文档语言一致）")
    parser.add_argument("-k", type=int, default=5, help="返回条数，默认 5")
    parser.add_argument("--archive", action="store_true", help="检索旧版本归档集合")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    collection_name = ARCHIVE_COLLECTION if args.archive else CURRENT_COLLECTION
    embedder = Embedder(args.model)
    query_vector = embedder.encode([args.query])[0]

    store = VectorStore(PERSIST)
    result = store.search(collection_name, query_vector, k=args.k)

    print("=" * 70)
    print(f"查询: {args.query}")
    print(f"集合: {collection_name}")
    print("=" * 70)
    ids = result["ids"][0]
    distances = result["distances"][0]
    metas = result["metadatas"][0]
    documents = result["documents"][0]
    for rank, (cid, distance, meta, doc) in enumerate(
        zip(ids, distances, metas, documents), start=1
    ):
        score = 1 - distance  # cosine 相似度
        preview = doc.replace("\n", " ")[:160]
        print(f"\n[{rank}] score={score:.3f}")
        print(f"    title : {meta['title']}")
        print(f"    version/status: {meta['version']} / {meta['status']}")
        print(f"    section/page: {meta['section']} / p.{meta['page']}")
        print(f"    source: {meta['source_url']}")
        print(f"    preview: {preview}")


if __name__ == "__main__":
    main()