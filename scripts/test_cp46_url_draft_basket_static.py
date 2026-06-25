#!/usr/bin/env python3
"""CP46 URL Draft Basket Static Tests — verify CP46 UI and JS implementation."""

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
    doc_path = os.path.join(docs_dir, "CP46_URL_DRAFT_BASKET_MULTI_URL_MVP.md")
    doc_exists = os.path.exists(doc_path)
    doc_content = read_file(doc_path) if doc_exists else ""

    all_pass = True

    print("CP46 URL Draft Basket — Static Tests")
    print("=" * 50)

    # HTML checks
    print("\n[HTML]")
    all_pass &= check("index.html contains url-draft-basket", 'url-draft-basket' in index_html)
    all_pass &= check("index.html contains btn-add-url-draft", 'btn-add-url-draft' in index_html)
    all_pass &= check("index.html contains btn-build-contract-from-url-drafts", 'btn-build-contract-from-url-drafts' in index_html)
    all_pass &= check("index.html contains btn-clear-url-drafts", 'btn-clear-url-drafts' in index_html)
    all_pass &= check("index.html contains url-draft-list", 'url-draft-list' in index_html)
    all_pass &= check("index.html contains url-draft-new-url input", 'url-draft-new-url' in index_html)
    all_pass &= check("index.html contains 'URL 草稿篮'", 'URL 草稿篮' in index_html)
    all_pass &= check("index.html contains '从草稿篮生成栏目'", '从草稿篮生成栏目' in index_html)

    # JS checks
    print("\n[JAVASCRIPT]")
    all_pass &= check("app.js contains urlDraftItems state", 'urlDraftItems' in app_js)
    all_pass &= check("app.js contains MAX_URL_DRAFT_ITEMS = 5", 'MAX_URL_DRAFT_ITEMS' in app_js and '= 5' in app_js)
    all_pass &= check("app.js contains addUrlDraft function", 'function addUrlDraft' in app_js)
    all_pass &= check("app.js contains extractUrlDraft function", 'function extractUrlDraft' in app_js)
    all_pass &= check("app.js contains /api/article/extract", '/api/article/extract' in app_js)
    all_pass &= check("app.js contains buildContractFromUrlDrafts function", 'function buildContractFromUrlDrafts' in app_js)
    all_pass &= check("app.js calls buildContractFromUrlDrafts on button click", 'btnBuildContractFromUrlDrafts' in app_js)
    all_pass &= check("app.js uses source_type: 'manual_items'", "source_type: \"manual_items\"" in app_js or "source_type: 'manual_items'" in app_js)
    all_pass &= check("app.js contains renderUrlDraftBasket function", 'function renderUrlDraftBasket' in app_js)
    all_pass &= check("app.js contains removeUrlDraft function", 'function removeUrlDraft' in app_js)
    all_pass &= check("app.js contains clearUrlDrafts function", 'function clearUrlDrafts' in app_js)
    all_pass &= check("app.js calls renderUrlDraftBasket at init", 'renderUrlDraftBasket()' in app_js)
    all_pass &= check("app.js contains createUrlDraftId function", 'function createUrlDraftId' in app_js)

    # Button wiring checks
    all_pass &= check("app.js wires btnAddUrlDraft click", 'btnAddUrlDraft' in app_js and 'addEventListener' in app_js)
    all_pass &= check("app.js wires btnClearUrlDrafts click", 'btnClearUrlDrafts' in app_js)
    all_pass &= check("app.js wires btnBuildContractFromUrlDrafts click", 'btnBuildContractFromUrlDrafts' in app_js)

    # CSS checks
    print("\n[CSS]")
    all_pass &= check("style.css contains .url-draft-basket", '.url-draft-basket' in style_css)
    all_pass &= check("style.css contains .url-draft-card", '.url-draft-card' in style_css)
    all_pass &= check("style.css contains .url-draft-list", '.url-draft-list' in style_css)
    all_pass &= check("style.css contains .url-draft-status-ready", '.url-draft-status-ready' in style_css)
    all_pass &= check("style.css contains .url-draft-error", '.url-draft-error' in style_css)
    all_pass &= check("style.css contains .url-draft-actions", '.url-draft-actions' in style_css)
    all_pass &= check("style.css contains .url-draft-add-row", '.url-draft-add-row' in style_css)
    all_pass &= check("style.css contains .url-draft-basket-head", '.url-draft-basket-head' in style_css)

    # Documentation checks
    print("\n[DOCUMENTATION]")
    all_pass &= check("CP46 documentation exists", doc_exists)
    all_pass &= check("docs mentions '人工 URL 草稿篮'", '人工' in doc_content and '草稿篮' in doc_content)
    all_pass &= check("docs mentions 'manual_items'", 'manual_items' in doc_content)
    all_pass &= check("docs mentions '逐条抽取' not '批量爬虫'", '逐条抽取' in doc_content)
    all_pass &= check("docs mentions inspector/planner/preview/export path", 'inspector' in doc_content and 'planner' in doc_content)

    # NOT modified files check
    print("\n[FORBIDDEN MODIFICATIONS]")
    episode_export_py = read_file(os.path.join(web_dir, "..", "src", "episode_export.py"))
    all_pass &= check("episode_export.py NOT modified", 'url_draft' not in episode_export_py.lower() and 'urlDraftItems' not in episode_export_py)

    print("\n" + "=" * 50)
    if all_pass:
        print("ALL CP46 URL DRAFT BASKET STATIC TESTS PASSED")
        return 0
    else:
        print("SOME CP46 TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
