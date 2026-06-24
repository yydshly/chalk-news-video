"""Tests for fetch_hot_ai_news keyword matching (CP15.2.6).

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


if __name__ == "__main__":
    print("Running CP15.2.6 keyword matching tests...\n")
    success = run_tests()
    sys.exit(0 if success else 1)
