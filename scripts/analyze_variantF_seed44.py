"""
Variant F seed-44 INDEPENDENT VALIDATION analysis: comparison, Wilson CIs, Pareto,
FN:FP cost, logit-margin geometry, PGD-10->PGD-20 durability + gradient-masking check,
tiered-criteria scorecard, and the single Decision category.

Analysis only (reads existing test-eval CSVs). Same-seed baselines: FGSM defense seed44
(recall floor 0.044), Variant D seed44 (false-alarm reference, trained this run). Cross-seed
references: prior Variant E seed42 walk/run logit margin (2.716) and selection-v2 seed42
(recall 0.356 / FP 117) for context.

Outputs under results/safety_guided_defense/variantF_motion_margin/seed44/:
    variantF_seed44_comparison.csv
    analysis/{wilson_intervals,logit_margin_geometry,cost_curve,criteria_scorecard}.csv
    analysis/decision.txt
    figures/fig_pareto_seed44.png

Command: python scripts/analyze_variantF_seed44.py
"""
from __future__ import annotations
from pathlib import Path
import csv, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

EXP = Path(__file__).resolve().parents[1]
SG = EXP / "results" / "safety_guided_defense"
VF = SG / "variantF_motion_margin" / "seed44"
TE = VF / "test_eval"
FIG = VF / "figures"; ANA = VF / "analysis"
FIG.mkdir(parents=True, exist_ok=True); ANA.mkdir(parents=True, exist_ok=True)
CLASS = {0: "lie down", 1: "fall", 2: "walk", 3: "pickup", 4: "run", 5: "sit down", 6: "stand up"}
NONFALL = [0, 2, 3, 4, 5, 6]; WALK, RUN, FALL = 2, 4, 1
NFALL = 45
LOGIT = [f"logit_{CLASS[i].replace(' ', '_')}" for i in range(7)]
FGSM_FLOOR = 0.044                 # same-seed FGSM-defense seed44 PGD recall
PRIORE_MARGIN_REF = 2.716          # seed-42 prior Variant E walk/run logit margin (cross-seed)


def rows(p):
    p = Path(p)
    if not p.exists():
        return None
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def kv(p):
    return {r["metric"]: r["value"] for r in (rows(p) or [])}


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def src_counts(rs, col):
    c = {k: 0 for k in NONFALL}
    for r in rs:
        if int(r["true_label"]) != FALL and int(r[col]) == FALL:
            c[int(r["true_label"])] += 1
    return c


def wr_margin(prob_csv):
    rs = rows(prob_csv)
    if not rs:
        return float("nan")
    vals = [float(r["logit_fall"]) - float(r[LOGIT[int(r["true_label"])]])
            for r in rs if int(r["true_label"]) in (WALK, RUN) and int(r["predicted_label"]) == FALL]
    return float(np.median(vals)) if vals else float("nan")


