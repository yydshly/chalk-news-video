#!/usr/bin/env python3
"""CP53 Real Source Feed Snapshot MVP — Static + Unit Tests."""

import sys
import os
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.source_snapshot import (
    list_default_source_feeds,
    validate_snapshot_url,
    parse_rss_snapshot,
    parse_html_static_snapshot,
    fetch_source_snapshot_batch,
    SourceFeedConfig,
    _stable_id,
)


def check(name, condition):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}")
    return condition


def main():
    all_pass = True

    print("CP53 Source Snapshot — Tests")
    print("=" * 55)

    # --- Default feed configs ---
    print("\n[DEFAULT FEEDS]")
    feeds = list_default_source_feeds()
    all_pass &= check("default feed configs >= 5", len(feeds) >= 5)

    for feed in feeds:
        all_pass &= check(f"feed {feed.source_id} has source_id", bool(feed.source_id))
        all_pass &= check(f"feed {feed.source_id} has name", bool(feed.name))
        all_pass &= check(f"feed {feed.source_id} has homepage_url", bool(feed.homepage_url))
        all_pass &= check(f"feed {feed.source_id} has fetch_url", bool(feed.fetch_url))
        all_pass &= check(f"feed {feed.source_id} has source_kind", bool(feed.source_kind))
        all_pass &= check(f"feed {feed.source_id} has trust_level", bool(feed.trust_level))
        all_pass &= check(f"feed {feed.source_id} has tags list", isinstance(feed.tags, list))
        all_pass &= check(
            f"feed {feed.source_id} source_kind is rss or html_static",
            feed.source_kind in ("rss", "html_static"),
        )

    # --- URL Safety Validation ---
    print("\n[URL SAFETY]")

    # Blocked schemes
    all_pass &= check("reject javascript:", not validate_snapshot_url("javascript:alert(1)")[0])
    all_pass &= check("reject file://", not validate_snapshot_url("file:///etc/passwd")[0])
    all_pass &= check("reject data:", not validate_snapshot_url("data:text/html,<h1>")[0])
    all_pass &= check("reject ftp://", not validate_snapshot_url("ftp://example.com")[0])

    # Blocked hosts
    all_pass &= check("reject localhost", not validate_snapshot_url("http://localhost")[0])
    all_pass &= check("reject 127.0.0.1", not validate_snapshot_url("http://127.0.0.1")[0])
    all_pass &= check("reject 10.x private", not validate_snapshot_url("http://10.0.0.1")[0])
    all_pass &= check("reject 192.168.x", not validate_snapshot_url("http://192.168.1.1")[0])
    all_pass &= check("reject 172.16.x", not validate_snapshot_url("http://172.16.0.1")[0])

    # Allowed
    all_pass &= check("allow https openai.com", validate_snapshot_url("https://openai.com/blog")[0])
    all_pass &= check("allow https anthropic.com", validate_snapshot_url("https://www.anthropic.com/news")[0])

    # --- RSS Parser ---
    print("\n[RSS PARSER]")

    rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
    <channel>
    <title>Test Feed</title>
    <link>https://example.com</link>
    <item>
        <title>Test Article One</title>
        <link>https://example.com/article-1</link>
        <description>A short description for the first article.</description>
        <pubDate>Wed, 25 Jun 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
        <title>Test Article Two</title>
        <link>https://example.com/article-2</link>
        <description>A short description for the second article.</description>
        <pubDate>Tue, 24 Jun 2026 09:00:00 GMT</pubDate>
    </item>
    </channel>
    </rss>"""

    atom_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
    <title>Test Atom Feed</title>
    <link href="https://example.com"/>
    <entry>
        <title>Atom Entry One</title>
        <link href="https://example.com/atom-1"/>
        <summary>A summary for the first atom entry.</summary>
        <published>2026-06-25T08:00:00Z</published>
    </entry>
    </feed>"""

    config_rss = SourceFeedConfig(
        source_id="test_rss",
        name="Test RSS",
        homepage_url="https://example.com",
        fetch_url="https://example.com/rss.xml",
        source_kind="rss",
        trust_level="official",
        tags=["test"],
    )

    snap = parse_rss_snapshot(config_rss, rss_xml, limit=10)
    all_pass &= check("RSS snapshot has schema", snap.get("schema") == "source_snapshot_v1")
    all_pass &= check("RSS snapshot has items", len(snap.get("items", [])) == 2)
    all_pass &= check("RSS first item has title", snap["items"][0].get("title") == "Test Article One")
    all_pass &= check("RSS first item has url", snap["items"][0].get("url") == "https://example.com/article-1")
    all_pass &= check("RSS first item has stable id", bool(snap["items"][0].get("id")))
    all_pass &= check("RSS respects limit", len(parse_rss_snapshot(config_rss, rss_xml, limit=1)["items"]) == 1)

    # Atom parse
    config_atom = SourceFeedConfig(
        source_id="test_atom",
        name="Test Atom",
        homepage_url="https://example.com",
        fetch_url="https://example.com/atom.xml",
        source_kind="rss",
        trust_level="official",
        tags=["test"],
    )
    atom_snap = parse_rss_snapshot(config_atom, atom_xml, limit=10)
    all_pass &= check("Atom snapshot has item", len(atom_snap.get("items", [])) == 1)
    all_pass &= check("Atom item has title", atom_snap["items"][0].get("title") == "Atom Entry One")
    all_pass &= check("Atom item has href link", atom_snap["items"][0].get("url") == "https://example.com/atom-1")

    # --- HTML Static Parser ---
    print("\n[HTML STATIC PARSER]")

    html = """<!DOCTYPE html>
    <html><head><title>Test Page Title</title></head>
    <body>
        <a href="/article-1">Article 1 Link</a>
        <a href="/article-2">Article 2 Link</a>
        <a href="https://external.com/page">External Link</a>
    </body></html>"""

    config_html = SourceFeedConfig(
        source_id="test_html",
        name="Test HTML",
        homepage_url="https://test.com",
        fetch_url="https://test.com/index.html",
        source_kind="html_static",
        trust_level="official",
        tags=["test"],
    )

    html_snap = parse_html_static_snapshot(config_html, html, limit=5)
    all_pass &= check("HTML snapshot has items", len(html_snap.get("items", [])) > 0)
    all_pass &= check("HTML snapshot respects limit", len(html_snap.get("items", [])) <= 5)

    # --- Batch Snapshot ---
    print("\n[BATCH SNAPSHOT]")

    # No actual network calls in test env — just check batch structure
    batch = fetch_source_snapshot_batch(source_ids=["openai_blog"], limit_per_source=5)
    all_pass &= check("batch has schema", batch.get("schema") == "source_snapshot_batch_v1")
    all_pass &= check("batch has snapshots list", "snapshots" in batch)
    all_pass &= check("batch has batch_id", bool(batch.get("batch_id")))

    # --- No forbidden strings ---
    print("\n[FORBIDDEN STRINGS]")
    snapshot_file = os.path.join(os.path.dirname(__file__), "..", "src", "source_snapshot.py")
    with open(snapshot_file, encoding="utf-8") as f:
        src = f.read()
    all_pass &= check("no LLM implementation", "openai.ChatCompletion" not in src and "anthropic.messages" not in src.lower() and "llm.generate" not in src.lower())
    all_pass &= check("no TTS implementation", "tts.generate" not in src.lower() and "tts.speak" not in src.lower())
    all_pass &= check("no Remotion implementation", "from remotion" not in src.lower() and "remotion_root" not in src.lower())
    all_pass &= check("no openai LLM API", "openai.ChatCompletion" not in src and "anthropic messages" not in src.lower())
    all_pass &= check("no MP4 export modifications", "episode_export" not in src)

    # --- Redirect Safety Static Checks ---
    print("\n[REDIRECT SAFETY]")
    all_pass &= check("REDIRECT_STATUS_CODES exists", "REDIRECT_STATUS_CODES" in src)
    all_pass &= check("MAX_REDIRECTS = 1", "MAX_REDIRECTS = 1" in src)
    all_pass &= check("fetch_text_url reads max_bytes plus one", "max_bytes + 1" in src)
    all_pass &= check("redirect uses Location header", "Location" in src)
    all_pass &= check("redirect uses urljoin", "urljoin(current_url" in src)
    all_pass &= check("redirect target is revalidated", "validate_snapshot_url(next_url)" in src)
    all_pass &= check("redirect URL rejected error exists", "Redirect URL rejected" in src)
    all_pass &= check("too many redirects error exists", "Too many redirects" in src)
    all_pass &= check("redirect without location error exists", "Redirect without Location" in src)
    all_pass &= check("urllib.error imported", "import urllib.error" in src)
    all_pass &= check("redirect loop present", "for redirect_count in range" in src)

    # --- CLI script exists ---
    cli_file = os.path.join(os.path.dirname(__file__), "snapshot_sources.py")
    all_pass &= check("CLI script exists", os.path.exists(cli_file))
    if os.path.exists(cli_file):
        with open(cli_file, encoding="utf-8") as f:
            cli = f.read()
        all_pass &= check("CLI imports source_snapshot", "source_snapshot" in cli)
        all_pass &= check("CLI handles --source arg", "--source" in cli)
        all_pass &= check("CLI handles --limit arg", "--limit" in cli)

    # --- API endpoint check (server.py) ---
    server_file = os.path.join(os.path.dirname(__file__), "..", "src", "server.py")
    if os.path.exists(server_file):
        with open(server_file, encoding="utf-8") as f:
            srv = f.read()
        all_pass &= check("server.py has /api/source-snapshot route", "/api/source-snapshot" in srv)

    print("\n" + "=" * 55)
    if all_pass:
        print("ALL CP53 SOURCE SNAPSHOT TESTS PASSED")
        return 0
    else:
        print("SOME CP53 TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
