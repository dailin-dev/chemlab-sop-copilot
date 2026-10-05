"""开发集批量评测脚本。"""
from __future__ import annotations

import json
import pathlib
import re

from src.agent import Agent
from src.rag import answer_question

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVAL_SET = ROOT / "eval" / "eval_set.jsonl"
RESULTS = ROOT / "eval" / "eval_results.json"

AGENT_TYPES = {"version_check", "compare", "expiry_guard"}


def load_set() -> list[dict]:
    rows = []
    with open(EVAL_SET, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def contains_forbidden(text: str, phrase: str) -> bool:
    """识别禁用短语；若短语前紧跟中文否定词“不”，不算违规。"""
    pattern = r"(?<![不])" + re.escape(phrase.lower())
    return re.search(pattern, text) is not None


def run_one(case: dict) -> dict:
    question = case["question"]
    tool_names: list[str] = []
    citations: list[str] = []
    try:
        if case["type"] in AGENT_TYPES:
            agent = Agent(verbose=False)
            answer = agent.run(question)
            for message in agent.messages:
                calls = message.get("tool_calls") if isinstance(message, dict) else None
                if calls:
                    tool_names.extend(c["function"]["name"] for c in calls)
            if "参考依据" in answer:
                citations = ["agent_answer"]
        else:
            result = answer_question(question)
            answer = result["answer"]
            citations = result["references"]
    except Exception as exc:
        answer = f"[执行异常] {exc}"

    text = answer.lower()
    points = case.get("expected_answer_points", [])
    point_hits = [p for p in points if p.lower() in text]
    point_ratio = len(point_hits) / len(points) if points else 0.0
    must_not = case.get("must_not_include", [])
    violations = [m for m in must_not if contains_forbidden(text, m)]
    expected_tool = case.get("expected_tool", "")
    tool_ok = expected_tool in tool_names if expected_tool and tool_names else (
        expected_tool == "search_current_sop" if case["type"] == "rag_basic" else False
    )

    return {
        "id": case["id"],
        "type": case["type"],
        "answer": answer,
        "tools_called": tool_names,
        "expected_tool": expected_tool,
        "tool_ok": tool_ok,
        "has_citation": bool(citations),
        "point_hits": point_hits,
        "point_ratio": round(point_ratio, 2),
        "must_not_violations": violations,
        "needs_human_review": True,
    }


def main() -> None:
    cases = load_set()
    results = []
    for i, case in enumerate(cases, start=1):
        print(f"[{i}/{len(cases)}] {case['id']} ...")
        results.append(run_one(case))

    total = len(results)
    citation_rate = sum(r["has_citation"] for r in results) / total
    tool_rate = sum(r["tool_ok"] for r in results) / total
    point_rate = sum(r["point_ratio"] for r in results) / total

    expiry = [r for r in results if r["type"] == "expiry_guard"]
    expiry_misquote = (
        sum(bool(r["must_not_violations"]) for r in expiry) / len(expiry)
        if expiry else 0.0
    )

    with open(RESULTS, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"评测条数: {total}")
    print(f"引用命中率: {citation_rate:.1%}")
    print(f"工具选择正确率: {tool_rate:.1%}")
    print(f"答案要点覆盖率(半自动,需人工复核): {point_rate:.1%}")
    print(f"过期版本误引率(越低越好): {expiry_misquote:.1%}")
    print("逐条结果已保存:", RESULTS.relative_to(ROOT))
    print("提示：请人工复核 needs_human_review，确认答案语义是否正确。")


if __name__ == "__main__":
    main()