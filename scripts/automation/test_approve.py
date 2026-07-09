#!/usr/bin/env python
"""Stage 5 acceptance test for the approval round-trip. Scratchpad only — never writes a real
approval into automation/receipts/ (Claude must not fabricate the user's approval).

Asserts:
  R1 gated + verified + no approval        -> VERIFIED-AWAITING-APPROVAL
  R2 gated + verified + user approval      -> ACCEPTED           (round-trip)
  R3 gated + NOT verified + user approval  -> CLAIMED-UNVERIFIED (approval never overrides evidence)
  R4 write_approval(dry_run) produces actor.kind == user, status_claimed == approved

Run: python scripts/automation/test_approve.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import update_dashboard as ud  # noqa: E402


def run():
    base = Path(tempfile.mkdtemp(prefix="dash_appr_"))
    (base / "good.txt").write_text("ok", encoding="utf-8")
    tid = "FIX-GATED"
    good = {
        "task_id": tid, "automation": "fixture", "status_claimed": "done",
        "files_created": [{"path": "good.txt", "sha256": ""}],
        "commands_run": [], "acceptance_tests": [],
        "split_usage": {"test_read": False, "authorization_token": None},
        "actor": {"kind": "skill"},
    }
    bad = dict(good, files_created=[{"path": "MISSING.txt", "sha256": ""}])
    approval = {"task_id": tid, "actor": {"kind": "user"}, "status_claimed": "approved"}

    v_good = ud.verify_receipt(good, base=base)
    v_bad = ud.verify_receipt(bad, base=base)

    cases = [
        ("R1 verified/no-approval",
         ud.compute_display("done", v_good, gated=True, has_user_approval=False),
         "VERIFIED-AWAITING-APPROVAL"),
        ("R2 verified/approved",
         ud.compute_display("done", v_good, gated=True,
                            has_user_approval=ud.has_user_approval(tid, [good, approval])),
         "ACCEPTED"),
        ("R3 unverified/approved",
         ud.compute_display("done", v_bad, gated=True,
                            has_user_approval=ud.has_user_approval(tid, [bad, approval])),
         "CLAIMED-UNVERIFIED"),
    ]

    ok = True
    print("=== Stage 5 approval round-trip test ===")
    for name, got, want in cases:
        p = got == want
        ok &= p
        print(f"[{'PASS' if p else 'FAIL'}] {name:26s} -> {got:28s} (want {want})")

    rid, rec = ud.write_approval("FIX-GATED", receipts_dir=base, dry_run=True)
    p4 = rec["actor"]["kind"] == "user" and rec["status_claimed"] == "approved"
    ok &= p4
    print(f"[{'PASS' if p4 else 'FAIL'}] R4 write_approval(dry_run)  -> actor={rec['actor']['kind']}, "
          f"status={rec['status_claimed']}, id={rid}")

    print("\nRESULT:", "ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(run())
