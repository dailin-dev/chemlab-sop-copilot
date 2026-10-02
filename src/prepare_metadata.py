# src/prepare_metadata.py
"""生成 SOP 版本元数据 CSV，并打印统计与文件检查结果。"""
import pathlib
import pandas as pd

# 项目根目录（本文件位于 src/ 下，根目录是上一级）
ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_CSV = ROOT / "data" / "processed" / "sop_metadata.csv"

# 演示用版本元数据：doc_id 相同表示同一份文档的不同版本。
# 请把 title / file_path / source_url 替换为你实际收集的公开文档。
RECORDS = [
    # —— 第 1 组多版本：ICP-MS 操作规程 ——
    {
        "doc_id": "SOP-ICPMS-001",
        "title": "EPA Method 200.8: Determination of Trace Elements in Waters and Wastes by Inductively Coupled Plasma-Mass Spectrometry",
        "version": "V1.0",
        "effective_date": "2026-04-08",
        "expiry_date": "2026-09-01",
        "status": "superseded",
        "instrument_type": "ICP-MS",
        "category": "仪器操作",
        "source_url": "https://www.epa.gov/esam/epa-method-2008-determination-trace-elements-waters-and-wastes-inductively-coupled-plasma-mass",
        "file_path": "data/raw/epa_200_8_v1.pdf",
        "created_at": "2026-10-01",
    },
    {
        "doc_id": "SOP-ICPMS-001",
        "title": "EPA Method 200.8: Determination of Trace Elements in Waters and Wastes by Inductively Coupled Plasma-Mass Spectrometry",
        "version": "V2.0",
        "effective_date": "2026-09-01",
        "expiry_date": "",
        "status": "current",
        "instrument_type": "ICP-MS",
        "category": "仪器操作",
        "source_url": "https://www.epa.gov/esam/epa-method-2008-determination-trace-elements-waters-and-wastes-inductively-coupled-plasma-mass",
        "file_path": "data/raw/epa_200_8_v2.pdf",
        "created_at": "2026-10-01",
    },
    # —— 第 2 组多版本：GC-MS 操作规程 ——
    {
        "doc_id": "SOP-GCMS-001",
        "title": "EPA Method 8260D (SW-846): Volatile Organic Compounds by Gas Chromatography-Mass Spectrometry (GC/MS)",
        "version": "V1.0",
        "effective_date": "2017-02-10",
        "expiry_date": "2025-08-06",
        "status": "superseded",
        "instrument_type": "GC-MS",
        "category": "仪器操作",
        "source_url": "https://www.epa.gov/esam/epa-method-8260d-sw-846-volatile-organic-compounds-gas-chromatography-mass-spectrometry-gcms",
        "file_path": "data/raw/epa_8260d_V1.pdf",
        "created_at": "2026-10-01",
    },
    {
        "doc_id": "SOP-GCMS-001",
        "title": "EPA Method 8260D (SW-846): Volatile Organic Compounds by Gas Chromatography-Mass Spectrometry (GC/MS)",
        "version": "V2.0",
        "effective_date": "2025-08-06",
        "expiry_date": "",
        "status": "current",
        "instrument_type": "GC-MS",
        "category": "仪器操作",
        "source_url": "https://www.epa.gov/esam/epa-method-8260d-sw-846-volatile-organic-compounds-gas-chromatography-mass-spectrometry-gcms",
        "file_path": "data/raw/epa_8260d_V2.pdf",
        "created_at": "2026-10-01",
    },
    # —— 3 份单版本现行文档 ——
    {
        "doc_id": "SOP-ICPOES-001",
        "title": "Method 200.7: Determination of Metals and Trace Elements in Water and Wastes by Inductively Coupled Plasma-Atomic Emission Spectrometry",
        "version": "V1.0",
        "effective_date": "2026-04-17",
        "expiry_date": "",
        "status": "current",
        "instrument_type": "ICP-OES",
        "category": "仪器操作",
        "source_url": "https://www.epa.gov/esam/method-2007-determination-metals-and-trace-elements-water-and-wastes-inductively-coupled",
        "file_path": "data/raw/epa_200_7.pdf",
        "created_at": "2026-10-01",
    },
    {
        "doc_id": "SOP-PREP-001",
        "title": "EPA Method 3015A: Microwave Assisted Acid Digestion of Aqueous Samples and Extracts",
        "version": "V1.0",
        "effective_date": "2007-02-15",
        "expiry_date": "",
        "status": "current",
        "instrument_type": "通用",
        "category": "样品前处理",
        "source_url": "https://www.epa.gov/esam/epa-method-3015a-microwave-assisted-acid-digestion-aqueous-samples-and-extracts",
        "file_path": "data/raw/epa_3015a.pdf",
        "created_at": "2026-10-01",
    },
    {
        "doc_id": "SOP-PREP-002",
        "title": "U.S. EPA Method 3051A: Microwave Assisted Acid Digestion of Sediments, Sludges, and Oils",
        "version": "V1.0",
        "effective_date": "2007-02-15",
        "expiry_date": "",
        "status": "current",
        "instrument_type": "通用",
        "category": "样品前处理",
        "source_url": "https://www.epa.gov/esam/us-epa-method-3051a-microwave-assisted-acid-digestion-sediments-sludges-and-oils",
        "file_path": "data/raw/epa_3051a.pdf",
        "created_at": "2026-10-01",
    },
    {
        "doc_id": "SOP-SAFE-001",
        "title": "化学工程与技术学院实验室化学品安全管理实施细则",
        "version": "V1.0",
        "effective_date": "2025-03-26",
        "expiry_date": "",
        "status": "current",
        "instrument_type": "通用",
        "category": "安全",
        "source_url": r"https://cet.sysu.edu.cn/sites/default/files/2025-04/%E5%8C%96%E5%AD%A6%E5%B7%A5%E7%A8%8B%E4%B8%8E%E6%8A%80%E6%9C%AF%E5%AD%A6%E9%99%A2%E5%AE%9E%E9%AA%8C%E5%AE%A4%E5%8C%96%E5%AD%A6%E5%93%81%E5%AE%89%E5%85%A8%E7%AE%A1%E7%90%86%E5%AE%9E%E6%96%BD%E7%BB%86%E5%88%99%EF%BC%88%E5%8C%96%E5%B7%A5%E3%80%942025%E3%80%955%E5%8F%B7%EF%BC%89.pdf",
        "file_path": "data/raw/化学工程与技术学院实验室化学品安全管理实施细则.pdf",
        "created_at": "2026-10-01",
    },
    {
        "doc_id": "SOP-SAFE-002",
        "title": "化学化工学院实验室安全管理细则",
        "version": "V1.0",
        "effective_date": "2025-07-19",
        "expiry_date": "",
        "status": "current",
        "instrument_type": "通用",
        "category": "安全",
        "source_url": "https://chem.hnust.edu.cn/docs/2025-11/deda97f165e54ce0b7e3f5e61a5ec29d.pdf",
        "file_path": "data/raw/化学化工学院实验室安全管理细则.pdf",
        "created_at": "2026-10-01",
    },
]

