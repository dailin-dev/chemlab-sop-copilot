"""文本清洗：去页眉页脚、目录导视、断行、多余空白。"""
from __future__ import annotations

import re
from collections import Counter

from .loaders import Page

_TOC_LINE = re.compile(r"\.{4,}\s*\d+\s*$")
_MULTI_SPACE = re.compile(r"[ \t]+")
_MULTI_NEWLINE = re.compile(r"\n{3,}")
_HYPHEN_BREAK = re.compile(r"([A-Za-z])-\n([A-Za-z])")
_PAGE_NUM = re.compile(r"[-–—\s\d./]+")
_HEADING = re.compile(r"^\s*(\d+(\.\d+)*\.?\s+|[A-Z]\.\s+|[-*•]\s+|第[一二三四五六七八九十\d]+[章节])")
_END_PUNCT = re.compile(r"[.:;?!？。：；]$")


def _is_cjk(ch: str) -> bool:
    return bool(re.match(r"[\u4e00-\u9fff]", ch))


def find_running_lines(pages: list[Page], min_pages: int = 3, max_len: int = 70) -> set[str]:
    """统计在多页重复出现的短行，作为页眉/页脚剔除。"""
    counter: Counter[str] = Counter()
    for page in pages:
        once = {
            line.strip()
            for line in page.text.splitlines()
            if line.strip() and len(line.strip()) <= max_len
        }
        counter.update(once)
    return {line for line, count in counter.items() if count >= min_pages}


def _clean_line(line: str) -> str:
    line = line.replace("\u3000", " ")
    return _MULTI_SPACE.sub(" ", line).rstrip()


def _join_wrapped_lines(text: str) -> str:
    """把同段内被硬换行拆开的句子重新合并（保守策略）。"""
    out: list[str] = []
    buffer = ""
    for line in text.split("\n"):
        if not line.strip():
            if buffer:
                out.append(buffer)
                buffer = ""
            out.append("")
            continue
        structural = bool(_HEADING.match(line))
        if not buffer:
            buffer = line
        elif _END_PUNCT.search(buffer.rstrip()) or structural:
            out.append(buffer)
            buffer = line
        else:
            joiner = "" if _is_cjk(buffer[-1]) and _is_cjk(line[0]) else " "
            buffer = buffer.rstrip() + joiner + line.lstrip()
    if buffer:
        out.append(buffer)
    return "\n".join(out)


def clean_pages(pages: list[Page]) -> list[Page]:
    running = find_running_lines(pages)
    cleaned: list[Page] = []
    for page in pages:
        kept: list[str] = []
        for raw in page.text.splitlines():
            line = _clean_line(raw)
            if not line:
                kept.append("")
                continue
            if line in running:
                continue
            if _TOC_LINE.search(line):
                continue
            if len(line.strip()) <= 6 and _PAGE_NUM.fullmatch(line):
                continue
            kept.append(line)
        text = "\n".join(kept)
        text = _HYPHEN_BREAK.sub(r"\1\2", text)
        text = re.sub(r"(?<=[\u4e00-\u9fff])\n(?=[\u4e00-\u9fff])", "", text)
        text = _join_wrapped_lines(text)
        text = _MULTI_NEWLINE.sub("\n\n", text)
        cleaned.append(Page(page.page_num, text.strip()))
    return cleaned