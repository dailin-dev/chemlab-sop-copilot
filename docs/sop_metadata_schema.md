
# SOP 版本元数据字段草案

> 用途：每份 SOP 文档（及每个版本）对应一条元数据记录，支撑版本感知检索、过期拦截、新旧对比、引用溯源。
> Day01 据此设计具体的元数据表格（CSV/JSON）。

## 字段定义

| 字段名 | 含义 | 示例 | 是否必填 |

|---|---|---|---|

| doc_id | 文档唯一编号 | SOP-ICPMS-001 | 必填 |

| title | 文档名称 | ICP-MS 操作规程 | 必填 |

| version | 版本号 | V2.0 | 必填 |

| effective_date | 生效日期 | 2026-01-15 | 必填 |

| expiry_date | 失效日期（被新版替代时填） | 2026-06-01 | 选填 |

| status | 状态：current（现行）/ superseded（已废止）/ draft（草稿） | current | 必填 |

| instrument_type | 仪器类型 | ICP-MS / GC-MS / HPLC | 必填 |

| category | SOP 类别 | 仪器操作 / 样品前处理 / 安全 / 数据完整性 | 必填 |

| section | 章节（切块时记录） | 第3章 开机流程 | 选填 |

| source_url | 公开来源 URL | https://... | 公开数据必填 |

| file_path | 本地文件路径 | data/raw/icpms_v2.pdf | 必填 |

| checksum | 文件校验值（判断是否同一文件） | （自动生成） | 选填 |

| created_at | 记录创建时间 | 2026-09-29 | 必填 |

## 版本核查要支持的核心逻辑

1. 问答时只检索 status=current 的文档版本

2. 答案引用必须带 title + version + section

3. 同一 doc_id 存在多个版本时，能按 effective_date 排序并做差异对比

4. 用户查询命中 superseded 版本内容时，返回"该内容来自已废止版本 Vx.x，现行版本为 Vy.y"

