"""
Math-to-behavior diagnostic audit (analysis-only) for Variant E + selection-v2.

Reads existing artifacts (training logs, prediction/probability CSVs with per-class
logits, epsilon sweeps) and emits the derived CSVs + figures for the audit. No
training, no model loading, no attacks. Writes ONLY under the diagnostic_audit/
namespace. Sections 13 (stronger PGD) and 14 (embeddings) are handled separately.

Command: python scripts/audit_core.py
"""
from __future__ import annotations
from pathlib import Path
import csv, glob, math, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

EXP = Path(__file__).resolve().parents[1]
SG = EXP / "results" / "safety_guided_defense"
AUD = SG / "variantE_motion_hard_negative" / "selection_v2" / "diagnostic_audit"
FIG = AUD / "figures"
AUD.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
CLASS = {0: "lie down", 1: "fall", 2: "walk", 3: "pickup", 4: "run", 5: "sit down", 6: "stand up"}
NONFALL = [0, 2, 3, 4, 5, 6]; WALK, RUN, FALL = 2, 4, 1
NFALL_TEST = 45  # test fall windows


def rows(p):
    p = Path(p)
    if not p.exists():
        return None
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---- model registry: per seed, label -> dict(pred, prob, sweep, val) ----
def registry(N):
    ca = EXP / "results" / "converged_attacks"
    d_te = SG / f"seed{N}" / "test_eval"
    e_te = SG / "variantE_motion_hard_negative" / f"seed{N}" / "test_eval"
    v2 = SG / "variantE_motion_hard_negative" / "selection_v2" / f"seed{N}" / "test_eval"
    d_prob = (SG / "decision_analysis" / "seed42_test_probabilities" / "seed42_variantD_bySafetyScore") if N == 42 else (d_te / "variantD_bySafetyScore")
    reg = {
        "FGSM_defense": dict(pred=ca / f"defended_fgsm_at_seed{N}_pgd_predictions_test_epsilon_0_03.csv",
                             prob=None, sweep=ca / f"defended_fgsm_at_seed{N}_pgd_epsilon_sweep_test.csv"),
        "D_safety": dict(pred=d_te / "variantD_bySafetyScore_pgd_predictions_test_epsilon_0_03.csv",
                         prob=Path(f"{d_prob}_pgd_probabilities_test_epsilon_0_03.csv"),
                         sweep=d_te / "variantD_bySafetyScore_pgd_epsilon_sweep_test.csv"),
        "priorE_safety": dict(pred=e_te / "E_lam1p0_bySafetyScore_pgd_predictions_test_epsilon_0_03.csv",
                              prob=e_te / "E_lam1p0_bySafetyScore_pgd_probabilities_test_epsilon_0_03.csv",
                              sweep=e_te / "E_lam1p0_bySafetyScore_pgd_epsilon_sweep_test.csv"),
        "priorE_macroF1": dict(pred=e_te / "E_lam1p0_byValMacroF1_pgd_predictions_test_epsilon_0_03.csv",
                               prob=e_te / "E_lam1p0_byValMacroF1_pgd_probabilities_test_epsilon_0_03.csv",
                               sweep=e_te / "E_lam1p0_byValMacroF1_pgd_epsilon_sweep_test.csv"),
        "v2safety": dict(pred=v2 / "v2safety_pgd_predictions_test_epsilon_0_03.csv",
                         prob=v2 / "v2safety_pgd_probabilities_test_epsilon_0_03.csv",
                         sweep=v2 / "v2safety_pgd_epsilon_sweep_test.csv"),
        "v2lowFA": dict(pred=v2 / "v2lowFA_pgd_predictions_test_epsilon_0_03.csv",
                        prob=v2 / "v2lowFA_pgd_probabilities_test_epsilon_0_03.csv",
                        sweep=v2 / "v2lowFA_pgd_epsilon_sweep_test.csv"),
    }
    return reg


def pred_col(r):  # prediction CSV uses attacked_predicted_label
    return "attacked_predicted_label" if "attacked_predicted_label" in r else "predicted_label"


def binom_wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def confusion(rs, col):
    tp = fp = fn = tn = 0
    for r in rs:
        t = int(r["true_label"]) == FALL; p = int(r[col]) == FALL
        if t and p: tp += 1
        elif (not t) and p: fp += 1
        elif t and (not p): fn += 1
        else: tn += 1
    return tp, fp, fn, tn


