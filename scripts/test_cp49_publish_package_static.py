#!/usr/bin/env python3
"""CP49 Publish Package Copy Kit Static Tests."""

import sys
import os

def read_file(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def check(name, condition):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}")
    return condition

def main():
    web_dir = os.path.join(os.path.dirname(__file__), "..", "web")
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")

    index_html = read_file(os.path.join(web_dir, "index.html"))
    app_js = read_file(os.path.join(web_dir, "app.js"))
    style_css = read_file(os.path.join(web_dir, "style.css"))
    doc_path = os.path.join(docs_dir, "CP49_PUBLISH_PACKAGE_COPY_KIT.md")
    doc_exists = os.path.exists(doc_path)
    doc_content = read_file(doc_path) if doc_exists else ""

    all_pass = True

    print("CP49 Publish Package Copy Kit — Static Tests")
    print("=" * 55)

    # HTML checks
    print("\n[HTML]")
    all_pass &= check("index.html contains publish-package-panel", "publish-package-panel" in index_html)
    all_pass &= check("index.html contains btn-generate-publish-package", "btn-generate-publish-package" in index_html)
    all_pass &= check("index.html contains publish-package-status", "publish-package-status" in index_html)
    all_pass &= check("index.html contains publish-package-content", "publish-package-content" in index_html)
    all_pass &= check("index.html contains publish-title", "publish-title" in index_html)
    all_pass &= check("index.html contains publish-description", "publish-description" in index_html)
    all_pass &= check("index.html contains publish-platform-copy", "publish-platform-copy" in index_html)
    all_pass &= check("index.html contains publish-tags", "publish-tags" in index_html)
    all_pass &= check("index.html contains publish-cover-prompt", "publish-cover-prompt" in index_html)
    all_pass &= check("index.html contains publish-asset-links", "publish-asset-links" in index_html)
    all_pass &= check("index.html contains publish-source-summary", "publish-source-summary" in index_html)
    all_pass &= check("index.html contains data-copy-target", "data-copy-target" in index_html)
    all_pass &= check("index.html contains '发布素材包'", "发布素材包" in index_html)

    # JS checks
    print("\n[JAVASCRIPT]")
    all_pass &= check("app.js contains latestPublishPackage state", "latestPublishPackage" in app_js)
    all_pass &= check("app.js contains getCurrentPublishSourceItems", "function getCurrentPublishSourceItems" in app_js)
    all_pass &= check("app.js contains collectPublishTags", "function collectPublishTags" in app_js)
    all_pass &= check("app.js contains buildPublishPackage", "function buildPublishPackage" in app_js)
    all_pass &= check("app.js contains renderPublishPackage", "function renderPublishPackage" in app_js)
    all_pass &= check("app.js contains generatePublishPackage", "function generatePublishPackage" in app_js)
    all_pass &= check("app.js contains copyTextFromElementId", "function copyTextFromElementId" in app_js)
    all_pass &= check("app.js contains fallbackCopyText", "function fallbackCopyText" in app_js)
    all_pass &= check("app.js references currentEpisodeExportMp4Url", "currentEpisodeExportMp4Url" in app_js)
    all_pass &= check("app.js references latestSourceEpisodeItems", "latestSourceEpisodeItems" in app_js)
    all_pass &= check("app.js references episodeItemList", "episodeItemList" in app_js)
    all_pass &= check("app.js references latestSourceContract", "latestSourceContract" in app_js)
    all_pass &= check("app.js wires btnGeneratePublishPackage click", "btnGeneratePublishPackage" in app_js and "addEventListener" in app_js)
    all_pass &= check("app.js wires data-copy-target buttons", "data-copy-target" in app_js)
    # Forbidden: no real publish API
    all_pass &= check("app.js does NOT call douyin API", "douyin" not in app_js.lower() and "抖音" not in app_js)
    all_pass &= check("app.js does NOT call bilibili API", "bilibili" not in app_js.lower() and "b站" not in app_js and "B站" not in app_js)
    all_pass &= check("app.js does NOT call youtube upload API", "youtube" not in app_js.lower() and "upload" not in app_js)

    # CSS checks
    print("\n[CSS]")
    all_pass &= check("style.css contains .publish-package-panel", ".publish-package-panel" in style_css)
    all_pass &= check("style.css contains .publish-package-field", ".publish-package-field" in style_css)
    all_pass &= check("style.css contains .publish-package-field-wide", ".publish-package-field-wide" in style_css)
    all_pass &= check("style.css contains .publish-package-status.is-ready", ".publish-package-status" in style_css)
    all_pass &= check("style.css contains .btn-mini", ".btn-mini" in style_css)
    all_pass &= check("style.css contains .publish-package-grid", ".publish-package-grid" in style_css)

    # Documentation checks
    print("\n[DOCUMENTATION]")
    all_pass &= check("CP49 documentation exists", doc_exists)
    all_pass &= check("docs mentions no real publish platform", "真实发布" in doc_content or "real publish" in doc_content.lower())
    all_pass &= check("docs mentions no upload", "上传" in doc_content or "upload" in doc_content.lower())
    all_pass &= check("docs mentions manual copy", "手动" in doc_content or "manual" in doc_content.lower())
    all_pass &= check("docs mentions no LLM", "LLM" in doc_content or "llm" in doc_content.lower())

    # Forbidden modifications
    print("\n[FORBIDDEN MODIFICATIONS]")
    episode_export_py = read_file(os.path.join(web_dir, "..", "src", "episode_export.py"))
    all_pass &= check("episode_export.py NOT modified", "publishPackage" not in episode_export_py and "publish_package" not in episode_export_py)

    print("\n" + "=" * 55)
    if all_pass:
        print("ALL CP49 PUBLISH PACKAGE STATIC TESTS PASSED")
        return 0
    else:
        print("SOME CP49 TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
