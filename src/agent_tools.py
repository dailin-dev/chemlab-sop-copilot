"""Agent 的三个 Function Calling 工具：schema 定义 + 执行 + 分发。"""
from __future__ import annotations

import json
import pathlib

import pandas as pd

from .retriever import Retriever
from .vectorstore import VectorStore

ROOT = pathlib.Path(__file__).resolve().parent.parent
META_CSV = ROOT / "data" / "processed" / "sop_metadata.csv"
PERSIST = ROOT / "data" / "vectorstore" / "chroma"

_retriever: Retriever | None = None


def _ret() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


def _meta_df() -> pd.DataFrame:
    return pd.read_csv(META_CSV).fillna("")


def _match_doc(df: pd.DataFrame, doc_id: str = "", title: str = ""):
    if doc_id:
        sub = df[df["doc_id"].str.lower() == doc_id.lower()]
        if len(sub):
            return sub
    if title:
        sub = df[df["title"].str.contains(title, case=False, regex=False)]
        if len(sub):
            did = sub.iloc[0]["doc_id"]
            return df[df["doc_id"] == did]
    return df.iloc[0:0]


# —— 工具 1：检索现行 SOP ——
def tool_search_current_sop(query: str, k: int = 5) -> str:
    hits = _ret().search(query, k=int(k))
    slim = [
        {
            "title": h["title"],
            "version": h["version"],
            "status": h["status"],
            "section": h["section"],
            "page": h["page"],
            "source_url": h["source_url"],
            "text": h["text"],
        }
        for h in hits
    ]
    return json.dumps({"results": slim}, ensure_ascii=False)


# —— 工具 2：版本状态核查 ——
def tool_check_version_status(doc_id: str = "", title: str = "", version: str = "") -> str:
    df = _meta_df()
    sub = _match_doc(df, doc_id, title)
    if not len(sub):
        return json.dumps(
            {"found": False, "message": "未找到匹配文档，请让用户提供准确的 doc_id 或标题关键词"},
            ensure_ascii=False,
        )
    records = sub[
        ["doc_id", "title", "version", "effective_date", "expiry_date", "status"]
    ].to_dict("records")
    current = [r for r in records if r["status"] == "current"]
    asked = None
    if version:
        asked = next(
            (r for r in records if r["version"].lower() == version.lower()), None
        )
    return json.dumps(
        {
            "found": True,
            "doc_id": records[0]["doc_id"],
            "versions": records,
            "current_version": current[0]["version"] if current else None,
            "asked_version": asked,
        },
        ensure_ascii=False,
    )


# —— 工具 3：新旧版本对比 ——
def tool_compare_versions(doc_id: str = "", title: str = "") -> str:
    df = _meta_df()
    sub = _match_doc(df, doc_id, title)
    if not len(sub):
        return json.dumps(
            {"found": False, "message": "未找到匹配文档"}, ensure_ascii=False
        )
    did = sub.iloc[0]["doc_id"]
    meta_versions = sub[
        ["version", "effective_date", "expiry_date", "status"]
    ].to_dict("records")

    store = VectorStore(PERSIST)
    excerpts: dict = {}
    for collection_name in ("sop_current", "sop_archive"):
        try:
            collection = store.client.get_collection(collection_name)
        except Exception:
            continue
        got = collection.get(where={"doc_id": did}, include=["documents", "metadatas"])
        seen_section: set[str] = set()
        total = 0
        for document, meta in zip(got["documents"], got["metadatas"]):
            section = meta.get("section", "")
            if section in seen_section:
                continue
            seen_section.add(section)
            version = meta.get("version", "")
            piece = {"section": section, "text": document[:500]}
            excerpts.setdefault(version, []).append(piece)
            total += len(piece["text"])
            if total > 2500:
                break
    return json.dumps(
        {
            "found": True,
            "doc_id": did,
            "metadata_versions": meta_versions,
            "excerpts": excerpts,
        },
        ensure_ascii=False,
    )


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_current_sop",
            "description": "检索现行有效版本 SOP，用于回答操作步骤、仪器参数、分析方法、质量控制、安全等具体问题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "与文档语言一致的检索查询"},
                    "k": {"type": "integer", "description": "返回条数，默认 5"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_version_status",
            "description": "核查某文档的版本是现行(current)还是已废止(superseded)，或某指定版本是否有效，并返回当前现行版本号。",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string", "description": "文档编号，如 SOP-ICPMS-001"},
                    "title": {"type": "string", "description": "文档标题关键词"},
                    "version": {"type": "string", "description": "待核查版本，如 V1.0"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_versions",
            "description": "对比同一文档的新旧版本，返回版本元数据差异与各版本章节摘录，用于回答版本变化。",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "title": {"type": "string", "description": "文档标题关键词"},
                },
            },
        },
    },
]

_DISPATCH = {
    "search_current_sop": tool_search_current_sop,
    "check_version_status": tool_check_version_status,
    "compare_versions": tool_compare_versions,
}


def dispatch_tool(name: str, arguments: str) -> str:
    try:
        args = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError:
        args = {}
    function = _DISPATCH.get(name)
    if function is None:
        return json.dumps({"error": f"未知工具 {name}"}, ensure_ascii=False)
    try:
        return function(**args)
    except TypeError as exc:
        return json.dumps({"error": f"参数不匹配: {exc}"}, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": f"工具执行失败: {exc}"}, ensure_ascii=False)