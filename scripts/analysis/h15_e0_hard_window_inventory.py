"""
H15-E0 — Phase 0 hard-window inventory + cross-model union-oracle audit.

VALIDATION-ONLY, saved-scores-only. No training, no checkpoint loading, no attack
generation, no test-split file is opened, read, or referenced. Union/oracle numbers
are DIAGNOSTIC ONLY (non-deployable): they answer whether the fall windows H15 needs
are separable by ANY existing model, not whether any deployable rule achieves it.

Operating rule (validation-only, from the pre-registered H15 roadmap Gate 0):
per-model threshold tau_m = max val recall s.t. val FAR <= cap (primary cap 0.12,
FP <= 54/452), tie-break lower FAR then higher tau — the same frozen rule used by
every committed selection in this ledger. "Hard fall" for model m = fall window with
score < tau_m. "Hard non-fall" for model m = non-fall window with score >= tau_m.

Inputs: the 24 saved `*_pgd_probabilities_val_epsilon_0_03.csv` exports (9 training
families, 2 representations). Alignment is asserted via identical true-class
sequences (sample_id order) before any cross-model set operation.

Outputs (new files only):
  results/defense_attempt_inventory/h15_e0_hard_window_inventory/*.csv, *.png,
  h15_e0_key_numbers.json
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
OUT = RES / "defense_attempt_inventory" / "h15_e0_hard_window_inventory"
OUT.mkdir(parents=True, exist_ok=True)

SGD = RES / "safety_guided_defense"
BAS = SGD / "boundary_aware_selective_at"

PRIMARY_CAP = 0.12
CAPS = [0.10, 0.12, 0.15]
GATE_TP = 40   # Gate 0(a): union-oracle val recall >= 40/44
N_FALL = 44
N_NONFALL = 452

# (model_id, family, representation, is_family_representative, path)
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
     SGD / "variantG_bilstm_representation_test" / "seed42" / "g1_finetune_cleaninit"
     / "val_eval" / "BLF_v2macroF1_pgd_probabilities_val_epsilon_0_03.csv"),
    ("BLF_maxrec", "BiLSTM_finetune", "bilstm", False,
     SGD / "variantG_bilstm_representation_test" / "seed42" / "g1_finetune_cleaninit"
     / "val_eval" / "BLF_v2maxrec_pgd_probabilities_val_epsilon_0_03.csv"),
    ("BLF_safety", "BiLSTM_finetune", "bilstm", False,
     SGD / "variantG_bilstm_representation_test" / "seed42" / "g1_finetune_cleaninit"
     / "val_eval" / "BLF_v2safety_pgd_probabilities_val_epsilon_0_03.csv"),
]


LABEL_TO_NAME = {"0": "lie down", "1": "fall", "2": "walk", "3": "pickup",
                 "4": "run", "5": "sit down", "6": "stand up"}


def load(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["condition"] == "pgd"]
    sid = np.array([int(r["sample_id"]) for r in rows])
    y = np.array([int(r["fall_true_binary"]) for r in rows])
    s = np.array([float(r["fall_probability"]) for r in rows])
    tc = np.array([r["true_class_name"] for r in rows])
    if "predicted_class_name" in rows[0]:
        pc = np.array([r["predicted_class_name"] for r in rows])
    else:  # reduced schema (variantD decision_analysis exports)
        pc = np.array([LABEL_TO_NAME[r["predicted_label"]] for r in rows])
    # sanity: label->name mapping must agree with this file's own true columns
    for r in rows[:200]:
        assert LABEL_TO_NAME[r["true_label"]] == r["true_class_name"], path
    order = np.argsort(sid)
    return sid[order], y[order], s[order], tc[order], pc[order]


def confusion(y, s, tau):
    pred = s >= tau
    return (int(np.sum(pred & (y == 1))), int(np.sum(~pred & (y == 1))),
            int(np.sum(pred & (y == 0))), int(np.sum(~pred & (y == 0))))


def select_tau(y, s, cap):
    """Frozen ledger rule: max recall s.t. FAR <= cap; tie lower FAR, higher tau."""
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


# ------------------------------------------------ load + alignment assertion
data = {}
ref = None
for mid, fam, rep, is_rep, path in MODELS:
    sid, y, s, tc, pc = load(path)
    assert len(y) == 496 and int(y.sum()) == 44, f"{mid}: bad split shape"
    if ref is None:
        ref = (sid, tc)
    else:
        assert np.array_equal(ref[0], sid), f"{mid}: sample_id mismatch"
        assert np.array_equal(ref[1], tc), f"{mid}: true-class sequence mismatch"
    data[mid] = {"family": fam, "rep": rep, "is_rep": is_rep,
                 "y": y, "s": s, "tc": tc, "pc": pc, "path": str(path)}

SID, TC = ref
Y = data[MODELS[0][0]]["y"]
FALL_IDS = SID[Y == 1]
NF_IDS = SID[Y == 0]
model_ids = [m[0] for m in MODELS]
family_reps = [m[0] for m in MODELS if m[3]]
families = sorted({m[1] for m in MODELS})

key = {"n_models": len(model_ids), "n_families": len(families),
       "primary_cap": PRIMARY_CAP}

# --------------------------------------- per-model taus / hard sets (all caps)
taus = {}          # (mid, cap) -> tau
hard_fall = {}     # (mid, cap) -> set of fall sample_ids missed
hard_nf = {}       # (mid, cap) -> set of non-fall sample_ids alarmed
metrics_rows = []
for mid in model_ids:
    d = data[mid]
    for cap in CAPS:
        tau = select_tau(d["y"], d["s"], cap)
        taus[(mid, cap)] = tau
        miss = set(SID[(d["y"] == 1) & (d["s"] < tau)].tolist())
        alarm = set(SID[(d["y"] == 0) & (d["s"] >= tau)].tolist())
        hard_fall[(mid, cap)] = miss
        hard_nf[(mid, cap)] = alarm
        tp, fn, fp, tn = confusion(d["y"], d["s"], tau)
        metrics_rows.append({
            "model": mid, "family": d["family"], "representation": d["rep"],
            "family_representative": d["is_rep"], "far_cap": cap,
            "tau": round(tau, 6), "TP": tp, "FN": fn, "FP": fp, "TN": tn,
            "recall": round(tp / N_FALL, 4), "FAR": round(fp / N_NONFALL, 4),
            "val_pgd_auroc": round(auroc(d["y"], d["s"]), 4),
        })
write_csv(OUT / "per_model_operating_points.csv", metrics_rows)

# ------------------------------------------------- CSV 1: hard fall windows
rank_fall = {}  # mid -> {sample_id: rank among falls, 1 = highest score}
for mid in model_ids:
    d = data[mid]
    fs = d["s"][d["y"] == 1]
    order = np.argsort(-fs, kind="mergesort")
    r = np.empty(len(fs), dtype=int)
    r[order] = np.arange(1, len(fs) + 1)
    rank_fall[mid] = dict(zip(FALL_IDS.tolist(), r.tolist()))

rows1 = []
for mid in model_ids:
    d = data[mid]
    tau = taus[(mid, PRIMARY_CAP)]
    for i in np.where(d["y"] == 1)[0]:
        if d["s"][i] < tau:
            rows1.append({
                "split": "val", "sample_id": int(SID[i]), "true_class": TC[i],
                "model": mid, "family": d["family"],
                "representation": d["rep"],
                "fall_score": round(float(d["s"][i]), 6),
                "predicted_class": d["pc"][i],
                "below_operating_threshold": True,
                "operating_threshold_far012": round(tau, 6),
                "rank_among_falls_desc": rank_fall[mid][int(SID[i])],
            })
write_csv(OUT / "hard_fall_windows_by_model.csv",
          sorted(rows1, key=lambda r: (r["sample_id"], r["model"])))

# --------------------------------------------- CSV 2: hard non-fall windows
rank_nf = {}
for mid in model_ids:
    d = data[mid]
    ns = d["s"][d["y"] == 0]
    order = np.argsort(-ns, kind="mergesort")
    r = np.empty(len(ns), dtype=int)
    r[order] = np.arange(1, len(ns) + 1)
    rank_nf[mid] = dict(zip(NF_IDS.tolist(), r.tolist()))

rows2 = []
for mid in model_ids:
    d = data[mid]
    tau = taus[(mid, PRIMARY_CAP)]
    for i in np.where(d["y"] == 0)[0]:
        if d["s"][i] >= tau:
            rows2.append({
                "split": "val", "sample_id": int(SID[i]), "true_class": TC[i],
                "model": mid, "family": d["family"],
                "representation": d["rep"],
                "fall_score": round(float(d["s"][i]), 6),
                "predicted_class": d["pc"][i],
                "above_operating_threshold": True,
                "operating_threshold_far012": round(tau, 6),
                "rank_among_nonfalls_desc": rank_nf[mid][int(SID[i])],
            })
write_csv(OUT / "hard_nonfall_windows_by_model.csv",
          sorted(rows2, key=lambda r: (r["sample_id"], r["model"])))

# --------------------------------- CSV 3: cross-model hard-window overlap
def overlap_rows(kind, universe_ids, hard_sets):
    rows = []
    for wid in universe_ids.tolist():
        models_hard = [mid for mid in model_ids if wid in hard_sets[(mid, PRIMARY_CAP)]]
        if not models_hard:
            continue
        fams_hard = sorted({data[m]["family"] for m in models_hard})
        scores = np.array([float(data[m]["s"][SID == wid][0]) for m in model_ids])
        frac_models = len(models_hard) / len(model_ids)
        frac_fams = len(fams_hard) / len(families)
        if frac_fams == 1.0:
            interp = "universal_hard"
        elif frac_models >= 0.5:
            interp = "mostly_hard_rescued_by_some_model"
        else:
            interp = "model_specific"
        rows.append({
            "kind": kind, "sample_id": wid,
            "true_class": str(TC[SID == wid][0]),
            "n_models_hard": len(models_hard),
            "n_families_hard": len(fams_hard),
            "models_hard": ";".join(models_hard),
            "families_hard": ";".join(fams_hard),
            "mean_fall_score_all_models": round(float(scores.mean()), 6),
            "max_fall_score_all_models": round(float(scores.max()), 6),
            "min_fall_score_all_models": round(float(scores.min()), 6),
            "interpretation": interp,
        })
    return sorted(rows, key=lambda r: (-r["n_families_hard"], -r["n_models_hard"],
                                       r["sample_id"]))

rows3 = overlap_rows("hard_fall", FALL_IDS, hard_fall) \
      + overlap_rows("hard_nonfall", NF_IDS, hard_nf)
write_csv(OUT / "cross_model_hard_window_overlap.csv", rows3)

univ_falls = [r for r in rows3 if r["kind"] == "hard_fall"
              and r["interpretation"] == "universal_hard"]
key["universal_hard_falls"] = [(r["sample_id"], r["mean_fall_score_all_models"],
                                r["max_fall_score_all_models"]) for r in univ_falls]
key["n_universal_hard_falls"] = len(univ_falls)
key["n_hard_falls_any_model"] = sum(1 for r in rows3 if r["kind"] == "hard_fall")
univ_nf = [r for r in rows3 if r["kind"] == "hard_nonfall"
           and r["interpretation"] == "universal_hard"]
key["n_universal_hard_nonfalls"] = len(univ_nf)
key["n_hard_nonfalls_any_model"] = sum(1 for r in rows3 if r["kind"] == "hard_nonfall")

# ------------------------------------- CSV 4: validation union-oracle summary
WARN = ("DIAGNOSTIC ONLY - oracle/union uses per-model thresholds with hindsight "
        "window assignment; NOT deployable evidence; cannot claim any operating point")
rows4 = []
model_sets = {
    "all_24_score_axes": model_ids,
    "one_per_family_9": family_reps,
    "lenet_families_only_8": [m for m in family_reps
                              if data[m]["rep"] == "lenet"],
    "d13_trio_AFAC_D10_D11b": ["AFAC_maxscore", "GR1_macroF1", "SA1_lowFA"],
}
for set_name, mids in model_sets.items():
    for cap in CAPS:
        best_single = max(mids, key=lambda m: N_FALL - len(hard_fall[(m, cap)]))
        best_tp = N_FALL - len(hard_fall[(best_single, cap)])
        union_hit = set(FALL_IDS.tolist())
        for m in mids:
            union_hit -= set()  # keep type
        missed_by_all = set(FALL_IDS.tolist())
        for m in mids:
            missed_by_all &= hard_fall[(m, cap)]
        union_tp = N_FALL - len(missed_by_all)
        union_fp_pess = len(set().union(*[hard_nf[(m, cap)] for m in mids]))
        rows4.append({
            "model_set": set_name, "n_models": len(mids), "far_cap": cap,
            "fp_budget_per_model": int(np.floor(cap * N_NONFALL)),
            "best_single_model": best_single,
            "best_single_TP": best_tp,
            "best_single_recall": round(best_tp / N_FALL, 4),
            "union_oracle_TP": union_tp,
            "union_oracle_recall": round(union_tp / N_FALL, 4),
            "falls_missed_by_every_model": len(missed_by_all),
            "union_of_FP_sets_pessimistic": union_fp_pess,
            "h15_gate_feasible_TP_ge_40_at_cap_012":
                (cap == PRIMARY_CAP and union_tp >= GATE_TP),
            "warning": WARN,
        })
write_csv(OUT / "validation_union_oracle_summary.csv", rows4)
key["union_oracle"] = [
    {k: v for k, v in r.items() if k != "warning"} for r in rows4]

# per-representative rescue fraction (Gate 0(b))
rescue_rows = []
for m in family_reps:
    miss = hard_fall[(m, PRIMARY_CAP)]
    if not miss:
        rescue_rows.append({"model": m, "n_missed": 0, "n_rescued_elsewhere": 0,
                            "rescue_fraction": ""})
        continue
    rescued = sum(
        1 for wid in miss
        if any(wid not in hard_fall[(m2, PRIMARY_CAP)] for m2 in model_ids
               if m2 != m))
    rescue_rows.append({"model": m, "n_missed": len(miss),
                        "n_rescued_elsewhere": rescued,
                        "rescue_fraction": round(rescued / len(miss), 4)})
write_csv(OUT / "per_model_fall_rescue_fraction.csv", rescue_rows)
key["rescue_fractions"] = rescue_rows

# --------------------------- CSV 5: class-source hard-negative summary
rows5 = []
union_hard_nf = sorted(set().union(*[hard_nf[(m, PRIMARY_CAP)]
                                     for m in model_ids]))
total = len(union_hard_nf)
by_class = {}
for wid in union_hard_nf:
    cls = str(TC[SID == wid][0])
    by_class.setdefault(cls, []).append(wid)
for cls, wids in sorted(by_class.items(), key=lambda kv: -len(kv[1])):
    scores = []
    fam_counts = {}
    for wid in wids:
        for m in model_ids:
            if wid in hard_nf[(m, PRIMARY_CAP)]:
                scores.append(float(data[m]["s"][SID == wid][0]))
                fam_counts[data[m]["family"]] = fam_counts.get(
                    data[m]["family"], 0) + 1
    fam_str = ";".join(f"{f}:{c}" for f, c in
                       sorted(fam_counts.items(), key=lambda kv: -kv[1]))
    n_class_total = int(np.sum(TC[Y == 0] == cls))
    rows5.append({
        "true_nonfall_class": cls, "class_total_in_val": n_class_total,
        "n_hard_negatives_union": len(wids),
        "share_of_union_hard_negatives": round(len(wids) / total, 4),
        "class_rate": round(len(wids) / n_class_total, 4),
        "avg_fall_score_when_hard": round(float(np.mean(scores)), 6),
        "max_fall_score_when_hard": round(float(np.max(scores)), 6),
        "families_producing_them_with_counts": fam_str,
    })
write_csv(OUT / "class_source_hard_negative_summary.csv", rows5)
key["hard_negative_class_summary"] = [
    {k: r[k] for k in ("true_nonfall_class", "n_hard_negatives_union",
                       "share_of_union_hard_negatives", "class_rate")}
    for r in rows5]

# -------------------------------------------------------------------- plots
def jaccard(a, b):
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)

# P1: hard-fall overlap — window x family binary matrix + family Jaccard
fig, axes = plt.subplots(1, 2, figsize=(15, 6),
                         gridspec_kw={"width_ratios": [2.2, 1]})
fam_hard_fall = {f: set() for f in families}
for m in family_reps:
    fam_hard_fall[data[m]["family"]] = hard_fall[(m, PRIMARY_CAP)]
hard_any = sorted(set().union(*fam_hard_fall.values()))
M = np.array([[1 if wid in fam_hard_fall[f] else 0 for wid in hard_any]
              for f in families])
im = axes[0].imshow(M, aspect="auto", cmap="Reds", vmin=0, vmax=1)
axes[0].set_yticks(range(len(families)))
axes[0].set_yticklabels(families, fontsize=8)
axes[0].set_xticks(range(len(hard_any)))
axes[0].set_xticklabels(hard_any, fontsize=6, rotation=90)
axes[0].set_xlabel("fall window sample_id (hard for >=1 family rep, FAR cap 0.12)")
axes[0].set_title("Hard-fall windows by family (red = missed)", fontsize=10)
J = np.array([[jaccard(fam_hard_fall[f1], fam_hard_fall[f2])
               for f2 in families] for f1 in families])
im2 = axes[1].imshow(J, cmap="viridis", vmin=0, vmax=1)
axes[1].set_xticks(range(len(families)))
axes[1].set_xticklabels(families, fontsize=7, rotation=90)
axes[1].set_yticks(range(len(families)))
axes[1].set_yticklabels(families, fontsize=7)
axes[1].set_title("Hard-fall set Jaccard (family reps)", fontsize=10)
for i in range(len(families)):
    for j in range(len(families)):
        axes[1].text(j, i, f"{J[i, j]:.2f}", ha="center", va="center",
                     fontsize=6, color="w" if J[i, j] < 0.6 else "k")
fig.colorbar(im2, ax=axes[1], shrink=0.8)
fig.suptitle("H15-E0: hard fall-window overlap across model families "
             "(validation, per-family FAR<=0.12 thresholds)")
fig.tight_layout()
fig.savefig(OUT / "hard_fall_overlap_heatmap.png", dpi=150)
plt.close(fig)

# P2: hard non-fall Jaccard heatmap (family reps)
fam_hard_nf = {data[m]["family"]: hard_nf[(m, PRIMARY_CAP)] for m in family_reps}
fig, ax = plt.subplots(figsize=(8, 7))
J = np.array([[jaccard(fam_hard_nf[f1], fam_hard_nf[f2])
               for f2 in families] for f1 in families])
im = ax.imshow(J, cmap="viridis", vmin=0, vmax=1)
ax.set_xticks(range(len(families)))
ax.set_xticklabels(families, fontsize=8, rotation=90)
ax.set_yticks(range(len(families)))
ax.set_yticklabels(families, fontsize=8)
for i in range(len(families)):
    for j in range(len(families)):
        ax.text(j, i, f"{J[i, j]:.2f}", ha="center", va="center",
                fontsize=7, color="w" if J[i, j] < 0.6 else "k")
fig.colorbar(im, ax=ax, shrink=0.8)
ax.set_title("H15-E0: hard non-fall (false-alarm) set Jaccard across families\n"
             "(validation, per-family FAR<=0.12 thresholds)")
fig.tight_layout()
fig.savefig(OUT / "hard_nonfall_overlap_heatmap.png", dpi=150)
plt.close(fig)

# P3: validation recall-vs-FAR curves by family rep
fig, ax = plt.subplots(figsize=(9, 6))
for m in family_reps:
    d = data[m]
    caps_grid = np.linspace(0.0, 0.30, 121)
    recalls = []
    for cap in caps_grid:
        fp_budget = int(np.floor(cap * N_NONFALL))
        nf_sorted = np.sort(d["s"][d["y"] == 0])[::-1]
        tau = nf_sorted[fp_budget] + 1e-12 if fp_budget < len(nf_sorted) else 0.0
        recalls.append(np.mean(d["s"][d["y"] == 1] > tau))
    ls = "--" if d["rep"] == "bilstm" else "-"
    ax.plot(caps_grid, recalls, label=f"{d['family']} ({m})", lw=1.4, ls=ls)
ax.axvline(0.12, color="k", ls=":", lw=1)
ax.axhline(40 / 44, color="k", ls=":", lw=1)
ax.annotate("H15 val gate (0.909 @ 0.12)", xy=(0.12, 40 / 44),
            xytext=(0.16, 0.95), fontsize=8,
            arrowprops=dict(arrowstyle="->", lw=0.8))
ax.set_xlabel("validation FAR")
ax.set_ylabel("validation PGD fall recall")
ax.set_title("H15-E0: validation recall vs FAR by family representative "
             "(PGD eps=0.030)")
ax.legend(fontsize=7)
fig.tight_layout()
fig.savefig(OUT / "val_recall_vs_far_by_model.png", dpi=150)
plt.close(fig)

# P4: union-oracle curve vs best single (family reps)
fig, ax = plt.subplots(figsize=(9, 6))
caps_grid = np.linspace(0.02, 0.30, 57)
best_curve, union_curve = [], []
for cap in caps_grid:
    per_model_hits = []
    for m in family_reps:
        d = data[m]
        tau = select_tau(d["y"], d["s"], cap)
        per_model_hits.append(set(SID[(d["y"] == 1) & (d["s"] >= tau)].tolist()))
    best_curve.append(max(len(h) for h in per_model_hits) / N_FALL)
    union_curve.append(len(set().union(*per_model_hits)) / N_FALL)
ax.plot(caps_grid, best_curve, label="best single family rep", color="#1f77b4")
ax.plot(caps_grid, union_curve, label="union ORACLE (diagnostic only)",
        color="#d62728")
ax.fill_between(caps_grid, best_curve, union_curve, color="#d62728", alpha=0.12)
ax.axvline(0.12, color="k", ls=":", lw=1)
ax.axhline(40 / 44, color="k", ls=":", lw=1)
ax.set_xlabel("validation FAR cap (per-model threshold)")
ax.set_ylabel("validation PGD fall recall")
ax.set_title("H15-E0: union oracle vs best single model (validation only; "
             "oracle = non-deployable diagnostic)")
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(OUT / "union_oracle_vs_best_single.png", dpi=150)
plt.close(fig)

# P5: hard non-fall class-source bar plot
fig, ax = plt.subplots(figsize=(8, 5))
classes = [r["true_nonfall_class"] for r in rows5]
counts = [r["n_hard_negatives_union"] for r in rows5]
rates = [r["class_rate"] for r in rows5]
bars = ax.bar(classes, counts, color="#7f7f7f")
for b, rate in zip(bars, rates):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5,
            f"rate {rate:.2f}", ha="center", fontsize=8)
ax.set_ylabel("# union hard-negative windows (FAR cap 0.12, any model)")
ax.set_title("H15-E0: hard non-fall windows by true source class (validation)")
fig.tight_layout()
fig.savefig(OUT / "hard_negative_class_source_bar.png", dpi=150)
plt.close(fig)

# BiLSTM complementarity check: does the alternate representation rescue
# LeNet-universal misses, and at what FP overlap?
lenet_reps = [m for m in family_reps if data[m]["rep"] == "lenet"]
lenet_missed_by_all = set(FALL_IDS.tolist())
for m in lenet_reps:
    lenet_missed_by_all &= hard_fall[(m, PRIMARY_CAP)]
blf_miss = hard_fall[("BLF_macroF1", PRIMARY_CAP)]
key["lenet_universal_misses"] = sorted(lenet_missed_by_all)
key["lenet_universal_misses_rescued_by_bilstm"] = sorted(
    lenet_missed_by_all - blf_miss)
lenet_fp_union = set().union(*[hard_nf[(m, PRIMARY_CAP)] for m in lenet_reps])
blf_fp = hard_nf[("BLF_macroF1", PRIMARY_CAP)]
key["bilstm_fp_jaccard_vs_lenet_union"] = round(jaccard(blf_fp, lenet_fp_union), 4)
key["bilstm_new_fps_not_in_lenet_union"] = len(blf_fp - lenet_fp_union)

with (OUT / "h15_e0_key_numbers.json").open("w", encoding="utf-8") as f:
    json.dump(key, f, indent=2)
print(json.dumps(key, indent=2))
print("\nWrote H15-E0 outputs to", OUT)
