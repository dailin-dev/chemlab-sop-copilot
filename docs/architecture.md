# 系统架构 — ChemLab SOP Copilot

## 全链路流程

```mermaid
flowchart TD
    A[公开化学分析 SOP<br/>EPA 方法 / 高校安全细则] --> B[sop_metadata.csv<br/>版本元数据 current/superseded]
    A --> C[PDF 解析 loaders.py<br/>pdfplumber + pypdf]
    C --> D[文本清洗 cleaning.py]
    D --> E[结构化切块 chunking.py<br/>章节优先 + 长度重叠]
    E --> F[chunks.jsonl]
    F --> G[BGE-small-zh Embedding]
    G --> H[(Chroma)]
    H --> H1[sop_current 主集合<br/>仅现行版本]
    H --> H2[sop_archive 归档集合<br/>旧版本]
    Q[用户问题] --> R[检索 Top-K]
    H1 --> R
    R --> S[上下文组装 + Prompt 约束]
    S --> T[DeepSeek 生成答案]
    T --> U[引用溯源<br/>文档/版本/章节/页码]
    U --> V[FastAPI / Gradio]
    V --> W[用户]

    AG[Function Calling Agent] --> T1[工具1 SOP 检索]
    AG --> T2[工具2 版本状态/过期核查]
    AG --> T3[工具3 新旧版本对比]
    T1 --> H1
    T2 --> B
    T3 --> H1
    T3 --> H2
```

## 要点说明

- **双集合隔离**：current 进 `sop_current`，superseded 进 `sop_archive`；默认问答只检索 current，从机制上避免引用过期版本。
- **Agent 三工具**：SOP 检索走向量库；版本核查走元数据表；版本对比同时读取两个集合。
- **密钥不落地**：DeepSeek Key 仅通过环境变量注入，代码仓库与镜像均不含真实密钥。