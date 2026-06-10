"""Run AI-executable test cases from docs/test-cases/00-ai-manifest.json."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "test-cases" / "00-ai-manifest.json"
EXEC_LOG = ROOT / "docs" / "test-cases" / "EXECUTION_LOG.md"


@dataclass
class CaseResult:
    case_id: str
    title: str
    passed: bool
    exit_code: int
    command: list[str]
    output_tail: str
    suite: str | None = None


def load_manifest() -> dict:
    if not MANIFEST.is_file():
        raise SystemExit(f"Manifest not found: {MANIFEST}")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def filter_cases(
    manifest: dict,
    *,
    case_id: str | None,
    suite: str | None,
    priority: str | None,
    layer: str | None,
) -> list[dict]:
    cases = manifest["cases"]
    if case_id:
        matched = [c for c in cases if c["id"] == case_id]
        if not matched:
            raise SystemExit(f"Unknown case id: {case_id}")
        return matched
    if suite:
        suite_ids = set(manifest["suites"].get(suite, []))
        if not suite_ids:
            raise SystemExit(f"Unknown suite: {suite}")
        cases = [c for c in cases if c["id"] in suite_ids]
    if priority:
        cases = [c for c in cases if c.get("priority") == priority]
    if layer:
        cases = [c for c in cases if c.get("layer") == layer]
    return cases


def backend_reachable(base_url: str = "http://localhost:8200/health") -> bool:
    try:
        with urllib.request.urlopen(base_url, timeout=3) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def run_command(command: list[str], cwd: Path, timeout: int) -> tuple[int, str]:
    kwargs: dict = {
        "cwd": cwd,
        "capture_output": True,
        "text": True,
        "timeout": timeout,
    }
    # Windows: npx/npm are .cmd shims; shell=False raises FileNotFoundError.
    if sys.platform == "win32":
        proc = subprocess.run(subprocess.list2cmdline(command), shell=True, **kwargs)
    else:
        proc = subprocess.run(command, shell=False, **kwargs)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output


def evaluate_result(case: dict, exit_code: int, output: str) -> bool:
    criteria = case.get("success_criteria", {})
    expected_exit = criteria.get("exit_code", 0)
    if exit_code != expected_exit:
        return False
    if case.get("layer") == "pytest":
        if "FAILED" in output or "ERROR" in output:
            return False
        if criteria.get("min_passed"):
            m = re.search(r"(\d+) passed", output)
            if not m or int(m.group(1)) < criteria["min_passed"]:
                return False
    if case.get("layer") == "playwright":
        if re.search(r"\bfailed\b", output, re.I):
            return False
        # All skipped (e.g. backend down) is not a manifest PASS unless explicit.
        if re.search(r"\d+ skipped", output) and not re.search(r"\d+ passed", output):
            return False
    return True


def run_case(case: dict, *, suite: str | None = None) -> CaseResult:
    cwd = ROOT / case.get("cwd", ".")
    timeout = int(case.get("timeout_seconds", 600))
    command = case["command"]

    if case.get("layer") == "playwright" and not backend_reachable():
        return CaseResult(
            case_id=case["id"],
            title=case["title"],
            passed=False,
            exit_code=-1,
            command=command,
            output_tail=(
                "BLOCKED: backend :8200 unreachable. "
                "Start Docker Desktop, then: docker compose up -d && make backend"
            ),
            suite=suite,
        )

    exit_code, output = run_command(command, cwd, timeout)
    passed = evaluate_result(case, exit_code, output)
    tail = output.strip()[-2000:] if output else ""
    return CaseResult(
        case_id=case["id"],
        title=case["title"],
        passed=passed,
        exit_code=exit_code,
        command=command,
        output_tail=tail,
        suite=suite,
    )


def append_execution_log(results: list[CaseResult], manifest_version: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    block = [
        f"\n## AI Runner — {now}\n",
        f"- Manifest: v{manifest_version}\n",
        f"- Cases: {len(results)} · PASS {passed} · FAIL {failed}\n",
        "\n| Case | Result |\n|------|--------|\n",
    ]
    for r in results:
        status = "PASS" if r.passed else f"FAIL ({r.exit_code})"
        block.append(f"| {r.case_id} | {status} |\n")
    EXEC_LOG.parent.mkdir(parents=True, exist_ok=True)
    if EXEC_LOG.is_file():
        content = EXEC_LOG.read_text(encoding="utf-8")
    else:
        content = "# Test Execution Log\n"
    EXEC_LOG.write_text(content + "".join(block), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AI-executable test cases")
    parser.add_argument("case_id", nargs="?", help="Single case id, e.g. TC-RT-COLLECT-001")
    parser.add_argument("--suite", help="Suite id from manifest suites")
    parser.add_argument("--priority", choices=["P0", "P1", "P2"])
    parser.add_argument("--layer", choices=["pytest", "playwright", "make"])
    parser.add_argument("--list", action="store_true", help="List matching cases")
    parser.add_argument("--log", action="store_true", help="Append summary to EXECUTION_LOG.md")
    args = parser.parse_args()

    manifest = load_manifest()
    cases = filter_cases(
        manifest,
        case_id=args.case_id,
        suite=args.suite,
        priority=args.priority,
        layer=args.layer,
    )
    if not cases and not args.list:
        raise SystemExit("No cases matched filters")

    if args.list:
        for c in cases:
            print(f"{c['id']}\t{c.get('priority')}\t{c.get('layer')}\t{c['title']}")
        return

    results: list[CaseResult] = []
    for case in cases:
        result = run_case(case, suite=args.suite)
        results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.case_id} — {result.title}")
        if not result.passed:
            print(f"  cmd: {' '.join(result.command)}")
            print(f"  tail:\n{result.output_tail}")

    summary = {
        "manifest_version": manifest.get("version"),
        "total": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
        "cases": [{"id": r.case_id, "passed": r.passed, "exit_code": r.exit_code} for r in results],
    }
    print(json.dumps(summary, ensure_ascii=False))

    if args.log:
        append_execution_log(results, manifest.get("version", "?"))

    if any(not r.passed for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