# ============ Section 4: epoch trajectory ============
def epoch_trajectories():
    out = AUD / "epoch_trajectory_summary.csv"
    logs = {(N, kind): glob.glob(str(SG / ("variantE_motion_hard_negative/" + ("selection_v2/" if kind == "selv2" else "") + f"seed{N}") / "logs" / "*lam1p0*training_log.csv"))
            for N in (42, 43) for kind in ("priorE", "selv2")}
    # prior E and selv2 share the same per-epoch validation metrics (same training); use selv2 log (full all-epoch record)
    sel = {42: dict(priorE_safety=56, v2safety=56, v2lowFA=64, macroF1=66),
           43: dict(priorE_safety=18, v2safety=24, v2lowFA=31, macroF1=34)}
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "epoch", "val_clean_acc", "val_clean_macro_f1", "val_pgd_recall",
                    "val_pgd_false_alarms", "safety_score", "mean_motion_penalty", "is_priorE_safety",
                    "is_v2safety", "is_v2lowFA", "is_macroF1"])
        for N in (42, 43):
            log = logs[(N, "selv2")][0]
            for r in rows(log):
                e = int(r["epoch"]); s = sel[N]
                w.writerow([N, e, r["val_clean_accuracy"], r["val_clean_macro_f1"], r["val_pgd_fall_recall"],
                            r["val_pgd_false_fall_alarms"], r["safety_score"], r["mean_motion_penalty"],
                            int(e == s["priorE_safety"]), int(e == s["v2safety"]), int(e == s["v2lowFA"]), int(e == s["macroF1"])])
    # figures
    for N in (42, 43):
        rs = rows(logs[(N, "selv2")][0]); ep = [int(r["epoch"]) for r in rs]
        s = sel[N]
        fig, ax1 = plt.subplots(figsize=(11, 5.5))
        ax1.plot(ep, [float(r["val_clean_accuracy"]) for r in rs], "-", color="tab:blue", label="val clean acc")
        ax1.plot(ep, [float(r["val_clean_macro_f1"]) for r in rs], "--", color="tab:cyan", label="val macro-F1")
        ax1.plot(ep, [float(r["val_pgd_fall_recall"]) for r in rs], "-", color="tab:green", label="val PGD recall")
        ax1.plot(ep, [float(r["safety_score"]) for r in rs], ":", color="tab:gray", label="safety score")
        ax1.axhline(0.70, color="red", ls=":", lw=0.8, alpha=0.5)
        ax1.set_xlabel("epoch"); ax1.set_ylabel("validation metric / score"); ax1.set_ylim(0, 1.05)
        ax2 = ax1.twinx()
        ax2.plot(ep, [int(r["val_pgd_false_fall_alarms"]) for r in rs], "-", color="tab:orange", alpha=0.6, label="val PGD FP")
        ax2.set_ylabel("val PGD false alarms", color="tab:orange")
        for name, c, mk in [("priorE_safety", "purple", "v"), ("v2safety", "green", "^"), ("v2lowFA", "blue", "s"), ("macroF1", "olive", "D")]:
            e = s[name]
            ax1.axvline(e, color=c, ls="-", lw=1, alpha=0.5)
            ax1.annotate(name, (e, 1.0), rotation=90, fontsize=7, color=c, va="top")
        ax1.legend(loc="center left", fontsize=8); ax1.set_title(f"Seed {N} validation trajectory (selected epochs annotated)")
        fig.tight_layout(); fig.savefig(FIG / f"fig_epoch_trajectory_seed{N}.png", dpi=150); plt.close(fig)
    print("[S4] epoch trajectories")


# ============ Section 3: loss-scale diagnostics ============
def loss_scale():
    out = AUD / "loss_scale_diagnostics.csv"
    sel = {42: 56, 43: 24}  # v2safety epochs
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "epoch", "train_total_loss", "mean_motion_penalty_raw",
                    "lambda_motion", "lambda_x_penalty", "approx_CE", "penalty_to_CE_ratio", "is_v2safety"])
        traj = {}
        for N in (42, 43):
            log = glob.glob(str(SG / "variantE_motion_hard_negative" / "selection_v2" / f"seed{N}" / "logs" / "*lam1p0*training_log.csv"))[0]
            xs, mp = [], []
            for r in rows(log):
                e = int(r["epoch"]); tot = float(r["train_loss"]); pen = float(r["mean_motion_penalty"])
                lam = 1.0; lp = lam * pen; ce = tot - lp
                ratio = lp / ce if ce > 1e-9 else float("nan")
                w.writerow([N, e, f"{tot:.5f}", f"{pen:.5f}", lam, f"{lp:.5f}", f"{ce:.5f}", f"{ratio:.4f}", int(e == sel[N])])
                xs.append(e); mp.append(pen)
            traj[N] = (xs, mp)
    fig, ax = plt.subplots(figsize=(10, 5))
    for N, c in [(42, "tab:blue"), (43, "tab:orange")]:
        ax.plot(*traj[N], "-o", ms=3, color=c, label=f"seed {N} motion penalty (mean fall-prob of adv walk/run)")
        ax.axvline(sel[N], color=c, ls=":", lw=1)
    ax.set_xlabel("epoch"); ax.set_ylabel("mean motion penalty (raw, = mean P_fall(x_adv))")
    ax.set_title("Motion penalty trajectory (λ=1.0; vline = v2safety epoch)"); ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "fig_loss_scale_vs_epoch.png", dpi=150); plt.close(fig)
    print("[S3] loss scale")


