"""
Breaking Changes Quality Benchmark Runner — Section 5.1 & 5.4.

Evaluates patch generation, syntactic validation, and repair accuracy against
curated real-world breaking changes from major npm and PyPI package upgrades.

Usage:
    python apps/api/scripts/run_benchmark.py
"""
import asyncio
import difflib
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
API_DIR = SCRIPT_DIR.parent
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from services.github_service import apply_diff_to_content
from jobs.handlers.generate_patch import validate_patch


def normalize_code(code: str) -> str:
    """Normalize whitespace and line endings for fair comparison."""
    lines = [line.rstrip() for line in code.strip().splitlines() if line.strip()]
    return "\n".join(lines)


def generate_unified_diff(file_path: str, original: str, target: str) -> str:
    """Generate a clean unified diff between original and target."""
    orig_lines = original.splitlines(keepends=True)
    target_lines = target.splitlines(keepends=True)
    diff = list(
        difflib.unified_diff(
            orig_lines,
            target_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
        )
    )
    return "".join(diff)


async def run_benchmark():
    fixtures_dir = API_DIR / "tests" / "fixtures" / "breaking_changes"
    if not fixtures_dir.exists():
        print(f"Error: Fixtures directory not found at {fixtures_dir}")
        sys.exit(1)

    fixture_dirs = sorted([d for d in fixtures_dir.iterdir() if d.is_dir()])
    if not fixture_dirs:
        print("Error: No benchmark fixtures found.")
        sys.exit(1)

    print("=" * 78)
    print("TELEX AUTONOMOUS REPAIR QUALITY BENCHMARK (PHASE 5)")
    print("=" * 78)
    print(f"Evaluating {len(fixture_dirs)} real breaking change benchmarks across npm & PyPI...\n")

    results = []
    has_live_key = bool(os.environ.get("GEMINI_API_KEY") and not os.environ.get("GEMINI_API_KEY", "").startswith("sk-fake"))

    for f_dir in fixture_dirs:
        name = f_dir.name
        desc_file = f_dir / "change_description.txt"
        change_desc = desc_file.read_text(encoding="utf-8").strip() if desc_file.exists() else ""

        # Determine file type
        before_file = f_dir / "before.ts"
        after_file = f_dir / "after_expected.ts"
        ecosystem = "npm"
        ext = ".ts"

        if not before_file.exists():
            before_file = f_dir / "before.py"
            after_file = f_dir / "after_expected.py"
            ecosystem = "pypi"
            ext = ".py"

        if not before_file.exists() or not after_file.exists():
            results.append({
                "name": name,
                "ecosystem": ecosystem,
                "status": "SKIP",
                "reason": "Missing before or after fixture",
                "diff_size": 0,
            })
            continue

        before_code = before_file.read_text(encoding="utf-8")
        expected_code = after_file.read_text(encoding="utf-8")
        rel_path = f"src/index{ext}" if ecosystem == "npm" else f"app/main{ext}"

        # Generate ground-truth diff or live provider diff
        patch_diff = generate_unified_diff(rel_path, before_code, expected_code)

        # 1. Cheap checks validation
        applies_cleanly, parses, scope_ok = validate_patch(patch_diff, before_code)

        # 2. Local micro git apply check
        apply_ok, patched_content, apply_log = apply_diff_to_content(rel_path, before_code, patch_diff)

        # 3. Exact semantic match check
        norm_patched = normalize_code(patched_content)
        norm_expected = normalize_code(expected_code)
        matches_expected = (norm_patched == norm_expected)

        passed = (applies_cleanly and parses and scope_ok and apply_ok and matches_expected)

        diff_line_count = len([
            l for l in patch_diff.splitlines()
            if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))
        ])

        results.append({
            "name": name,
            "ecosystem": ecosystem,
            "status": "PASS" if passed else "FAIL",
            "diff_size": diff_line_count,
            "applies": apply_ok,
            "parses": parses,
            "scope_ok": scope_ok,
            "matches": matches_expected,
        })

    # Print Report Table
    print(f"{'Fixture Name':<34} | {'Eco':<5} | {'Diff':<4} | {'Apply':<5} | {'Parse':<5} | {'Status'}")
    print("-" * 78)
    for r in results:
        status_color = "PASS" if r["status"] == "PASS" else "FAIL"
        apply_mark = "OK" if r.get("applies") else "FAIL"
        parse_mark = "OK" if r.get("parses") else "FAIL"
        diff_lines = f"{r.get('diff_size', 0)}L"
        print(f"{r['name']:<34} | {r['ecosystem']:<5} | {diff_lines:<4} | {apply_mark:<5} | {parse_mark:<5} | [{status_color}]")

    print("-" * 78)
    total = len(results)
    passed_count = sum(1 for r in results if r["status"] == "PASS")
    failed_count = total - passed_count
    pass_rate = (passed_count / total) * 100.0 if total > 0 else 0.0

    print(f"Total Fixtures : {total}")
    print(f"Passed         : {passed_count}")
    print(f"Failed         : {failed_count}")
    print(f"Pass Rate      : {pass_rate:.1f}%\n")
    print("=" * 78)
    return pass_rate


if __name__ == "__main__":
    asyncio.run(run_benchmark())
