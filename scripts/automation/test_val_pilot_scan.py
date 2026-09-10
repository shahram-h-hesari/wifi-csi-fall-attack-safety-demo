"""Tests for val_pilot_scan.py: the step-3 read-only guarantees (design VAL_PILOT_GATE_DESIGN.md
Section 10 step 3 -- no writes anywhere it scans, refusal to open test/legacy-split paths) and the
step-4 receipt writer (write_receipts() -- one JSON pilot receipt per VERIFIED pilot, never a
NO-GO/NEEDS-REVIEW one, never under results/).

The step-3 tests exist because the original AUT-VPG-SCANNER receipt asserted both read-only
properties via informal, one-off command output rather than a checked-in, re-runnable test, which
the dashboard verifier correctly could not treat as evidence (its acceptance-test check requires
evidence_path to point to a real, existing artifact). This file is that artifact.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import val_pilot_scan as vps  # noqa: E402


def test_assert_not_test_refuses_forbidden_split_tokens_but_allows_val():
    # Uses fixed, literal paths (not pytest's tmp_path) so the directory name pytest would
    # generate from this test's own function name can never itself contain a forbidden token
    # and confound the assertion.
    for token in ("_test_", "_legacy_"):
        bad = Path(f"C:/fixtures/foo{token}bar.csv")
        try:
            vps._assert_not_test(bad)
        except vps.TestReadRefused:
            pass
        else:
            raise AssertionError(f"expected TestReadRefused for a path containing {token!r}")

    ok_path = Path("C:/fixtures/foo_val_bar.csv")
    vps._assert_not_test(ok_path)  # must not raise


def _write_synthetic_sweep(tmp_path: Path, axis: str) -> tuple[Path, Path]:
    sweep_dir = tmp_path / "sweep"
    sweep_dir.mkdir()
    # Matches the real convention (see results/.../val_sweep/eps0015/*.csv): "{axis}_epsNNNN_..."
    # — the "_epsNNNN_" infix is what scan()'s axis-discovery split("_eps")[0] relies on.
    (sweep_dir / f"{axis}_eps0015_pgd_probabilities_val_epsilon_0_015.csv").write_text(
        "fall_probability,label\n0.10,0\n0.90,1\n", encoding="utf-8"
    )

    frontier_csv = tmp_path / "frontier.csv"
    fieldnames = [
        "model", "split", "val_auroc", "recall_far10", "FAR_far10",
        "recall_far20", "tau_far10", "H15_pass_val", "F20_pass_val",
    ]
    with frontier_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            "model": axis, "split": "val", "val_auroc": "0.90", "recall_far10": "0.70",
            "FAR_far10": "0.10", "recall_far20": "0.80", "tau_far10": "0.50",
            "H15_pass_val": "True", "F20_pass_val": "True",
        })
    return sweep_dir, frontier_csv


def _write_synthetic_verified_sweep(tmp_path: Path, axis: str) -> tuple[Path, Path]:
    """A sweep dir + frontier CSV for an axis that verify_pilot() will accept as VERIFIED: full
    §2 metadata (checkpoint, run_name, seed, split, epsilon, model), a checkpoint file that exists
    on disk (so checkpoint hashing succeeds), and all 4 core metrics present in the frontier CSV."""
    sweep_dir, frontier_csv = _write_synthetic_sweep(tmp_path, axis)

    checkpoint = tmp_path / "synthetic_checkpoint.pt"
    checkpoint.write_bytes(b"not a real checkpoint, just needs to exist for sha256_file()")

    metadata = {
        "checkpoint": str(checkpoint), "run_name": "synthetic_run", "seed": 42,
        "split": "val", "epsilon": 0.015, "model": axis,
    }
    (sweep_dir / f"{axis}_eps0015_metadata_val_epsilon_0_015.json").write_text(
        json.dumps(metadata), encoding="utf-8"
    )
    return sweep_dir, frontier_csv


def _snapshot(root: Path) -> dict[str, tuple[int, float]]:
    return {
        str(p.relative_to(root)): (p.stat().st_size, p.stat().st_mtime)
        for p in root.rglob("*") if p.is_file()
    }


def test_scan_writes_nothing_and_reports_missing_metadata_as_no_go(tmp_path):
    axis = "AXIS1"
    sweep_dir, frontier_csv = _write_synthetic_sweep(tmp_path, axis)

    before = _snapshot(tmp_path)
    reports = vps.scan(sweep_dir, frontier_csv)
    after = _snapshot(tmp_path)

    assert before == after, "scan() must not create, modify, or touch any file it reads or scans"
    assert len(reports) == 1
    report = reports[0]
    assert report["axis"] == axis
    assert report["has_metadata_json"] is False
    assert report["has_checkpoint_binding"] is False
    # No metadata JSON was provided (by construction) -> the lib's own §2 rule is a terminal
    # NO-GO, never silently upgraded to a usable pilot.
    assert report["provenance_status"] == "NO-GO"
    assert "metadata_json_missing" in report["provenance_reasons"]


def test_write_receipts_writes_nothing_for_a_no_go_pilot(tmp_path):
    sweep_dir, frontier_csv = _write_synthetic_sweep(tmp_path, "AXIS1")
    reports = vps.scan(sweep_dir, frontier_csv)
    assert reports[0]["provenance_status"] == "NO-GO"

    out_dir = tmp_path / "val_pilot_receipts"
    written = vps.write_receipts(reports, out_dir=out_dir)

    assert written == []
    assert not out_dir.exists(), "no receipt written -> the receipts dir is never even created"


def test_write_receipts_writes_one_receipt_for_a_verified_pilot(tmp_path):
    axis = "AXIS1"
    sweep_dir, frontier_csv = _write_synthetic_verified_sweep(tmp_path, axis)
    reports = vps.scan(sweep_dir, frontier_csv)
    assert reports[0]["provenance_status"] == "VERIFIED", reports[0]["provenance_reasons"]

    out_dir = tmp_path / "val_pilot_receipts"
    written = vps.write_receipts(reports, out_dir=out_dir)

    assert len(written) == 1
    receipt = json.loads(written[0].read_text(encoding="utf-8"))
    assert receipt["receipt_version"] == 2
    assert receipt["run_name"] == "synthetic_run"
    assert receipt["seed"] == 42
    assert receipt["epsilon"] == 0.015
    assert receipt["split"] == "val"
    assert receipt["checkpoint_sha256"]  # the synthetic checkpoint file was hashed
    assert receipt["metrics"]["auroc"] == 0.90
    assert receipt["gate_verdict"] is not None
    assert receipt["acceptance"] is None  # only the user, not the scanner, ever sets this
    assert receipt["novelty_judgment"] is None  # human-only field, §5.4-3 -- scanner never fills it


def test_write_receipts_refuses_a_results_tree_out_dir(tmp_path):
    sweep_dir, frontier_csv = _write_synthetic_verified_sweep(tmp_path, "AXIS1")
    reports = vps.scan(sweep_dir, frontier_csv)

    bad_out_dir = tmp_path / "results" / "val_pilot_receipts"
    try:
        vps.write_receipts(reports, out_dir=bad_out_dir)
    except RuntimeError:
        pass
    else:
        raise AssertionError("expected write_receipts() to refuse a results/ out_dir")
    assert not bad_out_dir.exists()