# ============ Section 5: Pareto ============
def pareto():
    out = AUD / "pareto_points.csv"
    GUARD_ACC, GUARD_F1 = 0.70, 0.65
    # test metrics pulled from comparison/ safety_metrics
    def kv(p):
        d = {}
        for r in (rows(p) or []):
            d[r["metric"]] = r["value"]
        return d
    pts = []
    for N in (42, 43):
        reg = registry(N)
        # collect (label, recall, fp, clean_acc, clean_f1)
        # from pgd safety_metrics
        srcs = {
            "FGSM_defense": EXP / "results" / "converged_attacks" / f"defended_fgsm_at_seed{N}_pgd_safety_metrics_test_epsilon_0_03.csv",
            "D_safety": SG / f"seed{N}" / "test_eval" / "variantD_bySafetyScore_pgd_safety_metrics_test_epsilon_0_03.csv",
            "priorE_safety": SG / "variantE_motion_hard_negative" / f"seed{N}" / "test_eval" / "E_lam1p0_bySafetyScore_pgd_safety_metrics_test_epsilon_0_03.csv",
            "priorE_macroF1": SG / "variantE_motion_hard_negative" / f"seed{N}" / "test_eval" / "E_lam1p0_byValMacroF1_pgd_safety_metrics_test_epsilon_0_03.csv",
            "v2safety": SG / "variantE_motion_hard_negative" / "selection_v2" / f"seed{N}" / "test_eval" / "v2safety_pgd_safety_metrics_test_epsilon_0_03.csv",
            "v2lowFA": SG / "variantE_motion_hard_negative" / "selection_v2" / f"seed{N}" / "test_eval" / "v2lowFA_pgd_safety_metrics_test_epsilon_0_03.csv",
        }
        seed_pts = []
        for lab, p in srcs.items():
            d = kv(p)
            if not d:
                continue
            seed_pts.append(dict(seed=N, label=lab, recall=float(d["fall_recall"]), fp=int(d["false_fall_alarm_count"]),
                                 acc=float(d["clean_accuracy"]), f1=float(d["clean_macro_f1"]),
                                 clean_fr=float(d["clean_fall_recall"])))
        # dominance among guard-passing points (recall>=, fp<=, strict somewhere)
        for a in seed_pts:
            guarded = a["acc"] >= GUARD_ACC and a["f1"] >= GUARD_F1
            dominated = False
            for b in seed_pts:
                if b is a:
                    continue
                if (b["recall"] >= a["recall"] and b["fp"] <= a["fp"]
                        and (b["recall"] > a["recall"] or b["fp"] < a["fp"])):
                    dominated = True; break
            # classify
            if a["recall"] <= 0.02:
                cls = "invalid_recall_collapse"
            elif not guarded:
                cls = "fails_clean_guard"
            elif a["fp"] >= 140:
                cls = "high_recall_high_false_alarm"
            elif a["recall"] < 0.15:
                cls = "conservative_low_false_alarm" if a["fp"] < 90 else "clean_stable_low_recall"
            else:
                cls = "balanced"
            a["guard_pass"] = int(guarded); a["dominated"] = int(dominated)
            a["pareto_efficient"] = int(not dominated); a["class"] = cls
            pts.append(a)
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "label", "pgd_recall", "pgd_false_alarms", "clean_acc", "clean_macro_f1",
                    "clean_fall_recall", "guard_pass", "dominated", "pareto_efficient", "class"])
        for a in pts:
            w.writerow([a["seed"], a["label"], f"{a['recall']:.3f}", a["fp"], f"{a['acc']:.3f}",
                        f"{a['f1']:.3f}", f"{a['clean_fr']:.3f}", a["guard_pass"], a["dominated"],
                        a["pareto_efficient"], a["class"]])
    # figures per seed
    colors = {"FGSM_defense": "gray", "D_safety": "orange", "priorE_safety": "green",
              "priorE_macroF1": "olive", "v2safety": "blue", "v2lowFA": "purple"}
    for N in (42, 43):
        sp = [a for a in pts if a["seed"] == N]
        fig, ax = plt.subplots(figsize=(8, 6))
        for a in sp:
            ax.scatter(a["fp"], a["recall"], color=colors.get(a["label"], "k"), s=90, zorder=4,
                       edgecolors=("k" if a["pareto_efficient"] else "none"))
            ax.annotate(f"{a['label']}\n({a['class']})", (a["fp"], a["recall"]), fontsize=6, xytext=(4, 3), textcoords="offset points")
        ax.set_xlabel("PGD@0.030 false-fall alarms"); ax.set_ylabel("PGD@0.030 fall recall")
        ax.set_title(f"Seed {N} recall vs false alarms (black edge = Pareto-efficient among shown)")
        ax.grid(True, alpha=0.3)
        fig.tight_layout(); fig.savefig(FIG / f"fig_pareto_seed{N}.png", dpi=150); plt.close(fig)
    print("[S5] pareto")
    return pts


