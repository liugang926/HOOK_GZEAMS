#!/usr/bin/env python3
"""Render a GitHub Actions summary for grouped command gates."""

from __future__ import annotations

import argparse
import os
import pathlib
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-path", help="Output path for the rendered summary.")
    parser.add_argument("--title", required=True, help="Summary heading.")
    parser.add_argument("--group-label", default="Gate group", help="Label for the gate group line.")
    parser.add_argument("--group", required=True, help="Human-readable gate group description.")
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
    parser.add_argument(
        "--check",
        action="append",
        default=[],
        help="Check entry in the form label|status|mode|note|section. Note and section are optional.",
    )
    parser.add_argument(
        "--fail-mode",
        action="append",
        default=["required"],
        help="Gate modes that should mark the overall status as failed. Can be repeated.",
    )
    return parser.parse_args()


def resolve_summary_path(args: argparse.Namespace) -> pathlib.Path | None:
    summary_path = args.summary_path or os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return None
    return pathlib.Path(summary_path)


def normalize_status(status: str) -> str:
    mapping = {
        "success": "Passed",
        "failure": "Failed",
        "cancelled": "Cancelled",
        "skipped": "Skipped",
    }
    return mapping.get(status.lower(), status or "Unknown")


def parse_check(entry: str) -> tuple[str, str, str, str, str, str]:
    parts = entry.split("|", 5)
    while len(parts) < 6:
        parts.append("")
    label, status, mode, note, section, job_policy = parts
    return (
        label.strip(),
        normalize_status(status.strip()),
        mode.strip() or "required",
        note.strip(),
        section.strip(),
        job_policy.strip(),
    )


def overall_status(checks: list[tuple[str, str, str, str, str, str]], fail_modes: set[str]) -> str:
    for _, status, mode, _, _, _ in checks:
        if mode in fail_modes and status in {"Failed", "Cancelled"}:
            return "Failed"
    return "Passed"


def blocking_scope(mode: str) -> str:
    normalized = mode.strip().lower()
    mapping = {
        "required": "Blocking",
        "advisory": "Advisory only",
        "report-only": "Report only",
    }
    if normalized in mapping:
        return mapping[normalized]
    if not normalized:
        return "Unknown"
    return normalized.replace("-", " ").title()


def default_job_policy(mode: str) -> str:
    normalized = mode.strip().lower()
    mapping = {
        "required": "Required job",
        "advisory": "Non-blocking advisory",
        "report-only": "Report-only job",
    }
    if normalized in mapping:
        return mapping[normalized]
    if not normalized:
        return "Unspecified"
    return normalized.replace("-", " ").title()


def render_checks_table(lines: list[str], checks: list[tuple[str, str, str, str, str, str]]) -> None:
    lines.extend(
        [
            "| Gate | Mode | Blocking Scope | Job Policy | Outcome | Note |",
            "|------|------|----------------|------------|---------|------|",
        ]
    )

    for label, status, mode, note, _, job_policy in checks:
        note_text = note or "-"
        policy_text = job_policy or default_job_policy(mode)
        lines.append(
            f"| {label} | {mode} | {blocking_scope(mode)} | {policy_text} | {status} | {note_text} |"
        )


def render_summary(args: argparse.Namespace) -> str:
    checks = [parse_check(entry) for entry in args.check]
    lines = [
        f"## {args.title}",
        "",
        f"- {args.group_label}: `{args.group}`",
    ]

    if args.artifact:
        artifact_text = ", ".join(f"`{artifact}`" for artifact in args.artifact)
        lines.append(f"- {args.artifacts_label}: {artifact_text}")

    lines.extend(
        [
            "",
            f"Status: **{overall_status(checks, set(args.fail_mode))}**",
            "",
        ]
    )

    sections = [section for _, _, _, _, section, _ in checks if section]
    if not sections:
        render_checks_table(lines, checks)
        return "\n".join(lines) + "\n"

    grouped_checks: dict[str, list[tuple[str, str, str, str, str, str]]] = {}
    ordered_sections: list[str] = []

    for check in checks:
        section = check[4] or "Other Checks"
        if section not in grouped_checks:
            grouped_checks[section] = []
            ordered_sections.append(section)
        grouped_checks[section].append(check)

    for section in ordered_sections:
        lines.extend(["", f"### {section}", ""])
        render_checks_table(lines, grouped_checks[section])

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