REQUIRED_FIELDS = [
    "doc_id", "title", "version", "effective_date",
    "status", "instrument_type", "category", "source_url",
    "file_path", "created_at",
]


def main() -> None:
    df = pd.DataFrame(RECORDS)

    # 1) 字段完整性检查
    missing = [f for f in REQUIRED_FIELDS if f not in df.columns]
    if missing:
        raise ValueError(f"缺少字段: {missing}")
    empty_cells = df[REQUIRED_FIELDS].isna().sum().sum()
    if empty_cells:
        raise ValueError(f"必填字段存在空值，共 {empty_cells} 处")

    # 2) 状态合法性检查
    bad_status = set(df["status"]) - {"current", "superseded", "draft"}
    if bad_status:
        raise ValueError(f"非法状态: {bad_status}")

    # 3) 文件是否真实存在
    missing_files = [
        fp for fp in df["file_path"] if not (ROOT / fp).exists()
    ]
    if missing_files:
        print("⚠ 以下元数据指向的文件不存在，请检查 file_path：")
        for fp in missing_files:
            print("   -", fp)
    else:
        print("✅ 所有元数据指向的文件都存在")

    # 4) 写出 CSV（UTF-8，带 BOM 方便 Excel 直接打开中文）
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    # 5) 打印统计
    print("-" * 40)
    print(f"记录总数: {len(df)}")
    print(f"不同文档数(doc_id): {df['doc_id'].nunique()}")
    print("各状态数量:")
    for status in ["current", "superseded", "draft"]:
        print(f"   {status}: {(df['status'] == status).sum()}")
    print("每组版本:")
    for doc_id, grp in df.groupby("doc_id"):
        versions = ", ".join(
            f"{r.version}({r.status})" for r in grp.itertuples()
        )
        print(f"   {doc_id}: {grp['version'].nunique()} 个版本 -> {versions}")
    print("-" * 40)
    print("CSV 已写出:", OUT_CSV.relative_to(ROOT))


if __name__ == "__main__":
    main()