# ============ Section 6: decision-cost curves ============
def cost_curves(pts):
    out = AUD / "cost_curve_preference.csv"
    ratios = [1, 2, 5, 10, 20, 50]
    rowsout = []
    for N in (42, 43):
        sp = [a for a in pts if a["seed"] == N]
        for lab_fn in ratios:
            costs = {}
            for a in sp:
                missed = round((1 - a["recall"]) * NFALL_TEST)
                cost = lab_fn * missed + 1 * a["fp"]
                costs[a["label"]] = cost
            best = min(costs, key=costs.get)
            rowsout.append([N, f"{lab_fn}:1", best] + [f"{a}:{costs[a]}" for a in costs])
    # write
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        labels = sorted({a["label"] for a in pts})
        w.writerow(["seed", "FN_to_FP", "preferred"] + [f"cost_{l}" for l in labels])
        for N in (42, 43):
            sp = [a for a in pts if a["seed"] == N]
            for lab_fn in ratios:
                costs = {}
                for a in sp:
                    missed = round((1 - a["recall"]) * NFALL_TEST)
                    costs[a["label"]] = lab_fn * missed + a["fp"]
                best = min(costs, key=costs.get)
                w.writerow([N, f"{lab_fn}:1", best] + [costs.get(l, "") for l in labels])
    # figure: preferred checkpoint vs ratio
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, N in zip(axes, (42, 43)):
        sp = [a for a in pts if a["seed"] == N]
        labels = [a["label"] for a in sp]
        for a in sp:
            cs = [lab_fn * round((1 - a["recall"]) * NFALL_TEST) + a["fp"] for lab_fn in ratios]
            ax.plot(ratios, cs, "-o", ms=3, label=a["label"])
        ax.set_xscale("log"); ax.set_xticks(ratios); ax.set_xticklabels([f"{r}:1" for r in ratios])
        ax.set_xlabel("FN:FP cost ratio"); ax.set_ylabel("total cost (lower=preferred)")
        ax.set_title(f"seed {N}"); ax.grid(True, alpha=0.3); ax.legend(fontsize=7)
    fig.suptitle("Decision-cost by FN:FP ratio (experimental sensitivity, NOT clinical)")
    fig.tight_layout(); fig.savefig(FIG / "fig_cost_preference_by_ratio.png", dpi=150); plt.close(fig)
    print("[S6] cost curves")


# ============ Section 7: uncertainty + paired ============
def uncertainty():
    out = AUD / "uncertainty_intervals.csv"
    pc = AUD / "paired_comparisons.csv"
    labs = ["FGSM_defense", "D_safety", "priorE_safety", "priorE_macroF1", "v2safety", "v2lowFA"]
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "label", "n_fall", "tp", "fn", "recall", "recall_CI95_low", "recall_CI95_high",
                    "n_nonfall", "fp", "tn", "specificity", "spec_CI95_low", "spec_CI95_high",
                    "fall_precision", "binary_f1"])
        for N in (42, 43):
            reg = registry(N)
            for lab in labs:
                rs = rows(reg[lab]["pred"])
                if not rs:
                    continue
                col = pred_col(rs[0])
                tp, fp, fn, tn = confusion(rs, col)
                rec = tp / (tp + fn) if tp + fn else 0; rl, rh = binom_wilson(tp, tp + fn)
                spec = tn / (tn + fp) if tn + fp else 0; sl, sh = binom_wilson(tn, tn + fp)
                prec = tp / (tp + fp) if tp + fp else 0
                f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
                w.writerow([N, lab, tp + fn, tp, fn, f"{rec:.3f}", f"{rl:.3f}", f"{rh:.3f}",
                            tn + fp, fp, tn, f"{spec:.3f}", f"{sl:.3f}", f"{sh:.3f}", f"{prec:.3f}", f"{f1:.3f}"])
    # paired McNemar on fall windows (detected vs missed), v2safety vs each
    with pc.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "modelA", "modelB", "fall_both_detected", "A_only", "B_only", "neither",
                    "mcnemar_b", "mcnemar_c", "mcnemar_chi2_cc", "note"])
        for N in (42, 43):
            reg = registry(N)
            base = rows(reg["v2safety"]["pred"]); bc = pred_col(base[0])
            base_fall = {int(r["sample_id"]): (int(r[bc]) == FALL) for r in base if int(r["true_label"]) == FALL}
            for lab in ["D_safety", "priorE_safety", "FGSM_defense", "v2lowFA"]:
                rs = rows(reg[lab]["pred"]); cc = pred_col(rs[0])
                other = {int(r["sample_id"]): (int(r[cc]) == FALL) for r in rs if int(r["true_label"]) == FALL}
                both = a_only = b_only = neither = 0
                for sid in base_fall:
                    A = other.get(sid, False); B = base_fall[sid]  # A=other model, B=v2safety
                    if A and B: both += 1
                    elif A and not B: a_only += 1
                    elif B and not A: b_only += 1
                    else: neither += 1
                b_, c_ = a_only, b_only
                chi2 = ((abs(b_ - c_) - 1) ** 2) / (b_ + c_) if (b_ + c_) > 0 else 0.0
                w.writerow([N, lab, "v2safety", both, a_only, b_only, neither, b_, c_, f"{chi2:.3f}",
                            "b,c = discordant fall windows; chi2 with continuity correction"])
    print("[S7] uncertainty + paired")


