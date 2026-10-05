"""PDF 文本抽取：pdfplumber 优先，pypdf 兜底。"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass


@dataclass
class Page:
    page_num: int
    text: str


def _with_pdfplumber(path: pathlib.Path) -> list[Page]:
    import pdfplumber

    pages: list[Page] = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            pages.append(Page(i, page.extract_text() or ""))
    return pages


def _with_pypdf(path: pathlib.Path) -> list[Page]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages: list[Page] = []
    for i, page in enumerate(reader.pages, start=1):
        pages.append(Page(i, page.extract_text() or ""))
    return pages


def load_pdf(path: str | pathlib.Path) -> list[Page]:
    """返回逐页文本；两种抽取器都失败或全空时抛错。"""
    path = pathlib.Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    errors: list[str] = []
    for extractor in (_with_pdfplumber, _with_pypdf):
        try:
            pages = extractor(path)
            if any(p.text.strip() for p in pages):
                return pages
            errors.append(f"{extractor.__name__}: 抽取结果全空")
        except Exception as exc:
            errors.append(f"{extractor.__name__}: {exc}")
    raise RuntimeError(f"无法从 {path.name} 抽取文本 | {'; '.join(errors)}")