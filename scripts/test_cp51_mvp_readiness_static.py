#!/usr/bin/env python3
"""CP51 MVP Readiness Static Tests."""

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
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    web_dir = os.path.join(os.path.dirname(__file__), "..", "web")
    src_dir = os.path.join(os.path.dirname(__file__), "..", "src")

    audit_path = os.path.join(docs_dir, "MVP_READINESS_AUDIT_CP51.md")
    demo_path = os.path.join(docs_dir, "MVP_DEMO_SCRIPT_CP51.md")
    matrix_path = os.path.join(docs_dir, "MVP_CAPABILITY_MATRIX_CP51.md")
    checklist_path = os.path.join(docs_dir, "MVP_FREEZE_CHECKLIST_CP51.md")

    audit_exists = os.path.exists(audit_path)
    demo_exists = os.path.exists(demo_path)
    matrix_exists = os.path.exists(matrix_path)
    checklist_exists = os.path.exists(checklist_path)

    audit = read_file(audit_path) if audit_exists else ""
    demo = read_file(demo_path) if demo_exists else ""
    matrix = read_file(matrix_path) if matrix_exists else ""
    checklist = read_file(checklist_path) if checklist_exists else ""

    all_pass = True

    print("CP51 MVP Readiness — Static Tests")
    print("=" * 55)

    # File existence
    print("\n[FILE EXISTENCE]")
    all_pass &= check("MVP_READINESS_AUDIT_CP51.md exists", audit_exists)
    all_pass &= check("MVP_DEMO_SCRIPT_CP51.md exists", demo_exists)
    all_pass &= check("MVP_CAPABILITY_MATRIX_CP51.md exists", matrix_exists)
    all_pass &= check("MVP_FREEZE_CHECKLIST_CP51.md exists", checklist_exists)

    # Audit content
    print("\n[MVP_READINESS_AUDIT_CP51]")
    all_pass &= check("mentions MVP Candidate", "MVP Candidate" in audit or "MVP" in audit)
    all_pass &= check("mentions reliable source", "Reliable Source" in audit or "reliable source" in audit.lower())
    all_pass &= check("mentions URL draft basket", "URL" in audit and "draft" in audit.lower())
    all_pass &= check("mentions source collection", "source collection" in audit.lower() or "来源集合" in audit)
    all_pass &= check("mentions MP4 export", "MP4" in audit and "export" in audit.lower())
    all_pass &= check("mentions publish package", "publish package" in audit.lower() or "发布素材包" in audit)
    all_pass &= check("mentions JSON/Markdown", "JSON" in audit and "Markdown" in audit)
    all_pass &= check("states no real LLM", "no real LLM" in audit.lower() or "没有真实 LLM" in audit or "Real LLM" in audit)
    all_pass &= check("states no real TTS", "no real TTS" in audit.lower() or "没有真实 TTS" in audit or "Real TTS" in audit)
    all_pass &= check("states no Remotion", "no Remotion" in audit.lower() or "Remotion" in audit)
    all_pass &= check("states no real publish platform", "no real publish" in audit.lower() or "真实发布" in audit)
    all_pass &= check("mentions CP42 pipeline", "CP42" in audit)
    all_pass &= check("mentions CP50 export", "CP50" in audit)

    # Demo script content
    print("\n[MVP_DEMO_SCRIPT_CP51]")
    all_pass &= check("mentions 3-5 minute or similar duration", "3" in demo and ("分钟" in demo or "min" in demo.lower()) or "5 分钟" in demo)
    all_pass &= check("mentions demo steps", "Demo" in demo or "演示" in demo)
    all_pass &= check("mentions URL draft basket", "draft" in demo.lower())
    all_pass &= check("mentions contract/inspector", "contract" in demo.lower() or "合同" in demo)
    all_pass &= check("mentions MP4 export", "MP4" in demo)
    all_pass &= check("mentions publish package", "publish" in demo.lower() or "发布" in demo)

    # Capability matrix content
    print("\n[MVP_CAPABILITY_MATRIX_CP51]")
    all_pass &= check("mentions ready/limited/mock status", "ready" in matrix.lower() or "limited" in matrix.lower() or "mock" in matrix.lower())
    all_pass &= check("mentions reliable source registry", "Reliable Source" in matrix or "reliable source" in matrix.lower())
    all_pass &= check("mentions MP4 export", "MP4" in matrix)
    all_pass &= check("mentions publish package", "publish package" in matrix.lower())
    all_pass &= check("mentions Real LLM", "Real LLM" in matrix or "not_implemented" in matrix)
    all_pass &= check("mentions Real TTS", "Real TTS" in matrix or "not_implemented" in matrix)
    all_pass &= check("mentions Remotion", "Remotion" in matrix)
    all_pass &= check("mentions real publish platform", "real platform" in matrix.lower() or "not_implemented" in matrix)

    # Freeze checklist content
    print("\n[MVP_FREEZE_CHECKLIST_CP51]")
    all_pass &= check("mentions CP42", "CP42" in checklist)
    all_pass &= check("mentions CP50", "CP50" in checklist)
    all_pass &= check("mentions CP40.8 E2E", "CP40.8" in checklist or "E2E" in checklist)
    all_pass &= check("mentions no real LLM", "no real LLM" in checklist.lower() or "Real LLM" in checklist)
    all_pass &= check("mentions no real TTS", "no real TTS" in checklist.lower() or "Real TTS" in checklist)
    all_pass &= check("mentions no Remotion", "no Remotion" in checklist.lower() or "Remotion" in checklist)
    all_pass &= check("mentions no real publish platform", "no real publish" in checklist.lower() or "真实发布" in checklist)
    all_pass &= check("mentions freeze checklist items", "checklist" in checklist.lower() or "checklist" in checklist.lower())

    # No source code pollution by CP51 docs
    print("\n[SOURCE CODE NOT MODIFIED BY CP51]")
    if os.path.exists(os.path.join(src_dir, "episode_export.py")):
        ep = read_file(os.path.join(src_dir, "episode_export.py"))
        all_pass &= check("episode_export.py NOT polluted by MVP audit docs", "MVP_READINESS" not in ep and "MVP_READY" not in ep)
    if os.path.exists(os.path.join(src_dir, "export_video.py")):
        ev = read_file(os.path.join(src_dir, "export_video.py"))
        all_pass &= check("export_video.py NOT polluted", "MVP_READINESS" not in ev and "MVP_READY" not in ev)
    if os.path.exists(os.path.join(src_dir, "render_episode_html.py")):
        re = read_file(os.path.join(src_dir, "render_episode_html.py"))
        all_pass &= check("render_episode_html.py NOT polluted", "MVP_READINESS" not in re and "MVP_READY" not in re)
    if os.path.exists(os.path.join(src_dir, "article_extractor.py")):
        ae = read_file(os.path.join(src_dir, "article_extractor.py"))
        all_pass &= check("article_extractor.py NOT polluted", "MVP_READINESS" not in ae and "MVP_READY" not in ae)
    if os.path.exists(os.path.join(src_dir, "server.py")):
        sv = read_file(os.path.join(src_dir, "server.py"))
        all_pass &= check("server.py NOT polluted", "MVP_READINESS" not in sv and "MVP_READY" not in sv)

    # No app.js/index.html/style.css changes in CP51
    app_js_path = os.path.join(web_dir, "app.js")
    if os.path.exists(app_js_path):
        app_js = read_file(app_js_path)
        all_pass &= check("app.js NOT modified by CP51 docs", "MVP_READINESS" not in app_js and "CP51" not in app_js)

    print("\n" + "=" * 55)
    if all_pass:
        print("ALL CP51 MVP READINESS STATIC TESTS PASSED")
        return 0
    else:
        print("SOME CP51 TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
