"""RAG 核心：current 检索 -> 组装上下文 -> DeepSeek 生成 -> 程序追加参考依据。"""
from __future__ import annotations

from .llm import chat
from .retriever import Retriever

SYSTEM_PROMPT = (
    "你是化学分析实验室的 SOP 智能助手。请严格遵守：\n"
    "1. 只能依据用户给出的<资料n>回答，答案中引用处用 [n] 标注；\n"
    "2. 资料中没有依据时，直接回答“根据现行 SOP 无法确认该信息”，"
    "不得凭常识编造仪器参数、操作步骤或数值；\n"
    "3. 若资料标注为已废止/旧版本，提醒用户以现行版本为准；\n"
    "4. 操作步骤类问题用编号分步作答，语言简洁专业。"
)

_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


def _format_context(hits) -> str:
    blocks = []
    for i, hit in enumerate(hits, start=1):
        header = (
            f"<资料{i}> [{hit['title']} | 版本{hit['version']} | {hit['status']} "
            f"| {hit['section']} | 第{hit['page']}页 | {hit['source_url']}]"
        )
        blocks.append(header + "\n" + hit["text"])
    return "\n\n".join(blocks)


def _references(hits) -> list[str]:
    lines = []
    for i, hit in enumerate(hits, start=1):
        lines.append(
            f"[{i}] {hit['title']}（{hit['version']}，{hit['status']}）"
            f"{hit['section']}，第{hit['page']}页 来源：{hit['source_url']}"
        )
    return lines


def answer_question(question: str, k: int = 5, history=None) -> dict:
    hits = get_retriever().search(question, k=k)
    context = _format_context(hits) if hits else "（未检索到相关现行 SOP）"
    user_content = f"问题：{question}\n\n以下是检索到的现行 SOP 资料：\n\n{context}"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_content})

    response = chat(messages, temperature=0.2)
    answer = response.choices[0].message.content
    return {"answer": answer, "references": _references(hits), "hits": hits}