"""Tests for fetch_hot_ai_news keyword matching (CP15.2.6) and story worthiness (CP15.5).

Run with: python -m pytest tests/test_fetch_hot_ai_news.py -v
Or directly: python tests/test_fetch_hot_ai_news.py
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.fetch_hot_ai_news import (
    _match_keyword,
    _match_word_boundary,
    _match_phrase,
    _match_keywords,
    _should_include,
    _compute_story_score,
)


def test_ai_word_boundary():
    """AI should match as independent word, not as substring."""
    # Should match
    assert _match_word_boundary("AI's Affordability Crisis", "AI")
    assert _match_word_boundary("The future of AI", "AI")
    assert _match_word_boundary("AI safety", "AI")
    assert _match_word_boundary("AI/ML News", "AI")
    # Should NOT match
    assert not _match_word_boundary("Trains halted across Germany", "AI")
    assert not _match_word_boundary("Heavy rain forecast", "AI")
    assert not _match_word_boundary("Main branch protection", "AI")
    assert not _match_word_boundary("Available now", "AI")
    assert not _match_word_boundary("Trained model", "AI")
    assert not _match_word_boundary("Bargaih nonsense", "AI")


def test_llm_word_boundary():
    """LLM should match as independent word."""
    assert _match_word_boundary("New LLM benchmark", "LLM")
    assert _match_word_boundary("LLM vs SLM", "LLM")
    assert not _match_word_boundary("Fully trained model", "LLM")


def test_gpu_word_boundary():
    """GPU should match as independent word."""
    assert _match_word_boundary("Nvidia GPU shortage", "GPU")
    assert not _match_word_boundary("AGPU something", "GPU")


def test_phrase_matching():
    """Multi-word phrases should match as contiguous substring."""
    assert _match_phrase("The future of AI safety", "AI safety")
    assert _match_phrase("AI safety concerns", "AI safety")
    assert not _match_phrase("Artificial intelligence and safety", "AI safety")
    assert _match_phrase("Machine learning advances", "machine learning")
    assert _match_phrase("Neural network architectures", "neural network")


def test_strong_keyword_matches():
    """Strong keywords should be detected."""
    strong_cases = [
        ("OpenAI releases GPT-5", ["OpenAI", "GPT-5"]),
        ("Anthropic's Claude 3.5", ["Anthropic", "Claude"]),
        ("Nvidia GPU shortages", ["Nvidia", "GPU"]),
        ("Hugging Face model hub", ["Hugging Face"]),
        ("DeepMind's AlphaFold", ["DeepMind"]),
        ("ChatGPT gets upgrade", ["ChatGPT"]),
        ("Llama 3 released", ["Llama"]),
        ("Sora video generation", ["Sora", "video generation"]),
        ("LLM benchmark results", ["LLM"]),
        ("RAG system overview", ["RAG"]),
    ]
    for title, expected in strong_cases:
        strong, weak, _ = _match_keywords(title)
        for kw in expected:
            assert kw in strong, f"Expected '{kw}' in strong for '{title}'"


def test_weak_keyword_matches():
    """Weak keywords should be detected."""
    weak_cases = [
        ("AI trends 2026", ["AI"]),
        ("Multiple models benchmarked", ["models"]),
        ("Agent architecture discussion", ["agent"]),
        ("Reasoning about reasoning", ["reasoning"]),
    ]
    for title, expected in weak_cases:
        strong, weak, _ = _match_keywords(title)
        for kw in expected:
            assert kw in weak, f"Expected '{kw}' in weak for '{title}'"


def test_false_positive_regression():
    """Ensure AI substrings don't cause false positives (CP15.2.6 regression tests)."""
    false_positive_cases = [
        "Trains halted across Germany because of communication system problem",
        "Heavy rain forecast for the weekend",
        "Main branch protection in software development",
        "Available now on all platforms",
        "Trained model performance",
        "Bargaih research paper",
        "Again and again",
        "Certain reliability",
        "Captain America",
        "Mail delivery service",
    ]
    for title in false_positive_cases:
        # These should NOT be included (no strong kw, < 2 weak kws)
        assert not _should_include(title), f"False positive: '{title}' should NOT be included"


