"""
D14 validation gate -- VALIDATION ONLY. Never reads the held-out test split.

Reads the canonical D14 validation PGD score exports produced by the training script
(results/d14_partial_auc_low_far_ranking/config_<A|B>/seed<seed>/val_eval/
 d14_config_<A|B>_seed<seed>_pgd_probabilities_val_epsilon_0_03.csv), applies the
pre-registered threshold rule and gate, and emits exactly one verdict report:
  D14_FAIL_VALIDATION_GATE.md          (gate fails -> F20 chase ends; no test read)
  D14_GATE_PASS_NEEDS_APPROVAL.md      (gate passes -> awaits explicit human approval)

This script does NOT run any model, does NOT attack, and does NOT read test files. It only
reads existing validation score CSVs and computes statistics.

Gate (all required), using the median seed of the selected config at FAR cap 0.17:
  1. median-seed validation fall recall >= 38/44 = 0.8636
  2. stratified bootstrap: validation recall >= 0.80 in >= 75% of resamples
  3. stratified bootstrap: gain >= +2 TP over the AFAC validation reference (36/44) in >= 70%
  4. clean guard (checked from the training log): acc>=0.70, macro-F1>=0.65, fall recall>=0.90

CRITERION 3 (RESOLVED by the D14 clarification commit 06c93abb635b3bcaf2e5591f214bd57d00faf831):
the PAIRED stratified bootstrap is the PRIMARY gate. For each resample, D14 and the AFAC validation
reference are scored on the SAME resampled window IDs, and the primary gain is
Delta TP = TP_D14 - TP_AFAC at their pre-specified cap-0.17 validation thresholds; the gate requires
Delta TP >= 2 in >= 70% of resamples. The FIXED-reference comparison (D14 TP minus the constant 36)
is computed and reported as a SENSITIVITY CHECK ONLY and is NEVER used for the gate decision. If the
paired AFAC reference is unavailable, the primary Gate-3 cannot be evaluated and the gate does not
pass on the fixed result.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import d14_common as C  # noqa: E402


def load_val_scores(path: Path):
    C.refuse_if_test_path(path)
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    y = [int(r["fall_true_binary"]) for r in rows]
    s = [float(r["fall_probability"]) for r in rows]
    return y, s


def d14_val_pgd_path(config: str, seed: int) -> Path:
    return (C.D14_RESULTS_ROOT / f"config_{config}" / f"seed{seed}" / "val_eval"
            / f"d14_config_{config}_seed{seed}_pgd_probabilities_val_epsilon_0_03.csv")


def clean_guard_from_log(config: str, seed: int, best_epoch):
    """Read the training log and return the clean-guard metrics at the best epoch."""
    log = (C.D14_RESULTS_ROOT / f"config_{config}" / f"seed{seed}" / "training_logs"
           / f"d14_config_{config}_seed{seed}_training_log.csv")
    if not log.exists():
        return None
    with log.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    target = None
    for r in rows:
        if best_epoch is not None and int(r["epoch"]) == int(best_epoch):
            target = r
            break
    if target is None:
        return None
    acc = float(target["val_clean_accuracy"])
    mf1 = float(target["val_clean_macro_f1"])
    fr = float(target["val_clean_fall_recall"])
    return {
        "clean_accuracy": acc, "clean_macro_f1": mf1, "clean_fall_recall": fr,
        "guard_pass": (acc >= C.CLEAN_GUARD["min_clean_accuracy"]
                       and mf1 >= C.CLEAN_GUARD["min_clean_macro_f1"]
                       and fr >= C.CLEAN_GUARD["min_clean_fall_recall"]),
    }


def best_epoch_from_meta(config: str, seed: int):
    meta = (C.D14_RESULTS_ROOT / f"config_{config}" / f"seed{seed}"
            / f"d14_config_{config}_seed{seed}_metadata.json")
    if not meta.exists():
        return None
    with meta.open(encoding="utf-8") as f:
        return json.load(f).get("best_epoch")


def stratified_bootstrap(y, s, tau, y_ref=None, s_ref=None, tau_ref=None,
                         n=C.BOOTSTRAP_N, seed=C.BOOTSTRAP_SEED):
    """Resample fall and non-fall indices with replacement; recompute recall at the frozen
    threshold. If reference scores are given, also compute paired TP-gain per resample."""
    rng = random.Random(seed)
    fall_idx = [i for i, yi in enumerate(y) if yi == 1]
    nonfall_idx = [i for i, yi in enumerate(y) if yi == 0]
    recalls = []
    gains_paired = []
    gains_fixed = []
    for _ in range(n):
        fs = [rng.choice(fall_idx) for _ in fall_idx]
        nfs = [rng.choice(nonfall_idx) for _ in nonfall_idx]
        tp = sum(1 for i in fs if s[i] >= tau)
        recall = tp / len(fs)
        recalls.append(recall)
        gains_fixed.append(tp - C.AFAC_REF_TP)
        if y_ref is not None and tau_ref is not None:
            tp_ref = sum(1 for i in fs if s_ref[i] >= tau_ref)
            gains_paired.append(tp - tp_ref)
    frac_recall_ge_floor = sum(1 for r in recalls if r >= C.GATE_RECALL_FLOOR) / n
    frac_gain_fixed_ge = sum(1 for g in gains_fixed if g >= C.GATE_GAIN_TP) / n
    out = {
        "n_boot": n,
        "recall_median": sorted(recalls)[n // 2],
        "frac_recall_ge_0.80": frac_recall_ge_floor,
        "frac_gain_fixed_ge_2": frac_gain_fixed_ge,
    }
    if gains_paired:
        out["frac_gain_paired_ge_2"] = sum(1 for g in gains_paired if g >= C.GATE_GAIN_TP) / n
    return out


MISSING_EXPORT_STATUS = "CLEAN_GUARD_FAILED_NO_VALIDATION_EXPORT"
MISSING_EXPORT_NOTE = (
    "This run completed training but produced no clean-guard-eligible best checkpoint or "
    "validation export; it is treated as ineligible for promotion and as zero validation recall "
    "for conservative gate evaluation.")


def conservative_failure_result(config: str, seed: int):
    """Build a conservative FAILURE seed-result for a config/seed with no validation export.

    A config/seed can complete training yet produce no clean-guard-eligible best checkpoint, in
    which case the training script writes no validation score export (as observed for seed 42).
    Such a run is treated as ineligible for promotion and assigned conservative zero-recall
    failure metrics (TP=0, FN=44, FP=0, TN=452, recall=0.0, FAR=0.0, precision=0.0, F1=0.0,
    AUROC=NaN) and a failing clean guard. This can NEVER help D14 pass the gate: it ranks lowest in
    median selection, and if it becomes the median seed it fails gate condition 1 (TP < 38) and
    condition 4 (clean guard), and no bootstrap can run (no scores) so conditions 2 and 3 also fail.
    """
    fail = {"threshold": None, "TP": 0, "FN": C.VAL_FALL_WINDOWS, "FP": 0,
            "TN": C.VAL_NONFALL_WINDOWS, "recall": 0.0, "FAR": 0.0,
            "precision": 0.0, "F1": 0.0}
    return {"config": config, "seed": seed, "y": None, "s": None,
            "primary": dict(fail), "secondary": dict(fail), "best_epoch": None,
            "guard": {"clean_accuracy": None, "clean_macro_f1": None,
                      "clean_fall_recall": None, "guard_pass": False},
            "auroc": float("nan"), "status": MISSING_EXPORT_STATUS}


def per_seed_metrics(config: str, seed: int):
    path = d14_val_pgd_path(config, seed)
    if not path.exists():
        # Missing validation export -> the run produced no clean-guard-eligible best checkpoint
        # (or was not run). Do NOT drop it: treat it conservatively so it cannot help the gate.
        return conservative_failure_result(config, seed)
    y, s = load_val_scores(path)
    if len(y) != 496 or sum(y) != 44:
        raise SystemExit(f"REFUSED: {path} is not a 496-window/44-fall validation export "
                         f"(got {len(y)}/{sum(y)}).")
    prim = C.select_threshold(y, s, C.PRIMARY_FAR_CAP)
    sec = C.select_threshold(y, s, C.SECONDARY_FAR_CAP)
    best_epoch = best_epoch_from_meta(config, seed)
    guard = clean_guard_from_log(config, seed, best_epoch)
    return {"config": config, "seed": seed, "y": y, "s": s,
            "primary": prim, "secondary": sec, "best_epoch": best_epoch, "guard": guard,
            "auroc": C.auroc(y, s), "status": "OK"}


def median_seed(seed_results):
    """Median seed by validation fall recall at cap 0.17; tie-break lower FAR, then smaller seed."""
    ranked = sorted(
        seed_results,
        key=lambda r: (r["primary"]["recall"] if r["primary"] else -1.0,
                       -(r["primary"]["FAR"] if r["primary"] else 1.0),
                       -r["seed"]))
    # median of 3 = middle element by recall ranking
    return ranked[len(ranked) // 2]


def parse_args():
    p = argparse.ArgumentParser(
        description="D14 validation gate (validation-only; emits FAIL or GATE_PASS_NEEDS_APPROVAL).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--configs", nargs="+", default=["A", "B"], choices=["A", "B"],
                   help="Configs to evaluate (default both).")
    p.add_argument("--seeds", nargs="+", type=int, default=list(C.ALLOWED_SEEDS),
                   help="Seeds to evaluate (default 42 43 44).")
    return p.parse_args()


def main():
    args = parse_args()
    for sd in args.seeds:
        C.validate_seed(sd)
    for cf in args.configs:
        C.validate_config(cf)

    print("D14 validation gate -- validation only. No held-out test read has been performed "
          "by this script.")

    # AFAC reference (for paired bootstrap): existing validation PGD scores.
    afac_ref = None
    if C.AFAC_VAL_PGD_SCORES.exists():
        y_ref, s_ref = load_val_scores(C.AFAC_VAL_PGD_SCORES)
        ref_sel = C.select_threshold(y_ref, s_ref, C.PRIMARY_FAR_CAP)
        afac_ref = {"y": y_ref, "s": s_ref, "tau": ref_sel["threshold"] if ref_sel else None}

    # gather per config/seed. Every seed yields a result: real metrics if a validation export
    # exists, otherwise a conservative FAILURE result (never dropped, so it cannot help the gate).
    by_config = {}
    missing = []
    for cf in args.configs:
        seed_results = []
        for sd in args.seeds:
            m = per_seed_metrics(cf, sd)
            seed_results.append(m)
            if m["status"] == MISSING_EXPORT_STATUS:
                missing.append((cf, sd))
        by_config[cf] = seed_results

    if missing:
        print(f"[info] {len(missing)} config/seed run(s) with NO validation export "
              f"(clean-guard-failed, conservative failure): {missing}")
    if not by_config:
        raise SystemExit("No configs requested; nothing to gate. (No test read performed.)")

    # config selection: higher median-seed recall@0.17, then lower median-seed FAR, then Config A
    config_summ = []
    for cf, seed_results in by_config.items():
        ms = median_seed(seed_results)
        config_summ.append({"config": cf, "median_seed_result": ms,
                            "median_recall": ms["primary"]["recall"] if ms["primary"] else -1.0,
                            "median_far": ms["primary"]["FAR"] if ms["primary"] else 1.0})
    config_summ.sort(key=lambda c: (c["median_recall"], -c["median_far"], c["config"] != "A"),
                     reverse=True)
    chosen = config_summ[0]
    chosen_cf = chosen["config"]
    ms = chosen["median_seed_result"]

    # gate computation on the chosen config's median seed
    prim = ms["primary"]
    tau = prim["threshold"] if prim else None
    boot = None
    if tau is not None:
        boot = stratified_bootstrap(
            ms["y"], ms["s"], tau,
            y_ref=(afac_ref["y"] if afac_ref else None),
            s_ref=(afac_ref["s"] if afac_ref else None),
            tau_ref=(afac_ref["tau"] if afac_ref else None))

    cond1 = prim is not None and prim["TP"] >= C.GATE_MIN_MEDIAN_RECALL_TP
    cond2 = boot is not None and boot["frac_recall_ge_0.80"] >= C.GATE_RECALL_FLOOR_FRACTION
    # Gate condition 3 (clarification commit): the PAIRED stratified bootstrap is the PRIMARY gate
    # (D14 and AFAC scored on the same resampled window IDs). The fixed 36/44 comparison is a
    # SENSITIVITY CHECK ONLY and is NEVER used for the gate decision. If the paired reference is
    # unavailable, the primary Gate-3 cannot be evaluated and the gate cannot pass on the fixed
    # result alone.
    gain_paired = boot.get("frac_gain_paired_ge_2") if boot else None   # PRIMARY
    gain_fixed = boot.get("frac_gain_fixed_ge_2") if boot else None     # sensitivity only
    cond3 = gain_paired is not None and gain_paired >= C.GATE_GAIN_FRACTION
    guard = ms["guard"]
    cond4 = guard is not None and guard["guard_pass"]
    gate_pass = bool(cond1 and cond2 and cond3 and cond4)

    verdict = "D14_GATE_PASS_NEEDS_APPROVAL" if gate_pass else "D14_FAIL_VALIDATION_GATE"
    lines = []
    lines.append(f"# {verdict}")
    lines.append("")
    lines.append(f"Pre-registration commit `{C.D14_PREREG_COMMIT}`; clarification commit "
                 f"`{C.D14_CLARIFICATION_COMMIT}` (paired bootstrap = primary Gate-3; fixed 36/44 = "
                 f"sensitivity only).")
    lines.append("")
    lines.append("Validation-only D14 gate. **No held-out test read has been performed by this "
                 "script.**")
    lines.append("")
    lines.append(f"- Chosen config (tie-break: higher median recall@0.17 -> lower FAR -> Config A): "
                 f"**{chosen_cf}**")
    ms_status = ms.get("status", "OK")
    lines.append(f"- Median seed of chosen config: **{ms['seed']}** (best epoch {ms['best_epoch']}, "
                 f"status {ms_status})")
    if ms_status == MISSING_EXPORT_STATUS:
        lines.append(f"- Median-seed cap-0.17 operating point: "
                     f"CLEAN_GUARD_FAILED_NO_VALIDATION_EXPORT -> conservative failure "
                     f"TP/FN/FP/TN={prim['TP']}/{prim['FN']}/{prim['FP']}/{prim['TN']}, "
                     f"recall={prim['recall']:.4f}, FAR={prim['FAR']:.4f} (no threshold; no scores).")
        lines.append(f"- Note: {MISSING_EXPORT_NOTE}")
    elif prim and prim["threshold"] is not None:
        lines.append(f"- Median-seed cap-0.17 operating point: threshold={prim['threshold']:.6f}, "
                     f"TP/FN/FP/TN={prim['TP']}/{prim['FN']}/{prim['FP']}/{prim['TN']}, "
                     f"recall={prim['recall']:.4f}, FAR={prim['FAR']:.4f}")
        if ms["secondary"] and ms["secondary"]["threshold"] is not None:
            se = ms["secondary"]
            lines.append(f"- Median-seed cap-0.20 comparison: threshold={se['threshold']:.6f}, "
                         f"recall={se['recall']:.4f}, FAR={se['FAR']:.4f}")
    else:
        lines.append("- Median-seed cap-0.17 operating point: no threshold satisfied FAR cap 0.17.")
    lines.append(f"- Median-seed validation PGD AUROC: {ms['auroc']:.4f}")
    lines.append("")
    # Per config/seed status table (transparency about missing exports).
    lines.append("## Per config/seed status")
    for cf, seed_results in by_config.items():
        for r in sorted(seed_results, key=lambda r: r["seed"]):
            st = r.get("status", "OK")
            rec = r["primary"]["recall"] if r["primary"] else float("nan")
            lines.append(f"- Config {cf} seed {r['seed']}: {st}"
                         + (f" (cap-0.17 recall {rec:.4f})" if st == "OK" and r["primary"] else ""))
    lines.append("")
    lines.append("## Gate conditions")
    lines.append(f"1. median-seed recall >= 38/44 (0.8636): "
                 f"{'PASS' if cond1 else 'FAIL'} "
                 f"(TP={prim['TP'] if prim else 'n/a'})")
    if boot:
        paired_str = (f"{gain_paired:.3f}" if gain_paired is not None
                      else "UNAVAILABLE (AFAC reference missing; gate cannot pass on fixed alone)")
        fixed_str = f"{gain_fixed:.3f}" if gain_fixed is not None else "n/a"
        lines.append(f"2. bootstrap recall >= 0.80 in >= 75%: {'PASS' if cond2 else 'FAIL'} "
                     f"(observed {boot['frac_recall_ge_0.80']:.3f}, n={boot['n_boot']})")
        lines.append(f"3. PAIRED bootstrap gain (Delta TP = TP_D14 - TP_AFAC >= 2) in >= 70% "
                     f"[PRIMARY]: {'PASS' if cond3 else 'FAIL'} (paired observed {paired_str}). "
                     f"Fixed 36/44 comparison (SENSITIVITY ONLY, not used for gate): {fixed_str}")
    else:
        lines.append("2. bootstrap recall: FAIL (no cap-0.17 threshold available)")
        lines.append("3. bootstrap gain: FAIL (no cap-0.17 threshold available)")
    if guard and guard.get("clean_accuracy") is not None:
        lines.append(f"4. clean guard (acc>=0.70, mF1>=0.65, fallR>=0.90): "
                     f"{'PASS' if cond4 else 'FAIL'} "
                     f"(acc={guard['clean_accuracy']:.3f}, mF1={guard['clean_macro_f1']:.3f}, "
                     f"fallR={guard['clean_fall_recall']:.3f})")
    elif ms_status == MISSING_EXPORT_STATUS:
        lines.append("4. clean guard: FAIL (no clean-guard-eligible best checkpoint; "
                     "conservative failure)")
    else:
        lines.append("4. clean guard: FAIL (no training-log clean metrics found)")
    lines.append("")
    lines.append(f"## VERDICT: {verdict}")
    if gate_pass:
        lines.append("")
        lines.append("All four conditions pass. This does NOT trigger a test read. A single locked "
                     "held-out test read may be performed ONLY after explicit human approval, using "
                     "`apply_d14_locked_test_once.py` with the frozen thresholds written to "
                     "`d14_frozen_gate_thresholds.json`.")
    else:
        lines.append("")
        lines.append("At least one condition failed. Per the pre-registration, there is NO held-out "
                     "test read; the F20 chase ends, and the next step is the D9 TRADES/MART "
                     "baseline-completeness rerun.")
    lines.append("")
    lines.append("_No held-out test read has been performed by this script._")

    report_name = f"{verdict}.md"
    report_path = C.D14_RESULTS_ROOT / report_name
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[write] {report_path.relative_to(C.REPO)}")

    # A conservative-failure median seed has threshold=None and cannot pass the gate; the extra
    # threshold-not-None guard is defensive so a frozen-thresholds file is never written on failure.
    if gate_pass and prim is not None and prim["threshold"] is not None:
        frozen = {
            "verdict": verdict,
            "chosen_config": chosen_cf,
            "median_seed": ms["seed"],
            "best_epoch": ms["best_epoch"],
            "primary_far_cap": C.PRIMARY_FAR_CAP,
            "primary_frozen_threshold": prim["threshold"],
            "secondary_far_cap": C.SECONDARY_FAR_CAP,
            "secondary_frozen_threshold": (ms["secondary"]["threshold"] if ms["secondary"] else None),
            "note": "Frozen validation-selected thresholds for the single authorized D14 test read. "
                    "Do not modify. No test read has occurred yet.",
        }
        frozen_path = C.D14_RESULTS_ROOT / "d14_frozen_gate_thresholds.json"
        frozen_path.write_text(json.dumps(frozen, indent=2), encoding="utf-8")
        print(f"[write] {frozen_path.relative_to(C.REPO)} (frozen thresholds; NO test read performed)")

    print(f"[done] gate verdict: {verdict}. No held-out test read has been performed by this script.")


if __name__ == "__main__":
    main()
