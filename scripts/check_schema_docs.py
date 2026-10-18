"""Validate BASE-02-01 documents without importing Django or inspecting migrations.

Checks story coverage, ERD entities, cross-document table references and planned
fields. Runtime, schema implementation and migration validation belong to Task 2.
Run: python scripts/check_schema_docs.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "base-02-schema-contract.md"
STORIES = ROOT / "docs" / "user-stories.md"
PLAN = ROOT / "docs" / "sprint-1-technical-plan.md"
BY_STORY = ROOT / "docs" / "database-by-story.md"

ROUND_1_TABLES = [
    "User",
    "UserProfile",
    "UniversityIdentity",
    "Sport",
    "UserSportInterest",
    "Venue",
    "VenueSport",
    "VenueOpeningHour",
    "Party",
    "PartyMembership",
    "JoinRequest",
]

problems: list[str] = []


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def section(text: str, start: str, end: str | None = None) -> str:
    match = re.search(start, text, re.M)
    assert match, f"heading not found: {start}"
    rest = text[match.end() :]
    if end:
        stop = re.search(end, rest, re.M)
        rest = rest[: stop.start()] if stop else rest
    return rest


def rows(block: str) -> list[list[str]]:
    """Cells of every markdown table row, skipping the |---|---| separators."""
    result = []
    for line in block.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        result.append(cells)
    return result


def code_words(cell: str) -> set[str]:
    return {word for word in re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", cell)}


def dictionary(contract: str) -> dict[str, set[str]]:
    """Table name -> field names, read from the section 3 data dictionary."""
    block = section(contract, r"^## 3\. ", r"^## 4\. ")
    tables: dict[str, set[str]] = {}
    current = None
    for cells in rows(block):
        name = re.match(r"^\*\*([A-Za-z_][A-Za-z0-9_]*)\*\*", cells[0])
        if name:
            current = name.group(1)
            tables.setdefault(current, set())
            fields = code_words(cells[1]) if len(cells) > 1 else set()
            tables[current] |= fields
        elif current and len(cells) > 1 and not cells[0]:
            tables[current] |= code_words(cells[1])
    return tables


def erd_entities(contract: str) -> set[str]:
    """Entity names declared inside the fenced mermaid blocks of the ERD section."""
    block = section(contract, r"^## 2\. ERD", r"^## 3\. ")
    body = "\n".join(line for line in block.split("\n") if not line.strip().startswith("```"))
    return set(re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\{\s*$", body, re.M))


def check_story_coverage() -> None:
    stories = {int(n) for n in re.findall(r"^## US(\d+) ", read(STORIES), re.M)}
    if stories != set(range(1, 15)):
        problems.append(f"user-stories.md lists US {sorted(stories)}, expected 1-14")

    contract = read(CONTRACT)
    mapped = section(contract, r"^### 1\.1 ", r"^### 1\.2 ")
    missing = sorted(set(range(1, 15)) - {int(n) for n in re.findall(r"US(\d+)", mapped)})
    if missing:
        problems.append(f"section 1.1 does not map stories {missing} to tables")
    for token in ("ChatMessage", "Report", "ModerationAction", "Notification"):
        if token not in mapped:
            problems.append(f"section 1.1 has no whole-system row mentioning {token}")


def check_round_1_tables() -> None:
    contract = read(CONTRACT)
    listed = section(contract, r"^### 1\.2 ", r"^### 1\.3 ")
    if "11" not in listed:
        problems.append("section 1.2 no longer states the round 1 table count of 11")
    for table in ROUND_1_TABLES:
        if f"`{table}`" not in listed and table != "User":
            problems.append(f"section 1.2 does not list round 1 table {table}")


def check_erd_is_documented() -> None:
    contract = read(CONTRACT)
    documented = dictionary(contract)
    for entity in sorted(erd_entities(contract)):
        if entity == "django_session":  # framework table, described in prose only
            continue
        if entity not in documented:
            problems.append(f"ERD entity {entity} has no data dictionary entry")


def check_between_docs() -> None:
    documented = dictionary(read(CONTRACT))
    for cells in rows(section(read(BY_STORY), r"^## 4\. ", r"^\*\*ภาพความสัมพันธ์")):
        name = re.match(r"^`([A-Za-z_][A-Za-z0-9_]*)`", cells[0])
        if name and name.group(1) not in documented:
            problems.append(
                f"database-by-story.md lists {name.group(1)} which the contract"
                " data dictionary does not define"
            )


def check_technical_plan_fields() -> None:
    documented = dictionary(read(CONTRACT))
    block = section(read(PLAN), r"^## 3\. Database", r"^\*\*กฎที่ service")
    for cells in rows(block):
        table = cells[0].strip("`")
        if table not in ROUND_1_TABLES or len(cells) < 2:
            continue
        plan_fields = code_words(cells[1])
        # "id" is implied for every table and is not repeated in every dictionary row.
        unknown = sorted(plan_fields - documented.get(table, set()) - {"id"})
        if unknown:
            problems.append(
                f"Technical Plan fields for {table} missing from the contract: {unknown}"
            )


def main() -> int:
    checks = [
        check_story_coverage,
        check_round_1_tables,
        check_erd_is_documented,
        check_between_docs,
        check_technical_plan_fields,
    ]
    for check in checks:
        check()

    if problems:
        print("Schema doc check FAILED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(
        "Schema doc check passed: US1-US14 coverage, whole-system ERD vs data dictionary,"
        " Sprint 1 fields vs Technical Plan. Document checks only; runtime not checked."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
