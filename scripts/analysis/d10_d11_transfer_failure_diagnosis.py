"""
D10/D11 transfer-failure diagnosis — saved-score analysis ONLY.

Purpose: diagnose WHY D10/D11a/D11b validation success did not transfer to the
frozen held-out test split, using ONLY existing saved probability exports
(validation + test PGD epsilon=0.030 fall_probability CSVs) and the already
frozen validation-selected thresholds. No new inference, no new attack
generation, no training, no checkpoint is loaded, and no threshold is promoted.
Post-hoc test sweeps computed here are explicitly diagnostic characterization,
not frozen-threshold evidence.

Inputs (all pre-existing):
  - D8b/AFAC val:  results/afac_score_frozen_threshold_followup/val_eval/
  - D8b/AFAC test: results/safety_guided_defense/variantH_dual_tail_budget/
                   adaptive_lagrangian_far_constrained/optionB/seed42/test_eval/
  - D10/D11 val:   results/safety_guided_defense/boundary_aware_selective_at/...
  - D10/D11 test:  results/d10_d11_locked_test_followup/test_eval/
  - Frozen thresholds: d10_d11_threshold_selection_validation.csv,
                       afac_score_threshold_selection_validation.csv

Outputs (new files only, under results/defense_attempt_inventory/):
  d10_d11_transfer_diagnostics/*.csv, *.png, key_numbers.json
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "results"
OUT = RES / "defense_attempt_inventory" / "d10_d11_transfer_diagnostics"
OUT.mkdir(parents=True, exist_ok=True)

BASE = RES / "safety_guided_defense" / "boundary_aware_selective_at"
D10D11_TEST = RES / "d10_d11_locked_test_followup" / "test_eval"

FAR_CAPS = [0.10, 0.15, 0.18, 0.20, 0.22]
F20_TP_MIN = 36   # recall >= 0.80 with 45 test falls
F20_FP_MAX = 91   # FAR <= 0.20 with 455 test non-falls

METHODS = [
    {
        "id": "D8b_AFAC",
        "label": "D8b / AFAC-score (optionB_maxscore)",
        "val_csv": RES / "afac_score_frozen_threshold_followup" / "val_eval"
        / "optionB_maxscore_pgd_probabilities_val_epsilon_0_03.csv",
        "test_csv": RES / "safety_guided_defense" / "variantH_dual_tail_budget"
        / "adaptive_lagrangian_far_constrained" / "optionB" / "seed42"
        / "test_eval" / "optionB_maxscore_pgd_probabilities_test_epsilon_0_03.csv",
    },
    {
        "id": "D10",
        "label": "D10 GAIRAT (GR1_v2macroF1)",
        "val_csv": BASE / "gairat" / "seed42" / "GR1" / "val_eval"
        / "GR1_v2macroF1_pgd_probabilities_val_epsilon_0_03.csv",
        "test_csv": D10D11_TEST / "GR1_v2macroF1_pgd_probabilities_test_epsilon_0_03.csv",
    },
    {
        "id": "D11a",
        "label": "D11a Stage-1/BASAT (ST1b6_v2lowFA)",
        "val_csv": BASE / "seed42" / "beta6p0" / "val_eval"
        / "ST1b6_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv",
        "test_csv": D10D11_TEST / "ST1b6_v2lowFA_pgd_probabilities_test_epsilon_0_03.csv",
    },
    {
        "id": "D11b",
        "label": "D11b SAT (SA1_v2lowFA)",
        "val_csv": BASE / "sat" / "seed42" / "SA1" / "val_eval"
        / "SA1_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv",
        "test_csv": D10D11_TEST / "SA1_v2lowFA_pgd_probabilities_test_epsilon_0_03.csv",
    },
]

# Frozen validation-selected thresholds, verbatim from the committed selection CSVs.
FROZEN = {
    "D10": {0.20: 0.075261, 0.15: 0.148867, 0.10: 0.250327},
    "D11a": {0.20: 0.051834, 0.15: 0.111270, 0.10: 0.174677},
    "D11b": {0.20: 0.048495, 0.15: 0.083365, 0.10: 0.124667},
    "D8b_AFAC": {0.18: 0.170908, 0.20: 0.147881, 0.15: 0.181992, 0.10: 0.234373},
}
D8B_POSTHOC_TAU = 0.153246  # the historical D8b post-hoc F20 operating point


def load_split(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["condition"] == "pgd"]
    if not rows:
        raise ValueError(f"no PGD rows in {path}")
    y = np.array([int(r["fall_true_binary"]) for r in rows])
    s = np.array([float(r["fall_probability"]) for r in rows])
    true_cls = np.array([r["true_class_name"] for r in rows])
    pred_cls = np.array([r["predicted_class_name"] for r in rows])
    return y, s, true_cls, pred_cls


def confusion(y, s, tau):
    pred = s >= tau
    tp = int(np.sum(pred & (y == 1)))
    fn = int(np.sum(~pred & (y == 1)))
    fp = int(np.sum(pred & (y == 0)))
    tn = int(np.sum(~pred & (y == 0)))
    return tp, fn, fp, tn


def select_threshold(y, s, cap):
    """Replicates the frozen rule: max recall s.t. FAR <= cap;
    tie-break lower FAR, then higher tau. Candidates = distinct scores."""
    n_pos = int(np.sum(y == 1))
    n_neg = int(np.sum(y == 0))
    best = None
    for tau in sorted(set(s.tolist()), reverse=True):
        tp, fn, fp, tn = confusion(y, s, tau)
        far = fp / n_neg
        if far > cap:
            continue
        rec = tp / n_pos
        key = (rec, -far, tau)
        if best is None or key > best[0]:
            best = (key, tau, tp, fn, fp, tn)
    return best


def posthoc_best(y, s, cap):
    """Diagnostic-only: best recall achievable on THIS split s.t. FAR <= cap."""
    return select_threshold(y, s, cap)


def auroc(y, s):
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), dtype=float)
    sorted_s = s[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and sorted_s[j + 1] == sorted_s[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    n_pos = int(np.sum(y == 1))
    n_neg = len(y) - n_pos
    u = ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * n_neg)


def ks_stat(a, b):
    grid = np.sort(np.concatenate([a, b]))
    fa = np.searchsorted(np.sort(a), grid, side="right") / len(a)
    fb = np.searchsorted(np.sort(b), grid, side="right") / len(b)
    return float(np.max(np.abs(fa - fb)))


def survival(scores, tau):
    return float(np.mean(scores >= tau))


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


data = {}
for m in METHODS:
    yv, sv, tv, pv = load_split(m["val_csv"])
    yt, st, tt, pt = load_split(m["test_csv"])
    assert len(yv) == 496 and int(yv.sum()) == 44, f"{m['id']} val split mismatch"
    assert len(yt) == 500 and int(yt.sum()) == 45, f"{m['id']} test split mismatch"
    data[m["id"]] = {
        "label": m["label"],
        "val": (yv, sv, tv, pv),
        "test": (yt, st, tt, pt),
    }

key_numbers = {}

# ---------------------------------------------------------------- A. quantiles
QS_FALL = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90]
QS_NF = [0.50, 0.75, 0.90, 0.95, 0.975, 0.99]
quant_rows = []
for mid, d in data.items():
    for split in ("val", "test"):
        y, s, _, _ = d[split]
        fall, nf = s[y == 1], s[y == 0]
        row = {"method": mid, "split": split,
               "n_fall": len(fall), "n_nonfall": len(nf)}
        for q in QS_FALL:
            row[f"fall_q{q:g}"] = round(float(np.quantile(fall, q)), 6)
        for q in QS_NF:
            row[f"nonfall_q{q:g}"] = round(float(np.quantile(nf, q)), 6)
        row["auroc"] = round(auroc(y, s), 6)
        quant_rows.append(row)
write_csv(OUT / "diag_score_quantiles_val_vs_test.csv", quant_rows)

# KS statistics val vs test, per class group
ks_rows = []
for mid, d in data.items():
    yv, sv, _, _ = d["val"]
    yt, st, _, _ = d["test"]
    ks_rows.append({
        "method": mid,
        "ks_fall_val_vs_test": round(ks_stat(sv[yv == 1], st[yt == 1]), 4),
        "ks_nonfall_val_vs_test": round(ks_stat(sv[yv == 0], st[yt == 0]), 4),
        "val_auroc": round(auroc(yv, sv), 4),
        "test_auroc": round(auroc(yt, st), 4),
    })
write_csv(OUT / "diag_ks_val_vs_test.csv", ks_rows)

# ------------------------------------------- B. recall at FAR caps, three ways
cap_rows = []
for mid, d in data.items():
    yv, sv, _, _ = d["val"]
    yt, st, _, _ = d["test"]
    for cap in FAR_CAPS:
        frozen_tau = FROZEN.get(mid, {}).get(cap)
        if frozen_tau is None:
            sel = select_threshold(yv, sv, cap)
            tau, src = sel[1], "replicated_rule"
        else:
            tau, src = frozen_tau, "frozen_csv"
        tpv, fnv, fpv, tnv = confusion(yv, sv, tau)
        tpt, fnt, fpt, tnt = confusion(yt, st, tau)
        ph = posthoc_best(yt, st, cap)
        _, ph_tau, ph_tp, ph_fn, ph_fp, ph_tn = ph
        cap_rows.append({
            "method": mid, "far_cap": cap, "tau_source": src,
            "val_selected_tau": round(tau, 6),
            "val_recall": round(tpv / 44, 4), "val_FAR": round(fpv / 452, 4),
            "test_TP": tpt, "test_FN": fnt, "test_FP": fpt, "test_TN": tnt,
            "test_recall_frozen": round(tpt / 45, 4),
            "test_FAR_frozen": round(fpt / 455, 4),
            "recall_gap_val_minus_test": round(tpv / 44 - tpt / 45, 4),
            "FAR_gap_test_minus_val": round(fpt / 455 - fpv / 452, 4),
            "posthoc_test_tau": round(ph_tau, 6),
            "posthoc_test_recall": round(ph_tp / 45, 4),
            "posthoc_test_TP": ph_tp, "posthoc_test_FP": ph_fp,
            "posthoc_test_FAR": round(ph_fp / 455, 4),
        })
write_csv(OUT / "diag_recall_at_far_caps.csv", cap_rows)

# --------------------------------------------------- C. F20 feasibility window
f20_rows = []
for mid, d in data.items():
    yt, st, _, _ = d["test"]
    feas_taus = [tau for tau in sorted(set(st.tolist()))
                 if (lambda c: c[0] >= F20_TP_MIN and c[2] <= F20_FP_MAX)
                 (confusion(yt, st, tau))]
    fall_sorted = np.sort(st[yt == 1])[::-1]
    nf_sorted = np.sort(st[yt == 0])[::-1]
    fall_36th = float(fall_sorted[F20_TP_MIN - 1])      # tau must be <= this
    nf_92nd = float(nf_sorted[F20_FP_MAX])              # tau must be > this
    # max TP subject to FP <= 91 (oracle boundary)
    best_tp_at_fp91 = max(
        (confusion(yt, st, tau)[0] for tau in sorted(set(st.tolist()))
         if confusion(yt, st, tau)[2] <= F20_FP_MAX), default=0)
    f20_rows.append({
        "method": mid,
        "f20_feasible_on_test": bool(feas_taus),
        "n_feasible_candidate_taus": len(feas_taus),
        "feasible_tau_min": round(min(feas_taus), 6) if feas_taus else "",
        "feasible_tau_max": round(max(feas_taus), 6) if feas_taus else "",
        "tau_upper_bound_fall36th": round(fall_36th, 6),
        "tau_lower_bound_nf92nd": round(nf_92nd, 6),
        "window_width": round(fall_36th - nf_92nd, 6),
        "max_TP_at_FP_le_91": best_tp_at_fp91,
        "TP_shortfall_vs_36": F20_TP_MIN - best_tp_at_fp91,
    })
write_csv(OUT / "diag_f20_feasibility_on_test.csv", f20_rows)
key_numbers["f20_feasibility"] = f20_rows

# -------------------------------- D. threshold sensitivity near frozen 0.20 tau
sens_rows = []
DELTAS = [0.005, 0.01, 0.02, 0.05]
for mid, d in data.items():
    yt, st, _, _ = d["test"]
    tau0 = FROZEN[mid].get(0.20)
    tp0, fn0, fp0, tn0 = confusion(yt, st, tau0)
    for dlt in DELTAS:
        lo, hi = tau0 - dlt, tau0 + dlt
        in_band = (st >= lo) & (st < hi)
        tp_lo, _, fp_lo, _ = confusion(yt, st, lo)
        tp_hi, _, fp_hi, _ = confusion(yt, st, hi)
        sens_rows.append({
            "method": mid, "frozen_tau_far020": tau0, "delta": dlt,
            "TP_at_tau": tp0, "FP_at_tau": fp0,
            "n_fall_in_band": int(np.sum(in_band & (yt == 1))),
            "n_nonfall_in_band": int(np.sum(in_band & (yt == 0))),
            "TP_at_tau_minus_delta": tp_lo, "FP_at_tau_minus_delta": fp_lo,
            "TP_at_tau_plus_delta": tp_hi, "FP_at_tau_plus_delta": fp_hi,
        })
write_csv(OUT / "diag_threshold_sensitivity_far020.csv", sens_rows)

# --------------------------- E. FN / excess-FP distance from frozen 0.20 tau
dist_rows = []
for mid, d in data.items():
    yt, st, tt, pt = d["test"]
    tau0 = FROZEN[mid].get(0.20)
    fn_scores = st[(yt == 1) & (st < tau0)]
    fp_scores = st[(yt == 0) & (st >= tau0)]
    fn_dist = tau0 - fn_scores
    fp_dist = np.sort(fp_scores - tau0)  # ascending: most marginal first
    n_excess_fp = max(0, len(fp_scores) - F20_FP_MAX)
    # threshold move needed to reach TP >= 36, and FP cost of that move
    fall_sorted = np.sort(st[yt == 1])[::-1]
    tau_for_tp36 = float(fall_sorted[F20_TP_MIN - 1])
    fp_at_tau36 = confusion(yt, st, tau_for_tp36)[2]
    dist_rows.append({
        "method": mid, "frozen_tau_far020": tau0,
        "n_FN": len(fn_scores),
        "FN_dist_min": round(float(fn_dist.min()), 6) if len(fn_dist) else "",
        "FN_dist_median": round(float(np.median(fn_dist)), 6) if len(fn_dist) else "",
        "FN_dist_max": round(float(fn_dist.max()), 6) if len(fn_dist) else "",
        "n_FN_within_0p02_of_tau": int(np.sum(fn_dist <= 0.02)),
        "n_FN_beyond_0p10_of_tau": int(np.sum(fn_dist > 0.10)),
        "n_FP": len(fp_scores),
        "n_excess_FP_vs_91": n_excess_fp,
        "excess_FP_dist_above_tau_max_of_marginal":
            round(float(fp_dist[n_excess_fp - 1]), 6) if n_excess_fp else "",
        "tau_needed_for_TP36": round(tau_for_tp36, 6),
        "tau_move_needed_for_TP36": round(tau_for_tp36 - tau0, 6),
        "FP_at_tau_for_TP36": fp_at_tau36,
        "FP_overage_at_TP36": fp_at_tau36 - F20_FP_MAX,
    })
write_csv(OUT / "diag_fn_fp_distance_from_frozen_tau.csv", dist_rows)
key_numbers["fn_fp_distance"] = dist_rows

# ------------------------------------------- F. recall-drop decomposition
decomp_rows = []
for mid, d in data.items():
    yv, sv, _, _ = d["val"]
    yt, st, _, _ = d["test"]
    tau0 = FROZEN[mid].get(0.20)
    decomp_rows.append({
        "method": mid, "frozen_tau_far020": tau0,
        "val_fall_survival_at_tau": round(survival(sv[yv == 1], tau0), 4),
        "test_fall_survival_at_tau": round(survival(st[yt == 1], tau0), 4),
        "val_nonfall_survival_at_tau": round(survival(sv[yv == 0], tau0), 4),
        "test_nonfall_survival_at_tau": round(survival(st[yt == 0], tau0), 4),
    })
write_csv(OUT / "diag_recall_drop_decomposition.csv", decomp_rows)

# ------------------------------------------------- G. class-source diagnosis
cls_rows = []
def class_breakdown(mid, tag, yt, st, tt, pt, tau):
    fp_mask = (yt == 0) & (st >= tau)
    fn_mask = (yt == 1) & (st < tau)
    out = []
    classes, counts = np.unique(tt[yt == 0], return_counts=True)
    class_n = dict(zip(classes.tolist(), counts.tolist()))
    fp_cls, fp_counts = np.unique(tt[fp_mask], return_counts=True)
    for c, n in sorted(zip(fp_cls.tolist(), fp_counts.tolist()),
                       key=lambda x: -x[1]):
        out.append({"method": mid, "operating_point": tag, "tau": tau,
                    "kind": "false_alarm_source", "class": c, "count": n,
                    "class_total": class_n[c],
                    "class_rate": round(n / class_n[c], 4)})
    fn_dest, fn_counts = np.unique(pt[fn_mask], return_counts=True)
    for c, n in sorted(zip(fn_dest.tolist(), fn_counts.tolist()),
                       key=lambda x: -x[1]):
        out.append({"method": mid, "operating_point": tag, "tau": tau,
                    "kind": "missed_fall_destination", "class": c, "count": n,
                    "class_total": 45, "class_rate": round(n / 45, 4)})
    return out

for mid, d in data.items():
    yt, st, tt, pt = d["test"]
    cls_rows += class_breakdown(mid, "frozen_far020", yt, st, tt, pt,
                                FROZEN[mid][0.20])
yt, st, tt, pt = data["D8b_AFAC"]["test"]
cls_rows += class_breakdown("D8b_AFAC", "posthoc_F20_reference", yt, st, tt, pt,
                            D8B_POSTHOC_TAU)
write_csv(OUT / "diag_class_source_breakdown.csv", cls_rows)

# --------------------------------------------------------------- H. plots
COLORS = {"D8b_AFAC": "#1f77b4", "D10": "#d62728",
          "D11a": "#ff7f0e", "D11b": "#2ca02c"}

# H1: fall vs non-fall test score distributions
fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
for ax, (mid, d) in zip(axes.flat, data.items()):
    yt, st, _, _ = d["test"]
    bins = np.linspace(0, 1, 51)
    ax.hist(st[yt == 0], bins=bins, density=True, alpha=0.55,
            label="non-fall (n=455)", color="#7f7f7f")
    ax.hist(st[yt == 1], bins=bins, density=True, alpha=0.55,
            label="fall (n=45)", color=COLORS[mid])
    tau0 = FROZEN[mid][0.20]
    ax.axvline(tau0, color="k", ls="--", lw=1.2,
               label=f"frozen tau(0.20)={tau0:.3f}")
    ax.set_yscale("log")
    ax.set_title(d["label"], fontsize=10)
    ax.legend(fontsize=7)
    ax.set_xlabel("fall_probability (PGD test)")
fig.suptitle("Held-out test: fall vs non-fall score distributions (PGD eps=0.030)")
fig.tight_layout()
fig.savefig(OUT / "fall_vs_nonfall_test_score_distributions.png", dpi=150)
plt.close(fig)

# H2: validation vs test ECDFs
fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
for ax, (mid, d) in zip(axes.flat, data.items()):
    yv, sv, _, _ = d["val"]
    yt, st, _, _ = d["test"]
    for scores, lab, color, ls in [
        (sv[yv == 1], "val fall", COLORS[mid], "-"),
        (st[yt == 1], "test fall", COLORS[mid], "--"),
        (sv[yv == 0], "val non-fall", "#7f7f7f", "-"),
        (st[yt == 0], "test non-fall", "#7f7f7f", "--"),
    ]:
        xs = np.sort(scores)
        ax.step(xs, np.arange(1, len(xs) + 1) / len(xs), where="post",
                label=lab, color=color, ls=ls, lw=1.4)
    tau0 = FROZEN[mid][0.20]
    ax.axvline(tau0, color="k", ls=":", lw=1)
    ax.set_title(d["label"], fontsize=10)
    ax.legend(fontsize=7, loc="lower right")
    ax.set_xlabel("fall_probability")
    ax.set_ylabel("ECDF")
fig.suptitle("Validation vs held-out test score ECDFs (PGD eps=0.030); "
             "dotted line = frozen FAR-0.20 threshold")
fig.tight_layout()
fig.savefig(OUT / "val_vs_test_score_ecdf.png", dpi=150)
plt.close(fig)

# H3: TP and FP vs threshold near the FAR=0.20 operating region
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for ax, (mid, d) in zip(axes.flat, data.items()):
    yt, st, _, _ = d["test"]
    taus = np.linspace(0.0, 0.40, 801)
    tps = [confusion(yt, st, t)[0] for t in taus]
    fps = [confusion(yt, st, t)[2] for t in taus]
    ax.plot(taus, tps, color=COLORS[mid], label="test TP")
    ax.plot(taus, fps, color="#7f7f7f", label="test FP")
    ax.axhline(F20_TP_MIN, color=COLORS[mid], ls=":", lw=1,
               label=f"TP={F20_TP_MIN} (F20)")
    ax.axhline(F20_FP_MAX, color="#7f7f7f", ls=":", lw=1,
               label=f"FP={F20_FP_MAX} (F20)")
    tau0 = FROZEN[mid][0.20]
    ax.axvline(tau0, color="k", ls="--", lw=1.2, label=f"frozen tau={tau0:.3f}")
    feas = [t for t in taus
            if confusion(yt, st, t)[0] >= F20_TP_MIN
            and confusion(yt, st, t)[2] <= F20_FP_MAX]
    if feas:
        ax.axvspan(min(feas), max(feas), color="green", alpha=0.18,
                   label="F20-feasible tau")
    ax.set_title(d["label"], fontsize=10)
    ax.set_xlabel("threshold tau")
    ax.set_ylabel("count")
    ax.legend(fontsize=7)
fig.suptitle("Held-out test TP/FP vs threshold near FAR=0.20 "
             "(green band = tau region satisfying F20, if any)")
fig.tight_layout()
fig.savefig(OUT / "tp_fp_vs_threshold_near_far020.png", dpi=150)
plt.close(fig)

# H4: non-fall upper tail by true source class
fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
CLS_COLORS = {"run": "#d62728", "walk": "#ff7f0e", "stand up": "#2ca02c",
              "pickup": "#1f77b4", "lie down": "#9467bd", "sit down": "#8c564b"}
for ax, (mid, d) in zip(axes.flat, data.items()):
    yt, st, tt, _ = d["test"]
    taus = np.linspace(0.0, 0.40, 401)
    for cls in CLS_COLORS:
        mask = (yt == 0) & (tt == cls)
        if not mask.any():
            continue
        counts = [int(np.sum(st[mask] >= t)) for t in taus]
        ax.plot(taus, counts, label=f"{cls} (n={int(mask.sum())})",
                color=CLS_COLORS[cls], lw=1.4)
    tau0 = FROZEN[mid][0.20]
    ax.axvline(tau0, color="k", ls="--", lw=1.2)
    ax.set_title(d["label"], fontsize=10)
    ax.set_yscale("symlog", linthresh=1)
    ax.set_xlabel("threshold tau")
    ax.set_ylabel("# non-fall windows with score >= tau")
    ax.legend(fontsize=7)
fig.suptitle("Held-out test non-fall upper tail by true source class "
             "(dashed = frozen FAR-0.20 threshold)")
fig.tight_layout()
fig.savefig(OUT / "nonfall_upper_tail_by_source_class.png", dpi=150)
plt.close(fig)

# ----------------------------------------------------------- key numbers dump
key_numbers["recall_at_far_caps"] = cap_rows
key_numbers["threshold_sensitivity"] = sens_rows
key_numbers["recall_drop_decomposition"] = decomp_rows
key_numbers["ks_val_vs_test"] = ks_rows
with (OUT / "key_numbers.json").open("w", encoding="utf-8") as f:
    json.dump(key_numbers, f, indent=2)

print(json.dumps({"f20_feasibility": f20_rows,
                  "fn_fp_distance": dist_rows,
                  "decomposition": decomp_rows,
                  "ks": ks_rows}, indent=2))
print("\nWrote diagnostics to", OUT)
