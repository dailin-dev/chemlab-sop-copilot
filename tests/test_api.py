"""FastAPI 接口测试。"""
from fastapi.testclient import TestClient

from src import main


client = TestClient(main.app)


def _fake_answer(question, k=5):
    return {
        "answer": "这是模拟答案 [1]",
        "references": ["[1] 模拟文档（V2.0，current）第1页 来源：https://example.com"],
    }


class _FakeAgent:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def run(self, question, max_steps=5):
        return "模拟 Agent 答案"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ask_success(monkeypatch):
    monkeypatch.setattr(main.rag, "answer_question", _fake_answer)
    response = client.post("/ask", json={"question": "如何校准？", "k": 5})
    assert response.status_code == 200
    body = response.json()
    assert "模拟答案" in body["answer"]
    assert body["citations"]


def test_versions_success(monkeypatch):
    monkeypatch.setattr(
        main,
        "load_versions",
        lambda doc_id: {
            "doc_id": doc_id,
            "current_version": "V2.0",
            "versions": [{"version": "V2.0", "status": "current"}],
        },
    )
    response = client.get("/sop/SOP-ICPMS-001/versions")
    assert response.status_code == 200
    assert response.json()["current_version"] == "V2.0"


def test_agent_chat_success(monkeypatch):
    monkeypatch.setattr(main.agent_module, "Agent", _FakeAgent)
    response = client.post(
        "/agent/chat", json={"question": "V1.0 有效吗？", "session_id": "s1"}
    )
    assert response.status_code == 200
    assert "Agent" in response.json()["answer"]
    assert response.json()["session_id"] == "s1"


def test_missing_api_key_rejected(monkeypatch):
    monkeypatch.setattr(main, "REQUIRE_API_KEY", True)
    monkeypatch.setattr(main, "APP_API_KEY", "secret")
    response = client.get("/health")
    assert response.status_code == 200
    protected = client.post("/ask", json={"question": "x"})
    assert protected.status_code == 401


def test_correct_api_key_accepted(monkeypatch):
    monkeypatch.setattr(main, "REQUIRE_API_KEY", True)
    monkeypatch.setattr(main, "APP_API_KEY", "secret")
    monkeypatch.setattr(main.rag, "answer_question", _fake_answer)
    response = client.post(
        "/ask",
        json={"question": "x"},
        headers={"X-API-Key": "secret"},
    )
    assert response.status_code == 200