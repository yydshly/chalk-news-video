"""CP18.4: Lightweight test for render_ir.news metadata propagation.

Run:
    python tests/test_layout_news_metadata.py
or:
    python -m pytest tests/test_layout_news_metadata.py -v
"""

import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.layout import build_render_ir


def make_beat(bid, start, end, reveal, speaker="host", narration=""):
    return {"id": bid, "start": start, "end": end, "reveal": reveal,
            "speaker": speaker, "narration": narration}


def test_render_ir_news_full():
    """Test that render_ir.news is correctly populated from semantic_ir."""
    semantic_ir = {
        "schema_version": "0.5",
        "structure_type": "causal_chain",
        "title": "测试新闻标题",
        "summary": "测试摘要",
        "meta": {
            "source_title": "来源标题",
            "source_url": "https://example.com/news",
            "source_name": "Example",
            "published_at": "2026-06-24T00:00:00+00:00",
            "lang": "zh",
        },
        "nodes": [
            {"id": "n1", "label": "节点1", "description": "描述1"},
            {"id": "n2", "label": "节点2", "description": "描述2"},
        ],
        "edges": [
            {"id": "e1", "from": "n1", "to": "n2", "label": "导致"},
        ],
        "beats": [
            make_beat("b1", 0.0, 5.0, "title", "host", "标题 narration"),
            make_beat("b2", 5.0, 10.0, "n1", "host", "节点1 narration"),
            make_beat("b3", 10.0, 15.0, "e1", "host", "边1 narration"),
            make_beat("b4", 15.0, 20.0, "n2", "host", "节点2 narration"),
        ],
    }

    render_ir = build_render_ir(semantic_ir)

    assert render_ir["news"]["title"] == "测试新闻标题", \
        f"Expected '测试新闻标题', got {render_ir['news']['title']!r}"
    assert render_ir["news"]["summary"] == "测试摘要", \
        f"Expected '测试摘要', got {render_ir['news']['summary']!r}"
    assert render_ir["news"]["url"] == "https://example.com/news", \
        f"Expected 'https://example.com/news', got {render_ir['news']['url']!r}"
    assert render_ir["news"]["source"] == "Example", \
        f"Expected 'Example', got {render_ir['news']['source']!r}"

    print("PASS: test_render_ir_news_full")


def test_render_ir_news_fallback():
    """Test fallback: semantic_ir.title is empty, use meta.source_title."""
    semantic_ir = {
        "schema_version": "0.5",
        "structure_type": "causal_chain",
        "title": "",  # empty — should fall back to meta.source_title
        "summary": "摘要内容",
        "meta": {
            "source_title": "来源标题",
            "source_url": "https://example.com/fallback",
            "source_name": "FallbackSource",
            "lang": "zh",
        },
        "nodes": [
            {"id": "n1", "label": "节点", "description": "desc"},
        ],
        "edges": [],
        "beats": [
            make_beat("b1", 0.0, 5.0, "n1", "host", "node1"),
        ],
    }

    render_ir = build_render_ir(semantic_ir)

    assert render_ir["news"]["title"] == "来源标题", \
        f"Expected fallback '来源标题', got {render_ir['news']['title']!r}"
    assert render_ir["news"]["source"] == "FallbackSource", \
        f"Expected 'FallbackSource', got {render_ir['news']['source']!r}"

    print("PASS: test_render_ir_news_fallback")


def test_render_ir_news_empty():
    """Test empty case: no title anywhere, should get empty string."""
    semantic_ir = {
        "schema_version": "0.5",
        "structure_type": "causal_chain",
        "title": "",
        "summary": "",
        "meta": {},
        "nodes": [
            {"id": "n1", "label": "节点", "description": "desc"},
        ],
        "edges": [],
        "beats": [
            make_beat("b1", 0.0, 5.0, "n1", "host", "node1"),
        ],
    }

    render_ir = build_render_ir(semantic_ir)

    assert render_ir["news"]["title"] == ""
    assert render_ir["news"]["summary"] == ""
    assert render_ir["news"]["url"] == ""
    assert render_ir["news"]["source"] == ""

    print("PASS: test_render_ir_news_empty")


def test_render_ir_news_no_nodes():
    """Test _empty_render_ir path: no nodes → total_duration=0 but news preserved."""
    semantic_ir = {
        "schema_version": "0.5",
        "structure_type": "causal_chain",
        "title": "无节点标题",
        "summary": "无节点摘要",
        "meta": {
            "source_title": "无节点来源",
            "source_url": "https://example.com/no-nodes",
            "source_name": "NoNodesSource",
        },
        "nodes": [],
        "edges": [],
        "beats": [],
    }

    render_ir = build_render_ir(semantic_ir)

    assert render_ir["news"]["title"] == "无节点标题"
    assert render_ir["news"]["summary"] == "无节点摘要"
    assert render_ir["news"]["url"] == "https://example.com/no-nodes"
    assert render_ir["news"]["source"] == "NoNodesSource"
    assert render_ir["total_duration"] == 0.0

    print("PASS: test_render_ir_news_no_nodes")


if __name__ == "__main__":
    test_render_ir_news_full()
    test_render_ir_news_fallback()
    test_render_ir_news_empty()
    test_render_ir_news_no_nodes()
    print("\nAll tests PASSED.")
