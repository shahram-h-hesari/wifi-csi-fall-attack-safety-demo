"""
Variant F residual false-alarm geometry + operating-point diagnostic (analysis-only).

Uses committed Variant F v2safety probability/logit exports (seed42, seed44; clean + PGD@0.030)
to decide whether residual false alarms are near-boundary/filterable or still high-confidence
geometry failures. No training, no threshold change to saved metrics, no artifact overwrite.

Outputs under results/safety_guided_defense/variantF_false_alarm_diagnostic/:
  analysis/residual_fa_anatomy_seed{42,44}.csv      (per-window FA anatomy)
  analysis/source_class_summary.csv                  (FA by source class, both seeds)
  analysis/group_distributions.csv                   (true-fall vs FA vs walk/run-FA stats)
  analysis/operating_point_sweep_seed{42,44}.csv     (rules A-E full sweeps)
  analysis/target_satisfaction.csv                   (which (recall,FP) targets are met)
  analysis/cost_curve_gated.csv                      (FN:FP cost: raw vs best gated)
  analysis/cross_seed_threshold_stability.csv
  figures/*.png

Command: python scripts/diagnose_variantF_false_alarms.py
"""
from __future__ import annotations
from pathlib import Path
import csv, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

EXP = Path(__file__).resolve().parents[1]
SG = EXP / "results" / "safety_guided_defense"
OUT = SG / "variantF_false_alarm_diagnostic"
ANA = OUT / "analysis"; FIG = OUT / "figures"
ANA.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
CLASS = {0: "lie down", 1: "fall", 2: "walk", 3: "pickup", 4: "run", 5: "sit down", 6: "stand up"}
NONFALL = [0, 2, 3, 4, 5, 6]; WALK, RUN, FALL = 2, 4, 1
PROB = [f"prob_{CLASS[i].replace(' ', '_')}" for i in range(7)]
LOGIT = [f"logit_{CLASS[i].replace(' ', '_')}" for i in range(7)]
NFALL = 45
# raw Variant F v2safety reference (committed) + Variant D seed44 FP reference
RAW = {42: dict(recall=0.667, fp=115, wr=80), 44: dict(recall=0.622, fp=112, wr=73)}
VARIANTD_S44 = dict(fp=167, wr=116)


def prob_csv(seed, cond):
    return (SG / "variantF_motion_margin" / f"seed{seed}" / "test_eval" /
            f"F_lamM1p0_lamF1p0_v2safety_{cond}_probabilities_test_epsilon_0_03.csv")


def load(seed, cond):
    """Return list of per-window dicts with derived geometry features."""
    out = []
    with prob_csv(seed, cond).open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            t = int(r["true_label"]); p = int(r["predicted_label"])
            probs = np.array([float(r[c]) for c in PROB])
            logits = np.array([float(r[c]) for c in LOGIT])
            order = np.argsort(probs)[::-1]
            top1, top2 = order[0], order[1]
            lorder = np.argsort(logits)[::-1]
            second_logit = logits[lorder[1]]
            nonfall_logits = logits.copy(); nonfall_logits[FALL] = -1e9
            ent = float(-np.sum(probs * np.log(np.clip(probs, 1e-12, 1))))
            out.append(dict(sid=int(r["sample_id"]), true=t, pred=p,
                            fall_prob=float(probs[FALL]), true_prob=float(probs[t]),
                            second_class=int(top2), second_prob=float(probs[top2]),
                            fall_logit=float(logits[FALL]), true_logit=float(logits[t]),
                            max_nonfall_logit=float(nonfall_logits.max()),
                            m_fall_true=float(logits[FALL] - logits[t]),
                            m_fall_maxnf=float(logits[FALL] - nonfall_logits.max()),
                            m_top_second_logit=float(logits[FALL] - second_logit),
                            entropy=ent, conf_margin=float(probs[top1] - probs[top2])))
    return out


def med(xs):
    return float(np.median(xs)) if len(xs) else float("nan")


