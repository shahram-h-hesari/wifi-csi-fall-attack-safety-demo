"""
False-alarm probability/logit diagnosis + validation-selected threshold calibration.

ANALYSIS ONLY. No training, no protocol change. For the frozen Variant D
safety-guided checkpoints of seed 42 and seed 43, this:

  1. Generates per-window fall-class probabilities and logits on the VALIDATION
     and TEST splits under clean / FGSM@0.030 / PGD@0.030 (reusing the frozen
     attack math from run_converged_attacks; perturbations are byte-identical).
     Validation probabilities are written out because no prior artifact has them.

  2. Diagnoses false-fall alarms (Section 4): distribution of the fall-class
     probability for true falls vs walk/run/other false alarms, the fall-vs-true
     logit margin for false alarms, and their max confidence -- on TEST PGD@0.030.

  3. Runs a binary fall-alert threshold sweep (Section 5): the alert rule is
     `fall_probability >= t`. Thresholds are SELECTED ON VALIDATION ONLY (rules
     A-D) and then EVALUATED ON TEST, so there is no test-set tuning. A full
     test sweep curve is also written (clearly exploratory) for context.

Outputs (all under results/safety_guided_defense/decision_analysis/):
  validation_probabilities/seed{N}_variantD_bySafetyScore_{cond}_probabilities_val_epsilon_0_03.csv
  false_alarm_probability_diagnosis.csv
  threshold_selection_val_to_test.csv
  test_threshold_sweep_pgd.csv
  figures/fig_fall_prob_distributions.png
  figures/fig_threshold_recall_vs_falsealarms.png

Command:
    python scripts/analyze_false_alarm_calibration.py
"""

from __future__ import annotations

from pathlib import Path
import csv
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn

WALK, RUN, FALL = 2, 4, 1
EVAL_EPS = 0.03
PGD_STEPS = 10

# Per-seed reference: existing FGSM-defense PGD@0.030 fall recall on TEST
# (from committed results), used for threshold rule D.
FGSM_DEFENSE_PGD_RECALL = {42: 0.089, 43: 0.022}


def setup():
    exp = Path(__file__).resolve().parents[1]
    scripts_dir = exp / "scripts"
    benchmark = exp / "third_party" / "WiFi-CSI-Sensing-Benchmark"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import train_converged_clean_baseline as s1
    s1.patch_sensefi_dataset_loader(benchmark)
    if str(benchmark) not in sys.path:
        sys.path.insert(0, str(benchmark))
    import run_converged_attacks as rca
    from model_factory import build_model
    return exp, benchmark, s1, rca, build_model


def per_window(model, loader, criterion, device, rca, attack, eps, steps):
    """Return arrays: true, pred, fall_prob, max_conf, fall_logit, true_logit."""
    alpha = eps / 6.0
    model.eval()
    T, P, FPB, MC, FL, TL = [], [], [], [], [], []
    for inputs, labels in loader:
        inputs = inputs.to(device).float()
        labels = labels.to(device).long()
        if eps == 0.0:
            adv = inputs.detach()
        else:
            adv = rca.generate_attacked_batch(model, inputs, labels, criterion, attack, eps, alpha, steps)
        with torch.no_grad():
            logits = model(adv).float()
            probs = torch.softmax(logits, dim=1)
            conf, preds = torch.max(probs, dim=1)
        lg = logits.cpu().numpy(); pb = probs.cpu().numpy()
        lab = labels.cpu().numpy(); pr = preds.cpu().numpy(); cf = conf.cpu().numpy()
        for i in range(len(lab)):
            T.append(int(lab[i])); P.append(int(pr[i]))
            FPB.append(float(pb[i][FALL])); MC.append(float(cf[i]))
            FL.append(float(lg[i][FALL])); TL.append(float(lg[i][int(lab[i])]))
    return (np.array(T), np.array(P), np.array(FPB), np.array(MC), np.array(FL), np.array(TL))


