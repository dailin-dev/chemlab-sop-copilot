"""按章节标题切块，过长章节递归按长度切（带重叠）。"""
from __future__ import annotations

import re

from .loaders import Page

_HEADING = re.compile(
    r"^(?:"
    r"\d{1,2}(?:\.\d{1,2}){0,2}\.?\s+[A-Z\u4e00-\u9fff(（]"
    r"|第[一二三四五六七八九十百\d]+[章节条]"
    r"|[一二三四五六七八九十]+、"
    r")"
)

_META_KEYS = [
    "doc_id", "title", "version", "status", "instrument_type",
    "category", "source_url", "file_path",
]


def _is_heading(line: str) -> bool:
    s = line.strip()
    return len(s) <= 80 and bool(_HEADING.match(s))


def _find_break(window: str) -> int:
    best = -1
    for punct in ("。", "！", "？", "；", ". ", "? ", "! ", "; "):
        best = max(best, window.rfind(punct))
    return best


def _split_oversize(text: str, size: int, overlap: int) -> list[str]:
    if len(text) <= size:
        return [text]
    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            br = _find_break(text[start:end])
            if br > size * 0.5:
                end = start + br
        pieces.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [p for p in pieces if p]


def _page_segments(page: Page) -> list[tuple[str, str, int]]:
    segments: list[tuple[str, str, int]] = []
    title = ""
    body: list[str] = []

    def flush() -> None:
        if any(line.strip() for line in body):
            segments.append((title, "\n".join(body).strip(), page.page_num))

    for line in page.text.split("\n"):
        if _is_heading(line):
            flush()
            body = []
            title = line.strip()
        else:
            body.append(line)
    flush()
    return segments


def chunk_document(
    pages: list[Page],
    meta: dict,
    chunk_size: int = 850,
    overlap: int = 120,
) -> list[dict]:
    chunks: list[dict] = []
    counter = 0
    for page in pages:
        for section_title, body, page_num in _page_segments(page):
            content = f"{section_title}\n{body}" if section_title else body
            for piece in _split_oversize(content, chunk_size, overlap):
                safe_id = f"{meta['doc_id']}_{meta['version']}_{counter:04d}"
                for bad in (".", " ", "/", "\\"):
                    safe_id = safe_id.replace(bad, "-")
                chunk = {key: str(meta.get(key, "")) for key in _META_KEYS}
                chunk.update(
                    {
                        "chunk_id": safe_id,
                        "section": section_title,
                        "page": page_num,
                        "text": piece,
                    }
                )
                chunks.append(chunk)
                counter += 1
    return chunks