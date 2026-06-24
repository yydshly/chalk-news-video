"""Fetch hot AI news from Hacker News.

Checkpoint 15.2.5 responsibilities:
- Fetch top stories from HN Firebase API.
- Filter by AI-related keywords.
- Score by points, comments, recency, and keyword matches.
- Output hot_ai_candidates.json (top N candidates).
- Output latest_news.json (top 1 selected news).
- Do NOT fetch full article text (no paywall bypass, no copyright infringement).
- Do NOT use login or authentication.
"""

import argparse
import datetime
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Optional

import requests

from .utils import PROJECT_ROOT, save_json


# Default AI-related keywords for filtering and scoring
DEFAULT_KEYWORDS = [
    "AI", "LLM", "OpenAI", "Anthropic", "Claude", "Gemini",
    "agent", "agents", "inference", "model", "models",
    "GPU", "Nvidia", "AI safety", "DeepMind", "Hugging Face",
    "ChatGPT", "GPT-4", "GPT-5", "o1", "o3", "Claude 3",
    "mistral", "Llama", "Gemma", "Stable Diffusion",
    "Sora", "video generation", "reasoning", "chain-of-thought",
    "RAG", "embedding", "vector database",
    "artificial intelligence", "machine learning", "neural network",
]

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
HN_TOP_STORIES_URL = f"{HN_API_BASE}/topstories.json"
HN_ITEM_URL = f"{HN_API_BASE}/item"


# ---------- scoring helpers ----------


def _compute_recency_bonus(epoch_timestamp: int) -> int:
    """Compute recency bonus based on HN item timestamp.

    24h内 +30, 48h内 +15, 72h内 +5
    """
    now = int(time.time())
    age_hours = (now - epoch_timestamp) / 3600
    if age_hours <= 24:
        return 30
    elif age_hours <= 48:
        return 15
    elif age_hours <= 72:
        return 5
    return 0


def _compute_keyword_bonus(title: str, keywords: list[str]) -> tuple[int, list[str]]:
    """Compute keyword bonus from title and return matched keywords.

    Each major keyword match: +10, max +30.
    """
    title_lower = title.lower()
    matched = []
    major_keywords = {
        "openai", "anthropic", "claude", "gemini", "nvidia",
        "llm", "gpt-4", "gpt-5", "o1", "o3", "claude 3",
        "mistral", "llama", "gemma", "stable diffusion",
        "chatgpt", "sora",
    }
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in title_lower:
            matched.append(kw)
            # Only count major keywords for bonus
            if kw_lower in major_keywords:
                pass  # counted below

    # Count major keyword matches for bonus (max 3 x 10 = 30)
    major_matches = sum(1 for kw in matched if kw.lower() in major_keywords)
    bonus = min(major_matches * 10, 30)
    return bonus, matched


def _score_item(item: dict, keywords: list[str]) -> float:
    """Compute hotness score for an HN item.

    score = points * 1.0 + comments * 2.0 + recency_bonus + keyword_bonus
    """
    points = item.get("points", 0) or 0
    comments = item.get("descendants", 0) or 0
    score = points * 1.0 + comments * 2.0

    # Recency bonus
    ts = item.get("time")
    if ts:
        score += _compute_recency_bonus(ts)

    # Keyword bonus
    title = item.get("title", "")
    if title:
        _, matched = _compute_keyword_bonus(title, keywords)
        major_kw = {"openai", "anthropic", "claude", "gemini", "nvidia", "llm",
                    "gpt-4", "gpt-5", "o1", "o3", "claude 3", "mistral",
                    "llama", "gemma", "stable diffusion", "chatgpt", "sora"}
        major_matches = sum(1 for kw in matched if kw.lower() in major_kw)
        score += min(major_matches * 10, 30)

    return score


def _build_rank_reason(item: dict, matched_keywords: list[str], score: float) -> str:
    """Build human-readable rank reason."""
    parts = []
    pts = item.get("points", 0) or 0
    cmts = item.get("descendants", 0) or 0
    parts.append(f"points={pts}")
    parts.append(f"comments={cmts}")
    if matched_keywords:
        parts.append(f"matched={','.join(matched_keywords[:5])}")
    return f"score={score:.0f} " + " ".join(parts)