def write_prob_csv(path, T, P, FPB, MC, FL, TL, s1, cond, eps):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sample_id", "condition", "epsilon", "true_label", "true_class_name",
                    "predicted_label", "fall_true_binary", "fall_pred_binary",
                    "fall_probability", "max_confidence", "fall_logit", "true_class_logit"])
        for i in range(len(T)):
            w.writerow([i, cond, f"{eps:.6f}", T[i], s1.CLASS_NAMES.get(int(T[i]), "?"),
                        P[i], 1 if T[i] == FALL else 0, 1 if P[i] == FALL else 0,
                        f"{FPB[i]:.6f}", f"{MC[i]:.6f}", f"{FL[i]:.6f}", f"{TL[i]:.6f}"])


def stats(x):
    if len(x) == 0:
        return dict(n=0, mean=float("nan"), median=float("nan"), p25=float("nan"),
                    p75=float("nan"), min=float("nan"), max=float("nan"))
    return dict(n=len(x), mean=float(np.mean(x)), median=float(np.median(x)),
                p25=float(np.percentile(x, 25)), p75=float(np.percentile(x, 75)),
                min=float(np.min(x)), max=float(np.max(x)))


def binmetrics_threshold(T, FPB, t):
    """Binary fall alert = fall_prob >= t."""
    true_fall = (T == FALL)
    alert = (FPB >= t)
    tp = int(np.sum(true_fall & alert)); fn = int(np.sum(true_fall & ~alert))
    fp = int(np.sum(~true_fall & alert)); tn = int(np.sum(~true_fall & ~alert))
    rec = tp / (tp + fn) if tp + fn else 0.0
    prec = tp / (tp + fp) if tp + fp else 0.0
    spec = tn / (tn + fp) if tn + fp else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return dict(t=t, recall=rec, fp=fp, precision=prec, specificity=spec, fpr=fpr, f1=f1,
                missed=fn, tp=tp, tn=tn)


