import json
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "progress.py"
sys.path.insert(0, str(ROOT / "scripts"))

from progress import ProgressError, parse_progress  # noqa: E402


def progress_doc(overall="66.67%", summary_rows=None, task_rows=None):
    if summary_rows is None:
        summary_rows = [
            "| Architecture | 10 | 100% | DONE | main |",
            "| Backend | 20 | 50% | IN_PROGRESS | backend-agent |",
        ]
    if task_rows is None:
        task_rows = [
            "| A-001 | Architecture | Decide contracts | main | CRITICAL | Astra | high | DONE | 100% | - | PASS: architecture reviewed |",
            "| B-001 | Backend | Add API | backend-agent | MEDIUM | Terra | medium | DONE | 100% | A-001 | PASS: unit tests |",
            "| B-002 | Backend | Add search | backend-agent | MEDIUM | Terra | medium | TODO | 0% | B-001 | - |",
        ]
    return textwrap.dedent(
        f"""\
        # Project Progress

        Last Updated: 2026-09-26
        Overall Progress: {overall}

        ## Summary

        | Epic | Weight | Progress | Status | Owner |
        |---|---:|---:|---|---|
        {chr(10).join(summary_rows)}

        ## Tasks

        | ID | Epic | Task | Owner | Complexity | Model | Reasoning | Status | Progress | Depends On | Validation |
        |---|---|---|---|---|---|---|---|---:|---|---|
        {chr(10).join(task_rows)}
        """
    )


def replace_tasks_header(document, header):
    original = (
        "| ID | Epic | Task | Owner | Complexity | Model | Reasoning | Status | Progress | "
        "Depends On | Validation |"
    )
    return document.replace(original, header)


