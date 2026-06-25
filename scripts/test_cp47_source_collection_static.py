#!/usr/bin/env python3
"""CP47 Source Collection Saved Drafts Static Tests — verify CP47 UI and JS implementation."""

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
    doc_path = os.path.join(docs_dir, "CP47_SOURCE_COLLECTION_SAVED_DRAFTS.md")
    doc_exists = os.path.exists(doc_path)
    doc_content = read_file(doc_path) if doc_exists else ""

    all_pass = True

    print("CP47 Source Collection Saved Drafts — Static Tests")
    print("=" * 55)

    # HTML checks
    print("\n[HTML]")
    all_pass &= check("index.html contains source-collection-panel", "source-collection-panel" in index_html)
    all_pass &= check("index.html contains source-collection-name input", "source-collection-name" in index_html)
    all_pass &= check("index.html contains btn-save-source-collection", "btn-save-source-collection" in index_html)
    all_pass &= check("index.html contains btn-clear-source-collections", "btn-clear-source-collections" in index_html)
    all_pass &= check("index.html contains source-collection-list", "source-collection-list" in index_html)
    all_pass &= check("index.html contains '来源集合'", "来源集合" in index_html)
    all_pass &= check("index.html contains '保存集合'", "保存集合" in index_html)

    # JS checks
    print("\n[JAVASCRIPT]")
    all_pass &= check("app.js contains SOURCE_COLLECTION_STORAGE_KEY", "SOURCE_COLLECTION_STORAGE_KEY" in app_js)
    all_pass &= check("app.js contains MAX_SOURCE_COLLECTIONS = 20", "MAX_SOURCE_COLLECTIONS" in app_js and "= 20" in app_js)
    all_pass &= check("app.js contains sourceCollections state", "sourceCollections" in app_js)
    all_pass &= check("app.js contains saveCurrentSourceCollection", "function saveCurrentSourceCollection" in app_js)
    all_pass &= check("app.js contains restoreSourceCollection", "function restoreSourceCollection" in app_js)
    all_pass &= check("app.js contains deleteSourceCollection", "function deleteSourceCollection" in app_js)
    all_pass &= check("app.js contains clearSourceCollections", "function clearSourceCollections" in app_js)
    all_pass &= check("app.js contains renderSourceCollections", "function renderSourceCollections" in app_js)
    all_pass &= check("app.js contains loadSourceCollections", "function loadSourceCollections" in app_js)
    all_pass &= check("app.js contains persistSourceCollections", "function persistSourceCollections" in app_js)
    all_pass &= check("app.js contains localStorage", "localStorage" in app_js)
    all_pass &= check("app.js contains cloneUrlDraftItem", "function cloneUrlDraftItem" in app_js)
    all_pass &= check("app.js calls renderUrlDraftBasket on restore", "renderUrlDraftBasket()" in app_js)
    all_pass &= check("app.js does NOT call backend for saving collection", "fetch" not in app_js.split("function saveCurrentSourceCollection")[1].split("function")[0] or "api/episode" not in app_js.split("function saveCurrentSourceCollection")[1].split("function")[0])
    all_pass &= check("app.js still uses source_type: 'manual_items'", "source_type: \"manual_items\"" in app_js or "source_type: 'manual_items'" in app_js)
    all_pass &= check("app.js wires btnSaveSourceCollection", "btnSaveSourceCollection" in app_js and "addEventListener" in app_js)
    all_pass &= check("app.js wires btnClearSourceCollections", "btnClearSourceCollections" in app_js)
    all_pass &= check("app.js calls loadSourceCollections at init", "loadSourceCollections()" in app_js)
    all_pass &= check("app.js calls renderSourceCollections at init", "renderSourceCollections()" in app_js)

    # CSS checks
    print("\n[CSS]")
    all_pass &= check("style.css contains .source-collection-panel", ".source-collection-panel" in style_css)
    all_pass &= check("style.css contains .source-collection-card", ".source-collection-card" in style_css)
    all_pass &= check("style.css contains .source-collection-list", ".source-collection-list" in style_css)
    all_pass &= check("style.css contains .source-collection-head", ".source-collection-head" in style_css)
    all_pass &= check("style.css contains .source-collection-save-row", ".source-collection-save-row" in style_css)
    all_pass &= check("style.css contains .source-collection-actions", ".source-collection-actions" in style_css)
    all_pass &= check("style.css contains .source-collection-name", ".source-collection-name" in style_css)
    all_pass &= check("style.css contains .source-collection-meta", ".source-collection-meta" in style_css)
    all_pass &= check("style.css contains .source-collection-card-actions", ".source-collection-card-actions" in style_css)
    all_pass &= check("style.css contains .source-collection-first-url", ".source-collection-first-url" in style_css)

    # Documentation checks
    print("\n[DOCUMENTATION]")
    all_pass &= check("CP47 documentation exists", doc_exists)
    all_pass &= check("docs mentions localStorage", "localStorage" in doc_content)
    all_pass &= check("docs mentions no backend database", "无后端" in doc_content or "backend" in doc_content.lower())
    all_pass &= check("docs mentions no account system", "账号" in doc_content or "account" in doc_content.lower())
    all_pass &= check("docs mentions no crawler", "爬虫" in doc_content or "crawler" in doc_content.lower())

    # NOT modified files check
    print("\n[FORBIDDEN MODIFICATIONS]")
    episode_export_py = read_file(os.path.join(web_dir, "..", "src", "episode_export.py"))
    all_pass &= check("episode_export.py NOT modified", "sourceCollections" not in episode_export_py and "SOURCE_COLLECTION" not in episode_export_py)

    print("\n" + "=" * 55)
    if all_pass:
        print("ALL CP47 SOURCE COLLECTION STATIC TESTS PASSED")
        return 0
    else:
        print("SOME CP47 TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
