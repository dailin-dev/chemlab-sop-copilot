"""DeepSeek Chat 封装（OpenAI 兼容接口）。"""
from __future__ import annotations

import os
import pathlib

from dotenv import load_dotenv
from openai import OpenAI

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


def get_client() -> OpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("未在 .env 找到 DEEPSEEK_API_KEY")
    return OpenAI(api_key=api_key, base_url=BASE_URL)


def chat(messages, tools=None, temperature: float = 0.2, **kwargs):
    """调用 DeepSeek；传入 tools 即启用 Function Calling。"""
    params = {"model": MODEL, "messages": messages, "temperature": temperature}
    if tools:
        params["tools"] = tools
    params.update(kwargs)
    return get_client().chat.completions.create(**params)