def _hn_timestamp_to_iso(epoch_timestamp: int) -> str:
    """Convert HN Unix timestamp to ISO string."""
    return datetime.datetime.fromtimestamp(
        epoch_timestamp, tz=datetime.timezone.utc
    ).isoformat(timespec="seconds")


# ---------- HN fetch ----------


def _fetch_hn_top_stories_ids(limit: int = 500) -> list[int]:
    """Fetch top story IDs from HN Firebase API."""
    try:
        resp = requests.get(HN_TOP_STORIES_URL, timeout=10)
        resp.raise_for_status()
        ids = resp.json()
        return ids[:limit]
    except Exception as e:
        print(f"[fetch_hot_ai_news] Failed to fetch HN top stories: {e}", file=sys.stderr)
        return []


def _fetch_hn_item(item_id: int, retries: int = 2) -> Optional[dict]:
    """Fetch a single HN item from Firebase API."""
    url = f"{HN_ITEM_URL}/{item_id}.json"
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            if attempt < retries - 1:
                time.sleep(0.5)
            continue
    return None


def _fetch_hn_items(item_ids: list[int], max_items: int = 100) -> list[dict]:
    """Fetch multiple HN items with rate limiting."""
    items = []
    for i, item_id in enumerate(item_ids[:max_items]):
        if i > 0 and i % 10 == 0:
            time.sleep(0.5)  # Rate limit: be polite to HN API
        item = _fetch_hn_item(item_id)
        if item and item.get("title"):
            items.append(item)
    return items


# ---------- main fetch ----------


