"""Shared utilities: file IO, JSON helpers."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_json(path):
    """Load a JSON file as a Python object."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    """Save data as JSON with ensure_ascii=False and indent=2."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return p


def read_text(path):
    """Read a UTF-8 text file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
