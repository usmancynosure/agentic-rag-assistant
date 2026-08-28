"""Unit tests for the agent orchestrator (merge + generate + re-query loop)."""

from __future__ import annotations

from app.agent.merge import merge_evidence
from app.agent.orchestrator import AgentOrchestrator
from app.agent.state import Evidence
from app.core.config import get_settings
from app.services.retrieval.answerer import Answerer


class ScriptedPlanner:
    """Returns a preset plan per successive call."""

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
        self.description = f"{name} tool"
        self._evidence = evidence
        self.calls = 0

    def run(self, query: str, *, document_id: str | None = None) -> list[Evidence]:
        self.calls += 1
        return list(self._evidence)


class FakeLLM:
    def __init__(self, reply: str) -> None:
        self.reply = reply

    def generate(self, *, system: str, prompt: str, max_tokens: int) -> str:
        return self.reply


def _vec_evidence() -> Evidence:
    return Evidence(
        text="Grounding fact.", origin="vector", score=0.9, source_id="chk_1", title="a.txt"
    )


def _web_evidence() -> Evidence:
    return Evidence(
        text="Live fact.",
        origin="web",
        score=0.8,
        source_id="https://ex.com/x",
        title="Example",
        url="https://ex.com/x",
    )


# --- merge tests ---


def test_merge_ranks_dedupes_and_maps_origins() -> None:
    ev = [_web_evidence(), _vec_evidence(), _vec_evidence()]  # duplicate vector
    ctx = merge_evidence(ev, token_budget=1000)
    assert len(ctx.passages) == 2  # deduped by source_id
    assert ctx.passages[0].origin == "vector"  # 0.9 ranked first
    assert ctx.passages[1].origin == "web"
    assert ctx.passages[1].url == "https://ex.com/x"


# --- orchestrator tests ---


def _orchestrator(planner, tools, reply) -> AgentOrchestrator:
    return AgentOrchestrator(
        planner=planner,
        tools=tools,
        answerer=Answerer(llm=FakeLLM(reply), max_tokens=256),
        settings=get_settings(),
    )


def test_happy_path_single_pass() -> None:
    planner = ScriptedPlanner([["vector_search"]])
    vector = StaticTool("vector_search", [_vec_evidence()])
    orch = _orchestrator(planner, [vector], reply="Answer grounded [1].")

    result = orch.run(question="q", max_iterations=2)

    assert result.answer == "Answer grounded [1]."
    assert [c.index for c in result.citations] == [1]
    assert result.tools_run == ["vector_search"]
    assert result.iterations == 1
    assert vector.calls == 1


def test_requery_switches_tool_when_first_pass_insufficient() -> None:
    # Pass 1 plans web_search which returns nothing -> insufficient -> re-query.
    # Pass 2 plans vector_search which grounds the answer.
    planner = ScriptedPlanner([["web_search"], ["vector_search"]])
    web = StaticTool("web_search", [])  # returns no evidence
    vector = StaticTool("vector_search", [_vec_evidence()])
    orch = _orchestrator(planner, [web, vector], reply="Answer [1].")

    result = orch.run(question="q", max_iterations=2)

    assert result.tools_run == ["web_search", "vector_search"]
    assert result.iterations == 2
    assert [c.index for c in result.citations] == [1]


def test_unknown_planned_tool_is_skipped() -> None:
    planner = ScriptedPlanner([["nonexistent", "vector_search"]])
    vector = StaticTool("vector_search", [_vec_evidence()])
    orch = _orchestrator(planner, [vector], reply="Answer [1].")

    result = orch.run(question="q", max_iterations=1)
    assert result.tools_run == ["vector_search"]


def test_no_evidence_returns_insufficient() -> None:
    planner = ScriptedPlanner([["vector_search"]])
    vector = StaticTool("vector_search", [])
    orch = _orchestrator(planner, [vector], reply="unused")

    result = orch.run(question="q", max_iterations=1)
    assert "don't have enough information" in result.answer
    assert result.citations == []