# ---------- Section 1: residual FA anatomy ----------
def section1():
    src_rows = []
    for seed in (42, 44):
        rows = load(seed, "pgd")
        fa = [w for w in rows if w["true"] != FALL and w["pred"] == FALL]
        # per-window anatomy csv
        with (ANA / f"residual_fa_anatomy_seed{seed}.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["sample_id", "true_class", "pred_class", "fall_prob", "true_prob",
                        "second_class", "second_prob", "fall_logit", "true_logit", "max_nonfall_logit",
                        "logit_fall_minus_true", "logit_fall_minus_maxnonfall", "entropy",
                        "conf_margin", "is_walk_or_run"])
            for d in fa:
                w.writerow([d["sid"], CLASS[d["true"]], CLASS[d["pred"]], f"{d['fall_prob']:.4f}",
                            f"{d['true_prob']:.4f}", CLASS[d["second_class"]], f"{d['second_prob']:.4f}",
                            f"{d['fall_logit']:.3f}", f"{d['true_logit']:.3f}", f"{d['max_nonfall_logit']:.3f}",
                            f"{d['m_fall_true']:.3f}", f"{d['m_fall_maxnf']:.3f}", f"{d['entropy']:.3f}",
                            f"{d['conf_margin']:.3f}", int(d["true"] in (WALK, RUN))])
        tot = len(fa)
        for k in NONFALL:
            grp = [d for d in fa if d["true"] == k]
            src_rows.append([seed, CLASS[k], len(grp), f"{100*len(grp)/tot:.1f}" if tot else "0",
                             f"{med([d['fall_prob'] for d in grp]):.3f}",
                             f"{med([d['m_fall_true'] for d in grp]):.3f}",
                             f"{med([d['entropy'] for d in grp]):.3f}",
                             f"{med([d['conf_margin'] for d in grp]):.3f}"])
        src_rows.append([seed, "TOTAL", tot, "100.0",
                         f"{med([d['fall_prob'] for d in fa]):.3f}",
                         f"{med([d['m_fall_true'] for d in fa]):.3f}",
                         f"{med([d['entropy'] for d in fa]):.3f}",
                         f"{med([d['conf_margin'] for d in fa]):.3f}"])
    with (ANA / "source_class_summary.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "source_class", "n_false_alarms", "pct_of_total", "median_fall_prob",
                    "median_logit_fall_minus_true", "median_entropy", "median_conf_margin"])
        w.writerows(src_rows)
    print("[S1] residual FA anatomy")


# ---------- Section 2: FA vs true attacked falls ----------
def section2():
    rows_out = []
    for seed in (42, 44):
        rows = load(seed, "pgd")
        A = [w for w in rows if w["true"] == FALL and w["pred"] == FALL]   # detected true falls
        B = [w for w in rows if w["true"] != FALL and w["pred"] == FALL]   # all false alarms
        C = [w for w in rows if w["true"] in (WALK, RUN) and w["pred"] == FALL]  # walk/run FAs
        for name, grp in [("A_true_fall_detected", A), ("B_false_alarms", B), ("C_walkrun_FA", C)]:
            rows_out.append([seed, name, len(grp),
                             f"{med([d['fall_prob'] for d in grp]):.3f}",
                             f"{med([d['fall_logit'] for d in grp]):.3f}",
                             f"{med([d['m_fall_true'] for d in grp]):.3f}",
                             f"{med([d['m_fall_maxnf'] for d in grp]):.3f}",
                             f"{med([d['entropy'] for d in grp]):.3f}",
                             f"{med([d['conf_margin'] for d in grp]):.3f}"])
        # figures (per seed)
        def fp(grp): return np.array([d["fall_prob"] for d in grp])
        def mt(grp): return np.array([d["m_fall_true"] for d in grp])
        def en(grp): return np.array([d["entropy"] for d in grp])
        fig, ax = plt.subplots(1, 2, figsize=(13, 5))
        bins = np.linspace(0, 1, 21)
        ax[0].hist(fp(A), bins=bins, alpha=0.6, label="true fall detected", color="tab:green", density=True)
        ax[0].hist(fp(B), bins=bins, alpha=0.5, label="false alarms", color="tab:red", density=True)
        ax[0].set_xlabel("fall probability"); ax[0].set_ylabel("density"); ax[0].legend(fontsize=8)
        ax[0].set_title(f"seed {seed}: fall prob — true falls vs FAs")
        ax[1].hist(mt(A), bins=20, alpha=0.6, label="true fall detected", color="tab:green", density=True)
        ax[1].hist(mt(B), bins=20, alpha=0.5, label="false alarms", color="tab:red", density=True)
        ax[1].axvline(0, color="k", ls=":", lw=0.8)
        ax[1].set_xlabel("logit_fall - logit_true"); ax[1].legend(fontsize=8)
        ax[1].set_title(f"seed {seed}: logit margin")
        fig.tight_layout(); fig.savefig(FIG / f"fig_hist_fallprob_margin_seed{seed}.png", dpi=150); plt.close(fig)

        fig, ax = plt.subplots(1, 3, figsize=(16, 4.5))
        ax[0].hist(en(A), bins=20, alpha=0.6, label="true fall", color="tab:green", density=True)
        ax[0].hist(en(B), bins=20, alpha=0.5, label="FA", color="tab:red", density=True)
        ax[0].set_xlabel("entropy"); ax[0].legend(fontsize=8); ax[0].set_title(f"seed {seed}: entropy")
        ax[1].scatter(fp(A), mt(A), s=14, color="tab:green", alpha=0.6, label="true fall")
        ax[1].scatter(fp(B), mt(B), s=14, color="tab:red", alpha=0.5, label="FA")
        ax[1].set_xlabel("fall probability"); ax[1].set_ylabel("logit_fall - logit_true")
        ax[1].legend(fontsize=8); ax[1].set_title("fall prob vs margin")
        ax[2].scatter(fp(A), en(A), s=14, color="tab:green", alpha=0.6, label="true fall")
        ax[2].scatter(fp(B), en(B), s=14, color="tab:red", alpha=0.5, label="FA")
        ax[2].set_xlabel("fall probability"); ax[2].set_ylabel("entropy")
        ax[2].legend(fontsize=8); ax[2].set_title("fall prob vs entropy")
        fig.tight_layout(); fig.savefig(FIG / f"fig_separability_seed{seed}.png", dpi=150); plt.close(fig)
    with (ANA / "group_distributions.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "group", "n", "median_fall_prob", "median_fall_logit",
                    "median_logit_fall_minus_true", "median_logit_fall_minus_maxnonfall",
                    "median_entropy", "median_conf_margin"])
        w.writerows(rows_out)
    print("[S2] FA vs true falls + figures")


