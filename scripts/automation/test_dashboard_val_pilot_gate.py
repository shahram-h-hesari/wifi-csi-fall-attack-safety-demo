#!/usr/bin/env python
"""AUT-VPG-DASHBOARD acceptance tests for the val-pilot-gate dashboard section (design
VAL_PILOT_GATE_DESIGN.md §7/§10 step 4).

Synthetic tmp_path fixtures for empty/malformed/populated receipt-directory cases; the real
val_pilot_receipts/ dir and the real dashboard render are only ever READ. No network, no
subprocess, no experiment/queue action, no --split command.

Run: python -m pytest scripts/automation/test_dashboard_val_pilot_gate.py -v
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dashboard_val_pilot_gate as dvp  # noqa: E402

REPO = Path(__file__).resolve().parents[2]


def _write_receipt(dir_path: Path, name: str, **over) -> Path:
    dir_path.mkdir(parents=True, exist_ok=True)
    doc = {
        "receipt_version": 2,
        "run_name": "candidate_a", "seed": 42, "epsilon": 0.015,
        "checkpoint_path": "checkpoints/candidate_a.pt", "checkpoint_sha256": "abc123",
        "split": "val",
        "artifacts": {"probabilities_csv": "x.csv", "metadata_json": "x.json", "analysis": None},
        "metrics": {"recall": 0.90, "far": 0.10, "auroc": 0.95, "rfall_at_far_020": 0.95,
                    "rfall_at_far_010": 0.90, "rfall_at_far_005": None,
                    "clean_recall_degradation_pp": 2.5},
        "gate_verdict": "REVIEW-GO",
        "novelty_judgment": None,
        "verified_utc": "2026-07-20T19:00:00Z",
        "scanner_version": "test",
        "acceptance": None,
    }
    doc.update(over)
    p = dir_path / name
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


# =============================================================== 1. empty dir -> graceful empty state
def test_no_receipts_dir_renders_empty_state(tmp_path):
    out = dvp.render_val_pilot_gate({"val_pilot_receipts_dir": str(tmp_path / "does_not_exist")})
    assert dvp.BEGIN_MARK in out and dvp.END_MARK in out
    assert "No pilot receipts yet" in out
    assert "0" not in out.split("No pilot receipts yet")[0]  # no fabricated counts before the message


def test_empty_receipts_dir_renders_empty_state(tmp_path):
    d = tmp_path / "val_pilot_receipts"
    d.mkdir()
    out = dvp.render_val_pilot_gate({"val_pilot_receipts_dir": str(d)})
    assert "No pilot receipts yet" in out


# =============================================================== 2. malformed file -> warning, not a crash
def test_malformed_json_file_produces_warning_and_is_skipped(tmp_path):
    d = tmp_path / "val_pilot_receipts"
    d.mkdir()
    (d / "broken.json").write_text("{not valid json", encoding="utf-8")
    _write_receipt(d, "good.json")
    out = dvp.render_val_pilot_gate({"val_pilot_receipts_dir": str(d)})
    assert "broken.json" in out and "malformed" in out.lower()
    assert "**1** pilot receipt(s)" in out  # the good one still rendered


def test_missing_required_field_produces_warning_and_is_skipped(tmp_path):
    d = tmp_path / "val_pilot_receipts"
    d.mkdir()
    (d / "incomplete.json").write_text(json.dumps({"receipt_version": 2}), encoding="utf-8")
    out = dvp.render_val_pilot_gate({"val_pilot_receipts_dir": str(d)})
    assert "incomplete.json" in out and "missing required field" in out.lower()
    assert "No pilot receipts yet" in out  # zero VALID receipts remain


# =============================================================== 3. a valid receipt renders correctly
def test_populated_dir_renders_table_row_and_counts(tmp_path):
    d = tmp_path / "val_pilot_receipts"
    _write_receipt(d, "candidate_a_42_eps0.015.json")
    out = dvp.render_val_pilot_gate({"val_pilot_receipts_dir": str(d)})
    assert "**1** pilot receipt(s) on file — **1** VERIFIED, **0** ACCEPTED." in out
    assert "`candidate_a`: 1 recorded validation read(s)" in out
    assert "| `candidate_a` | 42 | 0.015 | 🟡 VERIFIED | REVIEW-GO | 0.95 | 0.9 | 0.95 | 2.5 |" in out


def test_accepted_receipt_renders_as_accepted(tmp_path):
    d = tmp_path / "val_pilot_receipts"
    _write_receipt(d, "candidate_a_42_eps0.015.json",
                    acceptance={"accepted_utc": "2026-07-21T00:00:00Z", "note": "user approved"})
    out = dvp.render_val_pilot_gate({"val_pilot_receipts_dir": str(d)})
    assert "**0** VERIFIED, **1** ACCEPTED." in out
    assert "🟢 ACCEPTED" in out


def test_two_seeds_same_candidate_counted_together(tmp_path):
    d = tmp_path / "val_pilot_receipts"
    _write_receipt(d, "candidate_a_42_eps0.015.json", seed=42)
    _write_receipt(d, "candidate_a_44_eps0.015.json", seed=44)
    out = dvp.render_val_pilot_gate({"val_pilot_receipts_dir": str(d)})
    assert "**2** pilot receipt(s) on file" in out
    assert "`candidate_a`: 2 recorded validation read(s)" in out


# =============================================================== 4. no-execution-authorization warning
def test_no_test_read_authorization_warning_present(tmp_path):
    d = tmp_path / "val_pilot_receipts"
    _write_receipt(d, "candidate_a_42_eps0.015.json")
    out = dvp.render_val_pilot_gate({"val_pilot_receipts_dir": str(d)})
    assert "no verdict below authorizes a frozen test read" in out.lower()

    empty_out = dvp.render_val_pilot_gate({"val_pilot_receipts_dir": str(tmp_path / "empty")})
    assert "never authorization for a frozen test read" in empty_out.lower()


# =============================================================== 5. deterministic / idempotent / pure
def test_rendering_deterministic_and_idempotent(tmp_path):
    d = tmp_path / "val_pilot_receipts"
    _write_receipt(d, "candidate_a_42_eps0.015.json")
    sources = {"val_pilot_receipts_dir": str(d)}
    a = dvp.render_val_pilot_gate(sources)
    b = dvp.render_val_pilot_gate(sources)
    assert a == b


def test_render_does_not_mutate_sources_or_write_anything(tmp_path):
    d = tmp_path / "val_pilot_receipts"
    _write_receipt(d, "candidate_a_42_eps0.015.json")
    sources = {"val_pilot_receipts_dir": str(d)}
    snap_sources = copy.deepcopy(sources)
    before = sorted(p.name for p in d.iterdir())
    dvp.render_val_pilot_gate(sources)
    after = sorted(p.name for p in d.iterdir())
    assert sources == snap_sources
    assert before == after


# =============================================================== 6. full-dashboard integration
def test_full_dashboard_includes_val_pilot_gate_section_and_stays_idempotent():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import update_dashboard as ud
    a_md, a_js, _ = ud.do_render(write=False)
    b_md, b_js, _ = ud.do_render(write=False)
    assert "## 7b. Validation-pilot gate" in a_md
    assert dvp.BEGIN_MARK in a_md and dvp.END_MARK in a_md
    assert a_md == b_md
    assert a_js == b_js


def test_existing_dashboard_sections_unaffected_by_new_section():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import update_dashboard as ud
    md, _, _ = ud.do_render(write=False)
    assert "## 1. Now / Next / Blocked" in md
    assert "## 2b. Next-Experiment Candidate Review" in md
    assert "## 7. Safety, integrity & frozen protocols" in md
    assert "## 8-9. Artifact inventory" in md


# =============================================================== extra: no verdict recomputation
def _source_without_module_docstring(path: Path) -> str:
    """Forbidden-pattern checks below apply to CODE, not prose -- the module docstring legitimately
    *describes* what this renderer must never do, using the same words a code-level violation
    would use. Strip it (the file's only triple-quoted block) so the check can't false-positive on
    its own documentation, mirroring how audit_table_citations.py strips comments before scanning."""
    src = path.read_text(encoding="utf-8")
    parts = src.split('"""', 2)
    return parts[0] + parts[2] if len(parts) == 3 else src


def test_renderer_never_recomputes_a_verdict_or_verifies_a_pilot():
    src = _source_without_module_docstring(Path(dvp.__file__))
    forbidden = ["compute_verdict(", "verify_pilot(", "import val_pilot_gate_lib",
                 "import val_pilot_scan", "subprocess", "--split"]
    for f in forbidden:
        assert f not in src, f"renderer must not re-implement/re-run verification ({f!r} found)"
