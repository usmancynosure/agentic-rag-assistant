"""Integration tests for the /agent/query endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.agent.orchestrator import AgentOrchestrator
from app.agent.state import Evidence
from app.api.deps import get_orchestrator
from app.core.config import get_settings
from app.main import create_app
from app.services.retrieval.answerer import Answerer


class ScriptedPlanner:
    def __init__(self, plans: list[list[str]]) -> None:
        self._plans = plans
        self._i = 0

    def plan(self, *, question, tools, iteration=0, prior_insufficient=False) -> list[str]:
        plan = self._plans[min(self._i, len(self._plans) - 1)]
        self._i += 1
        return plan


class StaticTool:
    def __init__(self, name: str, evidence: list[Evidence]) -> None:
        self.name = name
        self.description = name
        self._evidence = evidence

    def run(self, query: str, *, document_id: str | None = None) -> list[Evidence]:
        return list(self._evidence)


class FakeLLM:
    def __init__(self, reply: str) -> None:
        self.reply = reply

    def generate(self, *, system: str, prompt: str, max_tokens: int) -> str:
        return self.reply


def _client(planner, tools, reply) -> TestClient:
    orch = AgentOrchestrator(
        planner=planner,
        tools=tools,
        answerer=Answerer(llm=FakeLLM(reply), max_tokens=256),
        settings=get_settings(),
    )
    app = create_app()
    app.dependency_overrides[get_orchestrator] = lambda: orch
    return TestClient(app)


def _vec() -> Evidence:
    return Evidence(
        text="Grounded fact.", origin="vector", score=0.9, source_id="chk_1", title="a.txt"
    )


def _web() -> Evidence:
    return Evidence(
        text="Live fact.",
        origin="web",
        score=0.8,
        source_id="https://ex.com/x",
        title="Example",
        url="https://ex.com/x",
    )


def test_agent_query_returns_answer_citations_sources_and_trace() -> None:
    planner = ScriptedPlanner([["vector_search", "web_search"]])
    tools = [StaticTool("vector_search", [_vec()]), StaticTool("web_search", [_web()])]
    client = _client(planner, tools, reply="Grounded [1] and live [2].")

    resp = client.post("/api/v1/agent/query", json={"question": "q"})
    assert resp.status_code == 200
    body = resp.json()

    assert body["answer"] == "Grounded [1] and live [2]."
    assert {c["index"] for c in body["citations"]} == {1, 2}
    # web citation carries its url + origin
    web_cite = next(c for c in body["citations"] if c["origin"] == "web")
    assert web_cite["url"] == "https://ex.com/x"
    assert body["tools_run"] == ["vector_search", "web_search"]
    assert body["iterations"] == 1
    assert len(body["sources"]) == 2


def test_agent_query_insufficient_evidence() -> None:
    planner = ScriptedPlanner([["vector_search"]])
    tools = [StaticTool("vector_search", [])]
    client = _client(planner, tools, reply="unused")

    resp = client.post("/api/v1/agent/query", json={"question": "q", "max_iterations": 1})
    body = resp.json()
    assert "don't have enough information" in body["answer"]
    assert body["citations"] == []


def test_agent_query_validates_max_iterations() -> None:
    planner = ScriptedPlanner([["vector_search"]])
    client = _client(planner, [StaticTool("vector_search", [_vec()])], reply="a [1]")
    resp = client.post("/api/v1/agent/query", json={"question": "q", "max_iterations": 99})
    assert resp.status_code == 422
