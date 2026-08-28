"""Unit tests for the Tavily web_search tool."""

from __future__ import annotations

from typing import Any

from app.agent.tools.base import Tool
from app.agent.tools.web_search import TavilySearchTool


class FakeTavily:
    def __init__(self, results: list[dict[str, Any]]) -> None:
        self._results = results
        self.last: dict[str, Any] = {}

    def search(self, query: str, *, max_results: int) -> dict[str, Any]:
        self.last = {"query": query, "max_results": max_results}
        return {"results": self._results}


def test_satisfies_tool_protocol() -> None:
    tool = TavilySearchTool(api_key="k", client=FakeTavily([]))
    assert isinstance(tool, Tool)
    assert tool.name == "web_search"


def test_run_maps_results_to_web_evidence() -> None:
    client = FakeTavily(
        [
            {"title": "Paris", "url": "https://ex.com/p", "content": "Paris info", "score": 0.8},
            {"title": "France", "url": "https://ex.com/fr", "content": "Fr info", "score": 0.6},
        ]
    )
    tool = TavilySearchTool(api_key="k", max_results=5, client=client)
    ev = tool.run("capital of France")

    assert [e.origin for e in ev] == ["web", "web"]
    assert ev[0].url == "https://ex.com/p"
    assert ev[0].source_id == "https://ex.com/p"
    assert ev[0].title == "Paris"
    assert ev[0].text == "Paris info"
    assert client.last["max_results"] == 5


def test_results_without_content_are_dropped() -> None:
    client = FakeTavily([{"title": "empty", "url": "https://ex.com/e", "content": ""}])
    tool = TavilySearchTool(api_key="k", client=client)
    assert tool.run("q") == []


def test_missing_api_key_returns_empty_without_calling() -> None:
    tool = TavilySearchTool(api_key="")  # no client injected either
    assert tool.run("q") == []