# ============ Section 8: val-test reliability ============
def val_test():
    out = AUD / "val_test_reliability.csv"
    # selected-epoch validation metrics (from selv2 candidate CSV + selv2 log) vs test
    cand = {N: {r["selection"]: r for r in (rows(SG / "variantE_motion_hard_negative" / "selection_v2" / f"seed{N}" / "analysis" / f"seed{N}_variantE_selv2_lam1p0_selection_candidates.csv") or [])} for N in (42, 43)}
    # map checkpoint -> (val source, test safety_metrics)
    mapping = {
        "priorE_safety": "v2safety",   # prior E safety epoch == v2safety epoch on seed42(56); on seed43 prior=18 differs
        "v2safety": "v2safety", "v2lowFA": "v2lowFA", "macroF1": "v2macroF1",
    }
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "checkpoint", "selected_epoch", "val_clean_acc", "test_clean_acc",
                    "val_clean_macro_f1", "test_clean_macro_f1", "val_pgd_recall", "test_pgd_recall",
                    "val_pgd_false_alarms", "test_pgd_false_alarms", "val_minus_test_recall"])
        # use selv2 log for prior-E-safety val (seed43 epoch18) too
        for N in (42, 43):
            logrows = {int(r["epoch"]): r for r in rows(glob.glob(str(SG / "variantE_motion_hard_negative" / "selection_v2" / f"seed{N}" / "logs" / "*lam1p0*training_log.csv"))[0])}
            sel_ep = {42: dict(priorE_safety=56, v2safety=56, v2lowFA=64),
                      43: dict(priorE_safety=18, v2safety=24, v2lowFA=31)}[N]
            test_src = {
                "priorE_safety": SG / "variantE_motion_hard_negative" / f"seed{N}" / "test_eval" / "E_lam1p0_bySafetyScore_pgd_safety_metrics_test_epsilon_0_03.csv",
                "v2safety": SG / "variantE_motion_hard_negative" / "selection_v2" / f"seed{N}" / "test_eval" / "v2safety_pgd_safety_metrics_test_epsilon_0_03.csv",
                "v2lowFA": SG / "variantE_motion_hard_negative" / "selection_v2" / f"seed{N}" / "test_eval" / "v2lowFA_pgd_safety_metrics_test_epsilon_0_03.csv",
            }
            for ck, ep in sel_ep.items():
                vr = logrows[ep]
                td = {r["metric"]: r["value"] for r in (rows(test_src[ck]) or [])}
                if not td:
                    continue
                vrec = float(vr["val_pgd_fall_recall"]); trec = float(td["fall_recall"])
                w.writerow([N, ck, ep, vr["val_clean_accuracy"], td["clean_accuracy"],
                            vr["val_clean_macro_f1"], td["clean_macro_f1"], f"{vrec:.3f}", f"{trec:.3f}",
                            vr["val_pgd_false_fall_alarms"], td["false_fall_alarm_count"], f"{vrec - trec:.3f}"])
    # figures
    data = rows(out)
    fig, ax = plt.subplots(figsize=(6.5, 6))
    for r in data:
        ax.scatter(float(r["val_pgd_recall"]), float(r["test_pgd_recall"]),
                   marker=("o" if r["seed"] == "42" else "^"), s=80)
        ax.annotate(f"{r['checkpoint']}·s{r['seed']}", (float(r["val_pgd_recall"]), float(r["test_pgd_recall"])), fontsize=6)
    ax.plot([0, 0.6], [0, 0.6], "k--", lw=0.8); ax.set_xlabel("validation PGD recall"); ax.set_ylabel("test PGD recall")
    ax.set_title("Validation vs test PGD recall (○ seed42, △ seed43; dashed=identity)"); ax.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(FIG / "fig_val_vs_test_recall.png", dpi=150); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6.5, 6))
    for r in data:
        ax.scatter(int(r["val_pgd_false_alarms"]), int(r["test_pgd_false_alarms"]),
                   marker=("o" if r["seed"] == "42" else "^"), s=80)
        ax.annotate(f"{r['checkpoint']}·s{r['seed']}", (int(r["val_pgd_false_alarms"]), int(r["test_pgd_false_alarms"])), fontsize=6)
    mx = 160; ax.plot([0, mx], [0, mx], "k--", lw=0.8); ax.set_xlabel("validation PGD false alarms"); ax.set_ylabel("test PGD false alarms")
    ax.set_title("Validation vs test PGD false alarms"); ax.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(FIG / "fig_val_vs_test_false_alarms.png", dpi=150); plt.close(fig)
    print("[S8] val-test reliability")


