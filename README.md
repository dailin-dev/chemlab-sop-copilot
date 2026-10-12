---
sdk: gradio
app_file: app.py
---
# ChemLab SOP Copilot：化学分析实验室 SOP 智能问答与版本核查助手

## 项目简介

一个面向化学分析实验室的检索增强（RAG）智能助手，支持对**当前有效版本** SOP 问答、版本感知检索、新旧版本对比、过期版本拦截、检查清单提取与引用溯源。项目用于演示 RAG / Function Calling Agent 的完整工程链路，所有数据均来自公开 SOP，不包含任何企业内部资料。

## 核心功能

- **现行版本问答**：基于 RAG 回答操作步骤、参数、方法、质控、安全问题。
- **版本感知检索**：仅从 current（现行）版本检索，旧版本默认不参与。
- **新旧版本对比**：输出版本元数据差异与章节变化摘要。
- **过期版本拦截**：命中/询问已废止版本时提醒并指向现行版本。
- **引用溯源**：回答标注文档名、版本、章节、页码与来源链接。
- **Function Calling Agent**：模型自动选择并执行 SOP 检索、版本核查、版本对比 3 个工具。

## 数据来源

- 美国 EPA 公开分析方法：Method 200.7 / 200.8 / 8260D / 3015A / 3051A（https://www.epa.gov/methods ）。
- 高校公开实验室安全管理细则（PDF）。
- 版本元数据为基于上述公开文档自建的演示数据（current / superseded），不代表任何真实企业使用情况。

## 技术栈

Python、pypdf、pdfplumber、BGE-small-zh（BAAI/bge-small-zh-v1.5）、Chroma、DeepSeek（OpenAI 兼容）、手写 Function Calling Agent、FastAPI、Gradio、Docker、loguru、pytest。

## 目录结构

```text
chemlab-sop-copilot/
├─ app.py                 # Gradio 空间入口（ModelScope/HF）
├─ Dockerfile / docker-entrypoint.sh / .dockerignore
├─ requirements.txt
├─ src/
│  ├─ loaders.py          # PDF 抽取（pdfplumber + pypdf）
│  ├─ cleaning.py         # 文本清洗
│  ├─ chunking.py         # 章节/长度切块
│  ├─ run_chunking.py     # 生成 chunks.jsonl
│  ├─ embeddings.py       # BGE 向量化
│  ├─ vectorstore.py      # Chroma（current / archive 双集合）
│  ├─ build_index.py      # 构建向量库
│  ├─ llm.py              # DeepSeek 封装
│  ├─ retriever.py        # 检索封装
│  ├─ rag.py / run_rag.py # RAG 问答
│  ├─ agent_tools.py      # 3 个工具
│  ├─ agent.py            # Agent 循环与记忆
│  ├─ main.py             # FastAPI
│  └─ app.py              # Gradio Blocks
├─ eval/                  # 评测集、评测脚本与结果
├─ tests/                 # 接口测试
└─ docs/                  # 架构图
```

## 本地安装

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 环境变量

在项目根目录创建 `.env`（不要提交）：

```text
DEEPSEEK_API_KEY=sk-你的Key
APP_API_KEY=自定义访问密钥
REQUIRE_API_KEY=false
```

## 三种启动方式

FastAPI（含 Swagger，访问 /docs）：

```powershell
uvicorn src.main:app --reload
```

Gradio（本地 http://127.0.0.1:7860）：

```powershell
python -m src.app
```

Docker：

```powershell
docker build -t chemlab-copilot:latest .
docker run -d -p 8000:8000 -e DEEPSEEK_API_KEY=sk-你的Key chemlab-copilot:latest
```

## 评测方式与指标

评测集 `eval/eval_set.jsonl` 共 20 条（RAG 基础 10、版本核查 4、版本对比 3、过期拦截 3），运行 `python -m eval.run_eval` 得到以下结果（基于该演示评测集，非生产数据）：

| 指标 | 结果 |
|---|---|
| 引用命中率 | 100% |
| 工具选择正确率 | 100% |
| 答案要点覆盖率 | 80% |
| 过期版本误引率 | 0% |
| 接口测试 pytest | 6 passed |

## 公网 Demo

- ModelScope 创空间：https://www.modelscope.cn/studios/dailylab/chemlab-sop-copilot

## 项目局限与后续优化

- 为演示项目，数据规模有限，指标仅反映上述 20 条测试集，不代表生产环境准确率。
- 英文长查询偶有召回偏差，计划引入双语 Embedding、查询扩展、metadata 过滤与 Rerank。
- 版本对比当前为元数据 + 章节片段摘要，后续可做逐句 diff；会话为最近 N 轮短期记忆。

## 免责声明

本项目仅用于学习与作品集演示，数据均来自公开渠道，不包含任何公司内部 SOP 或机密信息；版本元数据为模拟数据，与任何真实机构无关。

