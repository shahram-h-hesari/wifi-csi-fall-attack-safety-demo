#!/usr/bin/env python
"""Stage 5 + APPROVAL-BIND acceptance tests for the approval round-trip. Scratchpad only — never
writes a real approval into automation/receipts/ (Claude must not fabricate the user's approval).

Original round-trip (R1-R4): a single claim + a single approval.
Claim-binding suite (A-H): approvals must be bound to the EXACT claim receipt they approve, never
merely to a task_id — an approval for an older, superseded claim must never silently cover a newer
one. Historical (pre-fix) approvals lacking the explicit binding field are honored ONLY via a
deterministic, conservative legacy rule: they approve exactly the claim that was active at the
moment the approval was written, and never carry forward to any later claim.

Run: python scripts/automation/test_approve.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import update_dashboard as ud  # noqa: E402


def run():
    ok = True
    print("=== Stage 5 approval round-trip test ===")
    ok &= _round_trip()
    print("\n=== APPROVAL-BIND claim-binding suite (A-H) ===")
    ok &= _case_a_exact_claim_approval()
    ok &= _case_b_old_approval_cannot_approve_new_claim()
    ok &= _case_c_new_exact_approval()
    ok &= _case_d_wrong_task()
    ok &= _case_e_write_approval_always_binds()
    ok &= _case_f_claim_hash_mismatch()
    ok &= _case_g_historical_compatibility()
    ok &= _case_h_cli_mechanism()
    print("\n=== REG-GOALS scenario reproduction (synthetic) ===")
    ok &= _reg_goals_scenario_repro()

    print("\nRESULT:", "ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


def _report(name, got, want):
    p = got == want
    print(f"[{'PASS' if p else 'FAIL'}] {name:38s} -> {got!r:28} (want {want!r})")
    return p


# --------------------------------------------------------------------- original round-trip (fixed)
def _round_trip():
    base = Path(tempfile.mkdtemp(prefix="dash_appr_"))
    (base / "good.txt").write_text("ok", encoding="utf-8")
    tid = "FIX-GATED"
    claim_rid = "2026-01-01T000000Z_fixture_FIX-GATED"
    good = {
        "receipt_id": claim_rid,
        "task_id": tid, "automation": "fixture", "status_claimed": "done",
        "files_created": [{"path": "good.txt", "sha256": ""}],
        "commands_run": [], "acceptance_tests": [],
        "split_usage": {"test_read": False, "authorization_token": None},
        "actor": {"kind": "skill"},
    }
    bad = dict(good, files_created=[{"path": "MISSING.txt", "sha256": ""}])
    approval = {
        "receipt_id": "2026-01-01T000100Z_user-approval_FIX-GATED",
        "task_id": tid, "actor": {"kind": "user"}, "status_claimed": "approved",
        "approved_claim_receipt_id": claim_rid,
    }

    v_good = ud.verify_receipt(good, base=base)
    v_bad = ud.verify_receipt(bad, base=base)

    ok = True
    ok &= _report("R1 verified/no-approval",
                   ud.compute_display("done", v_good, gated=True, has_user_approval=False),
                   "VERIFIED-AWAITING-APPROVAL")
    ok &= _report("R2 verified/approved (exact-bound)",
                   ud.compute_display("done", v_good, gated=True,
                                       has_user_approval=ud.has_user_approval(tid, [good, approval], base=base)),
                   "ACCEPTED")
    ok &= _report("R3 unverified/approved",
                   ud.compute_display("done", v_bad, gated=True,
                                       has_user_approval=ud.has_user_approval(tid, [bad, approval], base=base)),
                   "CLAIMED-UNVERIFIED")

    rid, rec = ud.write_approval("FIX-GATED", receipts_dir=base, dry_run=True, active_claim=good)
    p4 = rec is not None and rec["actor"]["kind"] == "user" and rec["status_claimed"] == "approved" \
        and rec.get("approved_claim_receipt_id") == claim_rid
    ok &= p4
    print(f"[{'PASS' if p4 else 'FAIL'}] R4 write_approval(dry_run, bound)  -> "
          f"actor={rec['actor']['kind']}, status={rec['status_claimed']}, "
          f"approved_claim_receipt_id={rec.get('approved_claim_receipt_id')}, id={rid}")
    return ok


# -------------------------------------------------------------------------------- A-H claim-binding
def _claim(task_id, rid, **extra):
    return {"receipt_id": rid, "task_id": task_id, "automation": "fixture",
            "status_claimed": "done", "actor": {"kind": "skill"}, **extra}


def _approval(task_id, rid, approved_claim_receipt_id=None, approved_claim_sha256=None):
    r = {"receipt_id": rid, "task_id": task_id, "actor": {"kind": "user"}, "status_claimed": "approved"}
    if approved_claim_receipt_id is not None:
        r["approved_claim_receipt_id"] = approved_claim_receipt_id
    if approved_claim_sha256 is not None:
        r["approved_claim_sha256"] = approved_claim_sha256
    return r


def _case_a_exact_claim_approval():
    """A. Claim A passes; Approval explicitly binds Claim A -> ACCEPTED."""
    claim_a = _claim("T-A", "2026-01-01T000000Z_x_T-A")
    approval_a = _approval("T-A", "2026-01-01T000100Z_user-approval_T-A", claim_a["receipt_id"])
    receipts = [claim_a, approval_a]
    got = ud.has_user_approval("T-A", receipts)
    return _report("A exact claim approval", got, True)


def _case_b_old_approval_cannot_approve_new_claim():
    """B. Approval binds Claim A; Claim B later supersedes Claim A; no Approval B ->
    active state VERIFIED-AWAITING-APPROVAL (the old approval must not transfer)."""
    claim_a = _claim("T-B", "2026-01-01T000000Z_x_T-B")
    approval_a = _approval("T-B", "2026-01-01T000100Z_user-approval_T-B", claim_a["receipt_id"])
    claim_b = _claim("T-B", "2026-01-02T000000Z_x_T-B", supersedes=claim_a["receipt_id"])
    receipts = [claim_a, approval_a, claim_b]
    active = ud.active_claim_for_task("T-B", receipts)
    active_ok = _report("B active claim is Claim B", active["receipt_id"], claim_b["receipt_id"])
    approved = ud.has_user_approval("T-B", receipts)
    disp = ud.compute_display("done", {"passed": True, "strength": "hash-verified", "checks": []},
                               gated=True, has_user_approval=approved)
    disp_ok = _report("B active state (no Approval B)", disp, "VERIFIED-AWAITING-APPROVAL")
    old_approval_never_moved = _report("B Approval A does not bind Claim B",
                                        ud.claim_approved_by(claim_b, receipts) is None, True)
    return active_ok and disp_ok and old_approval_never_moved


def _case_c_new_exact_approval():
    """C. Claim B passes; Approval B binds Claim B -> ACCEPTED."""
    claim_a = _claim("T-C", "2026-01-01T000000Z_x_T-C")
    approval_a = _approval("T-C", "2026-01-01T000100Z_user-approval_T-C", claim_a["receipt_id"])
    claim_b = _claim("T-C", "2026-01-02T000000Z_x_T-C", supersedes=claim_a["receipt_id"])
    approval_b = _approval("T-C", "2026-01-02T000100Z_user-approval_T-C", claim_b["receipt_id"])
    receipts = [claim_a, approval_a, claim_b, approval_b]
    got = ud.has_user_approval("T-C", receipts)
    return _report("C new exact approval (Approval B -> Claim B)", got, True)


def _case_d_wrong_task():
    """D. Approval references Claim B's receipt_id but declares a DIFFERENT task_id -> must
    never approve Claim B (task_id equality is a precondition, not just receipt_id match)."""
    claim_b = _claim("T-D-real", "2026-01-01T000000Z_x_T-D-real")
    mismatched_approval = _approval("T-D-other", "2026-01-01T000100Z_user-approval_T-D-other",
                                     claim_b["receipt_id"])
    receipts = [claim_b, mismatched_approval]
    got = ud.claim_approved_by(claim_b, receipts)
    return _report("D wrong-task approval rejected", got, None)


def _case_e_write_approval_always_binds():
    """E. A NEWLY GENERATED approval (via the real write_approval() generator, the only sanctioned
    path going forward) must always carry approved_claim_receipt_id -- the generator itself must
    never be able to produce an unbound approval. This guards the invariant at its source rather
    than merely tolerating well-formed input at the reader."""
    base = Path(tempfile.mkdtemp(prefix="dash_appr_e_"))
    claim = _claim("T-E", "2026-01-01T000000Z_x_T-E")
    rid, rec = ud.write_approval("T-E", receipts_dir=base, dry_run=True, active_claim=claim)
    has_binding = rec is not None and bool(rec.get("approved_claim_receipt_id"))
    matches = rec is not None and rec.get("approved_claim_receipt_id") == claim["receipt_id"]
    ok = _report("E generated approval always bound", has_binding and matches, True)
    # Defensive: a hand-crafted approval with an explicitly EMPTY binding field must be treated as
    # unbound (falls to the legacy path), never as a vacuous "matches everything" wildcard.
    empty_bound = _approval("T-E", "2026-01-01T000100Z_user-approval_T-E",
                             approved_claim_receipt_id="")
    empty_treated_as_unbound_but_legacy_still_applies = ud.claim_approved_by(
        claim, [claim, empty_bound])
    ok &= _report("E empty-string binding falls back to legacy (not a false-negative)",
                   empty_treated_as_unbound_but_legacy_still_applies is not None, True)
    return ok


def _case_f_claim_hash_mismatch():
    """F. Approval identifies Claim B correctly by ID but stores the WRONG claim hash ->
    provenance mismatch; must be treated as invalid, never approved."""
    base = Path(tempfile.mkdtemp(prefix="dash_appr_f_"))
    receipts_dir = base / "automation" / "receipts"
    receipts_dir.mkdir(parents=True)
    claim = _claim("T-F", "2026-01-01T000000Z_x_T-F")
    claim_path = receipts_dir / f"{claim['receipt_id']}.json"
    claim_path.write_text('{"receipt_id": "2026-01-01T000000Z_x_T-F"}', encoding="utf-8")
    wrong_hash_approval = _approval("T-F", "2026-01-01T000100Z_user-approval_T-F",
                                     approved_claim_receipt_id=claim["receipt_id"],
                                     approved_claim_sha256="0" * 64)
    got = ud.claim_approved_by(claim, [claim, wrong_hash_approval], base=base)
    ok = _report("F claim hash mismatch rejected", got, None)
    correct_hash = ud.sha256_file(claim_path)
    right_hash_approval = _approval("T-F", "2026-01-01T000200Z_user-approval_T-F",
                                     approved_claim_receipt_id=claim["receipt_id"],
                                     approved_claim_sha256=correct_hash)
    got2 = ud.claim_approved_by(claim, [claim, right_hash_approval], base=base)
    ok &= _report("F matching claim hash accepted", got2 is not None, True)
    return ok


def _case_g_historical_compatibility():
    """G. Synthetic HISTORICAL-format fixtures (approval receipts with NO binding field at all,
    exactly as every pre-APPROVAL-BIND receipt in this repo looks): an old approval may apply only
    to its deterministically-associated historical claim, and never carries forward to a later
    superseding claim."""
    claim_1 = _claim("T-G", "2026-01-01T000000Z_x_T-G")
    legacy_approval = {"receipt_id": "2026-01-01T000100Z_user-approval_T-G",
                        "task_id": "T-G", "actor": {"kind": "user"}, "status_claimed": "approved"}
    claim_2 = _claim("T-G", "2026-01-02T000000Z_x_T-G", supersedes=claim_1["receipt_id"])
    receipts = [claim_1, legacy_approval, claim_2]

    applies_to_original = ud.claim_approved_by(claim_1, receipts)
    ok = _report("G legacy approval applies to its own (historical) claim",
                  applies_to_original is not None and applies_to_original["receipt_id"] == legacy_approval["receipt_id"],
                  True)
    never_carries_forward = ud.claim_approved_by(claim_2, receipts)
    ok &= _report("G legacy approval never carries forward to superseding claim",
                  never_carries_forward, None)
    active_state_ok = _report("G active claim (Claim 2) is unapproved",
                               ud.has_user_approval("T-G", receipts), False)
    return ok and active_state_ok


def _case_h_cli_mechanism():
    """H. CLI mechanism (write_approval, the function do_approve() delegates to):
    H1 active claim has no exact approval -> a new approval must bind to the ACTIVE claim, even
       when an older approval exists for the same task.
    H2 exact active claim already approved -> detection must recognize it (do_approve()'s
       'already ACCEPTED; nothing to do' branch reads exactly this signal)."""
    base = Path(tempfile.mkdtemp(prefix="dash_appr_h_"))
    claim_a = _claim("T-H", "2026-01-01T000000Z_x_T-H")
    approval_a = _approval("T-H", "2026-01-01T000100Z_user-approval_T-H", claim_a["receipt_id"])
    claim_b = _claim("T-H", "2026-01-02T000000Z_x_T-H", supersedes=claim_a["receipt_id"])
    receipts_before = [claim_a, approval_a, claim_b]

    rid, rec = ud.write_approval("T-H", receipts_dir=base, dry_run=True,
                                  active_claim=claim_b, receipts=receipts_before)
    h1 = _report("H1 new approval binds to ACTIVE claim (not the old one)",
                  rec is not None and rec.get("approved_claim_receipt_id") == claim_b["receipt_id"],
                  True)

    approval_b = _approval("T-H", rid or "2026-01-02T000100Z_user-approval_T-H", claim_b["receipt_id"])
    receipts_after = receipts_before + [approval_b]
    h2 = _report("H2 active claim now detected as already-approved",
                  ud.claim_approved_by(claim_b, receipts_after) is not None, True)
    return h1 and h2


# ----------------------------------------------------------------- REG-GOALS scenario (synthetic)
def _reg_goals_scenario_repro():
    """Synthetic reproduction of the real REG-GOALS incident, per Part 6:
      Claim A + Approval A               = ACCEPTED
      Claim B (supersedes A), no Approval B = VERIFIED-AWAITING-APPROVAL
      Claim B + Approval B               = ACCEPTED
    No real repo receipts are read or written."""
    ok = True
    tid = "T-REPRO"

    claim_a = _claim(tid, "2026-01-01T000000Z_x_T-REPRO")
    approval_a = _approval(tid, "2026-01-01T000100Z_user-approval_T-REPRO", claim_a["receipt_id"])
    v = {"passed": True, "strength": "hash-verified", "checks": []}

    receipts = [claim_a, approval_a]
    disp = ud.compute_display("done", v, gated=True, has_user_approval=ud.has_user_approval(tid, receipts))
    ok &= _report("repro: Claim A + Approval A", disp, "ACCEPTED")

    claim_b = _claim(tid, "2026-01-02T000000Z_x_T-REPRO", supersedes=claim_a["receipt_id"])
    receipts = [claim_a, approval_a, claim_b]
    disp = ud.compute_display("done", v, gated=True, has_user_approval=ud.has_user_approval(tid, receipts))
    ok &= _report("repro: Claim B supersedes A, no Approval B", disp, "VERIFIED-AWAITING-APPROVAL")

    approval_b = _approval(tid, "2026-01-02T000100Z_user-approval_T-REPRO", claim_b["receipt_id"])
    receipts = [claim_a, approval_a, claim_b, approval_b]
    disp = ud.compute_display("done", v, gated=True, has_user_approval=ud.has_user_approval(tid, receipts))
    ok &= _report("repro: Claim B + Approval B", disp, "ACCEPTED")

    return ok


if __name__ == "__main__":
    raise SystemExit(run())
