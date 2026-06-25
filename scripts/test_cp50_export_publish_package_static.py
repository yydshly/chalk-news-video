#!/usr/bin/env python3
"""CP50 Export Publish Package Files Static Tests."""

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
    doc_path = os.path.join(docs_dir, "CP50_EXPORT_PUBLISH_PACKAGE_FILES.md")
    doc_exists = os.path.exists(doc_path)
    doc_content = read_file(doc_path) if doc_exists else ""

    all_pass = True

    print("CP50 Export Publish Package Files — Static Tests")
    print("=" * 55)

    # HTML checks
    print("\n[HTML]")
    all_pass &= check("index.html contains btn-export-publish-package-json", "btn-export-publish-package-json" in index_html)
    all_pass &= check("index.html contains btn-export-publish-package-md", "btn-export-publish-package-md" in index_html)
    all_pass &= check("index.html contains publish-package-actions", "publish-package-actions" in index_html)

    # JS checks
    print("\n[JAVASCRIPT]")
    all_pass &= check("app.js contains btnExportPublishPackageJson", "btnExportPublishPackageJson" in app_js)
    all_pass &= check("app.js contains btnExportPublishPackageMd", "btnExportPublishPackageMd" in app_js)
    all_pass &= check("app.js contains sanitizePublishFilename", "function sanitizePublishFilename" in app_js)
    all_pass &= check("app.js contains getPublishPackageFilename", "function getPublishPackageFilename" in app_js)
    all_pass &= check("app.js contains downloadTextFile", "function downloadTextFile" in app_js)
    all_pass &= check("app.js contains ensurePublishPackage", "function ensurePublishPackage" in app_js)
    all_pass &= check("app.js contains exportPublishPackageJson", "function exportPublishPackageJson" in app_js)
    all_pass &= check("app.js contains exportPublishPackageMarkdown", "function exportPublishPackageMarkdown" in app_js)
    all_pass &= check("app.js contains buildPublishPackageMarkdown", "function buildPublishPackageMarkdown" in app_js)
    all_pass &= check("app.js contains Blob", "Blob" in app_js)
    all_pass &= check("app.js contains URL.createObjectURL", "URL.createObjectURL" in app_js)
    all_pass &= check("app.js contains URL.revokeObjectURL", "URL.revokeObjectURL" in app_js)
    all_pass &= check("app.js contains application/json", "application/json" in app_js)
    all_pass &= check("app.js contains text/markdown", "text/markdown" in app_js)
    all_pass &= check("app.js contains schema chalk_publish_package_v1", "chalk_publish_package_v1" in app_js)
    all_pass &= check("app.js contains latestPublishPackage", "latestPublishPackage" in app_js)
    all_pass &= check("app.js contains buildPublishPackage", "function buildPublishPackage" in app_js)
    all_pass &= check("app.js wires export JSON button", "btnExportPublishPackageJson" in app_js and "addEventListener" in app_js)
    all_pass &= check("app.js wires export MD button", "btnExportPublishPackageMd" in app_js and "addEventListener" in app_js)
    # Forbidden
    all_pass &= check("app.js does NOT call upload API", "upload" not in app_js.lower() or "upload" not in app_js)
    all_pass &= check("app.js does NOT call douyin API", "douyin.com" not in app_js and "open.douyin" not in app_js)
    all_pass &= check("app.js does NOT call bilibili API", "bilibili.com" not in app_js and "api.bilibili" not in app_js)
    all_pass &= check("app.js does NOT call youtube upload API", "youtube.com/upload" not in app_js and "googleapis.com/youtube" not in app_js)

    # CSS checks
    print("\n[CSS]")
    all_pass &= check("style.css contains .publish-package-actions", ".publish-package-actions" in style_css)
    all_pass &= check("style.css contains responsive @media", "@media" in style_css and "max-width" in style_css)

    # Documentation checks
    print("\n[DOCUMENTATION]")
    all_pass &= check("CP50 documentation exists", doc_exists)
    all_pass &= check("docs mentions JSON", "JSON" in doc_content or "json" in doc_content.lower())
    all_pass &= check("docs mentions Markdown", "Markdown" in doc_content or "markdown" in doc_content.lower())
    all_pass &= check("docs mentions no upload", "上传" in doc_content or "upload" in doc_content.lower())
    all_pass &= check("docs mentions no real publish platform", "真实发布" in doc_content or "real publish" in doc_content.lower())

    # Forbidden modifications
    print("\n[FORBIDDEN MODIFICATIONS]")
    episode_export_py = read_file(os.path.join(web_dir, "..", "src", "episode_export.py"))
    all_pass &= check("episode_export.py NOT modified", "publishPackage" not in episode_export_py and "exportPublishPackage" not in episode_export_py)

    print("\n" + "=" * 55)
    if all_pass:
        print("ALL CP50 EXPORT PUBLISH PACKAGE STATIC TESTS PASSED")
        return 0
    else:
        print("SOME CP50 TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