# ============ Section 9: class counts + normalized FA ============
def class_counts():
    sys.path.insert(0, str(EXP / "scripts"))
    import train_converged_clean_baseline as s1
    bench = EXP / "third_party" / "WiFi-CSI-Sensing-Benchmark"
    s1.patch_sensefi_dataset_loader(bench)
    data = s1.load_raw_ut_har(bench)
    with (AUD / "class_counts.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["split", "class_index", "class_name", "count"])
        for split in ("train", "val", "test"):
            y = data[f"y_{split}"].numpy().astype(int)
            for k in range(7):
                w.writerow([split, k, CLASS[k], int((y == k).sum())])
    test_y = data["y_test"].numpy().astype(int)
    totals = {k: int((test_y == k).sum()) for k in NONFALL}
    out = AUD / "class_normalized_false_alarms.csv"
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "checkpoint", "true_class", "n_class_windows", "to_fall_count", "to_fall_rate"])
        for N in (42, 43):
            reg = registry(N)
            for lab in ["FGSM_defense", "D_safety", "priorE_safety", "v2safety", "v2lowFA"]:
                rs = rows(reg[lab]["pred"])
                if not rs:
                    continue
                col = pred_col(rs[0])
                for k in NONFALL:
                    cnt = sum(1 for r in rs if int(r["true_label"]) == k and int(r[col]) == FALL)
                    w.writerow([N, lab, CLASS[k], totals[k], cnt, f"{cnt/totals[k]:.3f}" if totals[k] else "0"])
    print("[S9] class counts + normalized FA")


