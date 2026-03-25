#!/usr/bin/env python3
"""Render a GitHub Actions step summary from JUnit and coverage XML."""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
import xml.etree.ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-path", help="Output path for the rendered summary.")
    parser.add_argument("--title", required=True, help="Summary heading.")
    parser.add_argument("--command-label", default="Command", help="Label for the command line.")
    parser.add_argument("--command", required=True, help="Command shown in the summary.")
    parser.add_argument(
        "--artifacts-label",
        default="Artifacts",
        help="Label for the artifact line.",
    )
    parser.add_argument(
        "--artifact",
        action="append",
        default=[],
        help="Artifact name to show in the summary. Can be repeated.",
    )
    parser.add_argument("--junit-path", required=True, help="Path to the JUnit XML file.")
    parser.add_argument("--coverage-path", help="Optional path to coverage XML.")
    parser.add_argument(
        "--covered-scenario",
        action="append",
        default=[],
        help="Scenario line shown under the covered scenarios section. Can be repeated.",
    )
    parser.add_argument(
        "--max-failing-cases",
        type=int,
        default=10,
        help="Maximum number of failing cases shown in the summary.",
    )
    parser.add_argument(
        "--missing-junit-message",
        default="JUnit XML was not generated. Check the workflow logs for details.",
        help="Message shown when the JUnit XML file does not exist.",
    )
    parser.add_argument(
        "--parse-error-prefix",
        default="Unable to parse JUnit XML summary",
        help="Prefix used when XML parsing fails.",
    )
    parser.add_argument(
        "--include-classname",
        action="store_true",
        help="Include testcase classname in failing case output when available.",
    )
    return parser.parse_args()


def resolve_summary_path(args: argparse.Namespace) -> pathlib.Path | None:
    summary_path = args.summary_path or os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return None
    return pathlib.Path(summary_path)


def load_junit_suite(junit_path: pathlib.Path) -> ET.Element:
    root = ET.parse(junit_path).getroot()
    if root.tag == "testsuite":
        return root

    suite = root.find("testsuite")
    if suite is not None:
        return suite

    raise ValueError("testsuite node not found")


def append_coverage_line(lines: list[str], coverage_path: pathlib.Path) -> None:
    if not coverage_path.exists():
        return

    try:
        coverage_root = ET.parse(coverage_path).getroot()
        line_rate = float(coverage_root.attrib.get("line-rate", 0))
        lines.append(f"- Line coverage: `{line_rate * 100:.2f}%`")
    except Exception as exc:  # pragma: no cover - defensive reporting
        lines.append(f"- Line coverage: unable to parse (`{exc}`)")


def collect_failing_cases(
    suite: ET.Element,
    *,
    include_classname: bool,
    max_cases: int,
) -> list[str]:
    failing_cases: list[str] = []
    for case in suite.iter("testcase"):
        if case.find("failure") is None and case.find("error") is None:
            continue

        name = case.attrib.get("name", "<unknown>")
        if include_classname:
            classname = case.attrib.get("classname", "").strip()
            failing_cases.append(f"{classname}.{name}" if classname else name)
        else:
            failing_cases.append(name)

        if len(failing_cases) >= max_cases:
            break

    return failing_cases


def render_summary(args: argparse.Namespace) -> str:
    junit_path = pathlib.Path(args.junit_path)
    coverage_path = pathlib.Path(args.coverage_path) if args.coverage_path else None

    lines = [
        f"## {args.title}",
        "",
        f"- {args.command_label}: `{args.command}`",
    ]

    if args.artifact:
        artifact_text = ", ".join(f"`{artifact}`" for artifact in args.artifact)
        lines.append(f"- {args.artifacts_label}: {artifact_text}")

    lines.append("")

    if not junit_path.exists():
        lines.append(args.missing_junit_message)
        return "\n".join(lines) + "\n"

    try:
        suite = load_junit_suite(junit_path)
        tests = int(suite.attrib.get("tests", 0))
        failures = int(suite.attrib.get("failures", 0))
        errors = int(suite.attrib.get("errors", 0))
        skipped = int(suite.attrib.get("skipped", 0))
        duration = float(suite.attrib.get("time", "0") or 0)
        passed = max(0, tests - failures - errors - skipped)
        status = "Passed" if failures == 0 and errors == 0 else "Failed"

        lines.extend(
            [
                f"Status: **{status}**",
                "",
                f"- Passed: `{passed}`",
                f"- Failures: `{failures}`",
                f"- Errors: `{errors}`",
                f"- Skipped: `{skipped}`",
                f"- Duration: `{duration:.3f}s`",
            ]
        )

        if coverage_path is not None:
            append_coverage_line(lines, coverage_path)

        if args.covered_scenario:
            lines.extend(["", "Covered scenarios:"])
            lines.extend(f"- {scenario}" for scenario in args.covered_scenario)

        failing_cases = collect_failing_cases(
            suite,
            include_classname=args.include_classname,
            max_cases=args.max_failing_cases,
        )
        if failing_cases:
            lines.extend(["", "Failing cases:"])
            lines.extend(f"- `{name}`" for name in failing_cases)
    except Exception as exc:  # pragma: no cover - defensive reporting
        lines.append(f"{args.parse_error_prefix}: `{exc}`")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    summary_path = resolve_summary_path(args)
    if summary_path is None:
        return 0

    summary_path.write_text(render_summary(args), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
