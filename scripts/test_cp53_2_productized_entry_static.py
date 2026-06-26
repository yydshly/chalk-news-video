#!/usr/bin/env python3
"""CP53.2 Productized Entry Stabilization — Static Tests."""

import os
import sys

def read_file(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def check(name, condition):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}")
    return condition

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    web_dir = os.path.join(project_root, "web")
    src_dir = os.path.join(project_root, "src")
    docs_dir = os.path.join(project_root, "docs")

    all_pass = True

    print("CP53.2 Productized Entry Stabilization — Static Tests")
    print("=" * 60)

    # --- Files exist ---
    print("\n[FILES EXIST]")
    all_pass &= check("web/simple.html exists", os.path.exists(os.path.join(web_dir, "simple.html")))
    all_pass &= check("web/simple.js exists", os.path.exists(os.path.join(web_dir, "simple.js")))
    all_pass &= check("web/simple.css exists", os.path.exists(os.path.join(web_dir, "simple.css")))
    all_pass &= check("web/showcase.html exists", os.path.exists(os.path.join(web_dir, "showcase.html")))
    all_pass &= check("web/showcase.js exists", os.path.exists(os.path.join(web_dir, "showcase.js")))

    # --- server.py routes ---
    print("\n[ROUTES]")
    server_py = read_file(os.path.join(src_dir, "server.py"))
    all_pass &= check("server.py has @app.get('/') route", '@app.get("/")' in server_py)
    all_pass &= check("server.py serves simple.html at /", 'simple.html' in server_py)
    all_pass &= check("server.py has /simple.js route", '@app.get("/simple.js")' in server_py)
    all_pass &= check("server.py serves simple.js at /simple.js", 'simple.js' in server_py)
    all_pass &= check("server.py has /simple.css route", '@app.get("/simple.css")' in server_py)
    all_pass &= check("server.py has /advanced route", '@app.get("/advanced")' in server_py)
    all_pass &= check("server.py serves index.html at /advanced", 'index.html' in server_py)
    all_pass &= check("server.py has /showcase route", '@app.get("/showcase")' in server_py)
    all_pass &= check("server.py serves showcase.html at /showcase", 'showcase.html' in server_py)
    all_pass &= check("server.py has /showcase.js route", '@app.get("/showcase.js")' in server_py)

    # --- No CP60 in current implementation ---
    print("\n[NO CP60 IN CURRENT CODE]")
    # server.py
    all_pass &= check("server.py has no CP60 label", "CP60" not in server_py)
    # web files
    for fname in ["simple.js", "showcase.js", "app.js", "simple.html", "showcase.html"]:
        fpath = os.path.join(web_dir, fname)
        content = read_file(fpath)
        all_pass &= check(f"{fname} has no CP60", "CP60" not in content)
    # src python files
    for fname in ["episode_tts.py", "render_episode_html.py", "export_video.py",
                  "episode_export.py", "source_snapshot.py"]:
        fpath = os.path.join(src_dir, fname)
        if os.path.exists(fpath):
            content = read_file(fpath)
            all_pass &= check(f"{fname} has no CP60", "CP60" not in content)

    # --- .gitignore contains outputs/ ---
    print("\n[GITIGNORE]")
    gitignore = read_file(os.path.join(project_root, ".gitignore"))
    all_pass &= check(".gitignore contains outputs/", "outputs/" in gitignore)
    all_pass &= check(".gitignore ignores outputs/episode_audio/", "outputs/episode_audio/" in gitignore)

    # --- No tracked outputs ---
    print("\n[NO TRACKED OUTPUTS]")
    import subprocess
    result = subprocess.run(
        ["git", "ls-files", "outputs"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    tracked = [l for l in result.stdout.strip().split("\n") if l]
    # Filter out .gitkeep files which are intentionally tracked
    tracked = [l for l in tracked if not l.endswith(".gitkeep")]
    all_pass &= check("no tracked outputs/episode_audio/ .wav files", len(tracked) == 0)

    # --- web/app.js advanced capabilities preserved ---
    print("\n[ADVANCED CAPABILITIES IN app.js]")
    app_js = read_file(os.path.join(web_dir, "app.js"))
    advanced_symbols = [
        ("urlDraftItems", "urlDraftItems"),
        ("renderUrlDraftBasket", "renderUrlDraftBasket"),
        ("sourceCollections", "sourceCollections"),
        ("renderSourceCollections", "renderSourceCollections"),
        ("latestSourceContract", "latestSourceContract"),
        ("latestSourceEpisodeItems", "latestSourceEpisodeItems"),
        ("renderSourceContractInspector", "renderSourceContractInspector"),
        ("applySourceContractToPlanner", "applySourceContractToPlanner"),
        ("renderProductionWorkflowPanel", "renderProductionWorkflowPanel"),
        ("buildPublishPackage", "buildPublishPackage"),
        ("generatePublishPackage", "generatePublishPackage"),
        ("exportPublishPackageJson", "exportPublishPackageJson"),
        ("exportPublishPackageMarkdown", "exportPublishPackageMarkdown"),
    ]
    for symbol, display in advanced_symbols:
        all_pass &= check(f"app.js contains {display}", symbol in app_js)

    # --- web/simple.js independence ---
    print("\n[SIMPLE.JS INDEPENDENCE]")
    simple_js = read_file(os.path.join(web_dir, "simple.js"))
    all_pass &= check("simple.js does not import app.js", "app.js" not in simple_js)
    all_pass &= check("simple.js does not depend on app.js globals", "app.js" not in simple_js.lower())

    # --- web/showcase.js independence ---
    print("\n[SHOWCASE.JS INDEPENDENCE]")
    showcase_js = read_file(os.path.join(web_dir, "showcase.js"))
    all_pass &= check("showcase.js does not import app.js", "app.js" not in showcase_js)
    all_pass &= check("showcase.js does not depend on app.js globals", "app.js" not in showcase_js.lower())

    # --- TTS claims ---
    print("\n[TTS CLAIMS]")
    # showcase.js should not claim stable TTS support
    showcase_js_text = showcase_js
    all_pass &= check(
        "showcase.js TTS label is experimental (not '支持')",
        "实验能力" in showcase_js_text or "待正式接入" in showcase_js_text or "planned" in showcase_js_text.lower()
    )

    # episode_tts.py should be labeled experimental
    episode_tts_path = os.path.join(src_dir, "episode_tts.py")
    if os.path.exists(episode_tts_path):
        tts_content = read_file(episode_tts_path)
        all_pass &= check(
            "episode_tts.py is labeled experimental",
            "experimental" in tts_content.lower() or "deprecated" in tts_content.lower()
        )

    # --- CP53.1 redirect safety preserved ---
    print("\n[CP53.1 REDIRECT SAFETY]")
    source_snapshot = read_file(os.path.join(src_dir, "source_snapshot.py"))
    all_pass &= check("source_snapshot.py has MAX_REDIRECTS = 1", "MAX_REDIRECTS = 1" in source_snapshot)
    all_pass &= check("source_snapshot.py has REDIRECT_STATUS_CODES", "REDIRECT_STATUS_CODES" in source_snapshot)
    all_pass &= check("source_snapshot.py revalidates redirect URL", "validate_snapshot_url(next_url)" in source_snapshot)
    all_pass &= check("source_snapshot.py reads max_bytes+1 for truncation", "max_bytes + 1" in source_snapshot)
    all_pass &= check("source_snapshot.py uses Location header", "Location" in source_snapshot)
    all_pass &= check("source_snapshot.py uses urljoin for redirect", "urljoin(current_url" in source_snapshot)
    all_pass &= check("source_snapshot.py has redirect loop guard", "for redirect_count in range" in source_snapshot)

    # --- No real platform publish API ---
    print("\n[NO REAL PLATFORM PUBLISH API]")
    all_pass &= check("server.py does not introduce Bilibili API", "bili" not in server_py.lower() or "bilibili" not in server_py.lower())
    all_pass &= check("server.py does not introduce YouTube API", "youtube.upload" not in server_py.lower())
    all_pass &= check("server.py does not introduce TikTok API", "tiktok.upload" not in server_py.lower())

    # --- No database introduced ---
    print("\n[NO DATABASE]")
    all_pass &= check("server.py does not import sqlite", "import sqlite" not in server_py)
    all_pass &= check("server.py does not import sqlalchemy", "import sqlalchemy" not in server_py.lower())
    all_pass &= check("server.py does not use redis", "redis" not in server_py.lower())

    # --- Episode TTS route exists and is experimental-labeled ---
    print("\n[EPISODE TTS ROUTE]")
    all_pass &= check("server.py has /api/episode/tts-audio route", "/api/episode/tts-audio" in server_py)
    all_pass &= check("server.py episode_tts docstring references CP56", "CP56" in server_py)

    print("\n" + "=" * 60)
    if all_pass:
        print("ALL CP53.2 PRODUCTIZED ENTRY STATIC TESTS PASSED")
        return 0
    else:
        print("SOME CP53.2 TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
