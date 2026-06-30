"""
DS-SGE Stage A figures: recall-FAR frontier, error-overlap, confusion matrices.

Reads the Stage A outputs (test_probabilities.csv, frontier_points.csv,
error_overlap.csv, gate_config.json, metrics_adaptive_gate_pgd_eps003.csv) and
renders the four committee figures. Plotting only; no model, no attack.

The frontier figure traces, on the TEST PGD condition, the achievable
recall-vs-FAR curve of: (a) thresholding f_R's P(fall), (b) thresholding f_B's
P(fall), and (c) the gate alpha*p_R+(1-alpha)*p_B at the locked alpha, plus the
locked operating point, the adaptive full-gate point, the best prior frontier
(G1 seed44: recall 0.600, FAR 0.143), and the target zone (FAR<=0.10,
recall>=0.80). This directly shows whether the gate moves OUT of or only ALONG
the frontier.

Command:
    python scripts/plot_dsge_stage_a.py --base results/.../A1/seed42
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


G1_SEED44 = {"recall": 0.600, "far": 0.143, "label": "G1 seed44 (best prior)"}
TARGET = {"recall": 0.80, "far": 0.10}


def threshold_curve(p, fall_true, taus):
    fall_true = fall_true.astype(bool)
    rec, far = [], []
    nfall = fall_true.sum(); nnon = (~fall_true).sum()
    for t in taus:
        pred = p >= t
        tp = (fall_true & pred).sum(); fp = (~fall_true & pred).sum()
        rec.append(tp / nfall if nfall else 0.0)
        far.append(fp / nnon if nnon else 0.0)
    return np.array(far), np.array(rec)


def plot_frontier(base: Path, cfg: dict):
    test = pd.read_csv(base / "test_probabilities.csv")
    pgd = test[test["attack_type"] == "pgd"]
    p_R = pgd["p_R_fall"].to_numpy(); p_B = pgd["p_B_fall"].to_numpy()
    y = pgd["fall_true_binary"].to_numpy()
    alpha, tau = cfg["alpha"], cfg["tau"]
    taus = np.linspace(0, 1, 201)

    far_R, rec_R = threshold_curve(p_R, y, taus)
    far_B, rec_B = threshold_curve(p_B, y, taus)
    S = alpha * p_R + (1 - alpha) * p_B
    far_G, rec_G = threshold_curve(S, y, taus)

    fig, ax = plt.subplots(figsize=(7.2, 6.0))
    # target zone
    ax.axhspan(TARGET["recall"], 1.0, xmin=0, xmax=TARGET["far"], alpha=0.10, color="green")
    ax.add_patch(plt.Rectangle((0, TARGET["recall"]), TARGET["far"], 1 - TARGET["recall"],
                               fill=True, alpha=0.12, color="green", label="target zone"))
    ax.axvline(TARGET["far"], ls=":", lw=1, color="green")
    ax.axhline(TARGET["recall"], ls=":", lw=1, color="green")

    ax.plot(far_R, rec_R, "-", color="#c0392b", lw=1.8, label="f_R threshold curve")
    ax.plot(far_B, rec_B, "-", color="#2980b9", lw=1.8, label="f_B threshold curve")
    ax.plot(far_G, rec_G, "-", color="#8e44ad", lw=2.2, label=f"gate curve (alpha={alpha:.2f})")

    # native argmax points
    fp = pd.read_csv(base / "frontier_points.csv")
    pgd_pts = fp[fp["attack"] == "pgd"]
    marker = {"f_R_alone_argmax": ("^", "#c0392b"), "f_B_alone_argmax": ("v", "#2980b9"),
              "DS_SGE_gate": ("*", "#8e44ad")}
    for _, r in pgd_pts.iterrows():
        m, c = marker.get(r["system"], ("o", "k"))
        ax.scatter(r["false_alarm_rate"], r["fall_recall"], marker=m, s=140, color=c,
                   edgecolor="k", zorder=5,
                   label=f"{r['system']} (PGD)")

    # locked gate operating point (explicit)
    ax.scatter([cfg["val_locked_metrics_all_conditions"]["pgd"]["false_alarm_rate"]],
               [cfg["val_locked_metrics_all_conditions"]["pgd"]["fall_recall"]],
               marker="X", s=80, color="#8e44ad", edgecolor="white", zorder=6)

    # adaptive full-gate point
    adp = pd.read_csv(base / "metrics_adaptive_gate_pgd_eps003.csv").iloc[0]
    ax.scatter([adp["false_alarm_rate"]], [adp["fall_recall"]], marker="P", s=160,
               color="black", zorder=6, label="adaptive full-gate PGD")

    # best prior frontier
    ax.scatter([G1_SEED44["far"]], [G1_SEED44["recall"]], marker="D", s=120,
               facecolor="none", edgecolor="darkgreen", lw=2, zorder=6, label=G1_SEED44["label"])

    ax.set_xlabel("attacked false-alarm rate  FP/(FP+TN)")
    ax.set_ylabel("attacked fall recall  TP/(TP+FN)")
    ax.set_xlim(-0.01, 0.6); ax.set_ylim(0, 1.02)
    ax.set_title("DS-SGE recall vs false-alarm frontier (TEST, PGD@0.03)")
    ax.legend(fontsize=7, loc="lower right", framealpha=0.9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(base / "figures" / "fig_recall_far_frontier.png", dpi=150)
    plt.close(fig)


def plot_overlap(base: Path):
    ov = pd.read_csv(base / "error_overlap.csv")
    row = ov[(ov["split"] == "test") & (ov["attack"] == "pgd")].iloc[0]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    axes[0].bar(["R only", "B only", "both"],
                [row["missed_by_R_only"], row["missed_by_B_only"], row["missed_by_both"]],
                color=["#c0392b", "#2980b9", "#7f8c8d"])
    axes[0].set_title(f"Missed falls (TEST PGD, n_fall={int(row['n_fall'])})\n"
                      f"union recall={row['argmax_union_recall']:.3f}  "
                      f"R={row['recall_R_argmax']:.3f}  B={row['recall_B_argmax']:.3f}")
    axes[0].set_ylabel("count")
    axes[1].bar(["R only", "B only", "both"],
                [row["fa_by_R_only"], row["fa_by_B_only"], row["fa_by_both"]],
                color=["#c0392b", "#2980b9", "#7f8c8d"])
    axes[1].set_title(f"False alarms (TEST PGD, n_nonfall={int(row['n_nonfall'])})")
    axes[1].set_ylabel("count")
    for ax in axes:
        for i, p in enumerate(ax.patches):
            ax.annotate(str(int(p.get_height())), (p.get_x() + p.get_width() / 2, p.get_height()),
                        ha="center", va="bottom")
    fig.suptitle("Specialist error complementarity (B detections nested in R = no gate gain)")
    fig.tight_layout()
    fig.savefig(base / "figures" / "fig_error_overlap.png", dpi=150)
    plt.close(fig)


def plot_confusion(base: Path, cfg: dict, cond: str, fname: str):
    test = pd.read_csv(base / "test_probabilities.csv")
    d = test[test["attack_type"] == cond]
    S = cfg["alpha"] * d["p_R_fall"].to_numpy() + (1 - cfg["alpha"]) * d["p_B_fall"].to_numpy()
    pred = (S >= cfg["tau"]).astype(int)
    y = d["fall_true_binary"].to_numpy()
    tp = int(((y == 1) & (pred == 1)).sum()); fn = int(((y == 1) & (pred == 0)).sum())
    fp = int(((y == 0) & (pred == 1)).sum()); tn = int(((y == 0) & (pred == 0)).sum())
    cm = np.array([[tn, fp], [fn, tp]])
    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["pred non-fall", "pred fall"])
    ax.set_yticklabels(["true non-fall", "true fall"])
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black", fontsize=14)
    ax.set_title(f"DS-SGE gate binary confusion ({cond.upper()}, TEST)\n"
                 f"alpha={cfg['alpha']:.2f} tau={cfg['tau']:.2f}")
    fig.colorbar(im, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(base / "figures" / fname, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    args = ap.parse_args()
    base = Path(args.base)
    (base / "figures").mkdir(parents=True, exist_ok=True)
    with open(base / "gate_config.json", encoding="utf-8") as f:
        cfg = json.load(f)
    plot_frontier(base, cfg)
    plot_overlap(base)
    plot_confusion(base, cfg, "clean", "fig_confusion_clean.png")
    plot_confusion(base, cfg, "pgd", "fig_confusion_pgd.png")
    print(f"[plots] wrote 4 figures to {base / 'figures'}")


if __name__ == "__main__":
    main()