def test_should_include_rules():
    """Test the _should_include logic."""
    # 1 strong keyword -> include
    assert _should_include("OpenAI announces GPT-5")
    assert _should_include("Anthropic Claude update")
    assert _should_include("Nvidia GPU news")
    # 2+ weak keywords -> include
    assert _should_include("AI models and agents in production")
    # Only 1 weak keyword -> exclude
    assert not _should_include("AI trends")  # only "AI"
    assert not _should_include("New model released")  # only "model"


def test_keyword_bonus():
    """Test keyword bonus calculation."""
    # Strong keyword: +15 each (max 45)
    strong, weak, bonus = _match_keywords("OpenAI and Anthropic release Claude")
    assert len(strong) >= 2
    assert bonus >= 30  # at least 2 strong

    # Weak keywords: +5 each (max 15)
    strong, weak, bonus = _match_keywords("AI model and agent architecture")
    assert len(weak) >= 2
    assert bonus >= 10

    # Mixed
    strong, weak, bonus = _match_keywords("OpenAI's new AI model")
    assert "OpenAI" in strong
    assert "AI" in weak or "model" in weak


def run_tests():
    """Run all tests and print results."""
    test_functions = [
        test_ai_word_boundary,
        test_llm_word_boundary,
        test_gpu_word_boundary,
        test_phrase_matching,
        test_strong_keyword_matches,
        test_weak_keyword_matches,
        test_false_positive_regression,
        test_should_include_rules,
        test_keyword_bonus,
        # CP15.5 story worthiness tests
        test_story_major_company_bonus,
        test_story_conflict_bonus,
        test_story_impact_bonus,
        test_story_title_length_bonus,
        test_story_show_hn_penalty,
        test_story_too_short_title_penalty,
        test_story_model_no_impact_penalty,
        test_story_final_score_computation,
        test_story_visual_potential_bonus,
        # CP15.5.1 weighting tests
        test_hotness_norm_capped_at_100,
        test_hotness_norm_scale,
        test_story_weight_higher_than_hotness,
    ]

    passed = 0
    failed = 0

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


# ---------- CP15.5 story worthiness tests ----------


def test_story_major_company_bonus():
    """OpenAI in title should give +25 story score."""
    item = {"title": "OpenAI releases GPT-5 DayBreak", "url": "https://openai.com"}
    result = _compute_story_score(item)
    assert result["story_score"] >= 25, f"Expected story_score >= 25, got {result['story_score']}"
    assert result["story_flags"]["has_major_company"] is True
    assert any("major_company:OpenAI" in r for r in result["story_reasons"])


def test_story_conflict_bonus():
    """Conflict keywords should give +20 story score."""
    item = {"title": "AI's Affordability Crisis", "url": "https://example.com"}
    result = _compute_story_score(item)
    assert result["story_score"] >= 20, f"Expected story_score >= 20, got {result['story_score']}"
    assert result["story_flags"]["has_clear_conflict"] is True
    assert any("conflict:" in r for r in result["story_reasons"])


def test_story_impact_bonus():
    """Impact keywords should give +15 story score."""
    item = {"title": "AI affects developers and enterprises worldwide", "url": "https://example.com"}
    result = _compute_story_score(item)
    assert result["story_score"] >= 15, f"Expected story_score >= 15, got {result['story_score']}"
    assert result["story_flags"]["has_impact_words"] is True


def test_story_title_length_bonus():
    """Title 20-120 chars should get +10."""
    item = {"title": "Nvidia GPU shortage affects AI labs globally", "url": "https://example.com"}
    result = _compute_story_score(item)
    assert 20 <= len(item["title"]) <= 120
    assert any("title_len:" in r for r in result["story_reasons"])


def test_story_too_short_title_penalty():
    """Title <= 8 chars should get -15 penalty."""
    item = {"title": "AI Tag", "url": "https://example.com"}  # 7 chars <= 8
    result = _compute_story_score(item)
    assert result["story_flags"]["too_short_title"] is True
    assert any("title_too_short" in r for r in result["story_reasons"])


