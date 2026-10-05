"""阶段 A：读取元数据 -> 逐份 PDF 抽取/清洗/切块 -> 写 chunks.jsonl。可重复运行。"""
from __future__ import annotations

import json
import pathlib

import pandas as pd

from .chunking import chunk_document
from .cleaning import clean_pages
from .loaders import load_pdf

ROOT = pathlib.Path(__file__).resolve().parent.parent
META_CSV = ROOT / "data" / "processed" / "sop_metadata.csv"
OUT_JSONL = ROOT / "data" / "processed" / "chunks.jsonl"


def main() -> None:
    meta = pd.read_csv(META_CSV).fillna("")
    all_chunks: list[dict] = []
    report: list[tuple[str, str, int, int, str]] = []

    for row in meta.to_dict(orient="records"):
        pdf_path = ROOT / row["file_path"]
        try:
            pages = clean_pages(load_pdf(pdf_path))
            chunks = chunk_document(pages, row)
            all_chunks.extend(chunks)
            report.append((row["doc_id"], row["version"], len(pages), len(chunks), "OK"))
        except Exception as exc:
            report.append((row["doc_id"], row["version"], 0, 0, f"FAIL: {exc}"))

    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print("=" * 70)
    print(f"{'doc_id':<16}{'version':<8}{'pages':>6}{'chunks':>8}  状态")
    for doc_id, version, pages, chunks, status in report:
        print(f"{doc_id:<16}{version:<8}{pages:>6}{chunks:>8}  {status}")
    print("-" * 70)
    current = sum(1 for c in all_chunks if c["status"] == "current")
    archived = len(all_chunks) - current
    print(f"chunks 总数: {len(all_chunks)} | current: {current} | superseded: {archived}")
    print("已写出:", OUT_JSONL.relative_to(ROOT))
    failed = [r for r in report if r[4] != "OK"]
    if failed:
        print("⚠ 有文档抽取失败，见上表 FAIL 行（验收需说明原因）")


if __name__ == "__main__":
    main()