"""
Capstone figure: clean -> PGD separability collapse across every defense attempt and both
representations. One slope per approach (clean AUROC of P(fall) -> PGD AUROC), showing all models
start near-perfect on clean and collapse under PGD@0.03, none crossing the G1 ceiling toward the target.

Read-only: numbers are transcribed from the committed go/no-go artifacts (validation PGD-10). No
training, no test data. Saves PNG to final_defense_synthesis/figures/.
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

EXP = Path(__file__).resolve().parents[1]
OUT = EXP / "results/safety_guided_defense/final_defense_synthesis/figures"
OUT.mkdir(parents=True, exist_ok=True)
THESIS = EXP / "thesis_artifacts/chapter6/figures"
THESIS.mkdir(parents=True, exist_ok=True)

# (label, clean AUROC, PGD AUROC, family)  -- validation, P(fall), from committed artifacts
ROWS = [
    ("G1 LeNet\n(baseline)", 0.992, 0.876, "lenet"),
    ("DS-SGE\ngate",         0.99,  0.805, "lenet"),
    ("Option B\nLagrangian", 0.99,  0.840, "lenet"),
    ("TRADES\nβ=3",          0.99,  0.876, "lenet"),
    ("TRADES\nβ=6",          0.99,  0.869, "lenet"),
    ("GAIRAT",               0.99,  0.871, "lenet"),
    ("SAT",                  0.994, 0.873, "lenet"),
    ("BiLSTM G1\n(repr.)",   0.994, 0.726, "bilstm"),
]
CEILING = 0.876

fig, ax = plt.subplots(figsize=(11, 6))
xs = range(len(ROWS))
for x, (label, c, p, fam) in zip(xs, ROWS):
    col = "#c0392b" if fam == "bilstm" else "#2c3e50"
    ax.plot([x, x], [c, p], color=col, lw=2, alpha=0.55, zorder=1)
    ax.scatter([x], [c], s=70, color="#27ae60", zorder=3, edgecolor="white", linewidth=0.8)
    ax.scatter([x], [p], s=90, color=col, zorder=3, edgecolor="white", linewidth=0.8)
    ax.annotate(f"{p:.3f}", (x, p), textcoords="offset points", xytext=(0, -16),
                ha="center", fontsize=8.5, color=col, fontweight="bold")

ax.axhline(CEILING, color="#7f8c8d", ls="--", lw=1.3, zorder=0)
ax.text(len(ROWS) - 0.5, CEILING + 0.004, "best LeNet validation frontier (G1) ≈ 0.876",
        ha="right", fontsize=9, color="#7f8c8d")
ax.axhspan(0.90, 1.0, color="#2ecc71", alpha=0.07, zorder=0)
ax.text(0.05, 0.945, "higher separability would be needed to approach the target (illustrative band)",
        fontsize=8.5, color="#1e8449", style="italic")

ax.scatter([], [], s=70, color="#27ae60", label="clean AUROC of P(fall)")
ax.scatter([], [], s=90, color="#2c3e50", label="PGD@0.03 AUROC — LeNet interventions")
ax.scatter([], [], s=90, color="#c0392b", label="PGD@0.03 AUROC — BiLSTM (representation change)")
ax.legend(loc="lower left", fontsize=9, framealpha=0.9)

ax.set_xticks(list(xs)); ax.set_xticklabels([r[0] for r in ROWS], fontsize=9)
ax.set_ylabel("AUROC of fall-score separability (fall vs non-fall)", fontsize=11)
ax.set_ylim(0.66, 1.005)
ax.set_title("Observed PGD fall-separability frontier across defense and representation variants\n"
             "Threshold-free AUROC of fall-score separability (validation, seed 42). PGD@0.030 "
             "lowers every model's\nseparability; the final safety target (recall ≥ 0.80 @ FAR ≤ 0.10) "
             "is a separate operating-point criterion.",
             fontsize=10.5)
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
for out in (OUT / "representation_ceiling.png", THESIS / "ch06_figure_6_9_pgd_separability_frontier.png"):
    fig.savefig(out, dpi=160)
    print(f"wrote {out}")
