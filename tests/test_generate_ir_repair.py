"""Tests for beat budget enforcement (CP15.5.2).

Run with: python -m pytest tests/test_generate_ir_repair.py -v
Or directly: python tests/test_generate_ir_repair.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.generate_ir import _enforce_beat_budget


def _make_semantic_ir(nodes, edges, callouts, beats):
    return {
        "schema_version": "0.1",
        "meta": {"source_title": "Test", "source_url": "http://test.com", "source_name": "Test", "lang": "zh"},
        "structure_type": "causal_chain",
        "title": "测试标题",
        "summary": "测试摘要",
        "nodes": nodes,
        "edges": edges,
        "callouts": callouts,
        "beats": beats,
    }


def _beat(id, reveal, speaker="host", narration="测试口播"):
    return {"id": id, "reveal": reveal, "speaker": speaker, "narration": narration}


def test_beat_budget_within_range_no_change():
    """Beats within [6, 10] should not be modified."""
    sem = _make_semantic_ir(
        [{"id": "n1", "label": "A"}, {"id": "n2", "label": "B"}],
        [{"id": "e1", "from": "n1", "to": "n2", "label": "leads to"}],
        [],
        [_beat("b1", "title"), _beat("b2", "n1"), _beat("b3", "n2"), _beat("b4", "e1"),
         _beat("b5", "n1"), _beat("b6", "n2")]
    )
    sem2, records = _enforce_beat_budget(sem, max_beats=10, min_beats=6)
    assert len(sem2["beats"]) == 6
    assert records == []
    # Confirm same object
    assert sem2["beats"][0]["id"] == "b1"


def test_beat_budget_over_10_trims_to_10():
    """Beats > 10 should be trimmed to exactly 10, keeping first (title) and last."""
    # Create 11 beats
    beats = [_beat("b1", "title")]
    for i in range(2, 12):
        beats.append(_beat(f"b{i}", f"n{(i % 3) + 1}"))
    sem = _make_semantic_ir(
        [{"id": "n1", "label": "A"}, {"id": "n2", "label": "B"}],
        [{"id": "e1", "from": "n1", "to": "n2", "label": "leads to"}],
        [],
        beats
    )
    assert len(sem["beats"]) == 11
    sem2, records = _enforce_beat_budget(sem, max_beats=10, min_beats=6)
    assert len(sem2["beats"]) == 10, f"Expected 10, got {len(sem2['beats'])}"
    assert sem2["beats"][0]["reveal"] == "title"  # title beat always preserved
    assert records[0]["type"] == "BEAT_BUDGET_TRIM"
    assert records[0]["before_beats"] == 11
    assert records[0]["after_beats"] == 10


def test_beat_budget_under_6_no_fabrication():
    """Beats < 6 should NOT be augmented (no fabrication)."""
    sem = _make_semantic_ir(
        [{"id": "n1", "label": "A"}, {"id": "n2", "label": "B"}],
        [{"id": "e1", "from": "n1", "to": "n2", "label": "leads to"}],
        [],
        [_beat("b1", "title"), _beat("b2", "n1"), _beat("b3", "n2")]
    )
    assert len(sem["beats"]) == 3
    sem2, records = _enforce_beat_budget(sem, max_beats=10, min_beats=6)
    assert len(sem2["beats"]) == 3  # unchanged
    assert records[0]["type"] == "BEAT_BUDGET_UNDER"
    assert records[0]["before_beats"] == 3


def test_beat_budget_preserves_title_reveal():
    """First beat (title reveal) must always be preserved even when trimming."""
    # 12 beats
    beats = [_beat("b1", "title")]
    for i in range(2, 13):
        beats.append(_beat(f"b{i}", f"n{(i % 3) + 1}"))
    sem = _make_semantic_ir(
        [{"id": "n1", "label": "A"}, {"id": "n2", "label": "B"}],
        [{"id": "e1", "from": "n1", "to": "n2", "label": "leads to"}],
        [],
        beats
    )
    sem2, records = _enforce_beat_budget(sem, max_beats=10, min_beats=6)
    assert sem2["beats"][0]["reveal"] == "title"
    assert sem2["beats"][0]["id"] == "b1"


def test_beat_budget_preserves_last_beat():
    """Last beat must always be preserved when trimming."""
    beats = [_beat("b1", "title")]
    for i in range(2, 12):
        beats.append(_beat(f"b{i}", f"n{(i % 3) + 1}"))
    beats.append(_beat("b12", "e1"))  # last beat reveals an edge
    sem = _make_semantic_ir(
        [{"id": "n1", "label": "A"}, {"id": "n2", "label": "B"}],
        [{"id": "e1", "from": "n1", "to": "n2", "label": "leads to"}],
        [],
        beats
    )
    sem2, records = _enforce_beat_budget(sem, max_beats=10, min_beats=6)
    assert sem2["beats"][-1]["reveal"] == "e1"  # last beat preserved


def test_beat_budget_trim_record_format():
    """Trim repair record must contain before/after counts."""
    beats = [_beat("b1", "title")] + [_beat(f"b{i}", f"n{(i%3)+1}") for i in range(2, 14)]
    sem = _make_semantic_ir(
        [{"id": "n1", "label": "A"}, {"id": "n2", "label": "B"}, {"id": "n3", "label": "C"}],
        [{"id": "e1", "from": "n1", "to": "n2"}],
        [],
        beats
    )
    sem2, records = _enforce_beat_budget(sem, max_beats=10, min_beats=6)
    assert len(records) >= 1
    rec = records[0]
    assert rec["type"] == "BEAT_BUDGET_TRIM"
    assert "before_beats" in rec
    assert "after_beats" in rec
    assert rec["before_beats"] == 13
    assert rec["after_beats"] == 10


def run_tests():
    test_functions = [
        test_beat_budget_within_range_no_change,
        test_beat_budget_over_10_trims_to_10,
        test_beat_budget_under_6_no_fabrication,
        test_beat_budget_preserves_title_reveal,
        test_beat_budget_preserves_last_beat,
        test_beat_budget_trim_record_format,
    ]
    passed = failed = 0
    for tf in test_functions:
        try:
            tf()
            print(f"  PASS: {tf.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {tf.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {tf.__name__}: {e}")
            failed += 1
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    print("Running CP15.5.2 beat budget repair tests...\n")
    success = run_tests()
    sys.exit(0 if success else 1)
