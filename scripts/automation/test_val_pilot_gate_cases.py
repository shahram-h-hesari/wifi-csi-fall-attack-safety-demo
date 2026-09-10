#!/usr/bin/env python
"""Fixture suite for the val-pilot gate core (design VAL_PILOT_GATE_DESIGN.md §8, cases A-L).

Test-first, BEFORE any real results/-walking scanner exists (design §10 step 2). Every fixture is
a SYNTHETIC artifact in a temp dir: no real checkpoint, no real validation CSV, no held-out-test
data, no --split command ever run. Read-only except for its own temp files. Runnable as a plain
script (prints PASS/FAIL, exits non-zero on failure) and under pytest.
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import val_pilot_gate_lib as vpg  # noqa: E402

# Gate thresholds mirror automation/acceptance/val-pilot-gate.yaml + the design §5 calibrated
# numbers. In the real scanner these are read from the acceptance file; the fixtures pin them so
# the verdict logic is exercised against known inputs.
THRESHOLDS = {
    "auroc_nogo_below": 0.88,
    "strong_rfall010_min": 0.70,
    "strong_auroc_min": 0.90,
    "strong_clean_degrade_max_pp": 5.0,
    "review_rfall010_lo": 0.50,
    "review_rfall010_hi": 0.70,
    "review_auroc_lo": 0.88,
    "review_auroc_hi": 0.90,
}
REFERENCE_FRONTIER = {"val_recall_at_far_le_10": 0.477}  # G1 LeNet best (acceptance file)

_RESULTS: list[tuple[bool, str]] = []


def check(cond: bool, label: str) -> None:
    _RESULTS.append((bool(cond), label))


def _write_ckpt(tmp: Path, name: str, content: bytes) -> Path:
    p = tmp / name
    p.write_bytes(content)
    return p


def _good_metadata(ckpt: Path) -> dict:
    return {
        "checkpoint": str(ckpt), "run_name": "ST1b6_lowFA", "seed": 42,
        "split": "val", "epsilon": 0.015, "model": "lenet",
        "timestamp": "2026-07-17T00:00:00Z",
    }


def _good_metrics() -> dict:
    return {"recall": 0.955, "far": 0.095, "auroc": 0.93,
            "rfall_at_far_020": 0.97, "rfall_at_far_010": 0.955,
            "clean_recall_degradation_pp": 2.0}


# --------------------------------------------------------------------- §8 verify/match fixtures
def run_fixtures(tmp: Path) -> None:
    ckpt = _write_ckpt(tmp, "st1b6.pt", b"WEIGHTS-V1")
    ckpt_hash = hashlib.sha256(b"WEIGHTS-V1").hexdigest()
    csv = tmp / "run_pgd_probabilities_val_epsilon_0_015.csv"
    csv.write_text("window,fall_probability\n0,0.9\n", encoding="utf-8")

    # A: complete pilot, all fields present -> VERIFIED, and a matching command matches.
    v = vpg.verify_pilot(probabilities_csv=csv, metadata=_good_metadata(ckpt),
                         checkpoint_path=ckpt, metrics=_good_metrics())
    check(v.status == vpg.VERIFIED and v.integrity_ok, "A verify complete pilot -> VERIFIED")
    check(v.checkpoint_sha256 == ckpt_hash, "A checkpoint hash computed")
    cmd = {"checkpoint": str(ckpt), "checkpoint_sha256": ckpt_hash,
           "run_name": "ST1b6_lowFA", "seed": 42, "epsilon": 0.015}
    m = vpg.match_command(command=cmd, pilot=v.fields, pilot_checkpoint_sha256=ckpt_hash,
                          current_checkpoint_sha256=ckpt_hash)
    check(m.matched and m.reason is None, "A matching command -> match")

    # B: pilot absent -> nothing to match (caller sees no verified pilot). Represented as a
    # verify on entirely-missing metadata (integrity NO-GO, never a match).
    vb = vpg.verify_pilot(probabilities_csv=None, metadata=None, checkpoint_path=None, metrics=None)
    check(vb.status == vpg.NO_GO and not vb.integrity_ok, "B absent pilot -> NO-GO (no match possible)")

    # C: checkpoint path matches, hash differs (retrained in place) -> non-match, checkpoint_hash.
    cmd_c = dict(cmd, checkpoint_sha256="deadbeef")
    mc = vpg.match_command(command=cmd_c, pilot=v.fields, pilot_checkpoint_sha256=ckpt_hash,
                           current_checkpoint_sha256=ckpt_hash)
    check(not mc.matched and mc.reason == "checkpoint_hash", "C hash differs -> non-match checkpoint_hash")

    # D: run-name mismatch -> non-match, run_name.
    md = vpg.match_command(command=dict(cmd, run_name="OTHER"), pilot=v.fields,
                           pilot_checkpoint_sha256=ckpt_hash, current_checkpoint_sha256=ckpt_hash)
    check(not md.matched and md.reason == "run_name", "D run_name mismatch -> non-match run_name")

    # E: seed mismatch -> non-match, seed.
    me = vpg.match_command(command=dict(cmd, seed=44), pilot=v.fields,
                           pilot_checkpoint_sha256=ckpt_hash, current_checkpoint_sha256=ckpt_hash)
    check(not me.matched and me.reason == "seed", "E seed mismatch -> non-match seed")

    # F: epsilon mismatch (0.03 vs 0.015) -> non-match, epsilon.
    mf = vpg.match_command(command=dict(cmd, epsilon=0.03), pilot=v.fields,
                           pilot_checkpoint_sha256=ckpt_hash, current_checkpoint_sha256=ckpt_hash)
    check(not mf.matched and mf.reason == "epsilon", "F epsilon mismatch -> non-match epsilon")

    # G: stale artifact — pilot verified, checkpoint since overwritten (current hash differs).
    ckpt.write_bytes(b"WEIGHTS-V2-RETRAINED")
    new_hash = vpg.sha256_file(ckpt)
    check(vpg.is_stale(recorded_sha256=ckpt_hash, checkpoint_path=ckpt), "G is_stale detects overwrite")
    mg = vpg.match_command(command=cmd, pilot=v.fields, pilot_checkpoint_sha256=ckpt_hash,
                           current_checkpoint_sha256=new_hash)
    check(not mg.matched and mg.reason == "stale_checkpoint", "G overwritten checkpoint -> non-match stale_checkpoint")
    ckpt.write_bytes(b"WEIGHTS-V1")  # restore for any later reuse

    # H: CSV exists, metadata JSON missing -> integrity NO-GO, never a match.
    vh = vpg.verify_pilot(probabilities_csv=csv, metadata=None, checkpoint_path=ckpt, metrics=_good_metrics())
    check(vh.status == vpg.NO_GO and not vh.integrity_ok, "H metadata missing -> NO-GO")

    # I: filename says test, metadata says val -> metadata authoritative, quarantine NEEDS-REVIEW.
    csv_test = tmp / "run_pgd_probabilities_test_epsilon_0_015.csv"
    csv_test.write_text("window,fall_probability\n0,0.9\n", encoding="utf-8")
    vi = vpg.verify_pilot(probabilities_csv=csv_test, metadata=_good_metadata(ckpt),
                          checkpoint_path=ckpt, metrics=_good_metrics())
    check(vi.status == vpg.NEEDS_REVIEW and not vi.integrity_ok,
          "I filename/metadata split disagreement -> NEEDS-REVIEW quarantine")

    # J: post-hoc test artifact offered as pilot (metadata split: test) -> hard non-evidence NO-GO.
    meta_test = dict(_good_metadata(ckpt), split="test")
    vj = vpg.verify_pilot(probabilities_csv=csv, metadata=meta_test, checkpoint_path=ckpt, metrics=_good_metrics())
    check(vj.status == vpg.NO_GO and not vj.integrity_ok, "J metadata split=test -> NO-GO non-evidence")

    # Also: checkpoint absent (design §2) -> NO-GO.
    meta_nockpt = _good_metadata(tmp / "does_not_exist.pt")
    vnc = vpg.verify_pilot(probabilities_csv=csv, metadata=meta_nockpt,
                           checkpoint_path=tmp / "does_not_exist.pt", metrics=_good_metrics())
    check(vnc.status == vpg.NO_GO and "checkpoint_file_absent" in vnc.reasons,
          "checkpoint absent -> NO-GO")

    # Metric coverage gap in otherwise-consistent evidence -> NEEDS-REVIEW (not NO-GO).
    partial = {"recall": 0.9, "far": 0.1, "auroc": 0.9, "rfall_at_far_020": None}
    vg = vpg.verify_pilot(probabilities_csv=csv, metadata=_good_metadata(ckpt),
                          checkpoint_path=ckpt, metrics=partial)
    check(vg.status == vpg.NEEDS_REVIEW and vg.integrity_ok, "metric gap -> NEEDS-REVIEW (integrity ok)")


# --------------------------------------------------------------------- §5 verdict fixtures
def run_verdict_fixtures() -> None:
    common = dict(thresholds=THRESHOLDS, reference_frontier=REFERENCE_FRONTIER)

    # STRONG-GO: rfall010>=0.70, auroc>=0.90, clean degrade<=5pp.
    strong = {"rfall_at_far_010": 0.72, "auroc": 0.91, "clean_recall_degradation_pp": 3.0}
    vd, _ = vpg.compute_verdict(metrics=strong, **common)
    check(vd == vpg.STRONG_GO, "verdict STRONG-GO all criteria met")

    # STRONG-GO numbers but clean degradation > 5pp -> default NEEDS-REVIEW (§5.4-1).
    degraded = dict(strong, clean_recall_degradation_pp=8.0)
    vd, _ = vpg.compute_verdict(metrics=degraded, **common)
    check(vd == vpg.NEEDS_REVIEW, "K high recall/auroc but clean degrade>5pp -> NEEDS-REVIEW")

    # REVIEW-GO: rfall010 in [0.50,0.70) and improves low-FAR over frontier (0.477).
    review = {"rfall_at_far_010": 0.60, "auroc": 0.89, "clean_recall_degradation_pp": 4.0}
    vd, _ = vpg.compute_verdict(metrics=review, **common)
    check(vd == vpg.REVIEW_GO, "verdict REVIEW-GO band + improves low-FAR")

    # NO-GO: AUROC below 0.88 and no low-FAR gain over frontier.
    weak = {"rfall_at_far_010": 0.40, "auroc": 0.80, "clean_recall_degradation_pp": 2.0}
    vd, r = vpg.compute_verdict(metrics=weak, **common)
    check(vd == vpg.NO_GO, "verdict NO-GO auroc<0.88 and no low-FAR gain")

    # L: dominated by a VERIFIED prior pilot (>= on all, strict on one) -> NO-GO.
    cand = {"rfall_at_far_010": 0.60, "auroc": 0.90, "clean_recall_degradation_pp": 4.0}
    dominator = {"run_name": "G1_seed44", "rfall_at_far_010": 0.65,
                 "auroc": 0.90, "clean_recall_degradation_pp": 4.0}
    vd, r = vpg.compute_verdict(metrics=cand, prior_verified_pilots=[dominator], **common)
    check(vd == vpg.NO_GO and any("dominated_by" in x for x in r), "L dominated candidate -> NO-GO")

    # L counterexample: strict improvement on one axis must NOT be dominated.
    not_dominated = {"rfall_at_far_010": 0.66, "auroc": 0.90, "clean_recall_degradation_pp": 4.0}
    vd, _ = vpg.compute_verdict(metrics=not_dominated, prior_verified_pilots=[dominator], **common)
    check(vd != vpg.NO_GO, "L strict-improvement candidate is NOT dominated")

    # Integrity failure overrides good metrics (§5.1 terminal).
    vd, _ = vpg.compute_verdict(metrics=strong, integrity_ok=False, **common)
    check(vd == vpg.NO_GO, "integrity failure overrides STRONG-GO metrics")


# --------------------------------------------------------------------- safety meta-fixtures (§8, §9)
def run_safety_meta() -> None:
    """Static safety scan of the gate lib. Strip comments/docstrings first so that describing a
    prohibition in prose (e.g. 'never runs --split test') does not read as doing it — only real
    code tokens count (same spirit as the guard suite's permissionDecision-comment fix)."""
    raw = (HERE / "val_pilot_gate_lib.py").read_text(encoding="utf-8")
    code_lines = []
    for ln in raw.splitlines():
        code = ln.split("#", 1)[0]          # drop line comments
        code_lines.append(code)
    src = "\n".join(code_lines)
    # crude triple-quoted docstring stripper (module + function docstrings are prose, not code)
    parts = src.split('"""')
    src = "".join(parts[::2])                # keep the outside-of-docstring segments

    for forbidden in ("subprocess", "os.system", "socket", "urllib", "requests",
                      "--split", "eval(", "exec("):
        check(forbidden not in src, f"lib code (comments/docstrings stripped) has no forbidden token: {forbidden!r}")
    # The lib must not open files for writing anywhere (only rb-hashing is allowed).
    writes = ".write_text(" in src or ".write_bytes(" in src
    non_rb_open = 'open(' in src.replace('.open("rb")', "")
    check(not writes and not non_rb_open, "lib performs no write / only rb-hashing open")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="valpilot-fixtures-") as td:
        run_fixtures(Path(td))
    run_verdict_fixtures()
    run_safety_meta()
    passed = sum(1 for ok, _ in _RESULTS if ok)
    for ok, label in _RESULTS:
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    print(f"\n{passed}/{len(_RESULTS)} fixtures passed")
    return 0 if passed == len(_RESULTS) else 1


def test_val_pilot_gate_fixtures():
    assert main() == 0


if __name__ == "__main__":
    raise SystemExit(main())
