"""
Option B: FAR-constrained adaptive-Lagrangian rescue (Gate-2 implementation; SMOKE/SELF-CHECK ONLY).

Implements ADAPTIVE_LAGRANGIAN_FAR_CONSTRAINED_PREREGISTRATION.md + IMPLEMENTATION_SPEC_AND_SMOKE_PLAN.md
(committed at df338705). The defense objective is the frozen Variant G G1 base + the two Variant H tail terms;
the ONLY new dynamic is that the nonfall-budget weight lambda_b is an adaptive Lagrange multiplier updated
ONCE PER EPOCH from the validation PGD-10 false-alarm rate:

    lambda_b(t+1) = clip(lambda_b(t) + eta * (FAR_val_PGD10(t) - 0.10), 0, lambda_b_max)
    lambda_b(0) = 0.25, eta = 0.10, lambda_b_max = 1.0, target FAR = 0.10

Reuse boundary (spec sec.2): this script REUSES the frozen helpers BY IMPORT ONLY and edits no existing file.
  * scripts/train_variantG_targeted_hardneg.py (tvg): load_foundation, compute_validation_bundle (via tsg),
    targeted_sign_check, V2_GUARD_ACC/F1.
  * scripts/train_variantH_dual_tail_budget.py (vh): train_one_epoch_variantH (the frozen G1 base + the two
    TopK tail terms incl. the k_abs_min floor), and the frozen base constants.
Importing vh is side-effect-safe (its module body only defines constants/functions; main() is __name__-guarded
and it already imports tvg the same way A1 did). NO helper logic is copied or duplicated. If a future change
made these imports unsafe, the spec requires stopping for code review before copying -- not done here.

Scope: seed 42 ONLY; LeNet only; UT-HAR only; train eps {0.005,0.015,0.03}. Window-level, digital-domain,
white-box; NOT solved/certified/clinical/over-the-air. THIS FILE IS SMOKE/SELF-CHECK ONLY -- the full pilot
is intentionally gated OFF (Gate 4 not reached). The test set is NEVER touched in training/selection.

Modes:
    --self-check  pure-function + gate checks (lambda update math, once-per-epoch, selection score, gate
                  rejection, val-nonfall count) -- no training, no .pt
    --smoke       tiny 2-epoch seed-42 run to a `_smoke` namespace exercising the adaptive loop (no .pt)
    --pilot       REFUSED in this Gate-2 implementation (requires Gate-4 approval)

Commands (NOT run in Gate 2):
    python scripts/train_optionB_adaptive_lagrangian.py --setting optionB --self-check
    python scripts/train_optionB_adaptive_lagrangian.py --setting optionB --smoke --epochs 2 --smoke-batches 6
"""
from __future__ import annotations
from pathlib import Path
import argparse, csv, json, platform, sys, time
from datetime import datetime, timezone
import numpy as np
import torch


# ----------------------------------------------------------------------------- safe imports (spec sec.2)
def _import_helpers():
    sd = Path(__file__).resolve().parent
    if str(sd) not in sys.path:
        sys.path.insert(0, str(sd))
    import train_variantG_targeted_hardneg as tvg          # frozen Variant G foundation
    import train_variantH_dual_tail_budget as vh           # frozen Variant H tail terms (incl. k_abs_min floor)
    return tvg, vh


tvg, vh = _import_helpers()
V2_GUARD_ACC, V2_GUARD_F1 = tvg.V2_GUARD_ACC, tvg.V2_GUARD_F1   # 0.70 / 0.65 (reused, not redefined)

# ----------------------------------------------------------------------------- pinned first-pilot constants
SETTING_NAME = "optionB"
LAM_R = 1.0                 # fixed rescue weight
LAM_B0 = 0.25              # lambda_b(0)
ETA = 0.10                 # adaptive step size
LAM_B_MAX = 1.0            # cap
TARGET_FAR = 0.10          # FAR constraint
K_ABS_MIN = 4              # fall-rescue floor (retained from A1)
EXPECTED_VAL_NONFALL = 452  # seed-42 UT-HAR validation non-fall count (496 - 44 falls)
# clean-guard floors (acc/mF1 reuse the frozen guard; clean-fall-recall floor is added by the spec)
GUARD_CLEAN_FALL_RECALL = 0.90
# pinned selection-score weights
SCORE_ALPHA, SCORE_BETA, SCORE_GAMMA = 4.0, 2.0, 2.0


