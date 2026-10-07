"""手写 Function Calling Agent：工具选择/执行/回传循环 + 最近 N 轮记忆 + CLI。"""
from __future__ import annotations

import argparse

from .agent_tools import TOOL_SCHEMAS, dispatch_tool
from .llm import chat

AGENT_SYSTEM = (
    "你是化学分析实验室 SOP 助手，可以调用工具。请遵守：\n"
    "1. 操作步骤/方法/参数/质量控制/安全等具体问题，先调用 search_current_sop 取现行 SOP 再回答；\n"
    "2. 询问某版本是否有效、是否过期，调用 check_version_status；\n"
    "3. 要求对比新旧版本差异，调用 compare_versions；\n"
    "4. 只能依据工具返回内容回答，无依据就说明无法确认，不得编造；\n"
    "5. 若工具显示某版本已废止，明确提醒用户并指出现行版本号；\n"
    "6. 回答末尾以“参考依据”列出涉及的文档、版本、章节与来源。"
)

MAX_MEMORY_MESSAGES = 12  # 最近约 6 轮


class Agent:
    def __init__(self, verbose: bool = True) -> None:
        self.messages = [{"role": "system", "content": AGENT_SYSTEM}]
        self.verbose = verbose

    def _log(self, text: str) -> None:
        if self.verbose:
            print(text)

    def _trim_memory(self) -> None:
        system = self.messages[0]
        body = self.messages[1:]
        if len(body) > MAX_MEMORY_MESSAGES:
            body = body[-MAX_MEMORY_MESSAGES:]
        self.messages = [system] + body

    def run(self, user_input: str, max_steps: int = 5) -> str:
        self.messages.append({"role": "user", "content": user_input})
        for step in range(max_steps):
            response = chat(self.messages, tools=TOOL_SCHEMAS)
            message = response.choices[0].message

            if message.tool_calls:
                names = ", ".join(tc.function.name for tc in message.tool_calls)
                self._log(f"[步骤{step + 1}] 选择工具: {names}")
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in message.tool_calls
                        ],
                    }
                )
                for tc in message.tool_calls:
                    result = dispatch_tool(tc.function.name, tc.function.arguments)
                    self._log(f"  工具 {tc.function.name} 返回 {len(result)} 字符")
                    self.messages.append(
                        {"role": "tool", "tool_call_id": tc.id, "content": result}
                    )
                continue

            self.messages.append({"role": "assistant", "content": message.content})
            self._trim_memory()
            return message.content

        fallback = "已达到最大工具调用步数，请缩小问题范围或稍后重试。"
        self.messages.append({"role": "assistant", "content": fallback})
        self._trim_memory()
        return fallback


def interactive() -> None:
    agent = Agent()
    print("ChemLab SOP Agent（输入 exit 退出）")
    while True:
        try:
            question = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question:
            continue
        if question.lower() in ("exit", "quit", "退出"):
            break
        print("\n助手:", agent.run(question))
    print("再见")


def main() -> None:
    parser = argparse.ArgumentParser(description="SOP Function Calling Agent")
    parser.add_argument("question", nargs="?", help="单次提问；不填进入多轮对话")
    args = parser.parse_args()
    if args.question:
        agent = Agent(verbose=True)
        print("\n助手:", agent.run(args.question))
    else:
        interactive()


if __name__ == "__main__":
    main()