class ProgressTests(unittest.TestCase):
    def write_doc(self, content):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "PROGRESS.md"
        path.write_text(content, encoding="utf-8")
        return path

    def test_valid_dag_reports_ready_and_weighted_progress(self):
        path = self.write_doc(progress_doc())

        result = parse_progress(path)

        self.assertEqual(result["ready_tasks"], ["B-002"])
        self.assertEqual(result["overall_progress"], 66.67)
        self.assertEqual(
            [(epic["epic"], epic["progress"], epic["status"]) for epic in result["epics"]],
            [("Architecture", 100, "DONE"), ("Backend", 50, "IN_PROGRESS")],
        )
        self.assertIn("mixed DONE+TODO", result["rules"]["epic_status"])

    def test_extra_columns_are_allowed(self):
        doc = progress_doc()
        doc = doc.replace(
            "| Epic | Weight | Progress | Status | Owner |",
            "| Epic | Weight | Progress | Status | Owner | Notes |",
        ).replace(
            "|---|---:|---:|---|---|",
            "|---|---:|---:|---|---|---|",
        ).replace(
            "| Architecture | 10 | 100% | DONE | main |",
            "| Architecture | 10 | 100% | DONE | main | ok |",
        ).replace(
            "| Backend | 20 | 50% | IN_PROGRESS | backend-agent |",
            "| Backend | 20 | 50% | IN_PROGRESS | backend-agent | ok |",
        )
        path = self.write_doc(doc)

        result = parse_progress(path)

        self.assertEqual(result["ready_tasks"], ["B-002"])

    def test_missing_overall_progress_is_invalid(self):
        path = self.write_doc(progress_doc().replace("Overall Progress: 66.67%\n", ""))

        with self.assertRaisesRegex(ProgressError, "missing Overall Progress"):
            parse_progress(path)

    def test_missing_summary_table_is_invalid(self):
        path = self.write_doc(
            textwrap.dedent(
                """\
                # Project Progress
                Overall Progress: 0%

                | ID | Epic | Task | Owner | Complexity | Model | Reasoning | Status | Progress | Depends On | Validation |
                |---|---|---|---|---|---|---|---|---:|---|---|
                """
            )
        )

        with self.assertRaisesRegex(ProgressError, "missing Summary table"):
            parse_progress(path)

    def test_missing_tasks_table_is_invalid(self):
        path = self.write_doc(
            textwrap.dedent(
                """\
                # Project Progress
                Overall Progress: 0%

                | Epic | Weight | Progress | Status | Owner |
                |---|---:|---:|---|---|
                """
            )
        )

        with self.assertRaisesRegex(ProgressError, "missing Tasks table"):
            parse_progress(path)

    def test_header_typo_is_invalid(self):
        path = self.write_doc(
            replace_tasks_header(
                progress_doc(),
                "| ID | Epic | Task | Owner | Complexity | Model | Reasoning | State | Progress | Depends On | Validation |",
            )
        )

        with self.assertRaisesRegex(ProgressError, "missing Tasks table"):
            parse_progress(path)

    def test_arbitrary_text_is_invalid(self):
        path = self.write_doc("nothing useful here\n")

        with self.assertRaisesRegex(ProgressError, "missing Overall Progress"):
            parse_progress(path)

    def test_fenced_example_tables_are_ignored(self):
        doc = textwrap.dedent(
            """\
            # Project Progress
            Overall Progress: 0%

            ```markdown
            | Epic | Weight | Progress | Status | Owner |
            |---|---:|---:|---|---|
            | Example | 10 | 0% | TODO | docs |
            ```

            | ID | Epic | Task | Owner | Complexity | Model | Reasoning | Status | Progress | Depends On | Validation |
            |---|---|---|---|---|---|---|---|---:|---|---|
            """
        )
        path = self.write_doc(doc)

        with self.assertRaisesRegex(ProgressError, "missing Summary table"):
            parse_progress(path)

    def test_duplicate_header_is_invalid(self):
        path = self.write_doc(
            replace_tasks_header(
                progress_doc(),
                "| ID | Epic | Task | Owner | Complexity | Model | Reasoning | Status | Progress | Depends On | Validation | ID |",
            )
        )

        with self.assertRaisesRegex(ProgressError, "duplicate header"):
            parse_progress(path)

    def test_mismatched_row_cell_count_is_invalid(self):
        path = self.write_doc(
            progress_doc(
                summary_rows=["| Backend | 20 | 0% | TODO |"],
                task_rows=[
                    "| B-001 | Backend | Add API | backend-agent | MEDIUM | Terra | medium | TODO | 0% | - | - |",
                ],
            )
        )

        with self.assertRaisesRegex(ProgressError, "row cell count"):
            parse_progress(path)

    def test_mismatched_separator_cell_count_is_invalid(self):
        path = self.write_doc(progress_doc().replace("|---|---:|---:|---|---|", "|---|---|"))

        with self.assertRaisesRegex(ProgressError, "separator cell count"):
            parse_progress(path)

    def test_unknown_dependency_is_invalid(self):
        path = self.write_doc(
            progress_doc(
                summary_rows=["| Backend | 20 | 0% | TODO | backend-agent |"],
                task_rows=[
                    "| B-001 | Backend | Add API | backend-agent | MEDIUM | Terra | medium | TODO | 0% | B-999 | - |",
                ],
            )
        )

        with self.assertRaisesRegex(ProgressError, "unknown task"):
            parse_progress(path)

    def test_unknown_epic_is_invalid(self):
        path = self.write_doc(
            progress_doc(
                summary_rows=["| Backend | 20 | 0% | TODO | backend-agent |"],
                task_rows=[
                    "| F-001 | Frontend | Add UI | frontend-agent | MEDIUM | Terra | medium | TODO | 0% | - | - |",
                ],
            )
        )

        with self.assertRaisesRegex(ProgressError, "unknown epic"):
            parse_progress(path)

    def test_self_dependency_is_invalid(self):
        path = self.write_doc(
            progress_doc(
                summary_rows=["| Backend | 20 | 0% | TODO | backend-agent |"],
                task_rows=[
                    "| B-001 | Backend | Add API | backend-agent | MEDIUM | Terra | medium | TODO | 0% | B-001 | - |",
                ],
            )
        )

        with self.assertRaisesRegex(ProgressError, "depends on itself"):
            parse_progress(path)

    def test_done_with_unmet_dependency_is_invalid(self):
        path = self.write_doc(
            progress_doc(
                overall="50%",
                summary_rows=["| Backend | 20 | 50% | IN_PROGRESS | backend-agent |"],
                task_rows=[
                    "| B-001 | Backend | Schema | backend-agent | MEDIUM | Terra | medium | TODO | 0% | - | - |",
                    "| B-002 | Backend | API | backend-agent | MEDIUM | Terra | medium | DONE | 100% | B-001 | PASS: unit tests |",
                ],
            )
        )

        with self.assertRaisesRegex(ProgressError, "unmet dependencies"):
            parse_progress(path)

    def test_invalid_complexity_is_rejected(self):
        path = self.write_doc(
            progress_doc(
                summary_rows=["| Backend | 20 | 0% | TODO | backend-agent |"],
                task_rows=[
                    "| B-001 | Backend | Add API | backend-agent | TINY | Terra | medium | TODO | 0% | - | - |",
                ],
            )
        )

        with self.assertRaisesRegex(ProgressError, "invalid complexity"):
            parse_progress(path)

    def test_cycle_is_invalid(self):
        path = self.write_doc(
            progress_doc(
                overall="0%",
                summary_rows=["| Backend | 20 | 0% | TODO | backend-agent |"],
                task_rows=[
                    "| B-001 | Backend | One | backend-agent | MEDIUM | Terra | medium | TODO | 0% | B-002 | - |",
                    "| B-002 | Backend | Two | backend-agent | MEDIUM | Terra | medium | TODO | 0% | B-001 | - |",
                ],
            )
        )

        with self.assertRaisesRegex(ProgressError, "cycle"):
            parse_progress(path)

    def test_duplicate_task_id_is_invalid(self):
        path = self.write_doc(
            progress_doc(
                summary_rows=["| Backend | 20 | 100% | DONE | backend-agent |"],
                task_rows=[
                    "| B-001 | Backend | One | backend-agent | MEDIUM | Terra | medium | DONE | 100% | - | PASS: unit tests |",
                    "| B-001 | Backend | Two | backend-agent | MEDIUM | Terra | medium | DONE | 100% | - | PASS: unit tests |",
                ],
            )
        )

        with self.assertRaisesRegex(ProgressError, "duplicate task ID"):
            parse_progress(path)

    def test_done_without_pass_validation_is_invalid(self):
        path = self.write_doc(
            progress_doc(
                summary_rows=["| Backend | 20 | 100% | DONE | backend-agent |"],
                task_rows=[
                    "| B-001 | Backend | Add API | backend-agent | MEDIUM | Terra | medium | DONE | 100% | - | wrote code |",
                ],
            )
        )

        with self.assertRaisesRegex(ProgressError, "PASS validation"):
            parse_progress(path)

    def test_blocked_task_does_not_hide_independent_ready_task(self):
        path = self.write_doc(
            progress_doc(
                overall="0%",
                summary_rows=[
                    "| Backend | 20 | 0% | BLOCKED | backend-agent |",
                    "| Frontend | 20 | 0% | TODO | frontend-agent |",
                ],
                task_rows=[
                    "| B-001 | Backend | Add API | backend-agent | MEDIUM | Terra | medium | BLOCKED | 0% | - | waiting for credentials |",
                    "| F-001 | Frontend | Add UI | frontend-agent | MEDIUM | Terra | medium | TODO | 0% | - | - |",
                ],
            )
        )

        result = parse_progress(path)

        self.assertEqual(result["ready_tasks"], ["F-001"])

    def test_invalid_weight_is_rejected(self):
        path = self.write_doc(
            progress_doc(
                summary_rows=["| Backend | 0 | 0% | TODO | backend-agent |"],
                task_rows=[
                    "| B-001 | Backend | Add API | backend-agent | MEDIUM | Terra | medium | TODO | 0% | - | - |",
                ],
            )
        )

        with self.assertRaisesRegex(ProgressError, "Weight must be positive"):
            parse_progress(path)

    def test_nonfinite_weight_is_rejected(self):
        path = self.write_doc(
            progress_doc(
                summary_rows=["| Backend | inf | 0% | TODO | backend-agent |"],
                task_rows=[
                    "| B-001 | Backend | Add API | backend-agent | MEDIUM | Terra | medium | TODO | 0% | - | - |",
                ],
            )
        )

        with self.assertRaisesRegex(ProgressError, "Weight must be finite"):
            parse_progress(path)

    def test_nonfinite_percent_is_rejected(self):
        path = self.write_doc(
            progress_doc(
                overall="nan%",
                summary_rows=["| Backend | 20 | 0% | TODO | backend-agent |"],
                task_rows=[
                    "| B-001 | Backend | Add API | backend-agent | MEDIUM | Terra | medium | TODO | 0% | - | - |",
                ],
            )
        )

        with self.assertRaisesRegex(ProgressError, "finite percentage"):
            parse_progress(path)

    def test_duplicate_epic_is_invalid(self):
        path = self.write_doc(
            progress_doc(
                overall="0%",
                summary_rows=[
                    "| Backend | 20 | 0% | TODO | backend-agent |",
                    "| Backend | 10 | 0% | TODO | backend-agent |",
                ],
                task_rows=[
                    "| B-001 | Backend | Add API | backend-agent | MEDIUM | Terra | medium | TODO | 0% | - | - |",
                ],
            )
        )

        with self.assertRaisesRegex(ProgressError, "duplicate epic"):
            parse_progress(path)

    def test_stale_weighted_overall_is_rejected(self):
        path = self.write_doc(progress_doc(overall="66.60%"))

        with self.assertRaisesRegex(ProgressError, "overall progress is stale"):
            parse_progress(path)

    def test_incomplete_project_never_displays_or_accepts_rounded_100_percent(self):
        task_rows = [
            "| A-001 | Big | Complete | main | LOW | AnyModel | any-effort | DONE | 100% | - | PASS: done |",
            "| B-001 | Tiny | Incomplete | main | LOW | AnyModel | any-effort | TODO | 0% | - | - |",
        ]
        valid = progress_doc(
            overall="99.99%",
            summary_rows=[
                "| Big | 99999 | 100% | DONE | main |",
                "| Tiny | 1 | 0% | TODO | main |",
            ],
            task_rows=task_rows,
        )
        result = parse_progress(self.write_doc(valid))
        self.assertEqual(result["overall_progress"], 99.99)

        stale = progress_doc(
            overall="100%",
            summary_rows=[
                "| Big | 99999 | 100% | DONE | main |",
                "| Tiny | 1 | 0% | TODO | main |",
            ],
            task_rows=task_rows,
        )
        with self.assertRaisesRegex(ProgressError, "overall progress is stale"):
            parse_progress(self.write_doc(stale))

    def test_split_table_line_preserves_empty_outer_cells(self):
        path = self.write_doc(
            progress_doc(
                summary_rows=["| Backend | 20 | 0% | TODO | backend-agent |"],
                task_rows=[
                    "| | Backend | Add API | backend-agent | MEDIUM | Terra | medium | TODO | 0% | - | - |",
                ],
            )
        )

        with self.assertRaisesRegex(ProgressError, "missing required value in column ID"):
            parse_progress(path)

    def test_duplicate_visible_overall_is_rejected_and_fenced_values_are_ignored(self):
        doc = progress_doc()
        fenced_first = "~~~text\nOverall Progress: 100%\n~~~\n" + doc
        self.assertEqual(parse_progress(self.write_doc(fenced_first))["overall_progress"], 66.67)

        duplicate_visible = doc.replace(
            "Overall Progress: 66.67%",
            "Overall Progress: 66.67%\nOverall Progress: 66.67%",
        )
        with self.assertRaisesRegex(ProgressError, "duplicate Overall Progress"):
            parse_progress(self.write_doc(duplicate_visible))

    def test_huge_weights_do_not_overflow_json_progress(self):
        doc = progress_doc(
            overall="50%",
            summary_rows=[
                "| MassiveA | 1e309 | 100% | DONE | main |",
                "| MassiveB | 1e309 | 0% | TODO | main |",
            ],
            task_rows=[
                "| A-001 | MassiveA | Done | main | LOW | AnyModel | any-effort | DONE | 100% | - | PASS: done |",
                "| B-001 | MassiveB | Todo | main | LOW | AnyModel | any-effort | TODO | 0% | - | - |",
            ],
        )

        with self.assertRaisesRegex(ProgressError, "Weight must be finite"):
            parse_progress(self.write_doc(doc))

        finite_huge = doc.replace("1e309", "1e308").replace("Overall Progress: 50%", "Overall Progress: 50%")
        result = parse_progress(self.write_doc(finite_huge))
        payload = json.dumps(result, allow_nan=False)
        self.assertIn('"overall_progress": 50', payload)

    def test_stale_summary_progress_is_rejected(self):
        path = self.write_doc(
            progress_doc(
                overall="50%",
                summary_rows=["| Backend | 20 | 40% | IN_PROGRESS | backend-agent |"],
                task_rows=[
                    "| B-001 | Backend | One | backend-agent | MEDIUM | Terra | medium | DONE | 100% | - | PASS: unit tests |",
                    "| B-002 | Backend | Two | backend-agent | MEDIUM | Terra | medium | TODO | 0% | B-001 | - |",
                ],
            )
        )

        with self.assertRaisesRegex(ProgressError, "cached progress is stale"):
            parse_progress(path)

    def test_stale_summary_status_is_rejected(self):
        path = self.write_doc(
            progress_doc(
                overall="50%",
                summary_rows=["| Backend | 20 | 50% | TODO | backend-agent |"],
                task_rows=[
                    "| B-001 | Backend | One | backend-agent | MEDIUM | Terra | medium | DONE | 100% | - | PASS: unit tests |",
                    "| B-002 | Backend | Two | backend-agent | MEDIUM | Terra | medium | TODO | 0% | B-001 | - |",
                ],
            )
        )

        with self.assertRaisesRegex(ProgressError, "cached status is stale"):
            parse_progress(path)

    def test_epic_status_rules(self):
        cases = [
            ("DONE", ["DONE"]),
            ("BLOCKED", ["TODO", "BLOCKED"]),
            ("IN_PROGRESS", ["TODO", "IN_PROGRESS"]),
            ("REVIEW", ["TODO", "REVIEW"]),
            ("IN_PROGRESS", ["DONE", "TODO"]),
            ("TODO", ["TODO"]),
        ]
        for expected, statuses in cases:
            with self.subTest(expected=expected, statuses=statuses):
                summary_progress = 100 if statuses == ["DONE"] else 50 if statuses == ["DONE", "TODO"] else 0
                overall = f"{summary_progress}%"
                summary_rows = [
                    f"| Backend | 20 | {summary_progress}% | {expected} | backend-agent |"
                ]
                task_rows = []
                for index, status in enumerate(statuses, start=1):
                    progress = "100%" if status == "DONE" else "0%"
                    validation = "PASS: unit tests" if status == "DONE" else "-"
                    task_rows.append(
                        f"| B-00{index} | Backend | Task {index} | backend-agent | MEDIUM | AnyModel | any-effort | {status} | {progress} | - | {validation} |"
                    )
                path = self.write_doc(
                    progress_doc(overall=overall, summary_rows=summary_rows, task_rows=task_rows)
                )

                result = parse_progress(path)

                self.assertEqual(result["epics"][0]["status"], expected)

    def test_empty_template_is_zero_progress(self):
        path = self.write_doc(
            textwrap.dedent(
                """\
                # Project Progress

                Overall Progress: 0%

                | Epic | Weight | Progress | Status | Owner |
                |---|---:|---:|---|---|

                | ID | Epic | Task | Owner | Complexity | Model | Reasoning | Status | Progress | Depends On | Validation |
                |---|---|---|---|---|---|---|---|---:|---|---|
                """
            )
        )

        result = parse_progress(path)

        self.assertEqual(result["overall_progress"], 0)
        self.assertEqual(result["ready_tasks"], [])
        self.assertEqual(result["epics"], [])

    def test_cli_outputs_json_and_does_not_mutate_file(self):
        path = self.write_doc(progress_doc())
        before = path.read_text(encoding="utf-8")

        completed = subprocess.run(
            [sys.executable, str(SCRIPT), str(path)],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertEqual(path.read_text(encoding="utf-8"), before)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["ready_tasks"], ["B-002"])


if __name__ == "__main__":
    unittest.main()
