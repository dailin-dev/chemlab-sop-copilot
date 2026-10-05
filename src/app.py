"""Gradio 前端。"""
from __future__ import annotations

import gradio as gr

from .agent import Agent
from .rag import answer_question


def respond(question: str, mode: str):
    if not question.strip():
        return "请输入问题。", ""
    if mode == "RAG 问答":
        result = answer_question(question)
        references = "\n".join(result["references"])
        return result["answer"], references or "（无引用）"
    agent = Agent(verbose=False)
    answer = agent.run(question)
    note = "Agent 模式：工具调用过程见终端日志，参考依据见回答末尾。"
    return answer, note


with gr.Blocks(title="ChemLab SOP Copilot") as demo:
    gr.Markdown(
        "# ChemLab SOP Copilot\n"
        "化学分析实验室 SOP 智能问答与版本核查助手（演示数据均来自公开 SOP）"
    )
    with gr.Row():
        question = gr.Textbox(label="问题", lines=2, placeholder="例如：ICP-MS 如何校准？")
        mode = gr.Radio(
            ["RAG 问答", "Agent"], value="RAG 问答", label="模式"
        )
    submit = gr.Button("提交")
    answer = gr.Markdown(label="回答")
    references = gr.Markdown(label="参考依据")
    submit.click(respond, inputs=[question, mode], outputs=[answer, references])


if __name__ == "__main__":
    demo.launch()