def main():
    exp, benchmark, s1, rca, build_model = setup()
    out = exp / "results" / "safety_guided_defense" / "decision_analysis"
    valdir = out / "validation_probabilities"
    figdir = out / "figures"
    valdir.mkdir(parents=True, exist_ok=True)
    figdir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    criterion = nn.CrossEntropyLoss()

    s1.set_seed(0)
    data = s1.load_raw_ut_har(benchmark)
    _, val_loader, test_loader, _ = s1.build_loaders(data, 64)

    conditions = [("clean", "fgsm", 0.0, 0), ("fgsm", "fgsm", EVAL_EPS, 0), ("pgd", "pgd", EVAL_EPS, PGD_STEPS)]
    ck_tmpl = "checkpoints/safety_guided_defense/seed{N}/seed{N}_variantD_fgsm_pgd_multieps_at_fw3_50clean_25fgsm_25pgd_bySafetyScore_best.pt"

    # Holders: data[seed][split][cond] = arrays tuple
    store = {}
    for N in (42, 43):
        ckpt = exp / ck_tmpl.format(N=N)
        state = torch.load(ckpt, map_location=device, weights_only=False)
        model = build_model("lenet").to(device)
        model.load_state_dict(state["model_state_dict"], strict=True)
        store[N] = {"val": {}, "test": {}}
        for split, loader in [("val", val_loader), ("test", test_loader)]:
            for cond, attack, eps, steps in conditions:
                arrs = per_window(model, loader, criterion, device, rca, attack, eps, steps)
                store[N][split][cond] = arrs
                if split == "val":
                    write_prob_csv(valdir / f"seed{N}_variantD_bySafetyScore_{cond}_probabilities_val_epsilon_0_03.csv",
                                   *arrs, s1, cond, eps)
        print(f"[generated] seed {N}: val+test probabilities for clean/fgsm/pgd")

    # ---------- Section 4: false-alarm probability diagnosis (TEST PGD) ----------
    diag_path = out / "false_alarm_probability_diagnosis.csv"
    with diag_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["seed", "group", "n", "fallprob_mean", "fallprob_median", "fallprob_p25",
                    "fallprob_p75", "fallprob_min", "fallprob_max",
                    "fall_minus_true_logit_mean", "fall_minus_true_logit_median", "maxconf_median"])
        for N in (42, 43):
            T, P, FPB, MC, FL, TL = store[N]["test"]["pgd"]
            margin = FL - TL
            groups = {
                "true_fall": (T == FALL),
                "walk_false_alarm": (T == WALK) & (P == FALL),
                "run_false_alarm": (T == RUN) & (P == FALL),
                "other_nonfall_false_alarm": (T != FALL) & (T != WALK) & (T != RUN) & (P == FALL),
            }
            for gname, mask in groups.items():
                st = stats(FPB[mask])
                mm = margin[mask]; mc = MC[mask]
                w.writerow([N, gname, st["n"], f"{st['mean']:.4f}", f"{st['median']:.4f}",
                            f"{st['p25']:.4f}", f"{st['p75']:.4f}", f"{st['min']:.4f}", f"{st['max']:.4f}",
                            (f"{np.mean(mm):.4f}" if len(mm) else "nan"),
                            (f"{np.median(mm):.4f}" if len(mm) else "nan"),
                            (f"{np.median(mc):.4f}" if len(mc) else "nan")])
    print(f"[wrote] {diag_path}")

    # ---------- Section 5: validation-selected threshold sweep ----------
    grid = np.round(np.arange(0.0, 1.0001, 0.01), 4)
    sel_path = out / "threshold_selection_val_to_test.csv"
    sweep_path = out / "test_threshold_sweep_pgd.csv"
    LAMBDA_FN, LAMBDA_FP = 10.0, 1.0
    FPR_BOUND = 0.15

    with sweep_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["seed", "threshold", "test_pgd_recall", "test_pgd_false_alarms",
                    "test_pgd_precision", "test_pgd_specificity", "test_pgd_fpr", "test_pgd_f1"])
        for N in (42, 43):
            T, P, FPB, *_ = store[N]["test"]["pgd"]
            for t in grid:
                m = binmetrics_threshold(T, FPB, t)
                w.writerow([N, f"{t:.2f}", f"{m['recall']:.4f}", m['fp'], f"{m['precision']:.4f}",
                            f"{m['specificity']:.4f}", f"{m['fpr']:.4f}", f"{m['f1']:.4f}"])
    print(f"[wrote] {sweep_path}")

    with sel_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["seed", "rule", "selected_threshold", "val_pgd_recall", "val_pgd_fpr",
                    "test_pgd_recall", "test_pgd_false_alarms", "test_pgd_precision",
                    "test_pgd_specificity", "test_pgd_fpr", "test_pgd_f1",
                    "argmax_test_pgd_recall", "argmax_test_pgd_false_alarms"])
        for N in (42, 43):
            vT, vP, vFPB, *_ = store[N]["val"]["pgd"]
            tT, tP, tFPB, *_ = store[N]["test"]["pgd"]
            val_curve = [binmetrics_threshold(vT, vFPB, t) for t in grid]
            # argmax operating point on test (reference)
            argmax_alert = (tP == FALL); tf = (tT == FALL)
            am_rec = int(np.sum(tf & argmax_alert)) / max(int(np.sum(tf)), 1)
            am_fp = int(np.sum(~tf & argmax_alert))

            def eval_test(t):
                return binmetrics_threshold(tT, tFPB, t)

            rules = {}
            # A: maximize val F1
            rules["A_max_val_f1"] = max(val_curve, key=lambda m: m["f1"])['t']
            # B: max val recall s.t. val FPR <= bound
            elig = [m for m in val_curve if m["fpr"] <= FPR_BOUND]
            rules["B_maxrecall_fpr<=0.15"] = (max(elig, key=lambda m: m["recall"])['t'] if elig else 1.0)
            # C: min cost = missed*lFN + fp*lFP on val
            rules["C_min_cost_FN10_FP1"] = min(val_curve, key=lambda m: m["missed"] * LAMBDA_FN + m["fp"] * LAMBDA_FP)['t']
            # D: min val FP s.t. val recall >= FGSM-defense test recall bar
            bar = FGSM_DEFENSE_PGD_RECALL[N]
            elig_d = [m for m in val_curve if m["recall"] >= bar]
            rules["D_minFP_recall>=fgsmdef"] = (min(elig_d, key=lambda m: m["fp"])['t'] if elig_d else 0.0)

            for rule, t in rules.items():
                vm = binmetrics_threshold(vT, vFPB, t)
                tm = eval_test(t)
                w.writerow([N, rule, f"{t:.2f}", f"{vm['recall']:.4f}", f"{vm['fpr']:.4f}",
                            f"{tm['recall']:.4f}", tm['fp'], f"{tm['precision']:.4f}",
                            f"{tm['specificity']:.4f}", f"{tm['fpr']:.4f}", f"{tm['f1']:.4f}",
                            f"{am_rec:.4f}", am_fp])
    print(f"[wrote] {sel_path}")

    # ---------- Figures ----------
    # Fig 1: fall_prob distributions (test PGD) per group, per seed.
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, N in zip(axes, (42, 43)):
        T, P, FPB, *_ = store[N]["test"]["pgd"]
        groups = [("true fall", (T == FALL), "tab:green"),
                  ("walk->fall FA", (T == WALK) & (P == FALL), "tab:red"),
                  ("run->fall FA", (T == RUN) & (P == FALL), "tab:purple"),
                  ("other FA", (T != FALL) & (T != WALK) & (T != RUN) & (P == FALL), "tab:gray")]
        data_box = [FPB[m] for _, m, _ in groups if np.sum(m) > 0]
        labels_box = [f"{lbl}\n(n={int(np.sum(m))})" for lbl, m, _ in groups if np.sum(m) > 0]
        ax.boxplot(data_box, labels=labels_box, showfliers=False)
        ax.set_title(f"Seed {N} - fall-prob by group (test, PGD@0.030)")
        ax.set_ylabel("fall-class probability"); ax.set_ylim(0, 1.0); ax.grid(True, axis="y", alpha=0.3)
        ax.tick_params(axis="x", labelsize=8)
    fig.tight_layout(); fig.savefig(figdir / "fig_fall_prob_distributions.png", dpi=150); plt.close(fig)
    print(f"[wrote] {figdir / 'fig_fall_prob_distributions.png'}")

    # Fig 2: test PGD recall vs false alarms as threshold varies, per seed.
    fig, ax = plt.subplots(figsize=(8, 6))
    for N, color in [(42, "tab:blue"), (43, "tab:orange")]:
        T, P, FPB, *_ = store[N]["test"]["pgd"]
        recs, fps = [], []
        for t in grid:
            m = binmetrics_threshold(T, FPB, t)
            recs.append(m["recall"]); fps.append(m["fp"])
        ax.plot(fps, recs, "-", color=color, label=f"seed {N} (threshold sweep)", linewidth=1.6)
        # argmax operating point
        tf = (T == FALL); am_rec = int(np.sum(tf & (P == FALL))) / max(int(np.sum(tf)), 1)
        am_fp = int(np.sum(~tf & (P == FALL)))
        ax.scatter([am_fp], [am_rec], color=color, marker="*", s=160, zorder=5,
                   label=f"seed {N} argmax operating point")
    ax.set_xlabel("false-fall alarms (test, PGD@0.030)"); ax.set_ylabel("fall recall (test, PGD@0.030)")
    ax.set_title("Binary fall-alert threshold sweep: recall vs false alarms")
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(figdir / "fig_threshold_recall_vs_falsealarms.png", dpi=150); plt.close(fig)
    print(f"[wrote] {figdir / 'fig_threshold_recall_vs_falsealarms.png'}")

    print("[done] false-alarm calibration analysis complete.")


if __name__ == "__main__":
    main()
