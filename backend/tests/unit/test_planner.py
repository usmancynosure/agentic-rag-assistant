"""Unit tests for the planner node."""

from __future__ import annotations

from app.agent.nodes.planner import Planner, parse_plan
from app.agent.state import Evidence


class _StubTool:
    def __init__(self, name: str, desc: str = "desc") -> None:
        self.name = name
        self.description = desc

    def run(self, query: str, *, document_id: str | None = None) -> list[Evidence]:
        return []


class FakeLLM:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.last_prompt = ""

    def generate(self, *, system: str, prompt: str, max_tokens: int) -> str:
        self.last_prompt = prompt
        return self.reply


VALID = {"vector_search", "web_search"}


def test_parse_plan_extracts_valid_names() -> None:
    raw = '{"tools": ["vector_search", "web_search"], "reasoning": "both"}'
    assert parse_plan(raw, VALID) == ["vector_search", "web_search"]


def test_parse_plan_filters_invalid_and_dedupes() -> None:
    raw = '{"tools": ["vector_search", "bogus", "vector_search"]}'
    assert parse_plan(raw, VALID) == ["vector_search"]


def test_parse_plan_handles_prose_wrapped_json() -> None:
    raw = 'Sure! Here is the plan:\n{"tools": ["web_search"]}\nHope that helps.'
    assert parse_plan(raw, VALID) == ["web_search"]


def test_parse_plan_falls_back_to_name_scan_on_bad_json() -> None:
    raw = "I think we should use vector_search here."
    assert parse_plan(raw, VALID) == ["vector_search"]


def test_planner_returns_parsed_plan() -> None:
    planner = Planner(llm=FakeLLM('{"tools": ["web_search"]}'))
    tools = [_StubTool("vector_search"), _StubTool("web_search")]
    assert planner.plan(question="latest news?", tools=tools) == ["web_search"]


def test_planner_defaults_to_vector_search_on_garbage() -> None:
    planner = Planner(llm=FakeLLM("no json, no tool names at all"))
    tools = [_StubTool("vector_search"), _StubTool("web_search")]
    assert planner.plan(question="q", tools=tools) == ["vector_search"]


def test_planner_empty_tools_returns_empty() -> None:
    planner = Planner(llm=FakeLLM("{}"))
    assert planner.plan(question="q", tools=[]) == []


def test_planner_requery_prompt_includes_hint() -> None:
    llm = FakeLLM('{"tools": ["web_search"]}')
    planner = Planner(llm=llm)
    tools = [_StubTool("vector_search"), _StubTool("web_search")]
    planner.plan(question="q", tools=tools, iteration=1, prior_insufficient=True)
    assert "did not retrieve enough evidence" in llm.last_prompt
