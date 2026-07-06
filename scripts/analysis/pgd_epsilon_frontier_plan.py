"""
PGD-epsilon recall/FAR frontier — VALIDATION-ONLY, saved-scores-only.

Computes, for every saved defense score axis and every PGD epsilon with a saved
per-window VALIDATION probability export, the best validation recall at FAR caps
{0.10, 0.15, 0.20} under the frozen ledger threshold rule (max recall s.t.
FAR <= cap; tie-break lower FAR, then higher tau).

Available epsilon grid: {0.000 (clean condition = PGD eps->0 limit), 0.030}.
The epsilon-sweep prediction files under results/epsilon_sweep_predictions/ and
results/converged_attacks/ contain ARGMAX LABELS ONLY (no fall_probability), so
they cannot support FAR-cap threshold selection and are excluded (recorded in
missing_epsilon_artifacts.csv). No training, no checkpoint loading, no attack
generation, no test file opened.

Targets evaluated on validation:
  H15: recall > 0.85 AND FAR < 0.15  (checked at the cap-0.15 operating point)
  F20: recall >= 0.80 AND FAR <= 0.20 (checked at the cap-0.20 operating point)

Outputs (new files only):
  results/defense_attempt_inventory/pgd_epsilon_frontier/*.csv, *.png
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
OUT = RES / "defense_attempt_inventory" / "pgd_epsilon_frontier"
OUT.mkdir(parents=True, exist_ok=True)

SGD = RES / "safety_guided_defense"
BAS = SGD / "boundary_aware_selective_at"

CAPS = [0.10, 0.15, 0.20]
N_FALL, N_NONFALL = 44, 452
EPS_GRID = [("0.000", "clean"), ("0.030", "pgd")]
MISSING_EPS = ["0.005", "0.010", "0.015", "0.020", "0.025", "0.040", "0.050"]

# (model_id, family, representation, is_family_representative, pgd val export)
MODELS = [
    ("AFAC_maxscore", "AFAC_optionB", "lenet", True,
     RES / "afac_score_frozen_threshold_followup" / "val_eval"
     / "optionB_maxscore_pgd_probabilities_val_epsilon_0_03.csv"),
    ("AFAC_optBminFA", "AFAC_optionB", "lenet", False,
     SGD / "dual_specialist_safety_gate" / "A1" / "seed42" / "probabilities"
     / "B_optBminFA_pgd_probabilities_val_epsilon_0_03.csv"),
    ("GR1_macroF1", "GR1_gairat", "lenet", True,
     BAS / "gairat" / "seed42" / "GR1" / "val_eval"
     / "GR1_v2macroF1_pgd_probabilities_val_epsilon_0_03.csv"),
    ("GR1_lowFA", "GR1_gairat", "lenet", False,
     BAS / "gairat" / "seed42" / "GR1" / "val_eval"
     / "GR1_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv"),
    ("GR1_safety", "GR1_gairat", "lenet", False,
     BAS / "gairat" / "seed42" / "GR1" / "val_eval"
     / "GR1_v2safety_pgd_probabilities_val_epsilon_0_03.csv"),
    ("SA1_lowFA", "SA1_sat", "lenet", True,
     BAS / "sat" / "seed42" / "SA1" / "val_eval"
     / "SA1_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv"),
    ("SA1_macroF1", "SA1_sat", "lenet", False,
     BAS / "sat" / "seed42" / "SA1" / "val_eval"
     / "SA1_v2macroF1_pgd_probabilities_val_epsilon_0_03.csv"),
    ("SA1_safety", "SA1_sat", "lenet", False,
     BAS / "sat" / "seed42" / "SA1" / "val_eval"
     / "SA1_v2safety_pgd_probabilities_val_epsilon_0_03.csv"),
    ("ST1_lowFA", "ST1_beta3p0", "lenet", True,
     BAS / "seed42" / "beta3p0" / "val_eval"
     / "ST1_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv"),
    ("ST1_macroF1", "ST1_beta3p0", "lenet", False,
     BAS / "seed42" / "beta3p0" / "val_eval"
     / "ST1_v2macroF1_pgd_probabilities_val_epsilon_0_03.csv"),
    ("ST1_safety", "ST1_beta3p0", "lenet", False,
     BAS / "seed42" / "beta3p0" / "val_eval"
     / "ST1_v2safety_pgd_probabilities_val_epsilon_0_03.csv"),
    ("ST1b6_lowFA", "ST1b6_beta6p0", "lenet", True,
     BAS / "seed42" / "beta6p0" / "val_eval"
     / "ST1b6_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv"),
    ("ST1b6_macroF1", "ST1b6_beta6p0", "lenet", False,
     BAS / "seed42" / "beta6p0" / "val_eval"
     / "ST1b6_v2macroF1_pgd_probabilities_val_epsilon_0_03.csv"),
    ("ST1b6_safety", "ST1b6_beta6p0", "lenet", False,
     BAS / "seed42" / "beta6p0" / "val_eval"
     / "ST1b6_v2safety_pgd_probabilities_val_epsilon_0_03.csv"),
    ("D14B_seed44", "D14_pauc_rank", "lenet", True,
     RES / "d14_partial_auc_low_far_ranking" / "config_B" / "seed44" / "val_eval"
     / "d14_config_B_seed44_pgd_probabilities_val_epsilon_0_03.csv"),
    ("D14B_seed43", "D14_pauc_rank", "lenet", False,
     RES / "d14_partial_auc_low_far_ranking" / "config_B" / "seed43" / "val_eval"
     / "d14_config_B_seed43_pgd_probabilities_val_epsilon_0_03.csv"),
    ("VD_seed42", "variantD", "lenet", True,
     SGD / "decision_analysis" / "validation_probabilities"
     / "seed42_variantD_bySafetyScore_pgd_probabilities_val_epsilon_0_03.csv"),
    ("VD_seed43", "variantD", "lenet", False,
     SGD / "decision_analysis" / "validation_probabilities"
     / "seed43_variantD_bySafetyScore_pgd_probabilities_val_epsilon_0_03.csv"),
    ("G1_safety_s44", "G1_hardneg", "lenet", True,
     SGD / "variantG_targeted_hardneg" / "seed44" / "test_eval"
     / "G_G1_v2safety_pgd_probabilities_val_epsilon_0_03.csv"),
    ("G1_lowFA_s42", "G1_hardneg", "lenet", False,
     SGD / "dual_specialist_safety_gate" / "A1" / "seed42" / "probabilities"
     / "B_G1lowFA_pgd_probabilities_val_epsilon_0_03.csv"),
    ("G1_maxrec_s42", "G1_hardneg", "lenet", False,
     SGD / "dual_specialist_safety_gate" / "A1" / "seed42" / "probabilities"
     / "R_G1maxrec_pgd_probabilities_val_epsilon_0_03.csv"),
    ("BLF_macroF1", "BiLSTM_finetune", "bilstm", True,
     SGD / "variantG_bilstm_representation_test" / "seed42"
     / "g1_finetune_cleaninit" / "val_eval"
     / "BLF_v2macroF1_pgd_probabilities_val_epsilon_0_03.csv"),
    ("BLF_maxrec", "BiLSTM_finetune", "bilstm", False,
     SGD / "variantG_bilstm_representation_test" / "seed42"
     / "g1_finetune_cleaninit" / "val_eval"
     / "BLF_v2maxrec_pgd_probabilities_val_epsilon_0_03.csv"),
    ("BLF_safety", "BiLSTM_finetune", "bilstm", False,
     SGD / "variantG_bilstm_representation_test" / "seed42"
     / "g1_finetune_cleaninit" / "val_eval"
     / "BLF_v2safety_pgd_probabilities_val_epsilon_0_03.csv"),
]

# family rep -> checkpoint path (for the DESIGNED, NOT-RUN sweep commands)
CHECKPOINTS = {
    "AFAC_maxscore": "checkpoints/safety_guided_defense/variantH_dual_tail_budget/"
    "adaptive_lagrangian_far_constrained/optionB/seed42/seed42_optionB_maxscore_best.pt",
    "GR1_macroF1": "checkpoints/safety_guided_defense/boundary_aware_selective_at/"
    "gairat/seed42/GR1/seed42_basat_gairat_GR1_v2macroF1_best.pt",
    "SA1_lowFA": "checkpoints/safety_guided_defense/boundary_aware_selective_at/"
    "sat/seed42/SA1/seed42_basat_sat_SA1_v2lowFA_best.pt",
    "ST1b6_lowFA": "checkpoints/safety_guided_defense/boundary_aware_selective_at/"
    "seed42/beta6p0/seed42_basat_stage1_beta6p0_v2lowFA_best.pt",
}


def load(path: Path, condition: str):
    with path.open(newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["condition"] == condition]
    assert rows, f"no {condition} rows in {path}"
    sid = np.array([int(r["sample_id"]) for r in rows])
    y = np.array([int(r["fall_true_binary"]) for r in rows])
    s = np.array([float(r["fall_probability"]) for r in rows])
    order = np.argsort(sid)
    y, s = y[order], s[order]
    assert len(y) == 496 and int(y.sum()) == 44, f"{path} bad split shape"
    return y, s


def confusion(y, s, tau):
    pred = s >= tau
    return (int(np.sum(pred & (y == 1))), int(np.sum(~pred & (y == 1))),
            int(np.sum(pred & (y == 0))), int(np.sum(~pred & (y == 0))))


def select_tau(y, s, cap):
    best = None
    for tau in sorted(set(s.tolist()), reverse=True):
        tp, fn, fp, tn = confusion(y, s, tau)
        far = fp / N_NONFALL
        if far > cap:
            continue
        key = (tp / N_FALL, -far, tau)
        if best is None or key > best[0]:
            best = (key, tau)
    return best[1]


def auroc(y, s):
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), dtype=float)
    ss = s[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and ss[j + 1] == ss[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    n_pos = int(np.sum(y == 1))
    u = ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * (len(y) - n_pos))


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


# ------------------------------------------------------ frontier computation
frontier_rows = []
results = {}   # (mid, eps) -> {cap: (tau, tp, fn, fp, tn, recall, far), auroc}
for mid, fam, rep, is_rep, pgd_path in MODELS:
    clean_path = Path(str(pgd_path).replace("_pgd_probabilities_",
                                            "_clean_probabilities_"))
    for eps, cond in EPS_GRID:
        path = pgd_path if cond == "pgd" else clean_path
        y, s = load(path, cond)
        entry = {"auroc": round(auroc(y, s), 4)}
        row = {"model": mid, "family": fam, "representation": rep,
               "family_representative": is_rep, "epsilon": eps,
               "condition": cond}
        for cap in CAPS:
            tau = select_tau(y, s, cap)
            tp, fn, fp, tn = confusion(y, s, tau)
            entry[cap] = (tau, tp, fn, fp, tn, tp / N_FALL, fp / N_NONFALL)
            tag = f"far{int(cap * 100):02d}"
            row[f"tau_{tag}"] = round(tau, 6)
            row[f"recall_{tag}"] = round(tp / N_FALL, 4)
            row[f"FAR_{tag}"] = round(fp / N_NONFALL, 4)
            row[f"TP_{tag}"], row[f"FN_{tag}"] = tp, fn
            row[f"FP_{tag}"], row[f"TN_{tag}"] = fp, tn
        row["val_auroc"] = entry["auroc"]
        r15, f15 = entry[0.15][5], entry[0.15][6]
        r20, f20 = entry[0.20][5], entry[0.20][6]
        row["H15_pass_val"] = bool(r15 > 0.85 and f15 < 0.15)
        row["F20_pass_val"] = bool(r20 >= 0.80 and f20 <= 0.20)
        results[(mid, eps)] = entry | {"H15": row["H15_pass_val"],
                                       "F20": row["F20_pass_val"]}
        frontier_rows.append(row)
write_csv(OUT / "epsilon_frontier_by_model.csv", frontier_rows)

# --------------------------------------------------------- target boundaries
boundary_rows = []
grid = [e for e, _ in EPS_GRID]
for mid, fam, rep, is_rep, _ in MODELS:
    h15_pass = [e for e in grid if results[(mid, e)]["H15"]]
    f20_pass = [e for e in grid if results[(mid, e)]["F20"]]
    h15_fail = [e for e in grid if not results[(mid, e)]["H15"]]
    f20_fail = [e for e in grid if not results[(mid, e)]["F20"]]
    boundary_rows.append({
        "model": mid, "family": fam,
        "max_eps_H15_val": max(h15_pass) if h15_pass else "none",
        "max_eps_F20_val": max(f20_pass) if f20_pass else "none",
        "first_eps_H15_fails": min(h15_fail) if h15_fail else "none_on_grid",
        "first_eps_F20_fails": min(f20_fail) if f20_fail else "none_on_grid",
        "grid_note": "grid = {0.000 (clean), 0.030} only; boundary inside "
                     "(0.000, 0.030) UNRESOLVED without the designed sweep",
    })
write_csv(OUT / "epsilon_target_boundary.csv", boundary_rows)

# ------------------------------------------------------- missing artifacts
missing_rows = []
for mid in ["AFAC_maxscore", "GR1_macroF1", "SA1_lowFA", "ST1b6_lowFA",
            "ST1_lowFA", "D14B_seed44", "G1_safety_s44", "VD_seed42",
            "BLF_macroF1"]:
    missing_rows.append({
        "model": mid,
        "missing_epsilon_values": ";".join(MISSING_EPS),
        "missing_split": "val (per-window fall-probability export)",
        "regenerable_validation_only": "yes - checkpoint exists; "
        "export_probability_predictions.py --split val (NOT RUN; needs approval)",
    })
missing_rows.append({
    "model": "undefended converged baseline (seeds 42/43/44)",
    "missing_epsilon_values": "ALL (0.000-0.075)",
    "missing_split": "val - existing sweep files are argmax-only "
    "(no fall_probability) and on short/test splits",
    "regenerable_validation_only": "yes - checkpoints exist; same export script",
})
write_csv(OUT / "missing_epsilon_artifacts.csv", missing_rows)

# ------------------------------------------------------------------- plots
reps = [(m[0], m[1]) for m in MODELS if m[3]]
cmap = plt.get_cmap("tab10")
rep_color = {mid: cmap(i % 10) for i, (mid, _) in enumerate(reps)}
xs = [float(e) for e in grid]

for cap in CAPS:
    fig, ax = plt.subplots(figsize=(9, 6))
    for mid, fam, repname, is_rep, _ in MODELS:
        ys = [results[(mid, e)][cap][5] for e in grid]
        if is_rep:
            ax.plot(xs, ys, "-o", color=rep_color[mid], lw=1.6,
                    label=f"{fam} ({mid})")
        else:
            ax.plot(xs, ys, "-", color="0.8", lw=0.8, zorder=0)
    if cap == 0.15:
        ax.axhline(0.85, color="k", ls="--", lw=1, label="H15 recall bar (>0.85)")
    if cap == 0.20:
        ax.axhline(0.80, color="k", ls="--", lw=1, label="F20 recall bar (>=0.80)")
    ax.axvspan(0.0005, 0.0295, color="orange", alpha=0.08)
    ax.text(0.015, 0.05, "no saved val artifacts\n(unresolved band)",
            ha="center", fontsize=8, color="darkorange")
    ax.set_xlabel("PGD epsilon (0.000 = clean condition)")
    ax.set_ylabel(f"validation recall at FAR <= {cap:.2f}")
    ax.set_title(f"Validation recall vs PGD epsilon at FAR cap {cap:.2f} "
                 "(saved artifacts only: eps in {0.000, 0.030})")
    ax.set_ylim(0, 1.02)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / f"recall_vs_epsilon_far{int(cap * 100):02d}.png", dpi=150)
    plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 6))
for mid, fam, repname, is_rep, _ in MODELS:
    ys = [results[(mid, e)]["auroc"] for e in grid]
    if is_rep:
        ax.plot(xs, ys, "-o", color=rep_color[mid], lw=1.6,
                label=f"{fam} ({mid})")
    else:
        ax.plot(xs, ys, "-", color="0.8", lw=0.8, zorder=0)
ax.axvspan(0.0005, 0.0295, color="orange", alpha=0.08)
ax.set_xlabel("PGD epsilon (0.000 = clean condition)")
ax.set_ylabel("validation AUROC (fall score)")
ax.set_title("Validation AUROC vs PGD epsilon (saved artifacts only)")
ax.legend(fontsize=7)
fig.tight_layout()
fig.savefig(OUT / "auroc_vs_epsilon.png", dpi=150)
plt.close(fig)

# target boundary pass/fail plot (family representatives)
fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
for ax, target in zip(axes, ["H15", "F20"]):
    for i, (mid, fam) in enumerate(reps):
        for e in grid:
            ok = results[(mid, e)][target]
            ax.scatter(float(e), i, marker="s", s=140,
                       color="#2ca02c" if ok else "#d62728", zorder=3)
    ax.axvspan(0.0005, 0.0295, color="orange", alpha=0.12)
    ax.set_yticks(range(len(reps)))
    ax.set_yticklabels([f"{fam}" for _, fam in reps], fontsize=8)
    ax.set_title(f"{target} pass (green) / fail (red) on validation; "
                 "orange band = no saved artifacts (boundary unresolved)",
                 fontsize=10)
axes[1].set_xlabel("PGD epsilon (0.000 = clean condition)")
fig.suptitle("H15 / F20 validation pass-fail regions vs PGD epsilon "
             "(family representatives)")
fig.tight_layout()
fig.savefig(OUT / "target_boundary_plot.png", dpi=150)
plt.close(fig)

# ------------------------------------------------------------- key numbers
summary = {
    "grid": grid,
    "any_H15_at_0.000": sorted({m for (m, e), r in results.items()
                                if e == "0.000" and r["H15"]}),
    "any_H15_at_0.030": sorted({m for (m, e), r in results.items()
                                if e == "0.030" and r["H15"]}),
    "any_F20_at_0.000": sorted({m for (m, e), r in results.items()
                                if e == "0.000" and r["F20"]}),
    "any_F20_at_0.030": sorted({m for (m, e), r in results.items()
                                if e == "0.030" and r["F20"]}),
}
with (OUT / "frontier_key_numbers.json").open("w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
print("\nWrote frontier outputs to", OUT)
