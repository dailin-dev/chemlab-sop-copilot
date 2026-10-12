"""Gradio 空间入口。"""
from __future__ import annotations

import contextlib
import os
import pathlib
import shutil
import time

# 云端优先使用 ModelScope 模型源，HF 作为兜底。
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

ROOT = pathlib.Path(__file__).resolve().parent
CHUNKS = ROOT / "data" / "processed" / "chunks.jsonl"

# ModelScope 多实例共享 /mnt/workspace，缓存、向量库和锁需要跨实例可见。
if pathlib.Path("/mnt/workspace").exists():
    RUNTIME_DIR = pathlib.Path("/mnt/workspace") / "chemlab-sop-copilot"
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    PERSIST_DIR = RUNTIME_DIR / "vectorstore"
    os.environ["CHEMLAB_PERSIST_DIR"] = str(PERSIST_DIR)
    os.environ["MODELSCOPE_CACHE"] = str(RUNTIME_DIR / "modelscope-cache")
    os.environ["HF_HOME"] = str(RUNTIME_DIR / "hf-cache")
else:
    RUNTIME_DIR = ROOT / ".runtime"
    PERSIST_DIR = ROOT / "data" / "vectorstore" / "chroma"

RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DB = PERSIST_DIR / "chroma.sqlite3"


@contextlib.contextmanager
def shared_startup_lock():
    """用共享工作区中的原子目录锁，序列化多实例模型下载和建库。"""
    lock_dir = RUNTIME_DIR / "startup.lock"
    owner = False
    deadline = time.time() + 900

    while True:
        try:
            os.mkdir(lock_dir)
            (lock_dir / "owner.pid").write_text(str(os.getpid()), encoding="utf-8")
            owner = True
            break
        except FileExistsError:
            if time.time() > deadline:
                # 正常建库约1-2分钟；超时后按僵死锁处理。
                shutil.rmtree(lock_dir, ignore_errors=True)
                continue
            time.sleep(2)

    try:
        yield
    finally:
        if owner:
            shutil.rmtree(lock_dir, ignore_errors=True)


def ensure_index() -> None:
    if CHROMA_DB.exists():
        return
    if not CHUNKS.exists():
        raise SystemExit("缺少 data/processed/chunks.jsonl，无法在空间内构建索引")
    from src.build_index import main as build_index

    print("[space] 首次启动，构建向量库 ...")
    build_index()


with shared_startup_lock():
    ensure_index()

from src.app import demo  # noqa: E402

if __name__ == "__main__":
    demo.launch()