# ----------------------------------------------------------------------------- pure functions (unit-tested)
def lambda_update(lam_cur, far_val, eta=ETA, lam_max=LAM_B_MAX, target=TARGET_FAR):
    """Epoch-level adaptive Lagrange update with non-negativity and cap:
        lam_next = clip(lam_cur + eta*(far_val - target), 0, lam_max).
    Pure; no EMA; no per-batch state."""
    raw = lam_cur + eta * (far_val - target)
    return float(min(max(raw, 0.0), lam_max))


def clean_guard_eligible(acc, macro_f1, clean_fall_recall):
    """Three-pronged hard clean guard (spec sec.4): all three floors required."""
    return bool(acc >= V2_GUARD_ACC and macro_f1 >= V2_GUARD_F1 and clean_fall_recall >= GUARD_CLEAN_FALL_RECALL)


def selection_score(pgd_recall, far, clean_fall_recall, clean_acc):
    """Pinned target-aligned score (validation bundle); one-sided hinges -> zero unless a floor is violated:
        Score = PGDRecall - 4*max(0,FAR-0.10) - 2*max(0,0.90-CleanFallRecall) - 2*max(0,0.70-CleanAcc)."""
    return float(pgd_recall
                 - SCORE_ALPHA * max(0.0, far - TARGET_FAR)
                 - SCORE_BETA * max(0.0, GUARD_CLEAN_FALL_RECALL - clean_fall_recall)
                 - SCORE_GAMMA * max(0.0, V2_GUARD_ACC - clean_acc))


def validation_nonfall_count(val_loader, fall_idx):
    """Count validation non-fall windows from LABELS ONLY (no test access). Used as the FAR denominator."""
    n = 0
    for _, labels in val_loader:
        y = labels.view(-1)
        n += int((y != fall_idx).sum().item())
    return n


# ----------------------------------------------------------------------------- gate (spec sec.1 / sec.5)
def enforce_gate(setting, seed, pilot):
    """Authorize ONLY (optionB + seed 42). Refuse everything else (incl. A2/A0/H2/H3, seed44/45/46) and refuse
    the pilot in this Gate-2 implementation."""
    if setting != SETTING_NAME:
        raise SystemExit(f"Disallowed setting {setting!r}: Option B is {SETTING_NAME!r} ONLY "
                         "(A2/A0/H2/H3 and any other setting are out of scope).")
    if seed != 42:
        raise SystemExit(f"Option B is seed-42 ONLY for now (got seed {seed}); seeds 44/45/46 are blocked "
                         "(require a separate committed pre-registration).")
    if pilot:
        raise SystemExit("The Option B FULL PILOT is NOT approved in this Gate-2 implementation. "
                         "Pass --self-check or --smoke. The seed-42 pilot requires explicit Gate-4 approval.")


