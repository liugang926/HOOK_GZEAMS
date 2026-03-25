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
        help="Check entry in the form label|status|mode|note. Note is optional.",
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


def parse_check(entry: str) -> tuple[str, str, str, str]:
    parts = entry.split("|", 3)
    while len(parts) < 4:
        parts.append("")
    label, status, mode, note = parts
    return label.strip(), normalize_status(status.strip()), mode.strip() or "required", note.strip()


def overall_status(checks: list[tuple[str, str, str, str]], fail_modes: set[str]) -> str:
    for _, status, mode, _ in checks:
        if mode in fail_modes and status in {"Failed", "Cancelled"}:
            return "Failed"
    return "Passed"


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
            "| Gate | Mode | Outcome | Note |",
            "|------|------|---------|------|",
        ]
    )

    for label, status, mode, note in checks:
        note_text = note or "-"
        lines.append(f"| {label} | {mode} | {status} | {note_text} |")

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
