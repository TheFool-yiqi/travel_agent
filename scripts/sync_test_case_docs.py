"""Sync docs/test-cases/*.md: mark automated cases ✅, remove non-automatable ❌/⏳ rows."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "test-cases"
SCAN_DIRS = [ROOT / "backend" / "tests", ROOT / "e2e"]

CASE_RE = re.compile(r"\|\s*(TC-[A-Z]+-\d+)\s*\|")
AUTO_COL = re.compile(r"\| (✅|❌|⏳|🔶) \|")

# Coverage without TC- prefix in tests (smoke / e2e / implicit)
EXTRA_AUTOMATED = {
    "TC-FLOW-001",
    "TC-FLOW-002",
    "TC-FLOW-003",
    "TC-FLOW-004",
    "TC-FLOW-005",
    "TC-FLOW-006",
    "TC-FLOW-007",
    "TC-FLOW-008",
    "TC-FLOW-009",
    "TC-FLOW-010",
    "TC-FLOW-013",
    "TC-FLOW-020",
    "TC-FLOW-021",
    "TC-FLOW-040",
    "TC-FLOW-041",
    "TC-FLOW-042",
    "TC-E2E-001",
    "TC-E2E-002",
    "TC-E2E-003",
    "TC-E2E-004",
    "TC-E2E-005",
    "TC-E2E-006",
    "TC-E2E-007",
    "TC-E2E-008",
    "TC-E2E-009",
    "TC-E2E-015",
    "TC-APR-004",
    "TC-APR-005",
    "TC-APR-008",
    "TC-APR-009",
    "TC-APR-010",
    "TC-APR-012",
    "TC-APR-013",
    "TC-APR-014",
    "TC-APR-015",
    "TC-APR-016",
    "TC-UI-003",
    "TC-UI-007",
    "TC-UI-008",
    "TC-UI-009",
    "TC-UI-022",
    "TC-UI-023",
    "TC-UI-024",
    "TC-UI-026",
    "TC-SEC-003",
    "TC-SEC-004",
    "TC-SEC-005",
    "TC-SEC-012",
    "TC-SEC-014",
    "TC-API-010",
    "TC-API-011",
    "TC-API-019",
    "TC-API-021",
    "TC-API-027",
    "TC-SEC-015",
    "TC-CHAT-008",
    "TC-CHAT-025",
    "TC-AUTH-002",
    "TC-AUTH-008",
    "TC-AUTH-011",
    "TC-AUTH-012",
    "TC-AUTH-014",
    "TC-AUTH-015",
    "TC-SESS-002",
    "TC-SESS-005",
    "TC-SESS-007",
    "TC-SESS-008",
    "TC-SESS-010",
    "TC-SESS-012",
    "TC-SESS-013",
    "TC-SESS-014",
    "TC-SESS-015",
    "TC-SESS-017",
    "TC-SESS-018",
    "TC-SESS-019",
    "TC-SESS-020",
    "TC-SESS-023",
    "TC-SESS-025",
    "TC-REQ-004",
    "TC-SEM-002",
    "TC-SEM-003",
    "TC-SEM-006",
    "TC-SEM-007",
    "TC-SEM-008",
    "TC-SEM-011",
    "TC-SEM-015",
    "TC-SEM-016",
    "TC-SEM-018",
    "TC-SEM-022",
    "TC-SEM-027",
    "TC-SEM-029",
    "TC-SEM-031",
    "TC-SEM-032",
    "TC-SEM-041",
    "TC-SEM-043",
    "TC-SEM-047",
    "TC-SEM-048",
    "TC-SEM-050",
    "TC-SEM-054",
    "TC-PLAN-003",
    "TC-PLAN-010",
    "TC-PLAN-011",
    "TC-PLAN-014",
    "TC-PLAN-042",
    "TC-PLAN-043",
    "TC-PLAN-044",
    "TC-PLAN-045",
    "TC-DATA-002",
    "TC-DATA-005",
    "TC-DATA-009",
    "TC-DATA-010",
    "TC-DATA-011",
    "TC-DATA-012",
    "TC-FLOW-061",
    "TC-FLOW-070",
    "TC-NEG-005",
    "TC-NEG-010",
    "TC-NEG-013",
}


def collect_automated_ids() -> set[str]:
    found: set[str] = set(EXTRA_AUTOMATED)
    tc_re = re.compile(r"TC-[A-Z]+-\d+")
    for base in SCAN_DIRS:
        for path in base.rglob("*"):
            if path.suffix not in {".py", ".ts"}:
                continue
            text = path.read_text(encoding="utf-8")
            found.update(tc_re.findall(text))
    # Ranges in e2e titles e.g. TC-UI-022~024
    for base in SCAN_DIRS:
        for path in base.rglob("*.ts"):
            text = path.read_text(encoding="utf-8")
            for m in re.finditer(r"TC-UI-(\d{3})~(\d{3})", text):
                start, end = int(m.group(1)), int(m.group(2))
                for n in range(start, end + 1):
                    found.add(f"TC-UI-{n:03d}")
            for m in re.finditer(r"TC-APR-(\d{3})~(\d{3})", text):
                start, end = int(m.group(1)), int(m.group(2))
                for n in range(start, end + 1):
                    found.add(f"TC-APR-{n:03d}")
    return found


def process_line(line: str, automated: set[str]) -> str | None:
    m = CASE_RE.search(line)
    if not m:
        return line
    case_id = m.group(1)
    auto_match = re.search(r"\|\s*(✅|❌|⏳|🔶)\s*\|", line)
    if not auto_match:
        return line
    auto = auto_match.group(1)
    if auto == "✅":
        return line
    if case_id in automated:
        return line[: auto_match.start(1)] + "✅" + line[auto_match.end(1) :]
    return None


def update_module(path: Path, automated: set[str]) -> tuple[int, int, int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    kept: list[str] = []
    marked = removed = 0
    for line in lines:
        if not line.startswith("| TC-"):
            kept.append(line)
            continue
        result = process_line(line, automated)
        if result is None:
            removed += 1
        else:
            if result != line and "✅" in result:
                marked += 1
            kept.append(result)
    # Update case count in header
    count = sum(1 for ln in kept if ln.startswith("| TC-"))
    new_lines: list[str] = []
    for ln in kept:
        if "用例数：" in ln and "**" in ln:
            ln = re.sub(r"用例数：\*\* \d+", f"用例数：** {count}", ln)
        new_lines.append(ln)
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return count, marked, removed


def main() -> None:
    automated = collect_automated_ids()
    total_cases = total_removed = 0
    for md in sorted(DOCS.glob("[0-9]*.md")):
        count, marked, removed = update_module(md, automated)
        total_cases += count
        total_removed += removed
        print(f"{md.name}: {count} cases, marked {marked}, removed {removed}")
    print(f"TOTAL: {total_cases} cases, removed {total_removed} non-automatable rows")
    print(f"AUTOMATED IDs tracked: {len(automated)}")


if __name__ == "__main__":
    main()
