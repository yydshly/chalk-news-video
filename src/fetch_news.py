"""Fetch the latest news from a configured RSS source.

Checkpoint 1 (V0.6) responsibilities:
- Read `config/sources.yaml`, pick an enabled source.
- Fetch its RSS feed.
- Extract the most recent item (summary + metadata).
- Optionally scrape the article body using `src.extract_content`.
- Write `outputs/latest/latest_news.json` (UTF-8, ensure_ascii=False, indent=2).

NOT in scope (later checkpoints):
- LLM / `generate_ir` / `validate_ir` / TTS / video export.
"""


import argparse
import datetime
import hashlib
import sys
from pathlib import Path

import feedparser

from . import extract_content
from .config_loader import load_yaml
from .utils import PROJECT_ROOT, save_json


OUTPUT_DIR = PROJECT_ROOT / "outputs" / "latest"
DEFAULT_OUTPUT_PATH = OUTPUT_DIR / "latest_news.json"
DEFAULT_SOURCES_PATH = PROJECT_ROOT / "config" / "sources.yaml"

MIN_CONTENT_LEN = 300  # chars; below this we try harder
PLACEHOLDER_TOKENS = ("待填", "todo", "fill", "fill-me", "example", "your-rss-url")


# ---------- source loading / validation ----------


def _is_placeholder_url(url):
    """True if the URL is empty, whitespace, or still a placeholder.

    Real URLs must start with http:// or https://. Anything else, or anything
    containing common placeholder tokens, is treated as not-yet-filled.
    """
    if url is None:
        return True
    u = str(url).strip()
    if not u:
        return True
    low = u.lower()
    if low.startswith("http://") or low.startswith("https://"):
        return False
    return any(tok in low for tok in PLACEHOLDER_TOKENS)


def load_enabled_sources(config_path=None):
    """Return the list of enabled source dicts from sources.yaml.

    Raises:
        FileNotFoundError: if sources.yaml does not exist.
    """
    cfg_path = Path(config_path) if config_path else DEFAULT_SOURCES_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(
            f"sources.yaml not found at {cfg_path}. "
            f"Create one (see README.md for the schema) before running fetch_news."
        )
    data = load_yaml(cfg_path)
    sources = (data or {}).get("sources", []) or []
    return [s for s in sources if s.get("enabled")]


def _validate_source(source):
    sid = source.get("id")
    if not sid:
        raise ValueError(f"source entry is missing 'id': {source}")
    if source.get("type") != "rss":
        raise ValueError(
            f"source '{sid}' has unsupported type '{source.get('type')!r}'. "
            f"Only 'rss' is implemented in Checkpoint 1."
        )
    if _is_placeholder_url(source.get("url")):
        raise ValueError(
            f"source '{sid}' has an empty or placeholder URL. "
            f"Edit config/sources.yaml and set a real RSS URL before running fetch_news."
        )


# ---------- parsing helpers ----------


def _entry_url(entry):
    return entry.get("link") or entry.get("id") or entry.get("guid") or ""


def _entry_summary(entry):
    return (entry.get("summary") or entry.get("description") or "").strip()


def _parse_published(entry):
    for key in ("published", "updated", "created"):
        v = entry.get(key)
        if v:
            # feedparser exposes parsed values as time.struct_time; str() is stable
            return str(v)
    return None


def _stable_id(source_id, entry):
    """Stable hash-based id; identical inputs give identical ids across runs."""
    seed = "|".join([
        source_id or "",
        _entry_url(entry),
        (entry.get("title") or "").strip(),
        _parse_published(entry) or "",
    ])
    h = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    return f"{source_id}-{h[:12]}"


def _pick_content(summary, url, content_strategy):
    """Choose the article body based on `content_strategy` and summary length.

    Returns (content, content_source) where content_source is one of:
        rss_summary | extracted_html | fallback_summary
    """
    summary = (summary or "").strip()
    if len(summary) >= MIN_CONTENT_LEN:
        return summary, "rss_summary"

    if content_strategy == "summary_then_extract" and url:
        extracted = extract_content.extract_article_content(url)
        if extracted and len(extracted.strip()) >= MIN_CONTENT_LEN:
            return extracted.strip(), "extracted_html"

    return summary, "fallback_summary"


# ---------- main fetch ----------


def fetch_latest_news(source_id=None, config_path=None):
    """Fetch the most recent item from a configured source.

    Args:
        source_id: id of a specific enabled source, or None for the first one.
        config_path: path to sources.yaml (defaults to config/sources.yaml).

    Returns:
        dict matching the latest_news.json schema.

    Raises:
        FileNotFoundError: sources.yaml missing.
        RuntimeError: no enabled source, empty/placeholder URL, RSS parse failure,
                      no entries, or empty content.
        ValueError: source_id not enabled / source not valid.
    """
    sources = load_enabled_sources(config_path)
    if not sources:
        raise RuntimeError(
            "No enabled source in config/sources.yaml. "
            "Set 'enabled: true' on at least one source."
        )

    if source_id:
        chosen = [s for s in sources if s.get("id") == source_id]
        if not chosen:
            available = [s.get("id") for s in sources]
            raise ValueError(
                f"Source '{source_id}' is not enabled. "
                f"Enabled sources: {available}"
            )
        source = chosen[0]
    else:
        source = sources[0]

    _validate_source(source)

    sid = source["id"]
    name = source.get("name", sid)
    url = source["url"]

    feed = feedparser.parse(url)
    if not feed.entries:
        detail = ""
        if getattr(feed, "bozo", False):
            detail = f" ({feed.get('bozo_exception')})"
        raise RuntimeError(
            f"RSS feed '{url}' returned no entries{detail}. "
            f"Check that the URL is correct and reachable."
        )

    entry = feed.entries[0]
    title = (entry.get("title") or "").strip()
    link = _entry_url(entry)
    summary = _entry_summary(entry)
    published = _parse_published(entry)
    content_strategy = source.get("content_strategy", "summary_then_extract")

    content, content_source = _pick_content(summary, link, content_strategy)

    if not content or not content.strip():
        raise RuntimeError(
            f"Could not obtain non-empty content for '{title}' from '{url}'. "
            f"Try a different source or check the article URL."
        )

    return {
        "id": _stable_id(sid, entry),
        "title": title,
        "url": link,
        "source_id": sid,
        "source_name": name,
        "published_at": published,
        "summary": summary,
        "content": content,
        "content_source": content_source,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc)
            .isoformat(timespec="seconds"),
    }


# ---------- CLI ----------


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Fetch the latest news from a configured RSS source.",
    )
    parser.add_argument(
        "--source", type=str, default=None,
        help="Source id from sources.yaml. Defaults to the first enabled source.",
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to sources.yaml (default: config/sources.yaml).",
    )
    parser.add_argument(
        "--output", type=str, default=str(DEFAULT_OUTPUT_PATH),
        help="Output path (default: outputs/latest/latest_news.json).",
    )
    args = parser.parse_args(argv)

    try:
        news = fetch_latest_news(source_id=args.source, config_path=args.config)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    out = Path(args.output)
    save_json(news, out)
    print(
        f"[fetch_news] wrote {out.resolve()} "
        f"(id={news['id']}, content_source={news['content_source']}, "
        f"content_chars={len(news['content'])})"
    )


if __name__ == "__main__":
    main()