# ----------------------------------------------------------------------------- adaptive training loop
def _adaptive_train(args, F, mode):
    """Shared epoch loop with the once-per-epoch adaptive lambda_b update. `mode` in {'smoke'}.
    Selection is validation-only; the test loader (F['_test_loader']) is NEVER referenced here."""
    tsg, s1, device = F["tsg"], F["s1"], F["device"]
    fall_idx = F["fall_idx"]

    # FAR denominator from validation labels; split-integrity guard (spec sec.2/sec.5).
    n_val_nonfall = validation_nonfall_count(F["val_loader"], fall_idx)
    if n_val_nonfall != EXPECTED_VAL_NONFALL:
        raise SystemExit(f"STOP (split mismatch): N_val_nonfall={n_val_nonfall}, expected "
                         f"{EXPECTED_VAL_NONFALL} for the seed-42 UT-HAR split.")

    max_batches = args.smoke_batches if mode == "smoke" else None
    lam_b_current = LAM_B0
    history = []
    updates = 0
    budget_ever_nz = rescue_ever_nz = False
    best = {"maxscore": (-1e9, -1), "maxrec": ((-1e9, 1e9), -1), "minFA": ((1e9, -1e9), -1)}

    for epoch in range(1, args.epochs + 1):
        tr = vh.train_one_epoch_variantH(
            F["model"], F["train_loader"], F["train_criterion"], F["atk_criterion"], F["optimizer"], device,
            F["train_epsilons"], args.train_pgd_steps, F["rng"], tsg, lam_b_current, LAM_R, fall_idx,
            max_batches=max_batches, fall_k_abs_min=K_ABS_MIN)
        for k in ("train_loss", "mean_base", "mean_nonfall_budget", "mean_fall_rescue"):
            if not np.isfinite(tr[k]):
                raise SystemExit(f"STOP (numerical): {k} not finite at epoch {epoch} (NaN/inf).")
        budget_ever_nz = budget_ever_nz or (tr["mean_nonfall_budget"] > 0)
        rescue_ever_nz = rescue_ever_nz or (tr["mean_fall_rescue"] > 0)

        vb = tsg.compute_validation_bundle(s1, F["model"], F["val_loader"], F["atk_criterion"], device)
        if "val_pgd_false_fall_alarms" not in vb or "val_pgd_fall_recall" not in vb:
            raise SystemExit(f"STOP: missing PGD validation metrics at epoch {epoch} (cannot form FAR signal).")
        fp = vb["val_pgd_false_fall_alarms"]; rec = vb["val_pgd_fall_recall"]
        acc = vb["val_clean_accuracy"]; f1 = vb["val_clean_macro_f1"]; cfr = vb["val_clean_fall_recall"]

        far_val = fp / n_val_nonfall                                   # FAR_val_PGD10(t)
        eligible = clean_guard_eligible(acc, f1, cfr)
        score = selection_score(rec, far_val, cfr, acc)

        lam_b_next = lambda_update(lam_b_current, far_val)             # exactly one update this epoch
        updates += 1
        if not (0.0 <= lam_b_next <= LAM_B_MAX):
            raise SystemExit(f"STOP: lambda_b update {lam_b_next} outside [0,{LAM_B_MAX}] at epoch {epoch}.")

        flags = {"maxscore": 0, "maxrec": 0, "minFA": 0}
        if eligible:
            if score > best["maxscore"][0]:
                best["maxscore"] = (score, epoch); flags["maxscore"] = 1
            if (rec, -fp) > best["maxrec"][0]:
                best["maxrec"] = ((rec, -fp), epoch); flags["maxrec"] = 1
            if (fp, -rec) < best["minFA"][0]:
                best["minFA"] = ((fp, -rec), epoch); flags["minFA"] = 1

        history.append({
            "epoch": epoch, "lambda_b_current": lam_b_current, "lambda_b_next": lam_b_next,
            "far_val_pgd10": far_val, "n_val_nonfall": n_val_nonfall,
            "val_pgd_false_fall_alarms": fp, "val_pgd_fall_recall": rec,
            "val_clean_accuracy": acc, "val_clean_macro_f1": f1, "val_clean_fall_recall": cfr,
            "mean_nonfall_budget": tr["mean_nonfall_budget"], "mean_fall_rescue": tr["mean_fall_rescue"],
            "budget_to_rescue_loss_ratio": tr["budget_to_rescue_loss_ratio"],
            "fall_selected_count": tr["fall_selected_count"],
            "fall_k_abs_floor_active_frac": tr["fall_k_abs_floor_active_frac"],
            "clean_guard_eligible": int(eligible), "selection_score": score,
            "sel_maxscore": flags["maxscore"], "sel_maxrec": flags["maxrec"], "sel_minFA": flags["minFA"]})
        print(f"  epoch {epoch}/{args.epochs} | lam_b {lam_b_current:.3f}->{lam_b_next:.3f} "
              f"FAR={far_val:.3f} FP={fp} pgd_rec={rec:.3f} | acc={acc:.3f} f1={f1:.3f} cFR={cfr:.3f} "
              f"budget={tr['mean_nonfall_budget']:.3f} rescue={tr['mean_fall_rescue']:.3f} "
              f"floor={tr['fall_k_abs_floor_active_frac']:.2f} elig={int(eligible)} score={score:.3f}")

        lam_b_current = lam_b_next                                     # used by the NEXT epoch

    if not budget_ever_nz:
        raise SystemExit("STOP: nonfall_budget was always zero despite valid nonfall examples.")
    if not rescue_ever_nz:
        raise SystemExit("STOP: fall_rescue was always zero despite valid fall examples.")
    assert updates == args.epochs, f"adaptive update cadence broken: {updates} updates over {args.epochs} epochs"
    return history, best, n_val_nonfall


