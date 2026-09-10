"""Reconstruct Chapter 4 cross-architecture and ResNet18 artifacts.

This is a reconstructed reproducibility generator from verified source data.
The original generator for these thesis-facing artifacts was not found.

The script reads existing CSV and LaTeX artifacts, then writes reconstructed
figures, tables, and comparison reports under:

    results/reconstructed_ch04_cross_arch_resnet/

It does not train models, run attacks, or modify thesis files.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
THESIS_ROOT = Path(
    r"C:\Users\Hesar\Documents\GitHub\thesis-overleaf-linked"
)
OUT_DIR = ROOT / "results" / "reconstructed_ch04_cross_arch_resnet"

MODEL_ORDER = ["LeNet", "GRU", "BiLSTM", "Transformer", "ResNet18"]
ATTACK_ORDER = ["fgsm", "pgd"]

T_CRIT_DF4_95 = 2.7764451051977987


PATHS = {
    "fig47_summary": ROOT
    / "results"
    / "cross_architecture"
    / "cross_architecture_seed42_pilot_summary.csv",
    "fig47_thresholds": ROOT
    / "results"
    / "cross_architecture"
    / "cross_architecture_seed42_pilot_thresholds.csv",
    "fig47_existing": ROOT
    / "results"
    / "cross_architecture"
    / "figures"
    / "cross_architecture_seed42_fall_recall_vs_epsilon.png",
    "fig47_thesis": THESIS_ROOT
    / "images"
    / "ch04_cross_arch_fall_recall_vs_epsilon.png",
    "fig48_summary": ROOT
    / "results"
    / "cross_architecture"
    / "resnet"
    / "resnet18_clean_qualified_summary.csv",
    "fig48_seedwise": ROOT
    / "results"
    / "cross_architecture"
    / "resnet"
    / "resnet18_clean_qualified_seedwise_metrics.csv",
    "fig48_thresholds": ROOT
    / "results"
    / "cross_architecture"
    / "resnet"
    / "resnet18_clean_qualified_thresholds.csv",
    "fig48_convergence": ROOT
    / "results"
    / "cross_architecture"
    / "resnet"
    / "resnet18_seed_convergence_status.csv",
    "fig48_existing": ROOT
    / "results"
    / "cross_architecture"
    / "resnet"
    / "figures"
    / "resnet18_clean_qualified_fall_recall_vs_epsilon.png",
    "fig48_thesis": THESIS_ROOT
    / "images"
    / "ch04_resnet18_multiseed_fall_recall_vs_epsilon.png",
    "table47_csv": ROOT
    / "results"
    / "cross_architecture"
    / "cross_architecture_multiseed_summary.csv",
    "table47_tex": ROOT / "tables" / "chapter_cross_architecture_multiseed_table.tex",
    "table47_note": ROOT
    / "notes"
    / "priority2_cross_architecture_multiseed_summary.md",
    "table48_summary": ROOT
    / "results"
    / "cross_architecture"
    / "resnet"
    / "resnet18_clean_qualified_summary.csv",
    "table48_seedwise": ROOT
    / "results"
    / "cross_architecture"
    / "resnet"
    / "resnet18_clean_qualified_seedwise_metrics.csv",
    "table48_thresholds": ROOT
    / "results"
    / "cross_architecture"
    / "resnet"
    / "resnet18_clean_qualified_thresholds.csv",
    "table48_tex": ROOT / "tables" / "chapter_resnet18_multiseed_table.tex",
}


OUTPUTS = {
    "fig47_reconstructed": OUT_DIR
    / "ch04_figure_4_7_cross_architecture_fall_recall_vs_epsilon_reconstructed.png",
    "fig47_thesis_clean": OUT_DIR
    / "ch04_figure_4_7_cross_architecture_fall_recall_vs_epsilon_thesis_clean.png",
    "fig48_reconstructed": OUT_DIR
    / "ch04_figure_4_8_resnet18_multiseed_fall_recall_vs_epsilon_reconstructed.png",
    "fig48_thesis_clean": OUT_DIR
    / "ch04_figure_4_8_resnet18_multiseed_fall_recall_vs_epsilon_thesis_clean.png",
    "table47_csv": OUT_DIR
    / "table_4_7_cross_architecture_multiseed_reconstructed.csv",
    "table47_tex": OUT_DIR
    / "table_4_7_cross_architecture_multiseed_reconstructed.tex",
    "table47_md": OUT_DIR
    / "table_4_7_cross_architecture_multiseed_reconstructed.md",
    "table48_csv": OUT_DIR / "table_4_8_resnet18_multiseed_reconstructed.csv",
    "table48_tex": OUT_DIR / "table_4_8_resnet18_multiseed_reconstructed.tex",
    "table48_md": OUT_DIR / "table_4_8_resnet18_multiseed_reconstructed.md",
    "report_md": OUT_DIR / "reconstruction_report.md",
    "hash_report": OUT_DIR / "hash_comparison_report.txt",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def require_inputs() -> None:
    missing = [rel(path) for path in PATHS.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required input files:\n" + "\n".join(missing))


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def image_dimensions(path: Path) -> tuple[int, int]:
    image = mpimg.imread(path)
    height, width = image.shape[:2]
    return int(width), int(height)


def file_hash_record(label: str, path: Path) -> dict[str, object]:
    if not path.exists():
        return {
            "label": label,
            "path": rel(path),
            "exists": False,
            "sha256": "",
            "width": "",
            "height": "",
            "bytes": "",
        }
    width, height = image_dimensions(path)
    return {
        "label": label,
        "path": rel(path),
        "exists": True,
        "sha256": sha256_file(path),
        "width": width,
        "height": height,
        "bytes": path.stat().st_size,
    }


def to_float(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = frame.copy()
    for column in columns:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    return out


def load_sweep(path_text: str) -> pd.DataFrame:
    path = ROOT / path_text.strip().replace("/", "\\")
    frame = read_csv(path)
    frame = to_float(frame, ["epsilon", "fall_recall"])
    return frame.sort_values("epsilon")


def plot_figure_4_7() -> None:
    thresholds = read_csv(PATHS["fig47_thresholds"])
    thresholds["model"] = thresholds["model"].astype(str)
    thresholds["attack"] = thresholds["attack"].astype(str).str.lower()

    colors = {
        "LeNet": "#4e7f4d",
        "GRU": "#2b5c8a",
        "BiLSTM": "#8d55bd",
        "Transformer": "#e47c32",
        "ResNet18": "#d9485f",
    }

    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "legend.fontsize": 10,
            "figure.titlesize": 14,
        }
    )

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), dpi=150, sharey=True)
    fig.suptitle(
        "Reconstructed Figure 4.7: cross-architecture fall recall vs epsilon",
        y=0.98,
    )

    for axis, attack in zip(axes, ATTACK_ORDER):
        for model in MODEL_ORDER:
            row = thresholds[
                (thresholds["model"] == model) & (thresholds["attack"] == attack)
            ].iloc[0]
            sweep = load_sweep(row["source_sweep_csv"])
            axis.plot(
                sweep["epsilon"],
                sweep["fall_recall"],
                marker="o",
                markersize=3.2,
                linewidth=1.5,
                color=colors[model],
                label=model,
            )
        axis.axvline(0.03, color="#777777", linestyle="--", linewidth=0.8)
        axis.set_title(f"{attack.upper()} (seed 42)")
        axis.set_xlabel("Perturbation epsilon (L-inf, processed tensor)")
        axis.set_xlim(-0.003, 0.078)
        axis.set_ylim(-0.02, 1.02)
        axis.grid(True, alpha=0.32)

    axes[0].set_ylabel("Fall recall (window-level safety proxy)")
    axes[0].legend(title="Architecture", loc="upper right", frameon=True)

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(
        OUTPUTS["fig47_reconstructed"],
        dpi=150,
        metadata={"Software": "reconstructed_ch04_cross_arch_resnet_artifacts.py"},
    )
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), dpi=150, sharey=True)
    fig.suptitle(
        "Cross-architecture fall recall vs epsilon (seed 42)",
        y=0.98,
    )

    for axis, attack in zip(axes, ATTACK_ORDER):
        for model in MODEL_ORDER:
            row = thresholds[
                (thresholds["model"] == model) & (thresholds["attack"] == attack)
            ].iloc[0]
            sweep = load_sweep(row["source_sweep_csv"])
            axis.plot(
                sweep["epsilon"],
                sweep["fall_recall"],
                marker="o",
                markersize=3.2,
                linewidth=1.5,
                color=colors[model],
                label=model,
            )
        axis.axvline(0.03, color="#777777", linestyle="--", linewidth=0.8)
        axis.set_title(f"{attack.upper()} (seed 42)")
        axis.set_xlabel("L-inf perturbation budget epsilon")
        axis.set_xlim(-0.003, 0.078)
        axis.set_ylim(-0.02, 1.02)
        axis.grid(True, alpha=0.32)

    axes[0].set_ylabel("Fall recall (window-level)")
    axes[0].legend(title="Architecture", loc="upper right", frameon=True)

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(
        OUTPUTS["fig47_thesis_clean"],
        dpi=150,
        metadata={"Software": "reconstructed_ch04_cross_arch_resnet_artifacts.py"},
    )
    plt.close(fig)


def summarize_resnet_sweeps() -> pd.DataFrame:
    thresholds = read_csv(PATHS["fig48_thresholds"])
    thresholds = thresholds[
        thresholds["seed"].astype(str).str.match(r"^[0-9]+$")
    ].copy()
    thresholds["seed"] = thresholds["seed"].astype(int)
    thresholds["attack"] = thresholds["attack"].astype(str).str.lower()

    frames = []
    for _, row in thresholds.iterrows():
        sweep = load_sweep(row["source_sweep_csv"])
        sweep = sweep[["epsilon", "fall_recall"]].copy()
        sweep["seed"] = int(row["seed"])
        sweep["attack"] = row["attack"]
        frames.append(sweep)

    all_sweeps = pd.concat(frames, ignore_index=True)
    rows = []
    for (attack, epsilon), group in all_sweeps.groupby(["attack", "epsilon"]):
        count = int(group["fall_recall"].count())
        mean = float(group["fall_recall"].mean())
        std = float(group["fall_recall"].std(ddof=1)) if count > 1 else 0.0
        if math.isnan(std):
            std = 0.0
        ci = T_CRIT_DF4_95 * std / math.sqrt(count) if count else 0.0
        rows.append(
            {
                "attack": attack,
                "epsilon": float(epsilon),
                "n": count,
                "mean": mean,
                "std": std,
                "ci95_low": max(0.0, mean - ci),
                "ci95_high": min(1.0, mean + ci),
            }
        )
    return pd.DataFrame(rows).sort_values(["attack", "epsilon"])


def plot_figure_4_8(resnet_sweeps: pd.DataFrame) -> None:
    colors = {"fgsm": "#e68613", "pgd": "#b8122d"}

    plt.rcParams.update(
        {
            "font.size": 16,
            "axes.titlesize": 24,
            "axes.labelsize": 20,
            "legend.fontsize": 18,
        }
    )

    fig, axis = plt.subplots(figsize=(16, 9), dpi=100)
    for attack in ATTACK_ORDER:
        attack_frame = resnet_sweeps[resnet_sweeps["attack"] == attack]
        x = attack_frame["epsilon"].tolist()
        y = attack_frame["mean"].tolist()
        low = attack_frame["ci95_low"].tolist()
        high = attack_frame["ci95_high"].tolist()
        axis.fill_between(x, low, high, color=colors[attack], alpha=0.18)
        axis.plot(
            x,
            y,
            marker="o",
            markersize=6,
            linewidth=2.8,
            color=colors[attack],
            label=attack.upper(),
        )

    axis.axvline(0.03, color="#777777", linestyle=":", linewidth=1.8)
    axis.text(0.0305, 0.90, "epsilon=0.03", color="#777777", fontsize=14)
    axis.set_title(
        "Reconstructed Figure 4.8: ResNet18 fall recall vs epsilon "
        "(5 clean-qualified seeds)"
    )
    axis.set_xlabel("L-inf perturbation budget epsilon")
    axis.set_ylabel("Fall recall (window-level)")
    axis.set_xlim(-0.0038, 0.0788)
    axis.set_ylim(0.0, 1.05)
    axis.grid(True, linestyle=":", alpha=0.55)
    axis.legend(loc="upper right", frameon=True)

    fig.tight_layout()
    fig.savefig(
        OUTPUTS["fig48_reconstructed"],
        dpi=100,
        metadata={"Software": "reconstructed_ch04_cross_arch_resnet_artifacts.py"},
    )
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(16, 9), dpi=100)
    for attack in ATTACK_ORDER:
        attack_frame = resnet_sweeps[resnet_sweeps["attack"] == attack]
        x = attack_frame["epsilon"].tolist()
        y = attack_frame["mean"].tolist()
        low = attack_frame["ci95_low"].tolist()
        high = attack_frame["ci95_high"].tolist()
        axis.fill_between(x, low, high, color=colors[attack], alpha=0.18)
        axis.plot(
            x,
            y,
            marker="o",
            markersize=6,
            linewidth=2.8,
            color=colors[attack],
            label=attack.upper(),
        )

    axis.axvline(0.03, color="#777777", linestyle=":", linewidth=1.8)
    axis.text(0.0305, 0.90, "epsilon=0.03", color="#777777", fontsize=14)
    axis.set_title("ResNet18 clean-qualified seeds: fall recall vs epsilon")
    axis.set_xlabel("L-inf perturbation budget epsilon")
    axis.set_ylabel("Fall recall (window-level)")
    axis.set_xlim(-0.0038, 0.0788)
    axis.set_ylim(0.0, 1.05)
    axis.grid(True, linestyle=":", alpha=0.55)
    axis.legend(loc="upper right", frameon=True)

    fig.tight_layout()
    fig.savefig(
        OUTPUTS["fig48_thesis_clean"],
        dpi=100,
        metadata={"Software": "reconstructed_ch04_cross_arch_resnet_artifacts.py"},
    )
    plt.close(fig)


def parse_count(text: object) -> tuple[int, int]:
    left, right = str(text).split("/")
    return int(left), int(right)


def clean_type_label(value: str) -> str:
    text = value.strip()
    replacements = {
        "shallow CNN (LeNet)": "Shallow CNN",
        "deep CNN (ResNet-18)": "Deep CNN",
        "recurrent (GRU)": "Recurrent",
        "bidirectional recurrent (BiLSTM)": "Bidirectional recurrent",
        "attention (ViT)": "Attention (ViT)",
    }
    return replacements.get(text, text)


def mean_sd_text(mean: float, sd: float, digits: int = 3) -> str:
    return f"{mean:.{digits}f} +/- {sd:.{digits}f}"


def mean_sd_latex(mean: float, sd: float, digits: int = 3, bold_zero: bool = False) -> str:
    body = f"{mean:.{digits}f} \\pm {sd:.{digits}f}"
    if bold_zero and abs(mean) < 0.0005 and abs(sd) < 0.0005:
        body = f"\\mathbf{{{body}}}"
    return f"${body}$"


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    def cell(value: object) -> str:
        return str(value).replace("\n", " ").strip()

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell(value) for value in row) + " |")
    return "\n".join(lines) + "\n"


def build_table_4_7() -> dict[str, object]:
    source = read_csv(PATHS["table47_csv"])
    source["architecture"] = source["architecture"].astype(str)
    ordered = (
        source.set_index("architecture")
        .loc[MODEL_ORDER]
        .reset_index()
        .copy()
    )

    records = []
    for _, row in ordered.iterrows():
        records.append(
            {
                "model": row["architecture"],
                "type": clean_type_label(row["type"]),
                "clean_fall_recall_mean": float(row["clean_fall_recall_mean"]),
                "clean_fall_recall_sd": float(row["clean_fall_recall_sd"]),
                "fgsm03_fall_recall_mean": float(row["fgsm03_fall_recall_mean"]),
                "fgsm03_fall_recall_sd": float(row["fgsm03_fall_recall_sd"]),
                "pgd03_fall_recall_mean": float(row["pgd03_fall_recall_mean"]),
                "pgd03_fall_recall_sd": float(row["pgd03_fall_recall_sd"]),
                "fgsm03_exact_collapse_count": row["fgsm03_exact_collapse_count"],
                "pgd03_exact_collapse_count": row["pgd03_exact_collapse_count"],
                "pgd_collapse_by_eps0035_count": row[
                    "pgd_collapse_by_eps0035_count"
                ],
                "evidence_status": row["evidence_status"],
                "notes": row["notes"],
                "source": row["source"],
            }
        )

    out = pd.DataFrame(records)
    out["clean_fall_recall_display"] = out.apply(
        lambda row: mean_sd_text(
            row["clean_fall_recall_mean"], row["clean_fall_recall_sd"]
        ),
        axis=1,
    )
    out["fgsm03_fall_recall_display"] = out.apply(
        lambda row: mean_sd_text(
            row["fgsm03_fall_recall_mean"], row["fgsm03_fall_recall_sd"]
        ),
        axis=1,
    )
    out["pgd03_fall_recall_display"] = out.apply(
        lambda row: mean_sd_text(
            row["pgd03_fall_recall_mean"], row["pgd03_fall_recall_sd"]
        ),
        axis=1,
    )
    out.to_csv(OUTPUTS["table47_csv"], index=False)

    pgd_exact_num = 0
    pgd_exact_den = 0
    pgd_by_num = 0
    pgd_by_den = 0
    for _, row in out.iterrows():
        num, den = parse_count(row["pgd03_exact_collapse_count"])
        pgd_exact_num += num
        pgd_exact_den += den
        num, den = parse_count(row["pgd_collapse_by_eps0035_count"])
        pgd_by_num += num
        pgd_by_den += den

    note = (
        f"PGD reaches exactly 0.000 fall recall at epsilon 0.03 in "
        f"{pgd_exact_num}/{pgd_exact_den} clean-qualified seed-runs and all "
        f"{pgd_by_den} by epsilon <= 0.035."
    )

    latex_lines = [
        "% Reconstructed Chapter 4 Table 4.7 from verified source CSV.",
        "% Original generation script not found.",
        "\\begin{table}[t]",
        "  \\centering",
        "  \\caption{Reconstructed cross-architecture multi-seed result.}",
        "  \\label{tab:cross-arch-multiseed-reconstructed}",
        "  \\begin{tabular}{l l c c c c}",
        "    \\toprule",
        (
            "    Model & Type & Clean fall recall & "
            "FGSM$_{\\varepsilon{=}0.03}$ & PGD$_{\\varepsilon{=}0.03}$ & "
            "Exact $0.000$ @ $\\varepsilon{=}0.03$ (FGSM / PGD) \\\\"
        ),
        "    \\midrule",
    ]
    md_rows = []
    for _, row in out.iterrows():
        clean = mean_sd_latex(
            row["clean_fall_recall_mean"], row["clean_fall_recall_sd"]
        )
        fgsm = mean_sd_latex(
            row["fgsm03_fall_recall_mean"], row["fgsm03_fall_recall_sd"]
        )
        pgd = mean_sd_latex(
            row["pgd03_fall_recall_mean"],
            row["pgd03_fall_recall_sd"],
            bold_zero=True,
        )
        exact = (
            f"{row['fgsm03_exact_collapse_count']} / "
            f"{row['pgd03_exact_collapse_count']}"
        )
        latex_lines.append(
            f"    {row['model']} & {row['type']} & {clean} & {fgsm} & {pgd} & "
            f"{exact} \\\\"
        )
        md_rows.append(
            [
                row["model"],
                row["type"],
                row["clean_fall_recall_display"],
                row["fgsm03_fall_recall_display"],
                row["pgd03_fall_recall_display"],
                exact,
            ]
        )
    latex_lines.extend(
        [
            "    \\bottomrule",
            "  \\end{tabular}",
            f"  \\\\[0.3em]{{\\footnotesize {note}}}",
            "\\end{table}",
            "",
        ]
    )
    OUTPUTS["table47_tex"].write_text("\n".join(latex_lines), encoding="utf-8")

    md = [
        "# Reconstructed Table 4.7",
        "",
        "Source: results/cross_architecture/cross_architecture_multiseed_summary.csv",
        "",
        markdown_table(
            [
                "Model",
                "Type",
                "Clean fall recall",
                "FGSM eps=0.03",
                "PGD eps=0.03",
                "Exact 0.000 at eps=0.03 (FGSM / PGD)",
            ],
            md_rows,
        ),
        note,
        "",
    ]
    OUTPUTS["table47_md"].write_text("\n".join(md), encoding="utf-8")

    return {"display": out, "note": note}


def stat_row(summary: pd.DataFrame, condition: str, metric: str) -> pd.Series:
    match = summary[
        (summary["condition"] == condition) & (summary["metric"] == metric)
    ]
    if match.empty:
        raise ValueError(f"Missing summary row for {condition} / {metric}")
    return match.iloc[0]


def condition_label(condition: str) -> str:
    return {
        "clean": "Clean",
        "fgsm_eps0.03": "FGSM epsilon=0.03",
        "pgd_eps0.03": "PGD epsilon=0.03",
    }[condition]


def condition_latex(condition: str) -> str:
    return {
        "clean": "Clean",
        "fgsm_eps0.03": "FGSM $\\varepsilon{=}0.03$",
        "pgd_eps0.03": "PGD $\\varepsilon{=}0.03$",
    }[condition]


def metric_label(metric: str) -> str:
    return {
        "fall_recall": "Fall recall",
        "false_fall_alarms": "False-fall alarms",
    }[metric]


def format_table48_mean_sd(condition: str, metric: str, mean: float, std: float) -> str:
    if metric == "fall_recall":
        return mean_sd_text(mean, std, 3)
    digits = 2 if condition == "clean" else 1
    return mean_sd_text(mean, std, digits)


def format_table48_mean_sd_latex(
    condition: str, metric: str, mean: float, std: float
) -> str:
    if metric == "fall_recall":
        return mean_sd_latex(
            mean,
            std,
            3,
            bold_zero=(condition == "pgd_eps0.03"),
        )
    digits = 2 if condition == "clean" else 1
    return mean_sd_latex(mean, std, digits)


def format_table48_ci(condition: str, metric: str, low: float, high: float) -> str:
    if metric == "fall_recall":
        low_clipped = max(0.0, low)
        high_clipped = min(1.0, high)
        if abs(low_clipped) < 0.0005 and high_clipped > 0.0005:
            low_text = "0"
        else:
            low_text = f"{low_clipped:.3f}"
        return f"[{low_text}, {high_clipped:.3f}]"
    return f"[{low:.1f}, {high:.1f}]"


def format_table48_ci_latex(condition: str, metric: str, low: float, high: float) -> str:
    return "$" + format_table48_ci(condition, metric, low, high).replace(", ", ",\\ ") + "$"


def build_table_4_8() -> dict[str, object]:
    summary = read_csv(PATHS["table48_summary"])
    seedwise = read_csv(PATHS["table48_seedwise"])
    convergence = read_csv(PATHS["fig48_convergence"])

    summary = to_float(
        summary,
        ["mean", "std", "sem", "ci95_low", "ci95_high"],
    )
    seedwise = to_float(
        seedwise,
        [
            "seed",
            "clean_accuracy",
            "clean_fall_recall",
            "pgd03_fall_recall",
        ],
    )
    convergence = to_float(
        convergence,
        ["seed", "clean_accuracy", "clean_fall_recall"],
    )

    aggregate_rows = []
    for condition in ["clean", "fgsm_eps0.03", "pgd_eps0.03"]:
        for metric in ["fall_recall", "false_fall_alarms"]:
            row = stat_row(summary, condition, metric)
            aggregate_rows.append(
                {
                    "panel": "aggregate",
                    "condition": condition_label(condition),
                    "metric": metric_label(metric),
                    "mean": float(row["mean"]),
                    "std": float(row["std"]),
                    "ci95_low": float(row["ci95_low"]),
                    "ci95_high": float(row["ci95_high"]),
                    "display_mean_sd": format_table48_mean_sd(
                        condition, metric, float(row["mean"]), float(row["std"])
                    ),
                    "display_ci": format_table48_ci(
                        condition,
                        metric,
                        float(row["ci95_low"]),
                        float(row["ci95_high"]),
                    ),
                    "seed": "",
                    "status": "",
                    "clean_accuracy": "",
                    "clean_fall_recall": "",
                    "pgd03_fall_recall": "",
                }
            )

    seed_rows = []
    clean_seedwise = seedwise.set_index("seed")
    convergence_by_seed = convergence.copy()
    convergence_by_seed["seed"] = convergence_by_seed["seed"].astype(int)
    convergence_by_seed = convergence_by_seed.set_index("seed")
    clean_seed_order = [int(seed) for seed in seedwise.sort_values("seed")["seed"]]
    excluded_seed_order = [
        int(seed)
        for seed in convergence_by_seed.sort_index().index
        if int(seed) not in clean_seed_order
    ]
    seed_order = clean_seed_order + excluded_seed_order
    for seed in seed_order:
        row = convergence_by_seed.loc[seed]
        status = str(row["status"]).replace("_", "-")
        pgd_value = ""
        if status == "clean-qualified":
            pgd_value = float(clean_seedwise.loc[seed, "pgd03_fall_recall"])
        seed_rows.append(
            {
                "panel": "seed",
                "condition": "",
                "metric": "",
                "mean": "",
                "std": "",
                "ci95_low": "",
                "ci95_high": "",
                "display_mean_sd": "",
                "display_ci": "",
                "seed": seed,
                "status": status,
                "clean_accuracy": float(row["clean_accuracy"]),
                "clean_fall_recall": float(row["clean_fall_recall"]),
                "pgd03_fall_recall": pgd_value,
            }
        )

    output_frame = pd.DataFrame(aggregate_rows + seed_rows)
    output_frame.to_csv(OUTPUTS["table48_csv"], index=False)

    latex_lines = [
        "% Reconstructed Chapter 4 Table 4.8 from verified source CSVs.",
        "% Original generation script not found.",
        "\\begin{table}[t]",
        "  \\centering",
        "  \\caption{Reconstructed ResNet18 multi-seed clean-qualified result.}",
        "  \\label{tab:resnet18-multiseed-reconstructed}",
        "  \\begin{tabular}{l l c c}",
        "    \\toprule",
        "    Condition & Metric & Mean $\\pm$ SD & 95\\% CI \\\\",
        "    \\midrule",
    ]
    md_agg_rows = []
    for condition in ["clean", "fgsm_eps0.03", "pgd_eps0.03"]:
        for metric in ["fall_recall", "false_fall_alarms"]:
            row = stat_row(summary, condition, metric)
            mean = float(row["mean"])
            std = float(row["std"])
            low = float(row["ci95_low"])
            high = float(row["ci95_high"])
            latex_lines.append(
                f"    {condition_latex(condition)} & {metric_label(metric)} & "
                f"{format_table48_mean_sd_latex(condition, metric, mean, std)} & "
                f"{format_table48_ci_latex(condition, metric, low, high)} \\\\"
            )
            md_agg_rows.append(
                [
                    condition_label(condition),
                    metric_label(metric),
                    format_table48_mean_sd(condition, metric, mean, std),
                    format_table48_ci(condition, metric, low, high),
                ]
            )
        if condition != "pgd_eps0.03":
            latex_lines.append("    \\midrule")

    latex_lines.extend(
        [
            "    \\bottomrule",
            "  \\end{tabular}",
            "",
            "  \\vspace{0.6em}",
            "",
            "  \\begin{tabular}{l l c c c}",
            "    \\toprule",
            (
                "    Seed & Status & Clean acc. & Clean fall recall & "
                "PGD $\\varepsilon{=}0.03$ fall recall \\\\"
            ),
            "    \\midrule",
        ]
    )

    md_seed_rows = []
    for row in seed_rows:
        clean_acc = f"{row['clean_accuracy']:.3f}"
        clean_recall = f"{row['clean_fall_recall']:.3f}"
        if row["pgd03_fall_recall"] == "":
            pgd = "--- (excluded)"
            pgd_latex = pgd
        else:
            pgd = f"{float(row['pgd03_fall_recall']):.3f}"
            pgd_latex = f"${pgd}$"
        status_latex = (
            "\\emph{non-converged}"
            if row["status"] == "non-converged"
            else row["status"]
        )
        latex_lines.append(
            f"    {row['seed']} & {status_latex} & ${clean_acc}$ & "
            f"${clean_recall}$ & {pgd_latex} \\\\"
        )
        md_seed_rows.append(
            [row["seed"], row["status"], clean_acc, clean_recall, pgd]
        )

    latex_lines.extend(
        [
            "    \\bottomrule",
            "  \\end{tabular}",
            "\\end{table}",
            "",
        ]
    )
    OUTPUTS["table48_tex"].write_text("\n".join(latex_lines), encoding="utf-8")

    md = [
        "# Reconstructed Table 4.8",
        "",
        "Source: results/cross_architecture/resnet/resnet18_clean_qualified_summary.csv",
        "",
        markdown_table(
            ["Condition", "Metric", "Mean +/- SD", "95% CI"],
            md_agg_rows,
        ),
        "## Seed Panel",
        "",
        markdown_table(
            [
                "Seed",
                "Status",
                "Clean acc.",
                "Clean fall recall",
                "PGD eps=0.03 fall recall",
            ],
            md_seed_rows,
        ),
        "",
    ]
    OUTPUTS["table48_md"].write_text("\n".join(md), encoding="utf-8")

    return {"aggregate": pd.DataFrame(aggregate_rows), "seed": pd.DataFrame(seed_rows)}


def compare_hashes(records: list[dict[str, object]]) -> dict[str, bool]:
    by_label = {record["label"]: record for record in records}
    return {
        "fig47_reconstructed_matches_experiment": (
            by_label["Figure 4.7 reconstructed"]["sha256"]
            == by_label["Figure 4.7 existing experiment"]["sha256"]
        ),
        "fig47_reconstructed_matches_thesis": (
            by_label["Figure 4.7 reconstructed"]["sha256"]
            == by_label["Figure 4.7 active thesis"]["sha256"]
        ),
        "fig47_experiment_matches_thesis": (
            by_label["Figure 4.7 existing experiment"]["sha256"]
            == by_label["Figure 4.7 active thesis"]["sha256"]
        ),
        "fig48_reconstructed_matches_experiment": (
            by_label["Figure 4.8 reconstructed"]["sha256"]
            == by_label["Figure 4.8 existing experiment"]["sha256"]
        ),
        "fig48_reconstructed_matches_thesis": (
            by_label["Figure 4.8 reconstructed"]["sha256"]
            == by_label["Figure 4.8 active thesis"]["sha256"]
        ),
        "fig48_experiment_matches_thesis": (
            by_label["Figure 4.8 existing experiment"]["sha256"]
            == by_label["Figure 4.8 active thesis"]["sha256"]
        ),
    }


def write_hash_report(records: list[dict[str, object]], matches: dict[str, bool]) -> None:
    lines = [
        "Chapter 4 reconstructed artifact hash comparison",
        "",
        "This report compares reconstructed figures against the existing experiment PNGs",
        "and the active thesis PNGs. A hash mismatch does not imply a metric mismatch;",
        "the reconstructed script is not the original missing generator.",
        "",
    ]
    for record in records:
        lines.extend(
            [
                record["label"],
                f"  path: {record['path']}",
                f"  exists: {record['exists']}",
                f"  sha256: {record['sha256']}",
                f"  dimensions: {record['width']}x{record['height']}",
                f"  bytes: {record['bytes']}",
                "",
            ]
        )

    lines.append("Pairwise matches")
    for key, value in matches.items():
        lines.append(f"  {key}: {'MATCH' if value else 'DIFFER'}")
    lines.append("")

    OUTPUTS["hash_report"].write_text("\n".join(lines), encoding="utf-8")


def write_reconstruction_report(
    records: list[dict[str, object]],
    matches: dict[str, bool],
    table47: dict[str, object],
    table48: dict[str, object],
) -> None:
    generated = [rel(path) for path in OUTPUTS.values()]
    source_lines = [f"- {name}: {rel(path)}" for name, path in PATHS.items()]
    generated_lines = [f"- {path}" for path in sorted(generated)]

    table47_rows = table47["display"]
    table47_md_rows = []
    for _, row in table47_rows.iterrows():
        table47_md_rows.append(
            [
                row["model"],
                row["clean_fall_recall_display"],
                row["fgsm03_fall_recall_display"],
                row["pgd03_fall_recall_display"],
                (
                    f"{row['fgsm03_exact_collapse_count']} / "
                    f"{row['pgd03_exact_collapse_count']}"
                ),
            ]
        )

    table48_agg = table48["aggregate"]
    table48_md_rows = []
    for _, row in table48_agg.iterrows():
        table48_md_rows.append(
            [
                row["condition"],
                row["metric"],
                row["display_mean_sd"],
                row["display_ci"],
            ]
        )

    image_rows = []
    for record in records:
        image_rows.append(
            [
                record["label"],
                record["sha256"],
                f"{record['width']}x{record['height']}",
                record["path"],
            ]
        )

    lines = [
        "# Chapter 4 Reconstructed Cross-Architecture/ResNet18 Artifacts",
        "",
        (
            "Status: Reconstructed reproducibility generator from verified source "
            "data; original generator not found."
        ),
        "",
        "No training or attacks are run by this script. Thesis files are read only for",
        "hash/dimension comparison; they are not modified.",
        "",
        "## Source Files",
        "",
        *source_lines,
        "",
        "## Generated Files",
        "",
        *generated_lines,
        "",
        "## Figure Hash and Dimension Summary",
        "",
        markdown_table(["Image", "SHA256", "Dimensions", "Path"], image_rows),
        "## Pairwise Figure Matches",
        "",
    ]
    for key, value in matches.items():
        lines.append(f"- {key}: {'MATCH' if value else 'DIFFER'}")

    lines.extend(
        [
            "",
            "## Table 4.7 Headline Values",
            "",
            markdown_table(
                [
                    "Model",
                    "Clean fall recall",
                    "FGSM eps=0.03",
                    "PGD eps=0.03",
                    "Exact 0.000 at eps=0.03 (FGSM / PGD)",
                ],
                table47_md_rows,
            ),
            table47["note"],
            "",
            "## Table 4.8 Headline Values",
            "",
            markdown_table(
                ["Condition", "Metric", "Mean +/- SD", "95% CI"],
                table48_md_rows,
            ),
            "",
            "## Provenance Note",
            "",
            (
                "This script can be included in provenance as: "
                "\"Reconstructed reproducibility generator from verified source "
                "data; original generator not found.\""
            ),
            "",
        ]
    )

    OUTPUTS["report_md"].write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    require_inputs()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    plot_figure_4_7()
    resnet_sweeps = summarize_resnet_sweeps()
    plot_figure_4_8(resnet_sweeps)
    table47 = build_table_4_7()
    table48 = build_table_4_8()

    image_records = [
        file_hash_record("Figure 4.7 reconstructed", OUTPUTS["fig47_reconstructed"]),
        file_hash_record("Figure 4.7 existing experiment", PATHS["fig47_existing"]),
        file_hash_record("Figure 4.7 active thesis", PATHS["fig47_thesis"]),
        file_hash_record("Figure 4.8 reconstructed", OUTPUTS["fig48_reconstructed"]),
        file_hash_record("Figure 4.8 existing experiment", PATHS["fig48_existing"]),
        file_hash_record("Figure 4.8 active thesis", PATHS["fig48_thesis"]),
    ]
    matches = compare_hashes(image_records)
    write_hash_report(image_records, matches)
    write_reconstruction_report(image_records, matches, table47, table48)

    print(f"Wrote reconstructed artifacts to {rel(OUT_DIR)}")
    for key, value in matches.items():
        print(f"{key}: {'MATCH' if value else 'DIFFER'}")


if __name__ == "__main__":
    main()