# ---------- Section 3: post-hoc operating-point sweep ----------
def metrics_under_alert(rows, alert_fn):
    tp = fp = fn = tn = wr = 0
    for d in rows:
        is_fall = d["true"] == FALL
        alert = (d["pred"] == FALL) and alert_fn(d)
        if is_fall and alert: tp += 1
        elif (not is_fall) and alert:
            fp += 1
            if d["true"] in (WALK, RUN): wr += 1
        elif is_fall and (not alert): fn += 1
        else: tn += 1
    rec = tp / NFALL
    prec = tp / (tp + fp) if tp + fp else 0.0
    spec = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return dict(recall=rec, fp=fp, wr=wr, precision=prec, specificity=spec, f1=f1, tp=tp)


def section3():
    targets = [(0.50, 100), (0.50, 80), (0.40, 80), (0.40, 60), (0.30, 50)]
    sat_rows = []
    best_gated = {}  # seed -> (rule, params, metrics)
    for seed in (42, 44):
        pgd = load(seed, "pgd")
        sweep_rows = []
        cand = []  # (rule, desc, metrics) candidates meeting some target, for cost/cross-seed
        pgrid = np.round(np.arange(0.0, 1.0001, 0.02), 3)
        mgrid = np.round(np.arange(0.0, 6.0001, 0.25), 3)
        hgrid = np.round(np.arange(0.0, 2.0001, 0.05), 3)
        # Rule A: P(fall) >= tau
        for tau in pgrid:
            m = metrics_under_alert(pgd, lambda d, t=tau: d["fall_prob"] >= t)
            sweep_rows.append(["A_pfall", f"{tau}", "", m["recall"], m["fp"], m["wr"], m["specificity"], m["precision"], m["f1"]])
            cand.append(("A_pfall", (tau, None), m))
        # Rule B: z_fall - z_second_logit >= tau
        for tau in mgrid:
            m = metrics_under_alert(pgd, lambda d, t=tau: d["m_top_second_logit"] >= t)
            sweep_rows.append(["B_logitmargin", f"{tau}", "", m["recall"], m["fp"], m["wr"], m["specificity"], m["precision"], m["f1"]])
            cand.append(("B_logitmargin", (tau, None), m))
        # Rule C: entropy <= tau
        for tau in hgrid:
            m = metrics_under_alert(pgd, lambda d, t=tau: d["entropy"] <= t)
            sweep_rows.append(["C_entropy", f"{tau}", "", m["recall"], m["fp"], m["wr"], m["specificity"], m["precision"], m["f1"]])
            cand.append(("C_entropy", (tau, None), m))
        # Rule D: P(fall)>=tp AND entropy<=th
        for tp_ in pgrid[::2]:
            for th in hgrid[::2]:
                m = metrics_under_alert(pgd, lambda d, a=tp_, b=th: d["fall_prob"] >= a and d["entropy"] <= b)
                sweep_rows.append(["D_pfall+entropy", f"{tp_}", f"{th}", m["recall"], m["fp"], m["wr"], m["specificity"], m["precision"], m["f1"]])
                cand.append(("D_pfall+entropy", (tp_, th), m))
        # Rule E: margin>=tm AND entropy<=th
        for tm in mgrid[::2]:
            for th in hgrid[::2]:
                m = metrics_under_alert(pgd, lambda d, a=tm, b=th: d["m_top_second_logit"] >= a and d["entropy"] <= b)
                sweep_rows.append(["E_margin+entropy", f"{tm}", f"{th}", m["recall"], m["fp"], m["wr"], m["specificity"], m["precision"], m["f1"]])
                cand.append(("E_margin+entropy", (tm, th), m))
        with (ANA / f"operating_point_sweep_seed{seed}.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["rule", "tau1", "tau2", "pgd_recall", "pgd_fp", "walkrun_fp", "specificity", "precision", "f1"])
            for r in sweep_rows:
                w.writerow([r[0], r[1], r[2], f"{r[3]:.3f}", r[4], r[5], f"{r[6]:.3f}", f"{r[7]:.3f}", f"{r[8]:.3f}"])
        # target satisfaction: for each target, best (max recall then min fp) candidate that meets it
        for (rmin, fmax) in targets:
            elig = [(rule, par, m) for rule, par, m in cand if m["recall"] >= rmin and m["fp"] <= fmax]
            if elig:
                rule, par, m = max(elig, key=lambda x: (x[2]["recall"], -x[2]["fp"]))
                sat_rows.append([seed, f"recall>={rmin} & FP<={fmax}", "YES", rule, str(par),
                                 f"{m['recall']:.3f}", m["fp"], m["wr"], f"{m['f1']:.3f}"])
            else:
                sat_rows.append([seed, f"recall>={rmin} & FP<={fmax}", "NO", "", "", "", "", "", ""])
        # store a 'best gated' point: max F1 among candidates with recall>=0.40 (for cost/cross-seed)
        good = [(rule, par, m) for rule, par, m in cand if m["recall"] >= 0.40]
        if good:
            best_gated[seed] = max(good, key=lambda x: x[2]["f1"])
    with (ANA / "target_satisfaction.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "target", "met", "rule", "thresholds", "recall", "fp", "walkrun_fp", "f1"])
        w.writerows(sat_rows)
    print("[S3] operating-point sweep + target satisfaction")
    return best_gated


# ---------- Section 4: cost curves ----------
def section4(best_gated):
    ratios = [1, 2, 5, 10, 20, 50]
    with (ANA / "cost_curve_gated.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "point", "recall", "fp"] + [f"cost_{r}to1" for r in ratios])
        for seed in (42, 44):
            raw = RAW[seed]
            for label, rec, fp in [("raw_variantF", raw["recall"], raw["fp"])] + (
                    [("best_gated", best_gated[seed][2]["recall"], best_gated[seed][2]["fp"])] if seed in best_gated else []):
                missed = round((1 - rec) * NFALL)
                w.writerow([seed, label, f"{rec:.3f}", fp] + [r * missed + fp for r in ratios])
    print("[S4] cost curves")


# ---------- Section 5: cross-seed threshold stability ----------
def section5():
    # apply a shared P(fall) threshold to BOTH seeds and report recall/FP
    rows = {seed: load(seed, "pgd") for seed in (42, 44)}
    taus = [0.50, 0.70, 0.80, 0.85, 0.90, 0.95]
    with (ANA / "cross_seed_threshold_stability.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rule", "tau", "s42_recall", "s42_fp", "s44_recall", "s44_fp", "both_recall>=0.40", "both_fp<=80"])
        for tau in taus:
            m42 = metrics_under_alert(rows[42], lambda d, t=tau: d["fall_prob"] >= t)
            m44 = metrics_under_alert(rows[44], lambda d, t=tau: d["fall_prob"] >= t)
            w.writerow(["A_pfall", tau, f"{m42['recall']:.3f}", m42["fp"], f"{m44['recall']:.3f}", m44["fp"],
                        int(m42["recall"] >= 0.40 and m44["recall"] >= 0.40),
                        int(m42["fp"] <= 80 and m44["fp"] <= 80)])
    print("[S5] cross-seed threshold stability")


if __name__ == "__main__":
    section1()
    section2()
    bg = section3()
    section4(bg)
    section5()
    print("[done] Variant F false-alarm diagnostic complete.")
