"""BGE Embedding：使用本地缓存的 BGE 模型，输出归一化向量（配合 cosine）。"""
from __future__ import annotations

DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"


class Embedder:
    def __init__(self, model_name: str = DEFAULT_MODEL, device: str | None = None) -> None:
        import torch
        from huggingface_hub import snapshot_download
        from transformers import AutoModel, AutoTokenizer

        # 离线环境下直接读取本地快照，避免每次启动访问 huggingface.co。
        model_path = snapshot_download(model_name, local_files_only=True)

        self.torch = torch
        self.name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path, local_files_only=True
        )
        self.model = AutoModel.from_pretrained(model_path, local_files_only=True)
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

            # bge-small-zh-v1.5 使用 CLS 向量作为句向量。
            cls_embeddings = outputs.last_hidden_state[:, 0]
            normalized = self.torch.nn.functional.normalize(
                cls_embeddings, p=2, dim=1
            )
            all_embeddings.append(normalized.cpu().numpy())

            if show_progress:
                print(f"encoded {min(start + batch_size, len(texts))}/{len(texts)}")

        return np.concatenate(all_embeddings, axis=0)