def fetch_hot_ai_news(
    source: str = "hn",
    hours: int = 72,
    limit: int = 20,
    keywords: Optional[list[str]] = None,
    output_path: Optional[Path] = None,
    candidates_output_path: Optional[Path] = None,
    dry_run: bool = False,
) -> dict:
    """Fetch hot AI news candidates from HN.

    Args:
        source: News source identifier (only 'hn' supported for now).
        hours: Window for recency bonus (default 72h).
        limit: Number of candidates to return (default 20).
        keywords: AI-related keyword list. Defaults to DEFAULT_KEYWORDS.
        output_path: Path for latest_news.json output.
        candidates_output_path: Path for hot_ai_candidates.json output.
        dry_run: If True, only return candidates without saving files.

    Returns:
        dict matching latest_news.json schema (selected top news).

    Raises:
        RuntimeError: When no candidates could be fetched or filtered.
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS

    if source != "hn":
        raise ValueError(f"Unsupported source: {source}. Only 'hn' is supported.")

    # Fetch HN top story IDs
    print(f"[fetch_hot_ai_news] Fetching HN top stories (limit=500)...")
    story_ids = _fetch_hn_top_stories_ids(limit=500)
    if not story_ids:
        raise RuntimeError("Failed to fetch HN top stories. Check network connectivity.")

    # Fetch individual items
    print(f"[fetch_hot_ai_news] Fetching up to 100 HN items for scoring...")
    items = _fetch_hn_items(story_ids, max_items=100)
    if not items:
        raise RuntimeError("Failed to fetch HN items. Check network connectivity.")

    print(f"[fetch_hot_ai_news] Fetched {len(items)} items, scoring and filtering...")

    # Filter by keywords and score
    now = int(time.time())
    cutoff = now - (hours * 3600)
    candidates = []

    for item in items:
        ts = item.get("time", 0)
        if ts < cutoff:
            continue  # Outside time window

        title = item.get("title", "")
        if not title:
            continue

        # Check if any keyword matches (must have at least 1 to be considered AI-related)
        title_lower = title.lower()
        matched_keywords = [kw for kw in keywords if kw.lower() in title_lower]

        if not matched_keywords:
            continue  # Skip non-AI stories

        # Score the item
        score = _score_item(item, keywords)

        # Build rank reason
        rank_reason = _build_rank_reason(item, matched_keywords, score)

        hn_url = item.get("url") or f"https://news.ycombinator.com/item?id={item.get('id')}"
        discussion_url = f"https://news.ycombinator.com/item?id={item.get('id')}"

        candidate = {
            "id": f"hn_{item.get('id')}",
            "title": title,
            "url": hn_url,
            "hn_url": discussion_url,
            "source_id": "hacker_news",
            "source_name": "Hacker News",
            "published_at": _hn_timestamp_to_iso(ts) if ts else None,
            "points": item.get("score", 0) or 0,
            "comments": item.get("descendants", 0) or 0,
            "score": score,
            "matched_keywords": matched_keywords,
            "rank_reason": rank_reason,
        }
        candidates.append(candidate)

    if not candidates:
        raise RuntimeError(
            f"No AI-related HN stories found in the last {hours}h. "
            f"Try expanding keywords or increasing time window."
        )

    # Sort by score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # Take top N
    top_candidates = candidates[:limit]

    # Build candidates output
    candidates_output = {
        "source": source,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "hours": hours,
        "keywords": keywords,
        "count": len(top_candidates),
        "items": top_candidates,
    }

    # Select top 1 for latest_news.json
    top = top_candidates[0]

    # Build latest_news.json (compatible with existing pipeline schema)
    # NOTE: We do NOT fetch full article text. Content is a summary of HN metadata only.
    latest_news = {
        "id": top["id"],
        "title": top["title"],
        "url": top["url"],
        "source_id": top["source_id"],
        "source_name": top["source_name"],
        "published_at": top["published_at"],
        "summary": f"[HN] {top['title']} — {top['points']} points, {top['comments']} comments. {' '.join(top['matched_keywords'][:5])}",
        "content": (
            f"Title: {top['title']}\n"
            f"URL: {top['url']}\n"
            f"HN Discussion: {top['hn_url']}\n"
            f"Points: {top['points']} | Comments: {top['comments']}\n"
            f"Matched Keywords: {', '.join(top['matched_keywords']) if top['matched_keywords'] else 'None'}\n"
            f"HN Hotness Score: {top['score']:.1f}\n"
            f"Rank Reason: {top['rank_reason']}\n\n"
            f"[NOTE] Full article text was not fetched. "
            f"This summary was generated from HN metadata only. "
            f"No paywall was bypassed. No copyright content was stored."
        ),
        "content_source": "hn_hot",
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "score": top["score"],
        "comments": top["comments"],
        "rank_reason": top["rank_reason"],
    }

    if dry_run:
        print(f"[fetch_hot_ai_news] Dry run — not saving files.")
        print(f"[fetch_hot_ai_news] Candidates: {len(top_candidates)}")
        print(f"[fetch_hot_ai_news] Top candidate: {top['title']}")
        return latest_news

    # Save outputs
    if candidates_output_path:
        save_json(candidates_output, candidates_output_path)
        print(f"[fetch_hot_ai_news] wrote {candidates_output_path} ({len(top_candidates)} candidates)")

    if output_path:
        save_json(latest_news, output_path)
        print(f"[fetch_hot_ai_news] wrote {output_path} (selected: {top['title']})")

    return latest_news


# ---------- CLI ----------


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Fetch hot AI news from Hacker News.",
    )
    parser.add_argument(
        "--source", type=str, default="hn",
        help="News source (default: hn). Only 'hn' is supported.",
    )
    parser.add_argument(
        "--hours", type=int, default=72,
        help="Time window in hours for recency bonus (default: 72).",
    )
    parser.add_argument(
        "--limit", type=int, default=20,
        help="Number of candidates to return (default: 20).",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output path for latest_news.json.",
    )
    parser.add_argument(
        "--candidates-output", type=str, default=None,
        help="Output path for hot_ai_candidates.json.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Only fetch and score, don't save files.",
    )
    parser.add_argument(
        "--keyword", type=str, action="append", dest="keywords",
        help="Additional keyword to filter/score. Can be repeated.",
    )

    args = parser.parse_args(argv)

    # Merge default + extra keywords
    keywords = list(DEFAULT_KEYWORDS)
    if args.keywords:
        for kw in args.keywords:
            if kw not in keywords:
                keywords.append(kw)

    output_path = Path(args.output) if args.output else None
    candidates_output_path = Path(args.candidates_output) if args.candidates_output else None

    try:
        result = fetch_hot_ai_news(
            source=args.source,
            hours=args.hours,
            limit=args.limit,
            keywords=keywords,
            output_path=output_path,
            candidates_output_path=candidates_output_path,
            dry_run=args.dry_run,
        )
        print(f"[fetch_hot_ai_news] Selected: {result['title']}")
        print(f"[fetch_hot_ai_news] URL: {result['url']}")
        print(f"[fetch_hot_ai_news] Score: {result['score']:.1f}")
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
