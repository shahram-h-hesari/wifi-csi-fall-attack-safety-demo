from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
DATA_CSV = HERE / "figure_6_1_summary.csv"
OUT_PNG = HERE / "figure_6_1_defense_effect_summary.png"

df = pd.read_csv(DATA_CSV)

expected = {
    ("Clean", "Undefended"): (0.9556, 0),
    ("Clean", "Defended FGSM-AT"): (0.9111, 8),
    ("FGSM 0.03", "Undefended"): (0.0000, 47),
    ("FGSM 0.03", "Defended FGSM-AT"): (0.3111, 27),
    ("PGD 0.03", "Undefended"): (0.0000, 48),
    ("PGD 0.03", "Defended FGSM-AT"): (0.0889, 54),
}

for _, row in df.iterrows():
    key = (row["condition"], row["model"])
    if key not in expected:
        raise RuntimeError(f"Unexpected row: {key}")
    exp_recall, exp_fp = expected[key]
    if abs(float(row["fall_recall"]) - exp_recall) > 1e-6 or int(row["false_fall_alarms"]) != exp_fp:
        raise RuntimeError(
            f"Data mismatch for {key}: got recall={row['fall_recall']}, "
            f"FP={row['false_fall_alarms']}; expected recall={exp_recall}, FP={exp_fp}"
        )

conditions = ["Clean", "FGSM 0.03", "PGD 0.03"]
models = ["Undefended", "Defended FGSM-AT"]
x = np.arange(len(conditions))
width = 0.36

fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))

ax = axes[0]
for i, model in enumerate(models):
    vals = [
        float(df[(df["condition"] == c) & (df["model"] == model)]["fall_recall"].iloc[0])
        for c in conditions
    ]
    offset = (i - 0.5) * width
    bars = ax.bar(x + offset, vals, width, label=model)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.025,
                f"{val:.3f}", ha="center", va="bottom", fontsize=8)

ax.set_title("(a) Fall recall")
ax.set_ylabel("Fall recall")
ax.set_xticks(x)
ax.set_xticklabels(conditions)
ax.set_ylim(0, 1.08)
ax.grid(axis="y", alpha=0.25)
ax.legend(fontsize=8)

ax = axes[1]
for i, model in enumerate(models):
    fps = [
        int(df[(df["condition"] == c) & (df["model"] == model)]["false_fall_alarms"].iloc[0])
        for c in conditions
    ]
    fars = [fp / 455 for fp in fps]
    offset = (i - 0.5) * width
    bars = ax.bar(x + offset, fps, width, label=model)
    for bar, fp, far in zip(bars, fps, fars):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f"{fp}\n({100*far:.1f}%)", ha="center", va="bottom", fontsize=8)

ax.set_title("(b) False-fall alarms")
ax.set_ylabel("False-fall alarms among 455 non-fall windows")
ax.set_xticks(x)
ax.set_xticklabels(conditions)
ax.set_ylim(0, 65)
ax.grid(axis="y", alpha=0.25)
ax.legend(fontsize=8)

fig.suptitle("Defense-effect summary under the primary ε = 0.030 attack condition", y=1.02)
fig.tight_layout()
fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
plt.close(fig)

print("Regenerated:", OUT_PNG)
print("Source CSV:", DATA_CSV)
print(df.to_string(index=False))
