#!/usr/bin/env python
"""Stage 4 acceptance test for the dashboard verifier (three-fixture case).

Exercises verify_receipt + compute_display on scratchpad fixtures — NOT the real receipts/ —
and asserts the three ladder outcomes from acceptance/dashboard-refresh.yaml:

  (a) good receipt, all evidence present        -> VERIFIED
  (b) receipt whose claimed file is missing      -> CLAIMED-UNVERIFIED (names the failed check)
  (c) gated task, full evidence, no approval      -> VERIFIED-AWAITING-APPROVAL

Writes three evidence snapshots to the scratchpad. Never touches results/, thesis, or real receipts.
Run: python scripts/automation/test_verify.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import update_dashboard as ud  # noqa: E402


def snapshot_dir() -> Path:
    d = Path(tempfile.gettempdir()) / "dashboard_stage4_fixtures"
    d.mkdir(parents=True, exist_ok=True)
    return d


def run():
    base = Path(tempfile.mkdtemp(prefix="dash_fix_"))
    (base / "good.txt").write_text("evidence present", encoding="utf-8")
    snaps = snapshot_dir()
    results = []

    # (a) good, non-gated
    good = {
        "task_id": "FIX-A", "automation": "fixture", "status_claimed": "done",
        "files_created": [{"path": "good.txt", "sha256": ""}],
        "commands_run": [{"cmd": "python noop.py", "exit_code": 0}],
        "split_usage": {"test_read": False, "authorization_token": None},
        "acceptance_tests": [], "actor": {"kind": "skill"},
    }
    v = ud.verify_receipt(good, base=base)
    disp = ud.compute_display("done", v, gated=False, has_user_approval=False)
    results.append(("A good/non-gated", disp, "VERIFIED", v))

    # (b) missing claimed file
    bad = dict(good, task_id="FIX-B",
               files_created=[{"path": "MISSING.txt", "sha256": ""}])
    v = ud.verify_receipt(bad, base=base)
    disp = ud.compute_display("done", v, gated=False, has_user_approval=False)
    results.append(("B missing-file", disp, "CLAIMED-UNVERIFIED", v))

    # (c) gated, full evidence, no approval
    v = ud.verify_receipt(good, base=base)
    disp = ud.compute_display("done", v, gated=True, has_user_approval=False)
    results.append(("C gated/no-approval", disp, "VERIFIED-AWAITING-APPROVAL", v))

    # extra: forbidden-command guard sanity
    forb = dict(good, task_id="FIX-D",
                commands_run=[{"cmd": "python export.py --split test", "exit_code": 0}])
    vf = ud.verify_receipt(forb, base=base)
    dispf = ud.compute_display("done", vf, gated=False, has_user_approval=False)
    results.append(("D forbidden --split test", dispf, "CLAIMED-UNVERIFIED", vf))

    ok = True
    print("=== Stage 4 verifier three-fixture test ===")
    for name, got, want, v in results:
        passed = got == want
        ok &= passed
        failed = [c["check"] + (f" ({c['detail']})" if c["detail"] else "")
                  for c in v["checks"] if not c["ok"]]
        print(f"[{'PASS' if passed else 'FAIL'}] {name:26s} -> {got:28s} (want {want})"
              + (f"  failed: {failed}" if failed else ""))
        (snaps / f"fixture_{name.split()[0]}.json").write_text(
            json.dumps({"case": name, "display": got, "expected": want,
                        "passed": passed, "verification": v}, indent=2), encoding="utf-8")

    print(f"\nEvidence snapshots: {snaps}")
    print("RESULT:", "ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(run())
