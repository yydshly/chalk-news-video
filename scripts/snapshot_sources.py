#!/usr/bin/env python3
"""CLI tool to fetch and display source feed snapshots (CP53).

Usage:
    python scripts/snapshot_sources.py
    python scripts/snapshot_sources.py --source openai_blog --limit 5
    python scripts/snapshot_sources.py --pretty
    python scripts/snapshot_sources.py --sources openai_blog anthropic_news --pretty
"""

import argparse
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def main():
    parser = argparse.ArgumentParser(description="Fetch AI news source feed snapshots")
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Single source_id to fetch (default: all)",
    )
    parser.add_argument(
        "--sources",
        type=str,
        nargs="+",
        default=None,
        help="List of source_ids to fetch",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Max items per source (default: 10)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    args = parser.parse_args()

    from src.source_snapshot import fetch_source_snapshot_batch, list_default_source_feeds

    if args.source:
        source_ids = [args.source]
    elif args.sources:
        source_ids = args.sources
    else:
        source_ids = None

    # Validate source_ids if provided
    if source_ids:
        all_ids = {f.source_id for f in list_default_source_feeds()}
        for sid in source_ids:
            if sid not in all_ids:
                print(f"Unknown source_id: {sid}", file=sys.stderr)
                available = ", ".join(sorted(all_ids))
                print(f"Available source_ids: {available}", file=sys.stderr)
                sys.exit(1)

    try:
        result = fetch_source_snapshot_batch(
            source_ids=source_ids,
            limit_per_source=args.limit,
        )
    except Exception as e:
        print(f"Error fetching snapshot: {e}", file=sys.stderr)
        sys.exit(1)

    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
