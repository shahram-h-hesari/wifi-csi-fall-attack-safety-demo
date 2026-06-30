"""
Read-only G1 seed-42 VALIDATION frontier baseline for the Safety-TRADES / BASAT Stage 1 go/no-go.

NO training, NO model loading, NO attack generation, NO test tuning. Reads committed per-window
probability CSVs only and writes a baseline artifact. This is the number the Safety-TRADES /
BASAT Stage 1 pilot must beat on VALIDATION before TEST is ever touched.

Primary baseline quantities (VALIDATION = the go/no-go reference):
  * val PGD AUROC of P(fall)   -- threshold-free fall-vs-nonfall separability; bootstrap 95% CI
  * val recall @ FAR<=10%      -- max fall recall s.t. FP/n_nonfall <= 0.10 over a P(fall) sweep
  * val PGD argmax operating point (reproduces the selection_candidates row as a cross-check)

Reference-only (already-evaluated committed predictions; NOT used for selection/go-no-go):
  * val clean / FGSM AUROC; TEST PGD-10 and PGD-20 AUROC.

G1 seed-42 selection epochs (analysis/seed42_variantG_G1_selection_candidates.csv):
  v2safety == v2maxrec (epoch 58); v2lowFA (epoch 68). The committed val PGD export 'R_G1maxrec'
  IS the v2safety/v2maxrec checkpoint; 'B_G1lowFA' is v2lowFA. v2safety is the pilot's primary
  selector, so it is the primary baseline here.

Eval attack note: committed 'pgd' = EVAL PGD (10 steps, alpha=eps/6); 'pgd20' = 20-step audit.
"""
from __future__ import annotations

from pathlib import Path
import csv
import json
import math
from datetime import datetime, timezone

import numpy as np

EXP = Path(__file__).resolve().parents[1]
FAR_BUDGET = 0.10

PROB_DIR = EXP / "results/safety_guided_defense/dual_specialist_safety_gate/A1/seed42/probabilities"
TEST_DIR = EXP / "results/safety_guided_defense/variantG_targeted_hardneg/seed42/test_eval"
OUT_DIR = EXP / "results/safety_guided_defense/boundary_aware_selective_at/seed42"

# (label, csv path). v2safety==v2maxrec(ep58) -> R_G1maxrec; v2lowFA(ep68) -> B_G1lowFA.
VAL_FILES = {
    "v2safety(=maxrec,ep58) val clean": PROB_DIR / "R_G1maxrec_clean_probabilities_val_epsilon_0_03.csv",
    "v2safety(=maxrec,ep58) val fgsm":  PROB_DIR / "R_G1maxrec_fgsm_probabilities_val_epsilon_0_03.csv",
    "v2safety(=maxrec,ep58) val pgd":   PROB_DIR / "R_G1maxrec_pgd_probabilities_val_epsilon_0_03.csv",
    "v2lowFA(ep68) val pgd":            PROB_DIR / "B_G1lowFA_pgd_probabilities_val_epsilon_0_03.csv",
}
TEST_REF_FILES = {
    "v2safety test pgd (PGD-10, ref)":  TEST_DIR / "G_G1_v2safety_pgd_probabilities_test_epsilon_0_03.csv",
    "v2safety test pgd20 (PGD-20, ref)": TEST_DIR / "G_G1_v2safety_pgd20_pgd_probabilities_test_epsilon_0_03.csv",
}


def load(path: Path):
    """Return (p_fall, fall_true_binary) float/int arrays from a committed probability CSV."""
    p, y = [], []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            p.append(float(row["fall_probability"]))
            y.append(int(row["fall_true_binary"]))
    return np.asarray(p, dtype=float), np.asarray(y, dtype=int)


def load_argmax(path: Path):
    """Return fall_pred_binary (argmax fall decision) for the val PGD operating-point cross-check."""
    fp = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fp.append(int(row["fall_pred_binary"]))
    return np.asarray(fp, dtype=int)


def auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Rank-based AUROC (Mann-Whitney U), tie-safe via average ranks."""
    order = np.argsort(scores, kind="mergesort")
    s = scores[order]
    y = labels[order]
    n = len(s)
    ranks = np.empty(n, dtype=float)
    i = 0
    while i < n:
        j = i
        while j < n and s[j] == s[i]:
            j += 1
        ranks[i:j] = (i + j - 1) / 2.0 + 1.0  # 1-based average rank
        i = j
    pos = int(y.sum())
    neg = n - pos
    if pos == 0 or neg == 0:
        return float("nan")
    sum_pos = ranks[y == 1].sum()
    return float((sum_pos - pos * (pos + 1) / 2.0) / (pos * neg))


def auroc_ci(scores: np.ndarray, labels: np.ndarray, n_boot: int = 2000, seed: int = 42):
    """Percentile bootstrap 95% CI for AUROC (resample windows with replacement)."""
    rng = np.random.default_rng(seed)
    n = len(scores)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        a = auroc(scores[idx], labels[idx])
        if not math.isnan(a):
            vals.append(a)
    if not vals:
        return (float("nan"), float("nan"))
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return (float(lo), float(hi))


def recall_at_far(scores: np.ndarray, labels: np.ndarray, far_budget: float = FAR_BUDGET) -> dict:
    """Max fall recall over a P(fall) threshold sweep s.t. FAR=FP/n_nonfall <= far_budget.
    Decision: predict fall if p_fall >= tau. Tie-break: among max recall, lowest FP, then higher tau."""
    y = labels.astype(bool)
    n_fall = int(y.sum())
    n_nonfall = int((~y).sum())
    taus = np.unique(np.concatenate([[0.0], scores, [1.0 + 1e-9]]))
    best = None
    feasible_any = False
    for tau in taus:
        pred = scores >= tau
        tp = int((y & pred).sum())
        fp = int((~y & pred).sum())
        recall = tp / n_fall if n_fall else 0.0
        far = fp / n_nonfall if n_nonfall else 0.0
        if far <= far_budget + 1e-12:
            feasible_any = True
            key = (recall, -fp, tau)  # max recall, then fewer FP, then higher tau
            if best is None or key > best[0]:
                best = (key, {"tau": float(tau), "recall": recall, "FAR": far,
                              "TP": tp, "FP": fp, "FN": n_fall - tp,
                              "n_fall": n_fall, "n_nonfall": n_nonfall})
    if not feasible_any:
        return {"feasible": False, "n_fall": n_fall, "n_nonfall": n_nonfall}
    out = best[1]
    out["feasible"] = True
    return out


def argmax_operating_point(scores_path: Path) -> dict:
    p, y = load(scores_path)
    fp_pred = load_argmax(scores_path)
    yb = y.astype(bool)
    pred = fp_pred.astype(bool)
    n_fall = int(yb.sum())
    n_nonfall = int((~yb).sum())
    tp = int((yb & pred).sum())
    fp = int((~yb & pred).sum())
    return {"recall": tp / n_fall if n_fall else 0.0, "FAR": fp / n_nonfall if n_nonfall else 0.0,
            "TP": tp, "FP": fp, "FN": n_fall - tp, "n_fall": n_fall, "n_nonfall": n_nonfall}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "purpose": "G1 seed-42 VALIDATION frontier baseline for Safety-TRADES / BASAT Stage 1 go/no-go",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True, "trained": False, "test_tuning": False,
        "far_budget": FAR_BUDGET,
        "primary_baseline_checkpoint": "G1 seed42 v2safety (== v2maxrec, epoch 58)",
        "eval_attack_note": "committed 'pgd' = eval PGD-10 (alpha=eps/6); 'pgd20' = 20-step audit",
        "validation": {}, "test_reference": {},
    }

    print("=" * 84)
    print("G1 seed-42 VALIDATION frontier baseline  (read-only; no training; no test tuning)")
    print("=" * 84)

    for label, path in VAL_FILES.items():
        if not path.exists():
            print(f"  MISSING: {label} -> {path.name}")
            result["validation"][label] = {"missing": str(path)}
            continue
        p, y = load(path)
        a = auroc(p, y)
        entry = {"file": path.name, "n": len(p), "n_fall": int(y.sum()),
                 "n_nonfall": int((~y.astype(bool)).sum()), "auroc_pfall": a}
        if "pgd" in label:
            lo, hi = auroc_ci(p, y)
            entry["auroc_ci95"] = [lo, hi]
            entry["recall_at_far10"] = recall_at_far(p, y)
            entry["argmax_operating_point"] = argmax_operating_point(path)
        result["validation"][label] = entry

        line = f"  {label:34s} AUROC P(fall)={a:.4f}"
        if "auroc_ci95" in entry:
            line += f"  CI95[{entry['auroc_ci95'][0]:.4f},{entry['auroc_ci95'][1]:.4f}]"
        print(line)
        if "recall_at_far10" in entry:
            r = entry["recall_at_far10"]
            if r.get("feasible"):
                print(f"      recall@FAR<=10%: recall={r['recall']:.4f} (TP={r['TP']}/{r['n_fall']}) "
                      f"FP={r['FP']} FAR={r['FAR']:.4f} tau={r['tau']:.4f}")
            else:
                print(f"      recall@FAR<=10%: INFEASIBLE (no threshold reaches FAR<=10%)")
            op = entry["argmax_operating_point"]
            print(f"      argmax op-point: recall={op['recall']:.4f} FP={op['FP']} FAR={op['FAR']:.4f}  "
                  f"(cross-check vs selection_candidates)")

    print("-" * 84)
    print("  TEST reference (already-evaluated committed predictions; NOT a go/no-go quantity):")
    for label, path in TEST_REF_FILES.items():
        if not path.exists():
            print(f"    MISSING: {label} -> {path.name}")
            result["test_reference"][label] = {"missing": str(path)}
            continue
        p, y = load(path)
        a = auroc(p, y)
        lo, hi = auroc_ci(p, y)
        result["test_reference"][label] = {"file": path.name, "auroc_pfall": a, "auroc_ci95": [lo, hi],
                                           "n_fall": int(y.sum()), "n_nonfall": int((~y.astype(bool)).sum())}
        print(f"    {label:34s} AUROC P(fall)={a:.4f}  CI95[{lo:.4f},{hi:.4f}]")

    # Go/no-go bar derived from the BEST available G1 checkpoint (not the weakest), so the
    # baseline cannot be gamed by comparing against a poorly-separated checkpoint. The
    # matched-selector comparison (v2safety-vs-v2safety) is reported alongside for fairness.
    val_pgd = {k: v for k, v in result["validation"].items()
               if "pgd" in k and isinstance(v, dict) and "auroc_pfall" in v and "recall_at_far10" in v}
    matched = result["validation"].get("v2safety(=maxrec,ep58) val pgd", {})
    if val_pgd:
        best_auroc_label = max(val_pgd, key=lambda k: val_pgd[k]["auroc_pfall"])
        best_auroc = val_pgd[best_auroc_label]["auroc_pfall"]
        feas = {k: v for k, v in val_pgd.items() if v["recall_at_far10"].get("feasible")}
        best_rec_label = max(feas, key=lambda k: feas[k]["recall_at_far10"]["recall"]) if feas else None
        best_rec = feas[best_rec_label]["recall_at_far10"]["recall"] if best_rec_label else None
        result["go_no_go_bar"] = {
            "rule": "Safety-TRADES must beat the BEST G1 selection-v2 checkpoint, not the matched selector only",
            "g1_best_val_pgd_auroc": best_auroc,
            "g1_best_val_pgd_auroc_checkpoint": best_auroc_label,
            "auroc_go_threshold_+0.03": round(best_auroc + 0.03, 4),
            "g1_best_val_recall_at_far10": best_rec,
            "g1_best_val_recall_at_far10_checkpoint": best_rec_label,
            "matched_selector_v2safety_auroc": matched.get("auroc_pfall"),
            "matched_selector_v2safety_recall_at_far10": matched.get("recall_at_far10", {}).get("recall"),
            "GO_requires": [
                f"best Safety-TRADES val PGD AUROC > {round(best_auroc + 0.03, 4)} "
                f"(best G1 {best_auroc:.4f} + 0.03 meaningful margin)",
                f"best Safety-TRADES val recall@FAR<=10% >= {best_rec:.4f} (no worse than best G1)"
                if best_rec is not None else "recall@FAR<=10% not worse than best G1",
                "clean guard holds (val acc>=0.70, macro_f1>=0.65)",
                "PGD-20 reveals no gradient masking/collapse",
                "confirm with paired bootstrap on matched-selector AUROC difference (CI excludes 0)",
            ],
            "caveat": "n_fall(val)=44; single-checkpoint AUROC CI half-width ~0.04. +0.03 is suggestive, "
                      "not conclusive; matched-selector paired bootstrap + (deferred) seed replication confirm.",
        }
        base_auroc, base_rec_disp = best_auroc, best_rec

    (OUT_DIR / "g1_baseline_val_frontier.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    # Short human-readable companion.
    bar = result.get("go_no_go_bar", {})
    md = ["# G1 seed-42 validation frontier baseline (Safety-TRADES / BASAT Stage 1 reference)", "",
          f"_Generated {result['generated_utc']}. Read-only; no training; no test tuning._", "",
          "Eval attack: committed `pgd` = PGD-10 (alpha=eps/6); `pgd20` = 20-step audit.",
          "Bar is set against the **best** G1 selection-v2 checkpoint, not the matched selector, so the "
          "baseline cannot be gamed.", "",
          "## Validation per-checkpoint (the go/no-go reference)", "",
          "| checkpoint | val PGD AUROC P(fall) | val recall@FAR<=10% | argmax op-point |",
          "|---|---|---|---|"]
    for label, e in result["validation"].items():
        if "pgd" not in label or "auroc_pfall" not in e:
            continue
        ci = e.get("auroc_ci95", [float("nan"), float("nan")])
        r = e.get("recall_at_far10", {})
        op = e.get("argmax_operating_point", {})
        rec_s = (f"{r['recall']:.4f} (TP={r['TP']}/{r['n_fall']}, FP={r['FP']}, FAR={r['FAR']:.3f})"
                 if r.get("feasible") else "infeasible")
        op_s = f"rec={op.get('recall', float('nan')):.3f} / FAR={op.get('FAR', float('nan')):.3f}"
        md.append(f"| {label} | {e['auroc_pfall']:.4f} [{ci[0]:.3f},{ci[1]:.3f}] | {rec_s} | {op_s} |")
    if bar:
        md += ["", "## Go/no-go bar for Safety-TRADES Stage 1 (beat the BEST G1 checkpoint)", "",
               f"- best G1 val PGD AUROC = **{bar['g1_best_val_pgd_auroc']:.4f}** "
               f"({bar['g1_best_val_pgd_auroc_checkpoint']})",
               f"- best G1 val recall@FAR<=10% = **{bar['g1_best_val_recall_at_far10']:.4f}** "
               f"({bar['g1_best_val_recall_at_far10_checkpoint']})",
               f"- matched-selector v2safety AUROC = {bar['matched_selector_v2safety_auroc']:.4f}, "
               f"recall@FAR<=10% = {bar['matched_selector_v2safety_recall_at_far10']:.4f}", "",
               "**GO requires all of:**"]
        md += [f"{i+1}. {req}" for i, req in enumerate(bar["GO_requires"])]
        md += ["", f"_Caveat: {bar['caveat']}_", "",
               "## Test reference (already-evaluated; NOT used for go/no-go)", ""]
        for label, e in result["test_reference"].items():
            if "auroc_pfall" in e:
                md.append(f"- {label}: AUROC P(fall) = {e['auroc_pfall']:.4f} "
                          f"CI95[{e['auroc_ci95'][0]:.4f}, {e['auroc_ci95'][1]:.4f}]")
    (OUT_DIR / "g1_baseline_val_frontier.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print("-" * 84)
    print(f"  wrote: {OUT_DIR / 'g1_baseline_val_frontier.json'}")
    print(f"  wrote: {OUT_DIR / 'g1_baseline_val_frontier.md'}")
    print("=" * 84)


if __name__ == "__main__":
    main()