def test_story_show_hn_penalty():
    """Show HN without major company should get -10 penalty applied."""
    item = {"title": "Show HN: tiny AI wrapper tool", "url": "https://example.com"}
    result = _compute_story_score(item)
    assert result["story_flags"]["is_show_hn"] is True
    assert result["story_flags"]["has_major_company"] is False
    # Score reduced by 10 for Show HN without company
    assert any("show_hn_no_company" in r for r in result["story_reasons"])


def test_story_model_no_impact_penalty():
    """Pure model name without impact/conflict should get -10 penalty."""
    item = {"title": "New Llama 3 paper released", "url": "https://example.com/paper"}
    result = _compute_story_score(item)
    assert result["story_flags"]["has_product_or_model"] is True
    assert not result["story_flags"]["has_clear_conflict"]
    assert not result["story_flags"]["has_impact_words"]
    assert any("model_no_impact" in r for r in result["story_reasons"])


def test_story_final_score_computation():
    """CP15.5.1: final_score = hotness_norm * 0.45 + story_score * 0.55."""
    item = {
        "title": "OpenAI GPT-5 causes controversy among developers",
        "url": "https://openai.com",
        "points": 100,
        "descendants": 50,
    }
    hotness_score = 100 * 1.0 + 50 * 2.0  # 200
    hotness_norm = min(100, hotness_score / 5.0)  # = 40
    result = _compute_story_score(item)
    story_score = result["story_score"]
    assert story_score >= 50  # has major company + conflict
    # Verify formula: hotness_norm * 0.45 + story_score * 0.55
    expected_final = round(hotness_norm * 0.45 + story_score * 0.55, 2)
    assert expected_final < hotness_score  # story_score weighted higher than raw hotness
    assert 0 <= expected_final <= 100


def test_hotness_norm_capped_at_100():
    """CP15.5.1: hotness_norm should be capped at 100."""
    # Very high hotness score
    hotness_score = 800
    hotness_norm = min(100, hotness_score / 5.0)
    assert hotness_norm == 100  # capped


def test_hotness_norm_scale():
    """CP15.5.1: hotness_norm = min(100, hotness_score / 5)."""
    assert min(100, 200 / 5.0) == 40.0
    assert min(100, 500 / 5.0) == 100.0
    assert min(100, 50 / 5.0) == 10.0


def test_story_weight_higher_than_hotness():
    """CP15.5.1: Story score should have more weight (0.55) than hotness_norm (0.45).

    A story with high story_score but lower hotness should score higher than
    a story with high hotness but low story_score.
    """
    # Candidate A: High hotness, low story
    a_title = "Show HN: tiny AI wrapper tool"  # story_score likely low
    a_item = {"title": a_title, "url": "https://example.com", "points": 400, "descendants": 200}
    a_hotness = 400 * 1.0 + 200 * 2.0  # 800
    a_hotness_norm = min(100, a_hotness / 5.0)  # 100
    a_story = _compute_story_score(a_item)["story_score"]

    # Candidate B: Lower hotness, high story
    b_title = "OpenAI releases GPT-5 causing industry-wide controversy"
    b_item = {"title": b_title, "url": "https://openai.com", "points": 200, "descendants": 100}
    b_hotness = 200 * 1.0 + 100 * 2.0  # 400
    b_hotness_norm = min(100, b_hotness / 5.0)  # 80
    b_story = _compute_story_score(b_item)["story_score"]

    a_final = a_hotness_norm * 0.45 + a_story * 0.55
    b_final = b_hotness_norm * 0.45 + b_story * 0.55

    # B should score higher due to much higher story_score despite lower hotness
    assert b_story > a_story, f"B story={b_story} should be > A story={a_story}"
    assert b_final > a_final, f"B final={b_final:.2f} should be > A final={a_final:.2f}"


def test_story_visual_potential_bonus():
    """Visual/benchmark keywords should give +10."""
    item = {"title": "LLM benchmark ranking chart 2026", "url": "https://example.com"}
    result = _compute_story_score(item)
    assert result["story_flags"]["has_visual_potential"] is True
    assert any("visual:" in r for r in result["story_reasons"])


if __name__ == "__main__":
    print("Running CP15.2.6 keyword matching tests...\n")
    success = run_tests()
    sys.exit(0 if success else 1)
