#!/usr/bin/env python3
"""Read and validate Rhymework PROGRESS.md files.

The parser intentionally supports only GitHub-style pipe tables:

    | A | B |
    |---|---|
    | x | y |

It is read-only and exits non-zero when cached snapshot progress,
dependencies, or current state are inconsistent.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SUMMARY_COLUMNS = ["Epic", "Weight", "Progress", "Status", "Owner"]
TASK_COLUMNS = [
    "ID",
    "Epic",
    "Task",
    "Owner",
    "Complexity",
    "Model",
    "Reasoning",
    "Status",
    "Progress",
    "Depends On",
    "Validation",
]
STATUSES = {"TODO", "IN_PROGRESS", "REVIEW", "DONE", "BLOCKED"}
COMPLEXITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
EPSILON = 0.01


class ProgressError(ValueError):
    pass


@dataclass(frozen=True)
class Epic:
    name: str
    weight: float
    progress: float
    status: str
    owner: str


@dataclass(frozen=True)
class Task:
    task_id: str
    epic: str
    task: str
    owner: str
    complexity: str
    model: str
    reasoning: str
    status: str
    progress: float
    depends_on: tuple[str, ...]
    validation: str


def parse_progress(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    visible_text = _strip_fenced_blocks(text)
    overall_cached = _parse_overall_progress(visible_text)
    tables = _extract_tables(visible_text)
    summary_rows = _rows_for_columns(tables, SUMMARY_COLUMNS, "Summary")
    task_rows = _rows_for_columns(tables, TASK_COLUMNS, "Tasks")

    epics = [_parse_epic(row) for row in summary_rows]
    tasks = [_parse_task(row) for row in task_rows]
    _validate(epics, tasks, overall_cached)
    epic_results = _epic_results(epics, tasks)
    overall = _overall_progress(epics, epic_results)
    ready = _ready_tasks(tasks)

    return {
        "overall_progress": _display_percent(overall, _all_tasks_done(tasks)),
        "ready_tasks": ready,
        "epics": [
            {
                "epic": epic.name,
                "weight": epic.weight,
                "progress": _display_percent(
                    epic_results[epic.name]["progress"],
                    _all_tasks_done(_tasks_for_epic(tasks, epic.name)),
                ),
                "status": epic_results[epic.name]["status"],
                "owner": epic.owner,
            }
            for epic in epics
        ],
        "tasks": [
            {
                "id": task.task_id,
                "epic": task.epic,
                "status": task.status,
                "progress": _derived_task_progress(task),
                "depends_on": list(task.depends_on),
            }
            for task in tasks
        ],
        "rules": {
            "ready": "TODO tasks whose dependencies are all DONE.",
            "task_progress": "DONE is 100%; every other status is 0%.",
            "done_validation": "DONE tasks require Validation beginning with 'PASS: '.",
            "epic_status": (
                "all DONE -> DONE; any BLOCKED -> BLOCKED; any IN_PROGRESS -> "
                "IN_PROGRESS; REVIEW without active work -> REVIEW; mixed DONE+TODO "
                "-> IN_PROGRESS; otherwise TODO."
            ),
        },
    }


def _parse_overall_progress(text: str) -> float | None:
    matches = re.findall(r"(?im)^\s*Overall Progress\s*:\s*([^\n]+?)\s*$", text)
    if not matches:
        raise ProgressError("missing Overall Progress")
    if len(matches) > 1:
        raise ProgressError("duplicate Overall Progress")
    return _parse_percent(matches[0], "Overall Progress")


def _strip_fenced_blocks(text: str) -> str:
    lines = text.splitlines()
    visible: list[str] = []
    fence_marker: str | None = None
    for line in lines:
        marker = _fence_marker(line)
        if marker and fence_marker is None:
            fence_marker = marker
            continue
        if fence_marker is not None:
            if marker == fence_marker:
                fence_marker = None
            continue
        visible.append(line)
    return "\n".join(visible)


def _fence_marker(line: str) -> str | None:
    stripped = line.lstrip()
    for marker in ("```", "~~~"):
        if stripped.startswith(marker):
            return marker
    return None


def _extract_tables(text: str) -> list[tuple[list[str], list[dict[str, str]]]]:
    lines = text.splitlines()
    tables: list[tuple[list[str], list[dict[str, str]]]] = []
    index = 0
    while index < len(lines):
        if not _is_table_line(lines[index]):
            index += 1
            continue
        if index + 1 >= len(lines) or not _is_separator_line(lines[index + 1]):
            index += 1
            continue
        headers = _split_table_line(lines[index])
        _validate_headers(headers)
        separator_cells = _split_table_line(lines[index + 1])
        if len(separator_cells) != len(headers):
            raise ProgressError("table separator cell count does not match header count")
        rows: list[dict[str, str]] = []
        index += 2
        while index < len(lines) and _is_table_line(lines[index]):
            cells = _split_table_line(lines[index])
            if len(cells) != len(headers):
                raise ProgressError("table row cell count does not match header count")
            rows.append(dict(zip(headers, cells)))
            index += 1
        tables.append((headers, rows))
    return tables


def _rows_for_columns(
    tables: Iterable[tuple[list[str], list[dict[str, str]]]], required: list[str], label: str
) -> list[dict[str, str]]:
    matches = [rows for headers, rows in tables if all(column in headers for column in required)]
    if not matches:
        raise ProgressError(f"missing {label} table")
    if len(matches) > 1:
        raise ProgressError(f"multiple {label} tables match required columns")
    return matches[0]


def _is_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def _is_separator_line(line: str) -> bool:
    cells = _split_table_line(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def _split_table_line(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        raise ProgressError("table line must start and end with pipe")
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def _validate_headers(headers: list[str]) -> None:
    _reject_duplicates(headers, "header")


def _parse_epic(row: dict[str, str]) -> Epic:
    return Epic(
        name=_required(row, "Epic"),
        weight=_parse_number(_required(row, "Weight"), "Weight"),
        progress=_parse_percent(_required(row, "Progress"), "Summary Progress"),
        status=_parse_status(_required(row, "Status")),
        owner=_required(row, "Owner"),
    )


def _parse_task(row: dict[str, str]) -> Task:
    return Task(
        task_id=_required(row, "ID"),
        epic=_required(row, "Epic"),
        task=_required(row, "Task"),
        owner=_required(row, "Owner"),
        complexity=_parse_complexity(_required(row, "Complexity")),
        model=_required(row, "Model"),
        reasoning=_required(row, "Reasoning"),
        status=_parse_status(_required(row, "Status")),
        progress=_parse_percent(_required(row, "Progress"), "Task Progress"),
        depends_on=_parse_dependencies(row.get("Depends On", "")),
        validation=row.get("Validation", "").strip(),
    )


def _required(row: dict[str, str], column: str) -> str:
    value = row.get(column, "").strip()
    if not value:
        raise ProgressError(f"missing required value in column {column}")
    return value


def _parse_status(value: str) -> str:
    if value not in STATUSES:
        raise ProgressError(f"invalid status {value!r}; expected one of {sorted(STATUSES)}")
    return value


def _parse_complexity(value: str) -> str:
    if value not in COMPLEXITIES:
        raise ProgressError(
            f"invalid complexity {value!r}; expected one of {sorted(COMPLEXITIES)}"
        )
    return value


def _parse_number(value: str, label: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise ProgressError(f"{label} must be numeric: {value!r}") from exc
    if not math.isfinite(number):
        raise ProgressError(f"{label} must be finite: {value!r}")
    if number <= 0:
        raise ProgressError(f"{label} must be positive: {value!r}")
    return number


def _parse_percent(value: str, label: str) -> float:
    raw = value.strip().removesuffix("%").strip()
    try:
        number = float(raw)
    except ValueError as exc:
        raise ProgressError(f"{label} must be a percentage: {value!r}") from exc
    if not math.isfinite(number) or number < 0 or number > 100:
        raise ProgressError(f"{label} must be a finite percentage from 0 to 100: {value!r}")
    return number


def _parse_dependencies(value: str) -> tuple[str, ...]:
    stripped = value.strip()
    if not stripped or stripped == "-":
        return ()
    return tuple(part.strip() for part in stripped.split(",") if part.strip())


def _validate(epics: list[Epic], tasks: list[Task], overall_cached: float | None) -> None:
    _reject_duplicates([epic.name for epic in epics], "epic")
    _reject_duplicates([task.task_id for task in tasks], "task ID")

    epic_names = {epic.name for epic in epics}
    task_ids = {task.task_id for task in tasks}
    for task in tasks:
        if task.epic not in epic_names:
            raise ProgressError(f"task {task.task_id} references unknown epic {task.epic!r}")
        for dep in task.depends_on:
            if dep == task.task_id:
                raise ProgressError(f"task {task.task_id} depends on itself")
            if dep not in task_ids:
                raise ProgressError(f"task {task.task_id} depends on unknown task {dep!r}")
        expected = _derived_task_progress(task)
        if not _close(task.progress, expected):
            raise ProgressError(
                f"task {task.task_id} cached progress is stale: {task.progress}% != {expected}%"
            )
        if task.status == "DONE" and not task.validation.startswith("PASS: "):
            raise ProgressError(f"task {task.task_id} is DONE without PASS validation evidence")

    _reject_cycles(tasks)

    done_ids = {task.task_id for task in tasks if task.status == "DONE"}
    for task in tasks:
        if task.status == "DONE":
            unmet = [dep for dep in task.depends_on if dep not in done_ids]
            if unmet:
                raise ProgressError(f"task {task.task_id} is DONE with unmet dependencies: {unmet}")

    if epics or tasks:
        counts = {epic.name: 0 for epic in epics}
        for task in tasks:
            counts[task.epic] += 1
        empty_epics = [name for name, count in counts.items() if count == 0]
        if empty_epics:
            raise ProgressError(f"declared epics without tasks: {empty_epics}")

    epic_results = _epic_results(epics, tasks)
    for epic in epics:
        result = epic_results[epic.name]
        epic_tasks = _tasks_for_epic(tasks, epic.name)
        displayed_progress = _display_percent(result["progress"], _all_tasks_done(epic_tasks))
        if not _close(epic.progress, displayed_progress):
            raise ProgressError(
                f"epic {epic.name} cached progress is stale: "
                f"{epic.progress}% != {displayed_progress}%"
            )
        if epic.status != result["status"]:
            raise ProgressError(
                f"epic {epic.name} cached status is stale: {epic.status} != {result['status']}"
            )

    if overall_cached is not None:
        overall = _overall_progress(epics, epic_results)
        displayed_overall = _display_percent(overall, _all_tasks_done(tasks))
        if not _close(overall_cached, displayed_overall):
            raise ProgressError(
                f"overall progress is stale: {overall_cached}% != {displayed_overall}%"
            )


def _reject_duplicates(values: list[str], label: str) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        raise ProgressError(f"duplicate {label}: {sorted(duplicates)}")


def _reject_cycles(tasks: list[Task]) -> None:
    graph = {task.task_id: set(task.depends_on) for task in tasks}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            raise ProgressError(f"dependency cycle includes {task_id}")
        visiting.add(task_id)
        for dependency in graph[task_id]:
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in graph:
        visit(task_id)


def _epic_results(epics: list[Epic], tasks: list[Task]) -> dict[str, dict[str, float | str]]:
    tasks_by_epic = {epic.name: [] for epic in epics}
    for task in tasks:
        if task.epic in tasks_by_epic:
            tasks_by_epic[task.epic].append(task)
    return {
        epic.name: {
            "progress": _derive_epic_progress(tasks_by_epic[epic.name]),
            "status": _derive_epic_status(tasks_by_epic[epic.name]),
        }
        for epic in epics
    }


def _derive_epic_progress(tasks: list[Task]) -> float:
    if not tasks:
        return 0.0
    done = sum(1 for task in tasks if task.status == "DONE")
    return done / len(tasks) * 100


def _derive_epic_status(tasks: list[Task]) -> str:
    if not tasks:
        return "TODO"
    statuses = {task.status for task in tasks}
    if statuses == {"DONE"}:
        return "DONE"
    if "BLOCKED" in statuses:
        return "BLOCKED"
    if "IN_PROGRESS" in statuses:
        return "IN_PROGRESS"
    if "REVIEW" in statuses:
        return "REVIEW"
    if "DONE" in statuses and "TODO" in statuses:
        return "IN_PROGRESS"
    return "TODO"


def _overall_progress(epics: list[Epic], results: dict[str, dict[str, float | str]]) -> float:
    if not epics:
        return 0.0
    max_weight = max(epic.weight for epic in epics)
    normalized_weights = [epic.weight / max_weight for epic in epics]
    total_weight = math.fsum(normalized_weights)
    weighted = math.fsum(
        float(results[epic.name]["progress"]) * weight
        for epic, weight in zip(epics, normalized_weights)
    )
    return weighted / total_weight


def _tasks_for_epic(tasks: list[Task], epic_name: str) -> list[Task]:
    return [task for task in tasks if task.epic == epic_name]


def _all_tasks_done(tasks: list[Task]) -> bool:
    return bool(tasks) and all(task.status == "DONE" for task in tasks)


def _ready_tasks(tasks: list[Task]) -> list[str]:
    done_ids = {task.task_id for task in tasks if task.status == "DONE"}
    return [
        task.task_id
        for task in tasks
        if task.status == "TODO" and all(dep in done_ids for dep in task.depends_on)
    ]


def _derived_task_progress(task: Task) -> float:
    return 100.0 if task.status == "DONE" else 0.0


def _round_percent(value: float) -> float:
    rounded = round(value, 2)
    return int(rounded) if float(rounded).is_integer() else rounded


def _display_percent(value: float, complete: bool) -> float:
    rounded = _round_percent(value)
    if not complete and rounded >= 100:
        return 99.99
    return rounded


def _close(left: float, right: float) -> bool:
    return abs(left - right) <= EPSILON


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("progress_file", type=Path)
    args = parser.parse_args(argv)

    try:
        result = parse_progress(args.progress_file)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ProgressError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