def main():
    ca = EXP / "results" / "converged_attacks"
    d44 = SG / "seed44" / "test_eval"
    refs = {
        "FGSM_defense_s44": (ca, "defended_fgsm_at_seed44", None),
        "D_safety_s44": (d44, "variantD_bySafetyScore",
                         d44 / "variantD_bySafetyScore_pgd_probabilities_test_epsilon_0_03.csv"),
    }
    vf_runs = sorted(p.name.replace("_pgd_safety_metrics_test_epsilon_0_03.csv", "")
                     for p in TE.glob("*_pgd_safety_metrics_test_epsilon_0_03.csv") if "_pgd20" not in p.name)

    comp = []
    for label, (d, run, prob) in refs.items():
        m = kv(Path(d) / f"{run}_pgd_safety_metrics_test_epsilon_0_03.csv")
        if not m:
            comp.append(dict(group="reference", label=label, missing=True)); continue
        pred = rows(Path(d) / f"{run}_pgd_predictions_test_epsilon_0_03.csv")
        sc = src_counts(pred, "attacked_predicted_label") if pred else {k: 0 for k in NONFALL}
        comp.append(dict(group="reference", label=label, missing=False, recall=float(m["fall_recall"]),
                         fp=int(m["false_fall_alarm_count"]), walkrun=sc[WALK] + sc[RUN],
                         acc=float(m["clean_accuracy"]), f1=float(m["clean_macro_f1"]),
                         clean_fr=float(m["clean_fall_recall"]),
                         wr_margin=wr_margin(prob) if prob else float("nan"), pgd20=float("nan")))
    for run in vf_runs:
        m = kv(TE / f"{run}_pgd_safety_metrics_test_epsilon_0_03.csv")
        pred = rows(TE / f"{run}_pgd_predictions_test_epsilon_0_03.csv")
        sc = src_counts(pred, "attacked_predicted_label") if pred else {k: 0 for k in NONFALL}
        p20 = kv(TE / f"{run}_pgd20_pgd_safety_metrics_test_epsilon_0_03.csv")
        comp.append(dict(group="variantF", label=run, missing=False, recall=float(m["fall_recall"]),
                         fp=int(m["false_fall_alarm_count"]), walkrun=sc[WALK] + sc[RUN],
                         acc=float(m["clean_accuracy"]), f1=float(m["clean_macro_f1"]),
                         clean_fr=float(m["clean_fall_recall"]),
                         wr_margin=wr_margin(TE / f"{run}_pgd_probabilities_test_epsilon_0_03.csv"),
                         pgd20=float(p20["fall_recall"]) if p20 else float("nan")))

    # comparison csv
    with (VF / "variantF_seed44_comparison.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "label", "pgd_recall", "pgd_FP", "walk_run_to_fall", "clean_acc",
                    "clean_macro_f1", "clean_fall_recall", "wr_logit_margin", "pgd20_recall"])
        for c in comp:
            if c.get("missing"):
                w.writerow([c["group"], c["label"], "MISSING", "", "", "", "", "", "", ""]); continue
            w.writerow([c["group"], c["label"], f"{c['recall']:.3f}", c["fp"], c["walkrun"],
                        f"{c['acc']:.3f}", f"{c['f1']:.3f}", f"{c['clean_fr']:.3f}",
                        f"{c['wr_margin']:.3f}", f"{c['pgd20']:.3f}"])

    # wilson
    with (ANA / "wilson_intervals.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["label", "recall", "tp", "n_fall", "wilson_low", "wilson_high"])
        for c in comp:
            if c.get("missing"):
                continue
            tp = round(c["recall"] * NFALL); lo, hi = wilson(tp, NFALL)
            w.writerow([c["label"], f"{c['recall']:.3f}", tp, NFALL, f"{lo:.3f}", f"{hi:.3f}"])

    # geometry
    with (ANA / "logit_margin_geometry.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["label", "wr_logit_margin", "vs_priorE_ref_2.716", "improved"])
        for c in comp:
            if c.get("missing") or math.isnan(c["wr_margin"]):
                continue
            w.writerow([c["label"], f"{c['wr_margin']:.3f}", f"{c['wr_margin']-PRIORE_MARGIN_REF:+.3f}",
                        int(c["wr_margin"] < PRIORE_MARGIN_REF)])

    # cost curve
    with (ANA / "cost_curve.csv").open("w", newline="") as f:
        w = csv.writer(f); ratios = [1, 2, 5, 10, 20, 50]
        w.writerow(["label"] + [f"cost_{r}to1" for r in ratios])
        for c in comp:
            if c.get("missing"):
                continue
            missed = round((1 - c["recall"]) * NFALL)
            w.writerow([c["label"]] + [r * missed + c["fp"] for r in ratios])

    # same-seed Variant D reference for criteria 6/7
    dref = next((c for c in comp if c["label"] == "D_safety_s44" and not c.get("missing")), None)
    D_FP = dref["fp"] if dref else 157          # fallback: seed-42 cross-seed
    D_WR = dref["walkrun"] if dref else 120
    d_seed = "seed44" if dref else "seed42(cross)"

    # scorecard + decision (Variant F candidates)
    decisions = {}
    with (ANA / "criteria_scorecard.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["candidate", "c1_acc>=.70", "c2_f1>=.65", "c3_cleanfr>=.90",
                    "c4_recall_tier", "c5_wilson_low>0", f"c6_FP<=D({d_seed},{D_FP})",
                    f"c7_walkrun<=D({D_WR})", "c8_geometry_improved", "c9_pgd20_tier",
                    "c10_no_masking", "decision_category"])
        for c in comp:
            if c["group"] != "variantF":
                continue
            tp = round(c["recall"] * NFALL); lo, _ = wilson(tp, NFALL)
            c1 = c["acc"] >= 0.70; c2 = c["f1"] >= 0.65; c3 = c["clean_fr"] >= 0.90
            # tiered recall
            r = c["recall"]
            c4 = "STRONG" if r >= 0.30 else ("SUPPORT" if r >= 0.20 else ("minimal" if r > FGSM_FLOOR else "FAIL"))
            c5 = lo > 0
            c6 = c["fp"] <= D_FP * 1.10
            c7 = c["walkrun"] <= D_WR * 1.10
            c8 = (not math.isnan(c["wr_margin"])) and c["wr_margin"] < PRIORE_MARGIN_REF
            # tiered pgd20
            p20 = c["pgd20"]; ratio = (p20 / r) if r > 0 else 0.0
            if math.isnan(p20) or p20 <= 0:
                c9 = "FAIL"
            elif ratio >= 0.75:
                c9 = "STRONG"
            elif p20 > FGSM_FLOOR and ratio >= 0.50:
                c9 = "SUPPORT"
            else:
                c9 = "weak"
            c10 = math.isnan(p20) or p20 <= r + 1e-9  # non-increasing PGD10->PGD20

            # decision category (most-favorable whose conditions all hold)
            guard = c1 and c2 and c3
            geom = c8
            strong = (guard and r >= 0.30 and c9 == "STRONG" and c["fp"] <= D_FP and c["walkrun"] <= D_WR and geom and c10)
            support = (guard and r >= 0.20 and r > FGSM_FLOOR and c5 and c9 in ("STRONG", "SUPPORT") and c6 and geom and c10)
            reject = ((not guard) or c["clean_fr"] < 0.90 or r <= FGSM_FLOOR or (not math.isnan(p20) and p20 <= 0)
                      or c["fp"] > D_FP * 1.25 or (not geom) or (not c10))
            if strong:
                cat = "STRONG SUPPORT"
            elif support:
                cat = "SUPPORT"
            elif reject:
                cat = "REJECT / DOES NOT GENERALIZE"
            else:
                cat = "WEAK SUPPORT / TRADE-OFF"
            decisions[c["label"]] = cat
            w.writerow([c["label"], int(c1), int(c2), int(c3), c4, int(c5), int(c6), int(c7),
                        int(c8), c9, int(c10), cat])

    # primary candidate decision (v2safety)
    primary = next((lbl for lbl in decisions if "v2safety" in lbl), None)
    with (ANA / "decision.txt").open("w") as f:
        f.write(f"D_safety reference used: {d_seed} (FP={D_FP}, walk/run={D_WR})\n")
        for lbl, cat in decisions.items():
            f.write(f"{lbl}: {cat}\n")
        if primary:
            f.write(f"\nPRIMARY (v2safety) DECISION: {decisions[primary]}\n")

    # pareto figure
    fig, ax = plt.subplots(figsize=(9, 6))
    for c in comp:
        if c.get("missing"):
            continue
        col = "tab:blue" if c["group"] == "variantF" else "tab:gray"
        mk = "^" if c["group"] == "variantF" else "o"
        ax.scatter(c["fp"], c["recall"], color=col, marker=mk, s=85, zorder=4)
        ax.annotate(c["label"].replace("seed44_variantF_margin_", "F:").replace("_gm0p5_gf0p5", ""),
                    (c["fp"], c["recall"]), fontsize=6, xytext=(3, 3), textcoords="offset points")
    ax.axhline(FGSM_FLOOR, color="red", ls=":", lw=0.8, alpha=0.6)
    ax.axhline(0.20, color="orange", ls=":", lw=0.8, alpha=0.5)
    ax.axhline(0.30, color="green", ls=":", lw=0.8, alpha=0.5)
    ax.set_xlabel("PGD@0.030 false-fall alarms"); ax.set_ylabel("PGD@0.030 fall recall")
    ax.set_title("Seed 44 Variant F (^) vs same-seed baselines (o); lines=floor/0.20/0.30")
    ax.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(FIG / "fig_pareto_seed44.png", dpi=150); plt.close(fig)
    print(f"D reference: {d_seed} FP={D_FP} wr={D_WR}")
    for lbl, cat in decisions.items():
        print(f"  {lbl}: {cat}")
    print("[done] seed-44 validation analysis complete.")


if __name__ == "__main__":
    main()
