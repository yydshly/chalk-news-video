#!/usr/bin/env python3
"""CP52 Post-MVP Roadmap Gate Static Tests."""

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

    gate_path = os.path.join(docs_dir, "CP52_POST_MVP_ROADMAP_GATE.md")
    matrix_path = os.path.join(docs_dir, "CP52_ROUTE_COMPARISON_MATRIX.md")
    plan_path = os.path.join(docs_dir, "CP52_NEXT_PHASE_PLAN.md")

    gate_exists = os.path.exists(gate_path)
    matrix_exists = os.path.exists(matrix_path)
    plan_exists = os.path.exists(plan_path)

    gate = read_file(gate_path) if gate_exists else ""
    matrix = read_file(matrix_path) if matrix_exists else ""
    plan = read_file(plan_path) if plan_exists else ""

    all_pass = True

    print("CP52 Post-MVP Roadmap Gate — Static Tests")
    print("=" * 55)

    # File existence
    print("\n[FILE EXISTENCE]")
    all_pass &= check("CP52_POST_MVP_ROADMAP_GATE.md exists", gate_exists)
    all_pass &= check("CP52_ROUTE_COMPARISON_MATRIX.md exists", matrix_exists)
    all_pass &= check("CP52_NEXT_PHASE_PLAN.md exists", plan_exists)

    # Gate content
    print("\n[ROADMAP GATE CONTENT]")
    all_pass &= check("mentions Route A", "Route A" in gate or "route A" in gate.lower())
    all_pass &= check("mentions 真实新闻采集", "真实新闻采集" in gate or "真实来源采集" in gate)
    all_pass &= check("mentions Route B", "Route B" in gate or "route B" in gate.lower())
    all_pass &= check("mentions real LLM", "real LLM" in gate.lower() or "Real LLM" in gate)
    all_pass &= check("mentions real TTS", "real TTS" in gate.lower() or "Real TTS" in gate)
    all_pass &= check("mentions Route C", "Route C" in gate or "route C" in gate.lower())
    all_pass &= check("mentions Remotion", "Remotion" in gate)
    all_pass &= check("mentions Route D", "Route D" in gate or "route D" in gate.lower())
    all_pass &= check("mentions 多用户", "多用户" in gate or "SaaS" in gate)
    all_pass &= check("recommends A + B or 真实来源采集 + LLM", ("Route A" in gate and "Route B" in gate) or ("真实来源采集" in gate and "LLM" in gate) or ("A" in gate and "B" in gate and "优先" in gate))
    all_pass &= check("says not prioritize multi-user/SaaS", "暂缓" in gate or "后置" in gate or "不优先" in gate.lower())
    all_pass &= check("says not prioritize Remotion first", "暂缓" in gate or "后置" in gate or "Remotion" in gate and "暂缓" in gate)

    # Matrix content
    print("\n[ROUTE COMPARISON MATRIX]")
    all_pass &= check("mentions value", "价值" in matrix or "value" in matrix.lower())
    all_pass &= check("mentions cost", "成本" in matrix or "cost" in matrix.lower())
    all_pass &= check("mentions risk", "风险" in matrix or "risk" in matrix.lower())
    all_pass &= check("mentions priority", "优先" in matrix or "priority" in matrix.lower())
    all_pass &= check("compares four routes", "Route A" in matrix and "Route B" in matrix and "Route C" in matrix and "Route D" in matrix)

    # Next phase plan content
    print("\n[NEXT PHASE PLAN]")
    all_pass &= check("mentions CP53", "CP53" in plan)
    all_pass &= check("mentions CP60", "CP60" in plan)
    all_pass &= check("mentions source_candidates_v1", "source_candidates_v1" in plan)
    all_pass &= check("mentions source_snapshot", "source_snapshot" in plan or "snapshot" in plan.lower())
    all_pass &= check("mentions LLM script draft", "script" in plan.lower() and "LLM" in plan)
    all_pass &= check("mentions TTS", "TTS" in plan)
    all_pass &= check("mentions Remotion spike", "Remotion" in plan or "Spike" in plan)

    # No pollution in source files
    print("\n[SOURCE FILES NOT POLLUTED]")
    for fname in ["episode_export.py", "export_video.py", "render_episode_html.py", "article_extractor.py", "server.py"]:
        fpath = os.path.join(src_dir, fname)
        if os.path.exists(fpath):
            content = read_file(fpath)
            all_pass &= check(f"{fname} NOT polluted by CP52 docs", "CP52" not in content and "POST_MVP" not in content and "ROADMAP_GATE" not in content)

    # No pollution in web files
    print("\n[WEB FILES NOT MODIFIED BY CP52]")
    app_js_path = os.path.join(web_dir, "app.js")
    if os.path.exists(app_js_path):
        content = read_file(app_js_path)
        all_pass &= check("app.js NOT modified by CP52", "CP52" not in content)

    print("\n" + "=" * 55)
    if all_pass:
        print("ALL CP52 POST-MVP ROADMAP STATIC TESTS PASSED")
        return 0
    else:
        print("SOME CP52 TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
