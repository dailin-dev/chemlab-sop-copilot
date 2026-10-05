"""FastAPI 服务入口。"""
from __future__ import annotations

import os
import pathlib
import time

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel

from . import agent as agent_module
from . import rag

ROOT = pathlib.Path(__file__).resolve().parent.parent
META_CSV = ROOT / "data" / "processed" / "sop_metadata.csv"

APP_API_KEY = os.getenv("APP_API_KEY", "chemlab-demo-key-2026")
REQUIRE_API_KEY = os.getenv("REQUIRE_API_KEY", "false").lower() == "true"

app = FastAPI(title="ChemLab SOP Copilot", version="1.0.0")


class AskRequest(BaseModel):
    question: str
    k: int = 5


class Citation(BaseModel):
    ref: str


class AskResponse(BaseModel):
    answer: str
    citations: list[str]


class AgentChatRequest(BaseModel):
    question: str
    session_id: str | None = None


class AgentChatResponse(BaseModel):
    answer: str
    session_id: str | None = None


def verify_api_key(x_api_key: str = Header(default="")) -> bool:
    if not REQUIRE_API_KEY:
        return True
    if not x_api_key or x_api_key != APP_API_KEY:
        raise HTTPException(status_code=401, detail="无效或缺失 X-API-Key")
    return True


@app.middleware("http")
async def access_log(request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("请求处理异常: {} {}", request.method, request.url.path)
        raise
    elapsed_ms = (time.time() - start) * 1000
    logger.info(
        "{} {} {} {:.0f}ms",
        request.method, request.url.path, response.status_code, elapsed_ms,
    )
    return response


@app.exception_handler(Exception)
async def unhandled_exception(request, exc):
    logger.exception("未捕获异常: {}", exc)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})


def load_versions(doc_id: str) -> dict:
    df = pd.read_csv(META_CSV).fillna("")
    sub = df[df["doc_id"].str.lower() == doc_id.lower()]
    if not len(sub):
        raise HTTPException(status_code=404, detail=f"未找到文档 {doc_id}")
    versions = sub[
        ["version", "status", "effective_date", "expiry_date"]
    ].to_dict("records")
    current = next((v["version"] for v in versions if v["status"] == "current"), None)
    return {"doc_id": doc_id, "current_version": current, "versions": versions}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse, dependencies=[Depends(verify_api_key)])
def ask(request: AskRequest):
    result = rag.answer_question(request.question, k=request.k)
    return AskResponse(answer=result["answer"], citations=result["references"])


@app.post(
    "/agent/chat",
    response_model=AgentChatResponse,
    dependencies=[Depends(verify_api_key)],
)
def agent_chat(request: AgentChatRequest):
    # 当前接口不持久化会话，Agent 记忆仅在单次请求内有效。
    agent = agent_module.Agent(verbose=False)
    answer = agent.run(request.question)
    return AgentChatResponse(answer=answer, session_id=request.session_id)


@app.get("/sop/{doc_id}/versions", dependencies=[Depends(verify_api_key)])
def versions(doc_id: str):
    return load_versions(doc_id)