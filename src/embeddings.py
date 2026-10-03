"""BGE 向量化封装。"""
from __future__ import annotations

import os
import pathlib

DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"
_REQUIRED_MODEL_FILES = [
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.txt",
    "model.safetensors",
]


def _runtime_dir() -> pathlib.Path:
    if pathlib.Path("/mnt/workspace").exists():
        return pathlib.Path("/mnt/workspace") / "chemlab-sop-copilot"
    return pathlib.Path(__file__).resolve().parent.parent / ".runtime"


def _model_is_complete(model_dir: str | pathlib.Path) -> bool:
    path = pathlib.Path(model_dir)
    return all((path / name).exists() for name in _REQUIRED_MODEL_FILES)


def _resolve_model_path(model_name: str) -> tuple[str, bool]:
    """解析模型目录，优先使用本地缓存和 ModelScope 源。"""
    runtime = _runtime_dir()
    if pathlib.Path("/mnt/workspace").exists():
        runtime.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("MODELSCOPE_CACHE", str(runtime / "modelscope-cache"))
        os.environ.setdefault("HF_HOME", str(runtime / "hf-cache"))
        os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

    from huggingface_hub import snapshot_download

    try:
        local_hf_path = snapshot_download(model_name, local_files_only=True)
        if _model_is_complete(local_hf_path):
            return local_hf_path, True
    except Exception:
        pass

    # 隔离缓存目录，避免多实例并发写入默认临时目录。
    try:
        try:
            from modelscope.hub.snapshot_download import (
                snapshot_download as modelscope_snapshot_download,
            )
        except ImportError:
            from modelscope import snapshot_download as modelscope_snapshot_download

        model_dir = modelscope_snapshot_download(model_name)
        if not _model_is_complete(model_dir):
            raise RuntimeError(f"模型下载不完整: {model_dir}")
        return model_dir, True
    except Exception:
        pass

    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    hf_path = snapshot_download(model_name, local_files_only=False)
    if not _model_is_complete(hf_path):
        raise RuntimeError(f"模型下载不完整: {hf_path}")
    return hf_path, False


class Embedder:
    def __init__(self, model_name: str = DEFAULT_MODEL, device: str | None = None) -> None:
        import torch
        from transformers import AutoModel, AutoTokenizer

        model_path, local_files_only = _resolve_model_path(model_name)

        self.torch = torch
        self.name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path, local_files_only=local_files_only
        )
        self.model = AutoModel.from_pretrained(
            model_path, local_files_only=local_files_only
        )
        self.model.eval()

        if device:
            self.device = torch.device(device)
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
        self.model.to(self.device)

    def encode(self, texts: list[str], batch_size: int = 32, show_progress: bool = False):
        import numpy as np

        all_embeddings = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            inputs = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(self.device)

            with self.torch.no_grad():
                outputs = self.model(**inputs)

            # BGE v1.5 使用 CLS 位置向量。
            cls_embeddings = outputs.last_hidden_state[:, 0]
            normalized = self.torch.nn.functional.normalize(
                cls_embeddings, p=2, dim=1
            )
            all_embeddings.append(normalized.cpu().numpy())

            if show_progress:
                print(f"encoded {min(start + batch_size, len(texts))}/{len(texts)}")

        return np.concatenate(all_embeddings, axis=0)
