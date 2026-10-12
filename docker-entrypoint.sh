#!/bin/sh
set -e

# 向量库不存在时（首次启动），用 chunks.jsonl 现场构建
if [ ! -f "data/vectorstore/chroma/chroma.sqlite3" ]; then
    echo "[entrypoint] 未发现向量库，开始构建索引 ..."
    python -m src.build_index
fi

exec uvicorn src.main:app --host 0.0.0.0 --port 8000