
# ChemLab SOP Copilot

化学分析实验室 SOP 智能问答与版本核查助手。

## 项目定位

面向化学分析实验室的 SOP（标准操作规程）智能助手，聚焦以下场景：

- 当前有效版本 SOP 的智能问答（"ICP-MS 开机第三步做什么？"）

- 版本感知检索（只从当前生效版本中找答案）

- 新旧版本对比（"V2.0 和 V1.3 的样品前处理部分有什么变化？"）

- 过期版本拦截（用户引用旧版本时给出提醒）

- 检查清单提取（自动抽取 SOP 中的操作检查项）

- 引用溯源（每个回答标注来源文档、版本号、章节/页码）

## 技术栈

Python / PDF 解析 / 文本切块 / BGE Embedding / Chroma 向量库 / Rerank /

DeepSeek LLM API / Function Calling / FastAPI / Gradio / Docker / HuggingFace Spaces

## 数据来源

全部使用公开化学分析 SOP 模板及自建模拟版本元数据，不涉及任何企业内部资料。

## 目录结构

- `data/raw`：原始公开 SOP PDF

- `data/processed`：清洗文本与切块结果

- `src`：Python 源码（`src/tools` 为 Agent 工具）

- `eval`：评测集与评测脚本

- `tests`：测试代码

- `docs`：文档与架构图

- `notes`：学习笔记

## 项目状态

- [x] Day00 环境准备与项目初始化

- [ ] Day01 公开 SOP 数据收集与版本元数据设计

- [ ] Day02 PDF 解析与文本切块

- [ ] Day03 Embedding 与向量库

- [ ] Day04 RAG 最小闭环

- [ ] Day05 Agent 与 Function Calling

- [ ] Day06 FastAPI 后端

- [ ] Day07 Gradio 前端、评测与部署