def run_smoke(args, F):
    """Tiny 2-epoch smoke exercising the adaptive loop. No .pt persisted; code-correctness only, no claims."""
    tag = args.smoke_tag or SETTING_NAME
    base = (F["exp"] / "results" / "safety_guided_defense" / "variantH_dual_tail_budget"
            / "adaptive_lagrangian_far_constrained" / "_smoke" / tag / f"seed{args.seed}")
    base.mkdir(parents=True, exist_ok=True)
    print("=" * 74)
    print(f"Option B --smoke  setting={SETTING_NAME}  seed={args.seed}  (adaptive-Lagrangian FAR-constrained)")
    print(f"  lam_r={LAM_R} lam_b(0)={LAM_B0} eta={ETA} lam_b_max={LAM_B_MAX} target_FAR={TARGET_FAR} "
          f"k_abs_min={K_ABS_MIN} | epochs={args.epochs} smoke_batches={args.smoke_batches}")
    # sign check before any smoke (same discipline as Variant G/H)
    _, ok = tvg.targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], F["fall_idx"], F["device"])
    if not ok:
        raise SystemExit("SIGN CHECK FAILED before smoke.")
    t0 = time.time()
    history, best, n_val_nonfall = _adaptive_train(args, F, mode="smoke")
    fields = list(history[0].keys())
    with (base / f"{SETTING_NAME}_smoke_log.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in history:
            w.writerow({k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]) for k in fields})
    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(), "stage": "optionB_smoke",
        "setting": SETTING_NAME, "seed": args.seed, "lam_r": LAM_R, "lam_b0": LAM_B0, "eta": ETA,
        "lam_b_max": LAM_B_MAX, "target_far": TARGET_FAR, "k_abs_min": K_ABS_MIN,
        "n_val_nonfall": n_val_nonfall, "epochs": args.epochs, "smoke_batches": args.smoke_batches,
        "update_rule": "lambda_b(t+1)=clip(lambda_b(t)+0.10*(FAR_val_PGD10(t)-0.10),0,1.0); once per epoch",
        "final": history[-1], "test_set_used": False,
        "note": "SMOKE ONLY -- code-correctness check, NOT a pilot or convergence result. Cold-start recall 0 "
                "is expected. No .pt persisted; no scientific claim.",
        "device": str(F["device"]), "python_version": platform.python_version(),
        "torch_version": torch.__version__, "elapsed_seconds": time.time() - t0}
    with (base / f"{SETTING_NAME}_smoke_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=float)
    print(f"  smoke done in {summary['elapsed_seconds']:.1f}s -> {base}")
    print("=" * 74)


def run_pilot(args, F):
    """Full seed-42 pilot -- INTENTIONALLY UNREACHABLE in the Gate-2 implementation (refused in main())."""
    raise SystemExit("run_pilot is gated: the Option B pilot requires Gate-4 approval (not in this commit).")


# ----------------------------------------------------------------------------- self-check (spec sec.6)
def _check_lambda_update():
    out = {}
    out["far0.15_0.25->0.255"] = abs(lambda_update(0.25, 0.15) - 0.255) < 1e-9
    out["far0.05_0.25->0.245"] = abs(lambda_update(0.25, 0.05) - 0.245) < 1e-9
    # high FAR iterated -> monotone increase, clips at cap, never exceeds
    lam = 0.25; seq = []
    for _ in range(50):
        lam = lambda_update(lam, 1.0); seq.append(lam)
    out["highFAR_clips_at_1.0"] = abs(seq[-1] - 1.0) < 1e-9 and max(seq) <= 1.0 + 1e-12
    # low FAR iterated -> monotone decrease, clips at 0, never negative
    lam = 0.25; seq = []
    for _ in range(50):
        lam = lambda_update(lam, 0.0); seq.append(lam)
    out["lowFAR_clips_at_0.0"] = abs(seq[-1] - 0.0) < 1e-9 and min(seq) >= -1e-12
    out["pass"] = all(out.values())
    return out


def _check_once_per_epoch(n_epochs=3):
    """Drive the update once per epoch over a synthetic FAR sequence; assert exactly n transitions."""
    fars = [0.20, 0.05, 0.12][:n_epochs]
    lam = LAM_B0; traj = [lam]
    for far in fars:
        lam = lambda_update(lam, far); traj.append(lam)
    return {"updates": len(traj) - 1, "expected": n_epochs, "pass": (len(traj) - 1) == n_epochs}


def _check_selection_score():
    # no violation: 0.6 - 0 - 0 - 0
    a = abs(selection_score(0.6, 0.10, 0.95, 0.72) - 0.6) < 1e-9
    # FAR violation only: 0.6 - 4*0.05 = 0.40
    b = abs(selection_score(0.6, 0.15, 0.95, 0.72) - 0.40) < 1e-9
    # all three violated: 0.6 - 4*0.05 - 2*0.10 - 2*0.05 = 0.6-0.2-0.2-0.1 = 0.10
    c = abs(selection_score(0.6, 0.15, 0.80, 0.65) - 0.10) < 1e-9
    return {"no_violation_0.60": a, "far_only_0.40": b, "all_three_0.10": c, "pass": a and b and c}


def _check_gate():
    out = {}
    for bad in [("H2", 42, False), ("A1", 42, False), ("A0", 42, False), ("optionB", 44, False)]:
        try:
            enforce_gate(*bad); out[str(bad)] = False           # should have raised
        except SystemExit:
            out[str(bad)] = True
    try:
        enforce_gate("optionB", 42, True); out["pilot_refused"] = False
    except SystemExit:
        out["pilot_refused"] = True
    try:
        enforce_gate("optionB", 42, False); out["optionB_seed42_smoke_ok"] = True
    except SystemExit:
        out["optionB_seed42_smoke_ok"] = False
    out["pass"] = all(out.values())
    return out


def run_self_check(args, F):
    print("=" * 74)
    print(f"Option B --self-check  setting={SETTING_NAME}")
    print(f"  class-index assertions PASSED: FALL={F['fall_idx']} NUM={F['num_classes']}")
    # targeted-PGD sign reuse (frozen Variant G check)
    sc, ok = tvg.targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], F["fall_idx"], F["device"])
    if not ok:
        raise SystemExit("SIGN CHECK FAILED in self-check.")
    lam = _check_lambda_update(); ope = _check_once_per_epoch(); ssc = _check_selection_score(); gate = _check_gate()
    # validation non-fall denominator from labels (no test access)
    n_val_nonfall = validation_nonfall_count(F["val_loader"], F["fall_idx"])
    nval = {"n_val_nonfall": n_val_nonfall, "expected": EXPECTED_VAL_NONFALL,
            "pass": n_val_nonfall == EXPECTED_VAL_NONFALL}
    notest = {"test_loader_present_but_unused": "_test_loader" in F, "pass": True}
    print(f"  lambda_update: {lam}")
    print(f"  once-per-epoch: {ope}")
    print(f"  selection_score: {ssc}")
    print(f"  gate: {gate}")
    print(f"  val_nonfall_count: {nval}")
    for name, blk in [("lambda_update", lam), ("once_per_epoch", ope), ("selection_score", ssc),
                      ("gate", gate), ("val_nonfall_count", nval)]:
        if not blk["pass"]:
            raise SystemExit(f"SELF-CHECK FAILED: {name} -> {blk}")
    print("  PASS: update math, once-per-epoch, selection score, gate rejection, val-nonfall count, sign check.")
    print("=" * 74)
    return {"lambda_update": lam, "once_per_epoch": ope, "selection_score": ssc, "gate": gate,
            "val_nonfall_count": nval, "no_test_access": notest, "sign_check_increased": bool(sc["increased"])}


