"""RAG 命令行：输入问题，打印带参考依据的答案。"""
from __future__ import annotations

import argparse

from .rag import answer_question


def main() -> None:
    parser = argparse.ArgumentParser(description="SOP RAG 问答 CLI")
    parser.add_argument("question", help="你的问题")
    parser.add_argument("-k", type=int, default=5, help="检索条数，默认 5")
    args = parser.parse_args()

    result = answer_question(args.question, k=args.k)
    print(result["answer"])
    print("\n参考依据：")
    for reference in result["references"]:
        print(reference)
    if not result["references"]:
        print("（本次未检索到可引用的现行 SOP）")


if __name__ == "__main__":
    main()