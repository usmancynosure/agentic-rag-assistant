"""Unit tests for the LangGraph skeleton and loop control."""

from __future__ import annotations

from typing import Any

from app.agent.graph import build_agent_graph, should_continue
from app.agent.state import AgentState, Evidence


def test_should_continue_ends_when_done() -> None:
    assert should_continue({"done": True, "iteration": 0, "max_iterations": 3}) == "end"


def test_should_continue_ends_at_max_iterations() -> None:
    assert should_continue({"iteration": 2, "max_iterations": 2}) == "end"


def test_should_continue_loops_otherwise() -> None:
    assert should_continue({"iteration": 0, "max_iterations": 2}) == "continue"


def _stub_graph(*, terminate_after: int) -> Any:
    """Build a graph whose generate node marks done after N iterations."""

    def plan(state: AgentState) -> dict[str, Any]:
        return {"plan": ["vector_search"], "iteration": state.get("iteration", 0) + 1}

    def tools(state: AgentState) -> dict[str, Any]:
        ev = Evidence(
            text="finding",
            origin="vector",
            score=0.9,
            source_id="chk_1",
            title="a.txt",
        )
        return {"evidence": [ev], "tools_run": ["vector_search"]}

    def assemble(_: AgentState) -> dict[str, Any]:
        return {}

    def generate(state: AgentState) -> dict[str, Any]:
        done = state.get("iteration", 0) >= terminate_after
        return {"answer": "draft", "done": done}

    return build_agent_graph(
        plan_node=plan, tools_node=tools, assemble_node=assemble, generate_node=generate
    )


def test_graph_runs_end_to_end_and_accumulates_evidence() -> None:
    app = _stub_graph(terminate_after=1)
    final = app.invoke({"question": "q", "iteration": 0, "max_iterations": 3})

    assert final["answer"] == "draft"
    assert final["done"] is True
    assert final["tools_run"] == ["vector_search"]  # one pass
    assert len(final["evidence"]) == 1


def test_graph_loops_until_max_iterations() -> None:
    # generate never sets done; the loop must stop at max_iterations.
    app = _stub_graph(terminate_after=999)
    final = app.invoke({"question": "q", "iteration": 0, "max_iterations": 3})

    # plan increments iteration each loop; evidence appends each loop.
    assert final["iteration"] == 3
    assert len(final["evidence"]) == 3
    assert final["tools_run"] == ["vector_search", "vector_search", "vector_search"]