# ----------------------------------------------------------------------------- CLI
def parse_args():
    p = argparse.ArgumentParser(description="Option B adaptive-Lagrangian FAR-constrained rescue (smoke-only).")
    p.add_argument("--setting", choices=[SETTING_NAME], required=True, help="optionB only")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=70)
    p.add_argument("--min-epochs", type=int, default=35)
    p.add_argument("--patience", type=int, default=15)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--train-pgd-steps", type=int, default=7)
    p.add_argument("--fall-weight", type=float, default=3.0)
    p.add_argument("--self-check", action="store_true")
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--smoke-batches", type=int, default=6)
    p.add_argument("--smoke-tag", default=None,
                   help="Optional subfolder for smoke/self-check artifacts (avoids overwriting committed ones).")
    p.add_argument("--pilot", action="store_true", help="REFUSED in this Gate-2 implementation (Gate-4 only).")
    return p.parse_args()


def main():
    args = parse_args()
    enforce_gate(args.setting, args.seed, args.pilot)            # blocks everything except optionB+seed42 smoke
    F = tvg.load_foundation(args)
    # assert the frozen train-epsilon set matches the pinned design (logged, not silently trusted)
    if sorted(round(e, 3) for e in F["train_epsilons"]) != [0.005, 0.015, 0.03]:
        raise SystemExit(f"STOP: train_epsilons {F['train_epsilons']} != pinned {{0.005,0.015,0.03}}.")
    if args.self_check:
        out = run_self_check(args, F)
        tag = args.smoke_tag or SETTING_NAME
        base = (F["exp"] / "results" / "safety_guided_defense" / "variantH_dual_tail_budget"
                / "adaptive_lagrangian_far_constrained" / "_smoke" / tag / f"seed{args.seed}")
        base.mkdir(parents=True, exist_ok=True)
        with (base / f"{SETTING_NAME}_selfcheck_summary.json").open("w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, default=float)
        return
    if args.smoke:
        run_smoke(args, F); return
    raise SystemExit("Option B training is gated: pass --self-check or --smoke. The full pilot needs Gate-4 "
                     "approval and is not runnable from this Gate-2 implementation.")


if __name__ == "__main__":
    main()
