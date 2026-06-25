#!/usr/bin/env python3
"""CP48 Production Workflow Checklist Static Tests."""

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
    doc_path = os.path.join(docs_dir, "CP48_PRODUCTION_WORKFLOW_CHECKLIST.md")
    doc_exists = os.path.exists(doc_path)
    doc_content = read_file(doc_path) if doc_exists else ""

    all_pass = True

    print("CP48 Production Workflow Checklist — Static Tests")
    print("=" * 55)

    # HTML checks
    print("\n[HTML]")
    all_pass &= check("index.html contains production-workflow-panel", "production-workflow-panel" in index_html)
    all_pass &= check("index.html contains production-workflow-steps", "production-workflow-steps" in index_html)
    all_pass &= check("index.html contains production-readiness-badge", "production-readiness-badge" in index_html)
    all_pass &= check("index.html contains production-workflow-summary", "production-workflow-summary" in index_html)
    all_pass &= check("index.html contains '生产检查清单'", "生产检查清单" in index_html)

    # JS checks
    print("\n[JAVASCRIPT]")
    all_pass &= check("app.js contains getProductionWorkflowState", "function getProductionWorkflowState" in app_js)
    all_pass &= check("app.js contains renderProductionWorkflowPanel", "function renderProductionWorkflowPanel" in app_js)
    all_pass &= check("app.js contains getNextProductionWorkflowHint", "function getNextProductionWorkflowHint" in app_js)
    all_pass &= check("app.js references urlDraftItems", "urlDraftItems" in app_js)
    all_pass &= check("app.js references sourceCollections", "sourceCollections" in app_js)
    all_pass &= check("app.js references latestSourceContract", "latestSourceContract" in app_js)
    all_pass &= check("app.js references latestSourceEpisodeItems", "latestSourceEpisodeItems" in app_js)
    all_pass &= check("app.js references episodeItemList", "episodeItemList" in app_js)
    all_pass &= check("app.js references latestEpisodePreviewUrl or latestEpisodeTemplateContract", "latestEpisodePreviewUrl" in app_js or "latestEpisodeTemplateContract" in app_js)
    all_pass &= check("app.js references currentEpisodeExportMp4Url or latestSucceededJob", "currentEpisodeExportMp4Url" in app_js or "latestSucceededJob" in app_js)
    all_pass &= check("app.js calls renderProductionWorkflowPanel after buildSourceContract", app_js.count("renderProductionWorkflowPanel") >= 3)
    all_pass &= check("app.js calls renderProductionWorkflowPanel after applySourceContractToPlanner", "applySourceContractToPlanner" in app_js and "renderProductionWorkflowPanel" in app_js)
    all_pass &= check("app.js calls renderProductionWorkflowPanel after addUrlDraft", "addUrlDraft" in app_js and "renderProductionWorkflowPanel" in app_js)
    all_pass &= check("app.js calls renderProductionWorkflowPanel in init", "renderProductionWorkflowPanel" in app_js.split("init()")[1].split("async function")[0] if "async function init()" in app_js else False)

    # CP48.1: workflow refresh on draft manual edits
    title_handler_region = app_js.split("titleInput.addEventListener(\"input\"")[1].split("summaryInput.addEventListener")[0] if "titleInput.addEventListener(\"input\"" in app_js else ""
    all_pass &= check("title input handler calls renderProductionWorkflowPanel", "renderProductionWorkflowPanel();" in title_handler_region)
    all_pass &= check("title input handler does NOT call renderUrlDraftBasket", "renderUrlDraftBasket(" not in title_handler_region)

    summary_handler_region = app_js.split("summaryInput.addEventListener(\"input\"")[1].split("card.querySelector")[0] if "summaryInput.addEventListener(\"input\"" in app_js else ""
    all_pass &= check("summary input handler calls renderProductionWorkflowPanel", "renderProductionWorkflowPanel();" in summary_handler_region)
    all_pass &= check("summary input handler does NOT call renderUrlDraftBasket", "renderUrlDraftBasket(" not in summary_handler_region)

    # CP48 workflow functions still exist
    all_pass &= check("getProductionWorkflowState function exists", "function getProductionWorkflowState" in app_js)
    all_pass &= check("renderProductionWorkflowPanel function exists", "function renderProductionWorkflowPanel" in app_js)

    # CSS checks
    print("\n[CSS]")
    all_pass &= check("style.css contains .production-workflow-panel", ".production-workflow-panel" in style_css)
    all_pass &= check("style.css contains .production-readiness-badge", ".production-readiness-badge" in style_css)
    all_pass &= check("style.css contains .production-workflow-step", ".production-workflow-step" in style_css)
    all_pass &= check("style.css contains .production-workflow-steps", ".production-workflow-steps" in style_css)
    all_pass &= check("style.css contains .is-ready badge style", ".is-ready" in style_css)
    all_pass &= check("style.css contains .is-blocked badge style", ".is-blocked" in style_css)
    all_pass &= check("style.css contains .production-workflow-summary", ".production-workflow-summary" in style_css)

    # Documentation checks
    print("\n[DOCUMENTATION]")
    all_pass &= check("CP48 documentation exists", doc_exists)
    all_pass &= check("docs mentions checklist", "检查清单" in doc_content or "checklist" in doc_content.lower())
    all_pass &= check("docs mentions publish readiness", "发布" in doc_content or "publish" in doc_content.lower())
    all_pass &= check("docs mentions no real publish platform", "真实发布" in doc_content or "publish platform" in doc_content.lower())
    all_pass &= check("docs mentions no backend database", "后端" in doc_content or "backend" in doc_content.lower())

    # Forbidden modifications
    print("\n[FORBIDDEN MODIFICATIONS]")
    episode_export_py = read_file(os.path.join(web_dir, "..", "src", "episode_export.py"))
    all_pass &= check("episode_export.py NOT modified", "productionWorkflow" not in episode_export_py)

    print("\n" + "=" * 55)
    if all_pass:
        print("ALL CP48 PRODUCTION WORKFLOW STATIC TESTS PASSED")
        return 0
    else:
        print("SOME CP48 TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