# ============ Section 10 + 15: logit margins, prob geometry, calibration ============
def margins_calibration():
    out = AUD / "logit_margin_diagnostics.csv"
    cal = AUD / "calibration_metrics.csv"
    labs = ["D_safety", "priorE_safety", "v2safety", "v2lowFA"]  # need prob CSVs
    prob_cols = [f"prob_{CLASS[i].replace(' ', '_')}" for i in range(7)]
    logit_cols = [f"logit_{CLASS[i].replace(' ', '_')}" for i in range(7)]

    def groups(rs):
        g = {"true_fall_detected": [], "true_fall_missed": [], "walk_FA": [], "run_FA": [], "other_FA": [], "rejected_walk_run": []}
        for r in rs:
            t = int(r["true_label"]); p = int(r["predicted_label"])
            if t == FALL:
                (g["true_fall_detected"] if p == FALL else g["true_fall_missed"]).append(r)
            elif p == FALL:
                if t == WALK: g["walk_FA"].append(r)
                elif t == RUN: g["run_FA"].append(r)
                else: g["other_FA"].append(r)
            elif t in (WALK, RUN):
                g["rejected_walk_run"].append(r)
        return g

    mrows = []; carows = []
    for N in (42, 43):
        reg = registry(N)
        for lab in labs:
            pr = reg[lab]["prob"]
            rs = rows(pr)
            if not rs:
                continue
            g = groups(rs)
            for gname, items in g.items():
                if not items:
                    mrows.append([N, lab, gname, 0] + ["nan"] * 4); continue
                fpb = np.array([float(r["fall_probability"]) for r in items])
                mc = np.array([float(r["max_confidence"]) for r in items])
                lf = np.array([float(r["logit_fall"]) for r in items])
                lt = np.array([float(r[logit_cols[int(r["true_label"])]]) for r in items])
                lnf = np.array([max(float(r[logit_cols[k]]) for k in range(7) if k != FALL) for r in items])
                mrows.append([N, lab, gname, len(items), f"{np.median(fpb):.3f}", f"{np.median(mc):.3f}",
                              f"{np.median(lf - lt):.3f}", f"{np.median(lf - lnf):.3f}"])
            # calibration (PGD): ECE, Brier, NLL over all windows
            P = np.array([[float(r[c]) for c in prob_cols] for r in rs])
            y = np.array([int(r["true_label"]) for r in rs])
            conf = P.max(1); predc = P.argmax(1); correct = (predc == y).astype(float)
            bins = np.linspace(0, 1, 11); ece = 0.0
            for i in range(10):
                m = (conf >= bins[i]) & (conf < bins[i + 1] if i < 9 else conf <= bins[i + 1])
                if m.sum() > 0:
                    ece += m.mean() * abs(correct[m].mean() - conf[m].mean())
            onehot = np.zeros_like(P); onehot[np.arange(len(y)), y] = 1
            brier = float(((P - onehot) ** 2).sum(1).mean())
            nll = float(-np.log(np.clip(P[np.arange(len(y)), y], 1e-9, 1)).mean())
            g2 = groups(rs)

            def mconf(items):
                return float(np.mean([float(r["max_confidence"]) for r in items])) if items else float("nan")
            carows.append([N, lab, f"{ece:.4f}", f"{brier:.4f}", f"{nll:.4f}",
                           f"{mconf(g2['true_fall_detected']):.3f}", f"{mconf(g2['true_fall_missed']):.3f}",
                           f"{mconf(g2['walk_FA'] + g2['run_FA']):.3f}", f"{mconf(g2['other_FA']):.3f}"])
    with out.open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["seed", "checkpoint", "group", "n", "median_fall_prob",
                                       "median_max_conf", "median_logit_fall_minus_true", "median_logit_fall_minus_maxnonfall"])
        w.writerows(mrows)
    with cal.open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["seed", "checkpoint", "ECE", "Brier", "NLL",
                                       "mconf_detected_fall", "mconf_missed_fall", "mconf_walk_run_FA", "mconf_other_FA"])
        w.writerows(carows)
    # figures
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, N in zip(axes, (42, 43)):
        reg = registry(N)
        for lab, c in [("priorE_safety", "tab:green"), ("v2safety", "tab:blue")]:
            rs = rows(reg[lab]["prob"])
            if not rs:
                continue
            g = groups(rs)
            data = [np.array([float(r["fall_probability"]) for r in g[k]]) for k in ["true_fall_detected", "true_fall_missed", "walk_FA", "run_FA"]]
            pos = np.arange(4) + (0.0 if lab == "priorE_safety" else 0.0)
        # plot v2safety only (cleaner)
        rs = rows(reg["v2safety"]["prob"]); g = groups(rs)
        keys = ["true_fall_detected", "true_fall_missed", "walk_FA", "run_FA", "other_FA"]
        dd = [np.array([float(r["fall_probability"]) for r in g[k]]) if g[k] else np.array([np.nan]) for k in keys]
        ax.boxplot(dd, labels=[f"{k}\n(n={len(g[k])})" for k in keys], showfliers=False)
        ax.set_title(f"seed {N} v2safety fall-prob by group (test PGD)"); ax.set_ylim(0, 1); ax.tick_params(axis="x", labelsize=7)
        ax.set_ylabel("fall probability")
    fig.tight_layout(); fig.savefig(FIG / "fig_fall_probability_distributions.png", dpi=150); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, N in zip(axes, (42, 43)):
        reg = registry(N); rs = rows(reg["v2safety"]["prob"]); g = groups(rs)
        keys = ["true_fall_detected", "walk_FA", "run_FA", "other_FA"]
        dd = []
        for k in keys:
            vals = []
            for r in g[k]:
                lf = float(r["logit_fall"]); lt = float(r[logit_cols[int(r["true_label"])]]); vals.append(lf - lt)
            dd.append(np.array(vals) if vals else np.array([np.nan]))
        ax.boxplot(dd, labels=[f"{k}\n(n={len(g[k])})" for k in keys], showfliers=False)
        ax.axhline(0, color="red", ls=":", lw=1)
        ax.set_title(f"seed {N} v2safety  logit_fall - logit_true (test PGD)"); ax.tick_params(axis="x", labelsize=7)
        ax.set_ylabel("logit_fall - logit_true_class")
    fig.tight_layout(); fig.savefig(FIG / "fig_logit_margin_distributions.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    et = ["detected_fall", "missed_fall", "walk_run_FA", "other_FA"]
    width = 0.2
    x = np.arange(len(et))
    for i, (N, lab) in enumerate([(42, "v2safety"), (43, "v2safety")]):
        reg = registry(N); rs = rows(reg[lab]["prob"]); g = groups(rs)
        vals = [np.mean([float(r["max_confidence"]) for r in g[k]]) if g[k] else np.nan
                for k in ["true_fall_detected", "true_fall_missed", "walk_FA", "run_FA"]]
        # combine walk+run
        wr = g["walk_FA"] + g["run_FA"]
        vals = [np.mean([float(r["max_confidence"]) for r in g["true_fall_detected"]]) if g["true_fall_detected"] else np.nan,
                np.mean([float(r["max_confidence"]) for r in g["true_fall_missed"]]) if g["true_fall_missed"] else np.nan,
                np.mean([float(r["max_confidence"]) for r in wr]) if wr else np.nan,
                np.mean([float(r["max_confidence"]) for r in g["other_FA"]]) if g["other_FA"] else np.nan]
        ax.bar(x + (i - 0.5) * width, vals, width, label=f"v2safety seed{N}")
    ax.set_xticks(x); ax.set_xticklabels(et); ax.set_ylabel("mean max-softmax confidence")
    ax.set_title("Confidence by error type (test PGD)"); ax.legend(fontsize=8); ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(FIG / "fig_confidence_by_error_type.png", dpi=150); plt.close(fig)
    print("[S10/15] margins + calibration")


# ============ Section 11 + 12: instance-level overlap ============
def overlap():
    labs = ["FGSM_defense", "D_safety", "priorE_safety", "v2safety", "v2lowFA"]
    with (AUD / "fall_window_overlap.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "metric", "value", "detail"])
        for N in (42, 43):
            reg = registry(N)
            det = {}  # lab -> set of detected fall sample_ids
            falls = None
            for lab in labs:
                rs = rows(reg[lab]["pred"]); col = pred_col(rs[0])
                fall_ids = {int(r["sample_id"]) for r in rs if int(r["true_label"]) == FALL}
                falls = fall_ids if falls is None else falls
                det[lab] = {int(r["sample_id"]) for r in rs if int(r["true_label"]) == FALL and int(r[col]) == FALL}
            allmodels = set.intersection(*det.values())
            nonemodels = falls - set.union(*det.values())
            w.writerow([N, "n_fall_windows", len(falls), ""])
            w.writerow([N, "detected_by_all", len(allmodels), sorted(allmodels)])
            w.writerow([N, "missed_by_all", len(nonemodels), sorted(nonemodels)])
            w.writerow([N, "lost_by_v2safety_vs_priorE", len(det["priorE_safety"] - det["v2safety"]), sorted(det["priorE_safety"] - det["v2safety"])])
            w.writerow([N, "recovered_by_v2safety_vs_priorE", len(det["v2safety"] - det["priorE_safety"]), sorted(det["v2safety"] - det["priorE_safety"])])
            w.writerow([N, "lost_by_v2safety_vs_D", len(det["D_safety"] - det["v2safety"]), sorted(det["D_safety"] - det["v2safety"])])
    with (AUD / "false_alarm_overlap.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "metric", "value", "detail"])
        for N in (42, 43):
            reg = registry(N)
            fa = {}
            for lab in labs:
                rs = rows(reg[lab]["pred"]); col = pred_col(rs[0])
                fa[lab] = {int(r["sample_id"]): int(r["true_label"]) for r in rs if int(r["true_label"]) != FALL and int(r[col]) == FALL}
            def wr_share(ids):
                return sum(1 for sid in ids if fa_any.get(sid) in (WALK, RUN))
            removed_prior = set(fa["priorE_safety"]) - set(fa["v2safety"])
            removed_D = set(fa["D_safety"]) - set(fa["v2safety"])
            introduced = set(fa["v2safety"]) - set(fa["priorE_safety"])
            common = set.intersection(*[set(fa[l]) for l in ["D_safety", "priorE_safety", "v2safety"]])
            fa_any = {**fa["D_safety"], **fa["priorE_safety"], **fa["v2safety"]}
            wr_removed = sum(1 for sid in removed_prior if fa["priorE_safety"][sid] in (WALK, RUN))
            w.writerow([N, "v2safety_total_FA", len(fa["v2safety"]), ""])
            w.writerow([N, "removed_vs_priorE", len(removed_prior), f"walk/run share={wr_removed}/{len(removed_prior)}"])
            w.writerow([N, "removed_vs_D", len(removed_D), ""])
            w.writerow([N, "introduced_vs_priorE", len(introduced), sorted(introduced)])
            w.writerow([N, "common_FA_D_priorE_v2", len(common), "shared hard cases"])
    print("[S11/12] overlap")


if __name__ == "__main__":
    epoch_trajectories()
    loss_scale()
    pts = pareto()
    cost_curves(pts)
    uncertainty()
    val_test()
    class_counts()
    margins_calibration()
    overlap()
    print("[done] audit_core complete.")
