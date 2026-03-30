"""Tests for GitHub Actions summary rendering helpers."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


def _load_render_gate_summary_module():
    script_path = Path(__file__).resolve().parents[4] / ".github" / "scripts" / "render_gate_summary.py"
    spec = importlib.util.spec_from_file_location("render_gate_summary", script_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


render_gate_summary = _load_render_gate_summary_module()


def build_args(*checks: str, fail_mode: list[str] | None = None, artifacts: list[str] | None = None):
    """Create a minimal argparse namespace for summary rendering tests."""
    return argparse.Namespace(
        summary_path=None,
        title="CI Status Check",
        group_label="Gate group",
        group="required branch protection checks",
        artifacts_label="Artifacts",
        artifact=artifacts or [],
        check=list(checks),
        fail_mode=fail_mode or ["required"],
    )


def test_render_gate_summary_treats_success_and_skipped_as_passed():
    args = build_args(
        "backend-lint|success|required|Python linting",
        "frontend-e2e|skipped|required|Allowed when the suite is not scheduled",
    )

    summary = render_gate_summary.render_summary(args)

    assert "Status: **Passed**" in summary
    assert "| backend-lint | required | Passed | Python linting |" in summary
    assert "| frontend-e2e | required | Skipped | Allowed when the suite is not scheduled |" in summary


def test_render_gate_summary_marks_required_failures_as_failed():
    args = build_args(
        "backend-test|failure|required|Pytest suite",
        "frontend-unit|success|required|Vitest suite",
    )

    summary = render_gate_summary.render_summary(args)

    assert "Status: **Failed**" in summary
    assert "| backend-test | required | Failed | Pytest suite |" in summary


def test_render_gate_summary_keeps_advisory_failures_non_blocking_by_default():
    args = build_args(
        "security-scan|failure|advisory|Security advisories found",
        "backend-test|success|required|Pytest suite",
    )

    summary = render_gate_summary.render_summary(args)

    assert "Status: **Passed**" in summary
    assert "| security-scan | advisory | Failed | Security advisories found |" in summary


def test_render_gate_summary_can_escalate_advisory_failures_via_fail_mode():
    args = build_args(
        "security-scan|failure|advisory|Security advisories found",
        fail_mode=["required", "advisory"],
        artifacts=["security-scan-reports"],
    )

    summary = render_gate_summary.render_summary(args)

    assert "Status: **Failed**" in summary
    assert "- Artifacts: `security-scan-reports`" in summary
