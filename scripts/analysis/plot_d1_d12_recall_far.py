"""
Plot D1-D12 defense operating points as fall recall vs false-alarm rate.

Analysis only: this script reads the existing defense-attempt inventory CSV and
writes a derived plot-data CSV, figure files, and a short Markdown summary. It
does not train models, run attacks, load checkpoints, or edit thesis files.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import PercentFormatter


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "results" / "defense_attempt_inventory"
INVENTORY_CSV = OUT_DIR / "defense_attempt_results_long.csv"
PLOT_DATA_CSV = OUT_DIR / "d1_d12_recall_far_plot_data.csv"
TPFP_DATA_CSV = OUT_DIR / "d1_d12_tp_fp_plot_data.csv"
CONFUSION_DATA_CSV = OUT_DIR / "d1_d12_confusion_plot_data.csv"
FULL_PNG = OUT_DIR / "d1_d12_recall_vs_far_full.png"
FULL_PDF = OUT_DIR / "d1_d12_recall_vs_far_full.pdf"
ZOOM_PNG = OUT_DIR / "d1_d12_recall_vs_far_zoom.png"
ZOOM_PDF = OUT_DIR / "d1_d12_recall_vs_far_zoom.pdf"
COMPACT_PNG = OUT_DIR / "d1_d12_recall_vs_far_compact.png"
COMPACT_PDF = OUT_DIR / "d1_d12_recall_vs_far_compact.pdf"
MIDZOOM_PNG = OUT_DIR / "d1_d12_recall_vs_far_midzoom.png"
MIDZOOM_PDF = OUT_DIR / "d1_d12_recall_vs_far_midzoom.pdf"
TPFP_PNG = OUT_DIR / "d1_d12_tp_vs_fp.png"
TPFP_PDF = OUT_DIR / "d1_d12_tp_vs_fp.pdf"
TPFP_COMPACT_PNG = OUT_DIR / "d1_d12_tp_vs_fp_compact.png"
TPFP_COMPACT_PDF = OUT_DIR / "d1_d12_tp_vs_fp_compact.pdf"
CONFUSION_DECOMP_PNG = OUT_DIR / "d1_d12_confusion_decomposition.png"
CONFUSION_DECOMP_PDF = OUT_DIR / "d1_d12_confusion_decomposition.pdf"
TARGET_GAP_PNG = OUT_DIR / "d1_d12_target_gap_quadrant.png"
TARGET_GAP_PDF = OUT_DIR / "d1_d12_target_gap_quadrant.pdf"
SUMMARY_MD = OUT_DIR / "d1_d12_recall_vs_far_summary.md"
TPFP_SUMMARY_MD = OUT_DIR / "d1_d12_tp_vs_fp_summary.md"
CONFUSION_SUMMARY_MD = OUT_DIR / "d1_d12_confusion_decomposition_summary.md"

TEST_FALL = 45
TEST_NONFALL = 455
VAL_FALL = 44
VAL_NONFALL = 452
F20_RECALL = 0.80
F20_FAR = 0.20
F20_TP = 36
F20_FP = 91
FULL_XLIM = (0.0, 0.46)
FULL_YLIM = (0.0, 1.04)
ZOOM_XLIM = (0.16, 0.22)
ZOOM_YLIM = (0.78, 0.93)
MIDZOOM_XLIM = (0.10, 0.30)
MIDZOOM_YLIM = (0.40, 1.00)
TPFP_XLIM = (0, 205)
TPFP_YLIM = (0, 46)
TARGET_GAP_XLIM = (-110, 65)
TARGET_GAP_YLIM = (-38, 8)

OUTPUT_COLUMNS = [
    "id",
    "variant",
    "approach",
    "evidence_level",
    "split",
    "attack",
    "epsilon",
    "fall_recall",
    "far",
    "tp",
    "fn",
    "fp",
    "tn",
    "auroc",
    "threshold",
    "f20_met",
    "source_path",
    "source_type",
    "notes",
    "plot_label",
    "plotted",
]

TPFP_OUTPUT_COLUMNS = [
    "id",
    "plot_label",
    "variant",
    "approach",
    "evidence_level",
    "split",
    "tp",
    "fp",
    "fn",
    "tn",
    "fall_recall",
    "far",
    "f20_met",
    "source_type",
    "source_path",
    "notes",
]

CONFUSION_OUTPUT_COLUMNS = [
    "id",
    "plot_label",
    "variant",
    "approach",
    "evidence_level",
    "split",
    "tp",
    "fn",
    "fp",
    "tn",
    "fall_recall",
    "far",
    "tp_gap",
    "fp_margin",
    "f20_met",
    "source_type",
    "source_path",
    "notes",
]


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "-"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def as_int(value: Any) -> int | None:
    number = as_float(value)
    if number is None:
        return None
    return int(round(number))


def clean(value: Any, digits: int = 6) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        if abs(value - round(value)) < 1e-12:
            return str(int(round(value)))
        return f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return str(value)


def read_inventory() -> list[dict[str, str]]:
    if not INVENTORY_CSV.exists():
        return []
    with INVENTORY_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


@dataclass(frozen=True)
class Target:
    id: str
    variant: str
    approach: str
    evidence_level: str
    split: str
    attack: str
    epsilon: float | None
    source_hint: str
    row_kind: str
    plot_label: str
    seed: int | None = 42
    fallback_tp: int | None = None
    fallback_fn: int | None = None
    fallback_fp: int | None = None
    fallback_tn: int | None = None
    fallback_recall: float | None = None
    fallback_far: float | None = None
    fallback_auroc: float | None = None
    fallback_threshold: float | None = None
    notes: str = ""


TARGETS = [
    Target(
        "D0",
        "PGD reference",
        "Undefended LeNet baseline",
        "test fixed/argmax",
        "test",
        "pgd",
        0.03,
        "converged_seed42_pgd_epsilon_sweep_test.csv",
        "fixed",
        "D0 ref",
        fallback_tp=0,
        fallback_fn=45,
        fallback_fp=48,
        fallback_tn=407,
        fallback_recall=0.0000,
        fallback_far=0.1055,
        notes="Gray reference baseline; not counted as a defense.",
    ),
    Target(
        "D1",
        "PGD fixed",
        "FGSM adversarial-training baseline",
        "test fixed/argmax",
        "test",
        "pgd",
        0.03,
        "defended_fgsm_at_seed42_pgd_epsilon_sweep_test.csv",
        "fixed",
        "D1",
        fallback_tp=4,
        fallback_fn=41,
        fallback_fp=54,
        fallback_tn=401,
        fallback_recall=0.0889,
        fallback_far=0.1187,
    ),
    Target(
        "D2",
        "PGD fixed",
        "Fall-weighted training",
        "test fixed/argmax",
        "test",
        "pgd",
        0.03,
        "variantC_bySafetyScore_pgd_epsilon_sweep_test.csv",
        "fixed",
        "D2",
        fallback_tp=22,
        fallback_fn=23,
        fallback_fp=190,
        fallback_tn=265,
        fallback_recall=0.4889,
        fallback_far=0.4176,
    ),
    Target(
        "D3",
        "fixed",
        "Multi-budget training",
        "test fixed/argmax",
        "test",
        "pgd",
        0.03,
        "seed42_variantD_bySafetyScore_pgd_probabilities_test_epsilon_0_03.csv",
        "fixed",
        "D3-fixed",
        fallback_tp=20,
        fallback_fn=25,
        fallback_fp=157,
        fallback_tn=298,
        fallback_recall=0.4444,
        fallback_far=0.3451,
    ),
    Target(
        "D3",
        "post-hoc FAR<=0.20",
        "Multi-budget training",
        "test post-hoc FAR sweep",
        "test",
        "pgd",
        0.03,
        "seed42_variantD_byValMacroF1_pgd_probabilities_test_epsilon_0_03.csv",
        "sweep",
        "D3-sweep",
        fallback_tp=11,
        fallback_fn=34,
        fallback_fp=88,
        fallback_tn=367,
        fallback_recall=0.2444,
        fallback_far=88 / 455,
        fallback_auroc=0.7455,
    ),
    Target(
        "D4",
        "fixed",
        "Motion/margin loss",
        "test fixed/argmax",
        "test",
        "pgd",
        0.03,
        "F_lamM1p0_lamF1p0_v2safety_pgd_sweep_predictions_test.csv",
        "fixed",
        "D4-fixed",
        fallback_tp=30,
        fallback_fn=15,
        fallback_fp=115,
        fallback_tn=340,
        fallback_recall=0.6667,
        fallback_far=0.2527,
    ),
    Target(
        "D4",
        "post-hoc FAR<=0.20",
        "Motion/margin loss",
        "test post-hoc FAR sweep",
        "test",
        "pgd",
        0.03,
        "F_lamM1p0_lamF0p5_v2lowFA_pgd_probabilities_test_epsilon_0_03.csv",
        "sweep",
        "D4-sweep",
        fallback_tp=28,
        fallback_fn=17,
        fallback_fp=91,
        fallback_tn=364,
        fallback_recall=0.6222,
        fallback_far=91 / 455,
        fallback_auroc=0.8098,
    ),
    Target(
        "D5",
        "fixed",
        "G1 hard-negative/source-aware margin",
        "test fixed/argmax",
        "test",
        "pgd",
        0.03,
        "G_G1_v2safety_pgd_probabilities_test_epsilon_0_03.csv",
        "fixed",
        "D5-fixed",
        seed=42,
        fallback_tp=31,
        fallback_fn=14,
        fallback_fp=104,
        fallback_tn=351,
        fallback_recall=0.6889,
        fallback_far=0.2286,
    ),
    Target(
        "D5",
        "post-hoc FAR<=0.20 seed44",
        "G1 hard-negative/source-aware margin",
        "test post-hoc FAR sweep",
        "test",
        "pgd",
        0.03,
        "G_G1_v2safety_pgd_probabilities_test_epsilon_0_03.csv",
        "sweep",
        "D5-sweep",
        seed=44,
        fallback_tp=31,
        fallback_fn=14,
        fallback_fp=85,
        fallback_tn=370,
        fallback_recall=0.6889,
        fallback_far=85 / 455,
        fallback_auroc=0.8379,
    ),
    Target(
        "D6a",
        "fixed",
        "Static dual-tail rescue/budget objective",
        "test fixed/argmax",
        "test",
        "pgd",
        0.03,
        "H_H1_v2safety_pgd_probabilities_test_epsilon_0_03.csv",
        "fixed",
        "D6a-fixed",
        fallback_tp=22,
        fallback_fn=23,
        fallback_fp=94,
        fallback_tn=361,
        fallback_recall=0.4889,
        fallback_far=0.2066,
    ),
    Target(
        "D6a",
        "post-hoc FAR<=0.20",
        "Static dual-tail rescue/budget objective",
        "test post-hoc FAR sweep",
        "test",
        "pgd",
        0.03,
        "H_H1_v2safety_pgd_probabilities_test_epsilon_0_03.csv",
        "sweep",
        "D6a-sweep",
        fallback_tp=22,
        fallback_fn=23,
        fallback_fp=90,
        fallback_tn=365,
        fallback_recall=0.4889,
        fallback_far=90 / 455,
        fallback_auroc=0.7679,
    ),
    Target(
        "D6b",
        "fixed",
        "Rebalanced dual-tail with fall-rescue floor",
        "test fixed/argmax",
        "test",
        "pgd",
        0.03,
        "A1_v2safety_pgd_probabilities_test_epsilon_0_03.csv",
        "fixed",
        "D6b-fixed",
        fallback_tp=25,
        fallback_fn=20,
        fallback_fp=68,
        fallback_tn=387,
        fallback_recall=0.5556,
        fallback_far=0.1495,
    ),
    Target(
        "D6b",
        "post-hoc FAR<=0.20",
        "Rebalanced dual-tail with fall-rescue floor",
        "test post-hoc FAR sweep",
        "test",
        "pgd",
        0.03,
        "A1_v2safety_pgd_probabilities_test_epsilon_0_03.csv",
        "sweep",
        "D6b-sweep",
        fallback_tp=31,
        fallback_fn=14,
        fallback_fp=89,
        fallback_tn=366,
        fallback_recall=0.6889,
        fallback_far=89 / 455,
        fallback_auroc=0.8242,
    ),
    Target(
        "D7",
        "fixed",
        "Dual-specialist gate",
        "test fixed/argmax",
        "test",
        "pgd",
        0.03,
        "R_G1maxrec_pgd_probabilities_test_epsilon_0_03.csv",
        "fixed",
        "D7-fixed",
        fallback_tp=31,
        fallback_fn=14,
        fallback_fp=104,
        fallback_tn=351,
        fallback_recall=0.6889,
        fallback_far=0.2286,
    ),
    Target(
        "D7",
        "post-hoc FAR<=0.20",
        "Dual-specialist gate",
        "test post-hoc FAR sweep",
        "test",
        "pgd",
        0.03,
        "B_G1lowFA_pgd_probabilities_test_epsilon_0_03.csv",
        "sweep",
        "D7-sweep",
        fallback_tp=29,
        fallback_fn=16,
        fallback_fp=88,
        fallback_tn=367,
        fallback_recall=0.6444,
        fallback_far=88 / 455,
        fallback_auroc=0.8328,
    ),
    Target(
        "D8a",
        "AFAC-recall fixed",
        "Adaptive False-Alarm Controller (AFAC)",
        "test fixed/argmax",
        "test",
        "pgd",
        0.03,
        "optionB_maxrec_pgd_probabilities_test_epsilon_0_03.csv",
        "fixed",
        "D8a-recall",
        fallback_tp=30,
        fallback_fn=15,
        fallback_fp=85,
        fallback_tn=370,
        fallback_recall=0.6667,
        fallback_far=0.1868,
    ),
    Target(
        "D8a",
        "AFAC-score fixed",
        "Adaptive False-Alarm Controller (AFAC)",
        "test fixed/argmax",
        "test",
        "pgd",
        0.03,
        "optionB_maxscore_pgd_probabilities_test_epsilon_0_03.csv",
        "fixed",
        "D8a-score",
        fallback_tp=19,
        fallback_fn=26,
        fallback_fp=59,
        fallback_tn=396,
        fallback_recall=0.4222,
        fallback_far=0.1297,
    ),
    Target(
        "D8a",
        "AFAC-lowFA fixed",
        "Adaptive False-Alarm Controller (AFAC)",
        "test fixed/argmax",
        "test",
        "pgd",
        0.03,
        "optionB_minFA_pgd_probabilities_test_epsilon_0_03.csv",
        "fixed",
        "D8a-lowFA",
        fallback_tp=6,
        fallback_fn=39,
        fallback_fp=36,
        fallback_tn=419,
        fallback_recall=0.1333,
        fallback_far=0.0791,
    ),
    Target(
        "D8b",
        "AFAC-score post-hoc FAR<=0.20",
        "Adaptive False-Alarm Controller (AFAC)",
        "test post-hoc FAR sweep",
        "test",
        "pgd",
        0.03,
        "optionB_maxscore_pgd_probabilities_test_epsilon_0_03.csv",
        "sweep",
        "D8b AFAC-score",
        fallback_tp=36,
        fallback_fn=9,
        fallback_fp=91,
        fallback_tn=364,
        fallback_recall=0.8000,
        fallback_far=91 / 455,
        fallback_auroc=0.8439,
        fallback_threshold=0.1532,
        notes="Only held-out test post-hoc operating point in IA.3 that reaches F20.",
    ),
    Target(
        "D9",
        "missing artifact",
        "TRADES-style consistency",
        "missing artifact",
        "",
        "",
        None,
        "",
        "missing",
        "D9 missing",
        seed=None,
        notes="No usable local TRADES-named standalone result artifact found.",
    ),
    Target(
        "D10",
        "validation-only FAR<=0.20",
        "GAIRAT-style boundary reweighting",
        "validation-only FAR sweep",
        "val",
        "pgd",
        0.03,
        "GR1_v2macroF1_pgd_probabilities_val_epsilon_0_03.csv",
        "sweep",
        "D10 val",
        fallback_tp=39,
        fallback_fn=5,
        fallback_fp=86,
        fallback_tn=366,
        fallback_recall=0.8864,
        fallback_far=86 / 452,
        fallback_auroc=0.8712,
    ),
    Target(
        "D11a",
        "validation-only FAR<=0.20",
        "SAT-style selective filtering (Stage-1/BASAT pilot)",
        "validation-only FAR sweep",
        "val",
        "pgd",
        0.03,
        "ST1b6_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv",
        "sweep",
        "D11a val",
        fallback_tp=40,
        fallback_fn=4,
        fallback_fp=86,
        fallback_tn=366,
        fallback_recall=0.9091,
        fallback_far=86 / 452,
        fallback_auroc=0.8690,
    ),
    Target(
        "D11b",
        "validation-only FAR<=0.20",
        "SAT-style selective filtering",
        "validation-only FAR sweep",
        "val",
        "pgd",
        0.03,
        "SA1_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv",
        "sweep",
        "D11b val",
        fallback_tp=39,
        fallback_fn=5,
        fallback_fp=85,
        fallback_tn=367,
        fallback_recall=0.8864,
        fallback_far=85 / 452,
        fallback_auroc=0.8728,
    ),
    Target(
        "D12",
        "validation-only FAR<=0.20",
        "BiLSTM representation pivot",
        "validation-only FAR sweep",
        "val",
        "pgd",
        0.03,
        "BLF_v2macroF1_pgd_probabilities_val_epsilon_0_03.csv",
        "sweep",
        "D12 val",
        fallback_tp=11,
        fallback_fn=33,
        fallback_fp=83,
        fallback_tn=369,
        fallback_recall=0.2500,
        fallback_far=83 / 452,
        fallback_auroc=0.7257,
    ),
]


def epsilon_matches(row_value: str, target: float | None) -> bool:
    if target is None:
        return True
    value = as_float(row_value)
    return value is not None and abs(value - target) < 1e-9


def kind_matches(row: dict[str, str], target: Target) -> bool:
    rule = row.get("checkpoint_or_threshold_rule", "").lower()
    source_type = row.get("source_type", "")
    status = row.get("result_status", "")
    if target.row_kind == "fixed":
        return "fixed argmax" in rule or "reported fixed" in rule
    if target.row_kind == "sweep":
        return "post-hoc" in rule or source_type == "per_window_score_csv"
    if target.row_kind == "missing":
        return source_type == "inventory_gap" or status == "not_found"
    return False


def find_inventory_row(rows: list[dict[str, str]], target: Target) -> dict[str, str] | None:
    if target.row_kind == "missing":
        for row in rows:
            if "TRADES-style fall-probability consistency" in row.get("method_thesis_name", ""):
                return row
        return None

    candidates = []
    for row in rows:
        source_file = row.get("source_file", "")
        if target.source_hint and target.source_hint not in source_file:
            continue
        if target.seed is not None and as_int(row.get("seed")) != target.seed:
            continue
        if target.split and row.get("split") != target.split:
            continue
        if target.attack and row.get("attack") != target.attack:
            continue
        if not epsilon_matches(row.get("epsilon", ""), target.epsilon):
            continue
        if not kind_matches(row, target):
            continue
        candidates.append(row)

    if not candidates:
        return None

    if target.row_kind == "fixed":
        priority = {
            "per_window_predictions_csv": 0,
            "reported_metrics_table": 1,
            "reported_metrics_csv": 2,
        }
    else:
        priority = {"per_window_score_csv": 0}
    return sorted(candidates, key=lambda row: priority.get(row.get("source_type", ""), 99))[0]


def infer_missing_count(target: Target, tp: int | None, fn: int | None, fp: int | None, tn: int | None) -> tuple[int | None, int | None, int | None, int | None]:
    fall_total = TEST_FALL if target.split == "test" else VAL_FALL if target.split == "val" else None
    nonfall_total = TEST_NONFALL if target.split == "test" else VAL_NONFALL if target.split == "val" else None
    if fall_total is not None:
        if tp is not None and fn is None:
            fn = fall_total - tp
        elif fn is not None and tp is None:
            tp = fall_total - fn
    if nonfall_total is not None:
        if fp is not None and tn is None:
            tn = nonfall_total - fp
        elif tn is not None and fp is None:
            fp = nonfall_total - tn
    return tp, fn, fp, tn


def make_output_row(target: Target, inventory_row: dict[str, str] | None) -> dict[str, Any]:
    if inventory_row is not None and target.row_kind != "missing":
        tp = as_int(inventory_row.get("TP"))
        fn = as_int(inventory_row.get("FN"))
        fp = as_int(inventory_row.get("FP"))
        tn = as_int(inventory_row.get("TN"))
        source_type = inventory_row.get("source_type", "")
        source_path = inventory_row.get("source_file", "")
        auroc = as_float(inventory_row.get("AUROC"))
        threshold = as_float(inventory_row.get("threshold"))
        note = "Recovered from defense_attempt_results_long.csv."
    elif inventory_row is not None and target.row_kind == "missing":
        tp = fn = fp = tn = None
        source_type = inventory_row.get("source_type", "inventory_gap")
        source_path = inventory_row.get("source_file", "")
        auroc = threshold = None
        note = "Inventory row marks this approach as not found."
    else:
        tp = target.fallback_tp
        fn = target.fallback_fn
        fp = target.fallback_fp
        tn = target.fallback_tn
        source_type = "table_ia3_fallback"
        source_path = "attached internal_defense_experiment_ledger.tex Table IA.3"
        auroc = target.fallback_auroc
        threshold = target.fallback_threshold
        note = "Fallback from Table IA.3 compact values."

    tp, fn, fp, tn = infer_missing_count(target, tp, fn, fp, tn)

    fall_recall = (tp / (tp + fn)) if tp is not None and fn is not None and (tp + fn) > 0 else target.fallback_recall
    far = (fp / (fp + tn)) if fp is not None and tn is not None and (fp + tn) > 0 else target.fallback_far
    f20_met = bool(fall_recall is not None and far is not None and fall_recall >= F20_RECALL and far <= F20_FAR)
    plotted = bool(fall_recall is not None and far is not None and target.row_kind != "missing")

    if target.notes:
        note = f"{note} {target.notes}"

    return {
        "id": target.id,
        "variant": target.variant,
        "approach": target.approach,
        "evidence_level": target.evidence_level,
        "split": target.split,
        "attack": target.attack,
        "epsilon": target.epsilon,
        "fall_recall": fall_recall,
        "far": far,
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "auroc": auroc,
        "threshold": threshold,
        "f20_met": f20_met,
        "source_path": source_path,
        "source_type": source_type,
        "notes": note,
        "plot_label": target.plot_label,
        "plotted": plotted,
    }


def compare_to_fallback(row: dict[str, Any], target: Target, tol: float = 5e-4) -> list[str]:
    if row["source_type"] == "table_ia3_fallback" or target.row_kind == "missing":
        return []

    checks = [
        ("TP", row.get("tp"), target.fallback_tp, 0),
        ("FN", row.get("fn"), target.fallback_fn, 0),
        ("FP", row.get("fp"), target.fallback_fp, 0),
        ("TN", row.get("tn"), target.fallback_tn, 0),
        ("fall_recall", row.get("fall_recall"), target.fallback_recall, tol),
        ("far", row.get("far"), target.fallback_far, tol),
        ("auroc", row.get("auroc"), target.fallback_auroc, tol),
        ("threshold", row.get("threshold"), target.fallback_threshold, tol),
    ]

    differences = []
    for name, actual, expected, allowed in checks:
        if expected is None or actual is None:
            continue
        if abs(float(actual) - float(expected)) > allowed:
            differences.append(f"{row['plot_label']}: {name} artifact={clean(actual)} IA3={clean(expected)}")
    return differences


def write_plot_data(rows: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with PLOT_DATA_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: clean(row.get(col)) for col in OUTPUT_COLUMNS})


def write_tpfp_plot_data(rows: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with TPFP_DATA_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TPFP_OUTPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: clean(row.get(col)) for col in TPFP_OUTPUT_COLUMNS})


def confusion_output_value(row: dict[str, Any], column: str) -> Any:
    if column == "tp_gap":
        return row["tp"] - F20_TP if row.get("tp") is not None else None
    if column == "fp_margin":
        return F20_FP - row["fp"] if row.get("fp") is not None else None
    return row.get(column)


def write_confusion_plot_data(rows: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with CONFUSION_DATA_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CONFUSION_OUTPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: clean(confusion_output_value(row, col)) for col in CONFUSION_OUTPUT_COLUMNS})


def marker_style(row: dict[str, Any]) -> tuple[str, str, int, float]:
    if row["id"] == "D0":
        return "o", "#8a8f98", 72, 0.88
    if row["evidence_level"] == "test fixed/argmax":
        return "o", "#2f6fb2", 86, 0.92
    if row["evidence_level"] == "test post-hoc FAR sweep":
        return "s", "#d0742f", 104, 0.95
    if row["evidence_level"] == "validation-only FAR sweep":
        return "^", "#2c8a5a", 108, 0.94
    return "x", "#5f6368", 72, 0.80


LABEL_OFFSETS = {
    "D0 ref": (12, 6),
    "D1": (12, -12),
    "D2": (-46, 12),
    "D3-fixed": (-18, -22),
    "D3-sweep": (12, -18),
    "D4-fixed": (14, 10),
    "D4-sweep": (14, -22),
    "D5-fixed": (14, 18),
    "D5-sweep": (10, 22),
    "D6a-fixed": (-62, -28),
    "D6a-sweep": (12, 18),
    "D6b-fixed": (14, -24),
    "D6b-sweep": (14, -34),
    "D7-fixed": (14, -14),
    "D7-sweep": (22, 14),
    "D8a-recall": (-74, 10),
    "D8a-score": (14, 10),
    "D8a-lowFA": (14, -14),
    "D8b AFAC-score": (18, 14),
    "D10 val": (-74, -8),
    "D11a val": (12, 16),
    "D11b val": (18, -24),
    "D12 val": (12, 12),
}


ZOOM_LABEL_OFFSETS = {
    "D8b AFAC-score": (32, -30),
    "D10 val": (40, 8),
    "D11a val": (28, 22),
    "D11b val": (-26, -58),
}


COMPACT_LABELS = {
    "D0 ref": "D0",
    "D3-fixed": "D3-f",
    "D3-sweep": "D3-s",
    "D4-fixed": "D4-f",
    "D4-sweep": "D4-s",
    "D5-fixed": "D5-f",
    "D5-sweep": "D5-s",
    "D6a-fixed": "D6a-f",
    "D6a-sweep": "D6a-s",
    "D6b-fixed": "D6b-f",
    "D6b-sweep": "D6b-s",
    "D7-fixed": "D7-f",
    "D7-sweep": "D7-s",
    "D8a-recall": "D8a-r",
    "D8a-score": "D8a-s",
    "D8a-lowFA": "D8a-l",
    "D8b AFAC-score": "D8b",
    "D10 val": "D10-v",
    "D11a val": "D11a-v",
    "D11b val": "D11b-v",
    "D12 val": "D12-v",
}


COMPACT_LABEL_OFFSETS = {
    "D0 ref": (8, 4),
    "D1": (8, -10),
    "D2": (-28, 8),
    "D3-fixed": (-14, -18),
    "D3-sweep": (10, -14),
    "D4-fixed": (10, 8),
    "D4-sweep": (10, -16),
    "D5-fixed": (10, 12),
    "D5-sweep": (8, 16),
    "D6a-fixed": (-44, -20),
    "D6a-sweep": (12, 18),
    "D6b-fixed": (8, -14),
    "D6b-sweep": (10, -22),
    "D7-fixed": (10, -10),
    "D7-sweep": (14, 10),
    "D8a-recall": (-48, 8),
    "D8a-score": (10, 8),
    "D8a-lowFA": (10, -10),
    "D8b AFAC-score": (12, 12),
    "D10 val": (-48, -6),
    "D11a val": (8, 12),
    "D11b val": (12, -18),
    "D12 val": (8, 8),
}


MIDZOOM_LABEL_OFFSETS = {
    "D4-fixed": (18, 10),
    "D4-sweep": (18, -20),
    "D5-fixed": (18, 24),
    "D5-sweep": (-2, 24),
    "D6a-fixed": (-60, -24),
    "D6a-sweep": (18, 16),
    "D6b-fixed": (14, -22),
    "D6b-sweep": (20, 4),
    "D7-fixed": (18, -14),
    "D7-sweep": (24, -10),
    "D8a-recall": (-58, 8),
    "D8a-score": (14, 10),
    "D8b AFAC-score": (18, 14),
    "D10 val": (36, -4),
    "D11a val": (26, 16),
    "D11b val": (-58, -12),
}


TPFP_LABEL_OFFSETS = {
    "D0 ref": (8, -12),
    "D1": (8, 8),
    "D2": (-52, 10),
    "D3-fixed": (-64, -12),
    "D3-sweep": (-76, -22),
    "D4-fixed": (12, 10),
    "D4-sweep": (10, -22),
    "D5-fixed": (16, 22),
    "D5-sweep": (-70, 16),
    "D6a-fixed": (14, -24),
    "D6a-sweep": (-82, 10),
    "D6b-fixed": (-76, 8),
    "D6b-sweep": (12, 4),
    "D7-fixed": (28, -28),
    "D7-sweep": (-76, -8),
    "D8a-recall": (-80, -12),
    "D8a-score": (12, 12),
    "D8a-lowFA": (10, -10),
    "D8b AFAC-score": (20, 4),
    "D10 val": (14, -6),
    "D11a val": (14, 16),
    "D11b val": (-78, 10),
    "D12 val": (-68, 10),
}


TPFP_COMPACT_LABEL_OFFSETS = {
    "D0 ref": (8, -10),
    "D1": (8, 8),
    "D2": (-30, 8),
    "D3-fixed": (-34, -10),
    "D3-sweep": (-42, -14),
    "D4-fixed": (10, 8),
    "D4-sweep": (8, -16),
    "D5-fixed": (12, 16),
    "D5-sweep": (-42, 14),
    "D6a-fixed": (10, -18),
    "D6a-sweep": (-48, 8),
    "D6b-fixed": (-44, 8),
    "D6b-sweep": (10, 4),
    "D7-fixed": (12, -10),
    "D7-sweep": (-44, -8),
    "D8a-recall": (-48, -10),
    "D8a-score": (10, 8),
    "D8a-lowFA": (8, -8),
    "D8b AFAC-score": (12, -18),
    "D10 val": (10, -4),
    "D11a val": (10, 12),
    "D11b val": (-48, 8),
    "D12 val": (-40, 8),
}


TARGET_GAP_LABEL_OFFSETS = {
    "D0 ref": (8, -10),
    "D1": (8, 8),
    "D2": (10, 8),
    "D3-fixed": (10, -12),
    "D3-sweep": (-46, -14),
    "D4-fixed": (10, 8),
    "D4-sweep": (12, -22),
    "D5-fixed": (14, 18),
    "D5-sweep": (-52, 14),
    "D6a-fixed": (10, -18),
    "D6a-sweep": (-52, -18),
    "D6b-fixed": (10, 8),
    "D6b-sweep": (14, 2),
    "D7-fixed": (14, -12),
    "D7-sweep": (10, -14),
    "D8a-recall": (-54, -4),
    "D8a-score": (10, -10),
    "D8a-lowFA": (10, -10),
    "D8b AFAC-score": (16, -26),
    "D10 val": (28, -2),
    "D11a val": (18, 14),
    "D11b val": (-58, 8),
    "D12 val": (10, -16),
}


def add_f20_guides(ax: plt.Axes, xlim: tuple[float, float], ylim: tuple[float, float], label: bool = False) -> None:
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)

    shade_x0 = xlim[0]
    shade_x1 = min(F20_FAR, xlim[1])
    shade_y0 = max(F20_RECALL, ylim[0])
    shade_y1 = ylim[1]
    if shade_x1 > shade_x0 and shade_y1 > shade_y0:
        ax.add_patch(
            Rectangle(
                (shade_x0, shade_y0),
                shade_x1 - shade_x0,
                shade_y1 - shade_y0,
                facecolor="#5aa469",
                alpha=0.10,
                edgecolor="#2f7d4d",
                linewidth=1.0,
                zorder=0,
            )
        )

    ax.axvline(F20_FAR, color="#2f7d4d", linestyle="--", linewidth=1.2, zorder=1)
    ax.axhline(F20_RECALL, color="#2f7d4d", linestyle="--", linewidth=1.2, zorder=1)

    if label:
        ax.annotate(
            "F20 target region",
            xy=(0.095, 0.91),
            ha="center",
            va="center",
            fontsize=9,
            color="#276741",
        )


def rows_in_window(rows: list[dict[str, Any]], xlim: tuple[float, float], ylim: tuple[float, float]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row["plotted"]
        and row["far"] is not None
        and row["fall_recall"] is not None
        and xlim[0] <= row["far"] <= xlim[1]
        and ylim[0] <= row["fall_recall"] <= ylim[1]
    ]


def draw_points(
    ax: plt.Axes,
    rows: list[dict[str, Any]],
    label_offsets: dict[str, tuple[int, int]],
    marker_scale: float = 1.0,
    label_fontsize: float = 8.4,
    draw_connectors: bool = False,
    include_values: bool = False,
    fontweight: str = "normal",
    label_formatter: Callable[[dict[str, Any]], str] | None = None,
    label_box_alpha: float = 0.86,
) -> None:
    for row in rows:
        marker, color, size, alpha = marker_style(row)
        edgecolor = "black" if row["plot_label"] == "D8b AFAC-score" else "white"
        linewidth = 1.8 if row["plot_label"] == "D8b AFAC-score" else 0.6
        afac_scale = 1.45 if row["plot_label"] == "D8b AFAC-score" else 1.0
        ax.scatter(
            row["far"],
            row["fall_recall"],
            marker=marker,
            s=size * afac_scale * marker_scale,
            color=color,
            alpha=alpha,
            edgecolor=edgecolor,
            linewidth=linewidth,
            zorder=4 if row["plot_label"] == "D8b AFAC-score" else 3,
        )
        dx, dy = label_offsets.get(row["plot_label"], (6, 6))
        arrowprops = None
        if draw_connectors:
            arrowprops = {"arrowstyle": "-", "color": "#4c4c4c", "lw": 0.7, "shrinkA": 3, "shrinkB": 4}
        label_text = label_formatter(row) if label_formatter is not None else row["plot_label"]
        if include_values:
            label_text = (
                f"{row['plot_label']}\n"
                f"FAR={row['far'] * 100:.1f}%, R={row['fall_recall'] * 100:.1f}%"
            )
        ax.annotate(
            label_text,
            (row["far"], row["fall_recall"]),
            textcoords="offset points",
            xytext=(dx, dy),
            fontsize=label_fontsize,
            fontweight=fontweight,
            color="#222222",
            arrowprops=arrowprops,
            bbox={"boxstyle": "round,pad=0.18", "facecolor": "white", "edgecolor": "#d8d8d8", "linewidth": 0.3, "alpha": label_box_alpha},
            zorder=5,
        )


def add_tpfp_guides(ax: plt.Axes, xlim: tuple[int, int] = TPFP_XLIM, ylim: tuple[int, int] = TPFP_YLIM, label: bool = False) -> None:
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    shade_x0 = xlim[0]
    shade_x1 = min(F20_FP, xlim[1])
    shade_y0 = max(F20_TP, ylim[0])
    shade_y1 = ylim[1]
    if shade_x1 > shade_x0 and shade_y1 > shade_y0:
        ax.add_patch(
            Rectangle(
                (shade_x0, shade_y0),
                shade_x1 - shade_x0,
                shade_y1 - shade_y0,
                facecolor="#5aa469",
                alpha=0.10,
                edgecolor="#2f7d4d",
                linewidth=1.0,
                zorder=0,
            )
        )

    ax.axvline(F20_FP, color="#2f7d4d", linestyle="--", linewidth=1.2, zorder=1)
    ax.axhline(F20_TP, color="#2f7d4d", linestyle="--", linewidth=1.2, zorder=1)
    if label:
        ax.annotate(
            "F20 count target\nTP >= 36, FP <= 91",
            xy=(42, 41),
            ha="center",
            va="center",
            fontsize=9,
            color="#276741",
        )


def draw_tpfp_points(
    ax: plt.Axes,
    rows: list[dict[str, Any]],
    label_offsets: dict[str, tuple[int, int]],
    marker_scale: float = 1.0,
    label_fontsize: float = 8.4,
    draw_connectors: bool = True,
    fontweight: str = "normal",
    label_formatter: Callable[[dict[str, Any]], str] | None = None,
    label_box_alpha: float = 0.86,
) -> None:
    for row in rows:
        marker, color, size, alpha = marker_style(row)
        edgecolor = "black" if row["plot_label"] == "D8b AFAC-score" else "white"
        linewidth = 1.8 if row["plot_label"] == "D8b AFAC-score" else 0.6
        afac_scale = 1.45 if row["plot_label"] == "D8b AFAC-score" else 1.0
        ax.scatter(
            row["fp"],
            row["tp"],
            marker=marker,
            s=size * afac_scale * marker_scale,
            color=color,
            alpha=alpha,
            edgecolor=edgecolor,
            linewidth=linewidth,
            zorder=4 if row["plot_label"] == "D8b AFAC-score" else 3,
        )
        dx, dy = label_offsets.get(row["plot_label"], (6, 6))
        arrowprops = None
        if draw_connectors:
            arrowprops = {"arrowstyle": "-", "color": "#4c4c4c", "lw": 0.7, "shrinkA": 3, "shrinkB": 4}
        label_text = label_formatter(row) if label_formatter is not None else row["plot_label"]
        ax.annotate(
            label_text,
            (row["fp"], row["tp"]),
            textcoords="offset points",
            xytext=(dx, dy),
            fontsize=label_fontsize,
            fontweight=fontweight,
            color="#222222",
            arrowprops=arrowprops,
            bbox={"boxstyle": "round,pad=0.18", "facecolor": "white", "edgecolor": "#d8d8d8", "linewidth": 0.3, "alpha": label_box_alpha},
            zorder=5,
        )


def style_percent_axes(ax: plt.Axes, xlabel: str = "False-alarm rate (FAR)", ylabel: str = "Fall recall") -> None:
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.xaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
    ax.grid(True, linestyle="-", linewidth=0.5, alpha=0.22)


def style_count_axes(ax: plt.Axes) -> None:
    ax.set_xlabel("False positives (FP): false fall alarms")
    ax.set_ylabel("True positives (TP): detected falls")
    ax.set_xticks(range(0, 201, 25))
    ax.set_yticks(range(0, 46, 5))
    ax.grid(True, linestyle="-", linewidth=0.5, alpha=0.22)


def legend_handles() -> list[Line2D]:
    return [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#2f6fb2", label="Test fixed/argmax", markersize=8),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="#d0742f", label="Test post-hoc FAR sweep", markersize=8),
        Line2D([0], [0], marker="^", color="w", markerfacecolor="#2c8a5a", label="Validation-only FAR sweep", markersize=8),
        Line2D([0], [0], marker="x", color="#5f6368", label="Missing artifact (not plotted)", markersize=8, linestyle="None"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#8a8f98", label="D0 reference baseline", markersize=8),
    ]


def draw_zoom_panel(ax: plt.Axes, rows: list[dict[str, Any]], title: str | None = None) -> None:
    ax.set_facecolor("white")
    ax.patch.set_alpha(1.0)
    add_f20_guides(ax, ZOOM_XLIM, ZOOM_YLIM)
    draw_points(
        ax,
        rows,
        ZOOM_LABEL_OFFSETS,
        marker_scale=2.05,
        label_fontsize=9.4,
        draw_connectors=True,
        include_values=True,
        fontweight="medium",
    )
    style_percent_axes(ax, xlabel="FAR", ylabel="Recall")
    ax.tick_params(labelsize=9)
    if title:
        ax.set_title(title, fontsize=13, pad=6)


def compact_label(row: dict[str, Any]) -> str:
    return COMPACT_LABELS.get(row["plot_label"], row["plot_label"])


def target_order_index(row: dict[str, Any]) -> int:
    for index, target in enumerate(TARGETS):
        if target.plot_label == row["plot_label"]:
            return index
    return 999


def confusion_group(row: dict[str, Any]) -> int:
    if row["id"] == "D0":
        return 3
    if row["evidence_level"] == "test fixed/argmax":
        return 0
    if row["evidence_level"] == "test post-hoc FAR sweep":
        return 1
    if row["evidence_level"] == "validation-only FAR sweep":
        return 2
    return 4


def ordered_confusion_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plotted = [row for row in rows if row["plotted"] and row["tp"] is not None and row["fp"] is not None]
    return sorted(plotted, key=lambda row: (confusion_group(row), target_order_index(row)))


def percent_label(kind: str, count: int, total: int) -> str:
    return f"{kind} {count} ({count / total * 100:.1f}%)"


def write_plot(rows: list[dict[str, Any]]) -> None:
    plotted = [row for row in rows if row["plotted"]]

    fig, ax = plt.subplots(figsize=(12.2, 8.2))
    add_f20_guides(ax, FULL_XLIM, FULL_YLIM, label=True)
    draw_points(ax, plotted, LABEL_OFFSETS, marker_scale=1.05, label_fontsize=8.7, draw_connectors=True, fontweight="medium")
    ax.annotate(
        "D8b reaches F20\n(test post-hoc sweep)",
        xy=(F20_FAR, F20_RECALL),
        xytext=(0.255, 0.975),
        arrowprops={"arrowstyle": "->", "color": "#6f4b1d", "lw": 1.1},
        fontsize=9,
        fontweight="medium",
        color="#5b3d17",
        bbox={"boxstyle": "round,pad=0.16", "facecolor": "white", "edgecolor": "none", "alpha": 0.80},
    )

    ax.set_title("D1-D12 Defense Operating Points: Fall Recall vs False-Alarm Rate", fontsize=14, pad=14)
    style_percent_axes(ax)
    ax.legend(handles=legend_handles(), loc="lower right", frameon=True, framealpha=0.92)

    fig.text(
        0.5,
        0.025,
        "PGD epsilon=0.030 where available. Marker style separates fixed test, post-hoc test sweep, "
        "validation-only sweep, and missing artifacts.",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#333333",
    )
    fig.subplots_adjust(left=0.09, right=0.985, top=0.90, bottom=0.12)
    fig.savefig(FULL_PNG, dpi=220)
    fig.savefig(FULL_PDF)
    plt.close(fig)


def write_compact_plot(rows: list[dict[str, Any]]) -> None:
    plotted = [row for row in rows if row["plotted"]]

    fig, ax = plt.subplots(figsize=(11.6, 7.8))
    add_f20_guides(ax, FULL_XLIM, FULL_YLIM, label=True)
    draw_points(
        ax,
        plotted,
        COMPACT_LABEL_OFFSETS,
        marker_scale=1.12,
        label_fontsize=8.4,
        draw_connectors=True,
        fontweight="medium",
        label_formatter=compact_label,
        label_box_alpha=0.82,
    )
    ax.annotate(
        "D8b reaches F20",
        xy=(F20_FAR, F20_RECALL),
        xytext=(0.245, 0.94),
        arrowprops={"arrowstyle": "->", "color": "#6f4b1d", "lw": 1.0},
        fontsize=9,
        fontweight="medium",
        color="#5b3d17",
        bbox={"boxstyle": "round,pad=0.16", "facecolor": "white", "edgecolor": "none", "alpha": 0.82},
    )
    ax.set_title("D1-D12 Defense Operating Points: Compact Recall-FAR Overview", fontsize=14, pad=14)
    style_percent_axes(ax)
    handles = legend_handles()
    notation = Line2D([], [], linestyle="None", marker="", color="none", label="f=fixed, s=sweep, v=validation, r=recall, l=lowFA")
    ax.legend(handles=handles + [notation], loc="lower right", frameon=True, framealpha=0.92, fontsize=8.6)

    fig.text(
        0.5,
        0.025,
        "Compact labels reduce text density while preserving evidence-type marker shapes.",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#333333",
    )
    fig.subplots_adjust(left=0.09, right=0.985, top=0.90, bottom=0.12)
    fig.savefig(COMPACT_PNG, dpi=220)
    fig.savefig(COMPACT_PDF)
    plt.close(fig)


def write_zoom_plot(rows: list[dict[str, Any]]) -> None:
    plotted = [row for row in rows if row["plotted"]]
    zoom_rows = rows_in_window(plotted, ZOOM_XLIM, ZOOM_YLIM)

    fig, ax = plt.subplots(figsize=(9.6, 6.3))
    draw_zoom_panel(ax, zoom_rows, title="Near-F20 Operating-Point Zoom")
    ax.legend(handles=legend_handles()[1:3], loc="lower left", frameon=True, framealpha=0.92)
    fig.text(
        0.5,
        0.02,
        "Zoom window: FAR 16%-22%, fall recall 78%-93%. D10/D11 are validation-only; D8b is held-out test post-hoc.",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#333333",
    )
    fig.subplots_adjust(left=0.12, right=0.965, top=0.90, bottom=0.14)
    fig.savefig(ZOOM_PNG, dpi=220)
    fig.savefig(ZOOM_PDF)
    plt.close(fig)


def write_midzoom_plot(rows: list[dict[str, Any]]) -> None:
    plotted = [row for row in rows if row["plotted"]]
    midzoom_rows = rows_in_window(plotted, MIDZOOM_XLIM, MIDZOOM_YLIM)

    fig, ax = plt.subplots(figsize=(9.8, 6.8))
    add_f20_guides(ax, MIDZOOM_XLIM, MIDZOOM_YLIM)
    draw_points(
        ax,
        midzoom_rows,
        MIDZOOM_LABEL_OFFSETS,
        marker_scale=1.45,
        label_fontsize=9.0,
        draw_connectors=True,
        fontweight="medium",
        label_formatter=compact_label,
        label_box_alpha=0.86,
    )
    ax.set_title("Medium-Range Recall-FAR Zoom", fontsize=13, pad=10)
    style_percent_axes(ax)
    ax.tick_params(labelsize=9)
    ax.legend(handles=legend_handles()[:3], loc="lower right", frameon=True, framealpha=0.92, fontsize=8.6)
    fig.text(
        0.5,
        0.02,
        "Medium zoom window: FAR 10%-30%, fall recall 40%-100%. Compact labels use f=fixed, s=sweep, v=validation, r=AFAC-recall.",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#333333",
    )
    fig.subplots_adjust(left=0.11, right=0.965, top=0.89, bottom=0.14)
    fig.savefig(MIDZOOM_PNG, dpi=220)
    fig.savefig(MIDZOOM_PDF)
    plt.close(fig)


def write_tpfp_plot(rows: list[dict[str, Any]]) -> None:
    plotted = [row for row in rows if row["plotted"] and row["tp"] is not None and row["fp"] is not None]

    fig, ax = plt.subplots(figsize=(12.4, 8.0))
    add_tpfp_guides(ax, label=True)
    draw_tpfp_points(
        ax,
        plotted,
        TPFP_LABEL_OFFSETS,
        marker_scale=1.10,
        label_fontsize=8.3,
        draw_connectors=True,
        fontweight="medium",
        label_box_alpha=0.84,
    )
    ax.annotate(
        "D8b reaches F20\nTP=36, FP=91",
        xy=(F20_FP, F20_TP),
        xytext=(122, 42),
        arrowprops={"arrowstyle": "->", "color": "#6f4b1d", "lw": 1.1},
        fontsize=9,
        fontweight="medium",
        color="#5b3d17",
        bbox={"boxstyle": "round,pad=0.16", "facecolor": "white", "edgecolor": "none", "alpha": 0.82},
    )
    ax.set_title("D1-D12 Defense Operating Points: True Positives vs False Positives", fontsize=14, pad=14)
    style_count_axes(ax)
    ax.legend(handles=legend_handles(), loc="lower right", frameon=True, framealpha=0.92, fontsize=8.6)
    fig.text(
        0.5,
        0.025,
        "Count-space F20 target: TP >= 36 of 45 fall windows and FP <= 91 of 455 non-fall windows. "
        "Marker style separates evidence type.",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#333333",
    )
    fig.subplots_adjust(left=0.09, right=0.985, top=0.90, bottom=0.12)
    fig.savefig(TPFP_PNG, dpi=220)
    fig.savefig(TPFP_PDF)
    plt.close(fig)


def write_tpfp_compact_plot(rows: list[dict[str, Any]]) -> None:
    plotted = [row for row in rows if row["plotted"] and row["tp"] is not None and row["fp"] is not None]

    fig, ax = plt.subplots(figsize=(11.8, 7.6))
    add_tpfp_guides(ax, label=True)
    draw_tpfp_points(
        ax,
        plotted,
        TPFP_COMPACT_LABEL_OFFSETS,
        marker_scale=1.14,
        label_fontsize=8.4,
        draw_connectors=True,
        fontweight="medium",
        label_formatter=compact_label,
        label_box_alpha=0.82,
    )
    ax.annotate(
        "D8b reaches F20",
        xy=(F20_FP, F20_TP),
        xytext=(122, 41),
        arrowprops={"arrowstyle": "->", "color": "#6f4b1d", "lw": 1.0},
        fontsize=9,
        fontweight="medium",
        color="#5b3d17",
        bbox={"boxstyle": "round,pad=0.16", "facecolor": "white", "edgecolor": "none", "alpha": 0.82},
    )
    ax.set_title("D1-D12 Defense Operating Points: Compact TP-FP Overview", fontsize=14, pad=14)
    style_count_axes(ax)
    handles = legend_handles()
    notation = Line2D([], [], linestyle="None", marker="", color="none", label="f=fixed, s=sweep, v=validation, r=recall, l=lowFA")
    ax.legend(handles=handles + [notation], loc="lower right", frameon=True, framealpha=0.92, fontsize=8.4)
    fig.text(
        0.5,
        0.025,
        "Compact count-space view of the fall-detection vs false-alarm burden tradeoff.",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#333333",
    )
    fig.subplots_adjust(left=0.09, right=0.985, top=0.90, bottom=0.12)
    fig.savefig(TPFP_COMPACT_PNG, dpi=220)
    fig.savefig(TPFP_COMPACT_PDF)
    plt.close(fig)


def write_confusion_decomposition_plot(rows: list[dict[str, Any]]) -> None:
    ordered_rows = ordered_confusion_rows(rows)
    y_positions = list(range(len(ordered_rows)))
    y_labels = [row["plot_label"] for row in ordered_rows]

    fig, axes = plt.subplots(ncols=2, sharey=True, figsize=(16.0, 11.2), gridspec_kw={"wspace": 0.08})
    fall_ax, nonfall_ax = axes

    tp_color = "#2c8a5a"
    fn_color = "#d46a6a"
    fp_color = "#d0742f"
    tn_color = "#4f7cac"

    for y, row in zip(y_positions, ordered_rows):
        if row["evidence_level"] == "validation-only FAR sweep":
            for ax in axes:
                ax.axhspan(y - 0.45, y + 0.45, color="#2c8a5a", alpha=0.06, zorder=0)
        if row["plot_label"] == "D8b AFAC-score":
            for ax in axes:
                ax.axhspan(y - 0.45, y + 0.45, color="#f0c36a", alpha=0.18, zorder=0)

        tp_pct = row["tp"] / TEST_FALL * 100
        fn_pct = row["fn"] / TEST_FALL * 100
        fp_pct = row["fp"] / TEST_NONFALL * 100
        tn_pct = row["tn"] / TEST_NONFALL * 100

        fall_ax.barh(y, tp_pct, color=tp_color, edgecolor="white", height=0.72, zorder=2)
        fall_ax.barh(y, fn_pct, left=tp_pct, color=fn_color, edgecolor="white", height=0.72, zorder=2)
        nonfall_ax.barh(y, fp_pct, color=fp_color, edgecolor="white", height=0.72, zorder=2)
        nonfall_ax.barh(y, tn_pct, left=fp_pct, color=tn_color, edgecolor="white", height=0.72, zorder=2)

        fall_ax.text(1.2, y, percent_label("TP", row["tp"], TEST_FALL), va="center", ha="left", fontsize=7.3, color="#111111")
        fall_ax.text(98.8, y, percent_label("FN", row["fn"], TEST_FALL), va="center", ha="right", fontsize=7.3, color="#111111")
        nonfall_ax.text(1.2, y, percent_label("FP", row["fp"], TEST_NONFALL), va="center", ha="left", fontsize=7.3, color="#111111")
        nonfall_ax.text(98.8, y, percent_label("TN", row["tn"], TEST_NONFALL), va="center", ha="right", fontsize=7.3, color="#111111")

    fall_ax.axvline(F20_RECALL * 100, color="#2f7d4d", linestyle="--", linewidth=1.2, zorder=3)
    nonfall_ax.axvline(F20_FAR * 100, color="#2f7d4d", linestyle="--", linewidth=1.2, zorder=3)
    fall_ax.text(F20_RECALL * 100 + 1.0, -0.72, "TP target 36/45 = 80%", fontsize=8, color="#276741", va="top")
    nonfall_ax.text(F20_FAR * 100 + 1.0, -0.72, "FP limit 91/455 = 20%", fontsize=8, color="#276741", va="top")

    for ax in axes:
        ax.set_xlim(0, 100)
        ax.grid(True, axis="x", linestyle="-", linewidth=0.5, alpha=0.22)
        ax.xaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
        ax.tick_params(axis="y", labelsize=8.2)
        ax.tick_params(axis="x", labelsize=8.5)

    fall_ax.set_yticks(y_positions)
    fall_ax.set_yticklabels(y_labels)
    fall_ax.invert_yaxis()
    fall_ax.set_xlabel("Fall windows: TP + FN (45 total)")
    nonfall_ax.set_xlabel("Non-fall windows: FP + TN (455 total)")
    fall_ax.set_title("Fall-side decomposition", fontsize=12, pad=10)
    nonfall_ax.set_title("Non-fall-side decomposition", fontsize=12, pad=10)

    handles = [
        Patch(facecolor=tp_color, label="TP: detected falls"),
        Patch(facecolor=fn_color, label="FN: missed falls"),
        Patch(facecolor=fp_color, label="FP: false fall alarms"),
        Patch(facecolor=tn_color, label="TN: correctly quiet non-falls"),
        Patch(facecolor="#f0c36a", alpha=0.35, label="D8b held-out test boundary"),
        Patch(facecolor="#2c8a5a", alpha=0.16, label="Validation-only rows"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.012), ncol=3, frameon=True, framealpha=0.94, fontsize=8.4)
    fig.suptitle("D1-D12 Confusion Decomposition: Fall Detection vs False-Alarm Burden", fontsize=15, y=0.982)
    fig.text(
        0.5,
        0.078,
        "Rows are grouped as held-out test fixed/argmax, held-out test post-hoc sweeps, validation-only sweeps, then D0 reference.",
        ha="center",
        fontsize=9,
        color="#333333",
    )
    fig.subplots_adjust(left=0.17, right=0.985, top=0.93, bottom=0.15)
    fig.savefig(CONFUSION_DECOMP_PNG, dpi=220)
    fig.savefig(CONFUSION_DECOMP_PDF)
    plt.close(fig)


def write_target_gap_quadrant_plot(rows: list[dict[str, Any]]) -> None:
    plotted = [row for row in rows if row["plotted"] and row["tp"] is not None and row["fp"] is not None]

    fig, ax = plt.subplots(figsize=(11.2, 8.0))
    ax.set_xlim(*TARGET_GAP_XLIM)
    ax.set_ylim(*TARGET_GAP_YLIM)
    xmin, xmax = TARGET_GAP_XLIM
    ymin, ymax = TARGET_GAP_YLIM
    ax.add_patch(Rectangle((0, 0), xmax, ymax, facecolor="#5aa469", alpha=0.10, zorder=0))
    ax.add_patch(Rectangle((xmin, 0), -xmin, ymax, facecolor="#d0742f", alpha=0.07, zorder=0))
    ax.add_patch(Rectangle((0, ymin), xmax, -ymin, facecolor="#4f7cac", alpha=0.06, zorder=0))
    ax.add_patch(Rectangle((xmin, ymin), -xmin, -ymin, facecolor="#d46a6a", alpha=0.06, zorder=0))
    ax.axvline(0, color="#2f7d4d", linestyle="--", linewidth=1.2, zorder=1)
    ax.axhline(0, color="#2f7d4d", linestyle="--", linewidth=1.2, zorder=1)

    ax.text(36, 5.7, "meets both", fontsize=9, color="#276741", ha="center", va="center")
    ax.text(-58, 5.7, "enough TP,\ntoo many FP", fontsize=8.5, color="#7a4b12", ha="center", va="center")
    ax.text(37, -33, "FP acceptable,\nTP low", fontsize=8.5, color="#275a88", ha="center", va="center")
    ax.text(-70, -33, "fails both", fontsize=8.5, color="#8f3939", ha="center", va="center")

    for row in plotted:
        marker, color, size, alpha = marker_style(row)
        x = F20_FP - row["fp"]
        y = row["tp"] - F20_TP
        edgecolor = "black" if row["plot_label"] == "D8b AFAC-score" else "white"
        linewidth = 1.8 if row["plot_label"] == "D8b AFAC-score" else 0.6
        afac_scale = 1.45 if row["plot_label"] == "D8b AFAC-score" else 1.0
        ax.scatter(
            x,
            y,
            marker=marker,
            s=size * afac_scale * 1.18,
            color=color,
            alpha=alpha,
            edgecolor=edgecolor,
            linewidth=linewidth,
            zorder=4 if row["plot_label"] == "D8b AFAC-score" else 3,
        )
        dx, dy = TARGET_GAP_LABEL_OFFSETS.get(row["plot_label"], (6, 6))
        ax.annotate(
            compact_label(row),
            (x, y),
            textcoords="offset points",
            xytext=(dx, dy),
            fontsize=8.3,
            fontweight="medium",
            arrowprops={"arrowstyle": "-", "color": "#4c4c4c", "lw": 0.7, "shrinkA": 3, "shrinkB": 4},
            bbox={"boxstyle": "round,pad=0.18", "facecolor": "white", "edgecolor": "#d8d8d8", "linewidth": 0.3, "alpha": 0.84},
            zorder=5,
        )

    ax.annotate(
        "D8b reaches held-out\ntest boundary",
        xy=(0, 0),
        xytext=(21, -7),
        arrowprops={"arrowstyle": "->", "color": "#6f4b1d", "lw": 1.0},
        fontsize=9,
        fontweight="medium",
        color="#5b3d17",
        bbox={"boxstyle": "round,pad=0.16", "facecolor": "white", "edgecolor": "none", "alpha": 0.82},
    )
    ax.set_title("D1-D12 Target-Gap Quadrant: Count-Space Judgment View", fontsize=14, pad=12)
    ax.set_xlabel("FP margin = 91 - FP (positive is better)")
    ax.set_ylabel("TP gap = TP - 36 (positive is better)")
    ax.grid(True, linestyle="-", linewidth=0.5, alpha=0.22)
    ax.legend(
        handles=legend_handles(),
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=3,
        frameon=True,
        framealpha=0.92,
        fontsize=8.5,
    )
    fig.text(
        0.5,
        0.055,
        "Targets: TP >= 36 detected falls and FP <= 91 false alarms. Validation-only rows are marked with green triangles.",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#333333",
    )
    fig.subplots_adjust(left=0.10, right=0.985, top=0.90, bottom=0.22)
    fig.savefig(TARGET_GAP_PNG, dpi=220)
    fig.savefig(TARGET_GAP_PDF)
    plt.close(fig)


def markdown_table(rows: list[dict[str, Any]]) -> str:
    columns = ["plot_label", "evidence_level", "split", "fall_recall", "far", "tp", "fn", "fp", "tn", "auroc", "source_type"]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        values = []
        for column in columns:
            value = row.get(column)
            if column in {"fall_recall", "far", "auroc"}:
                values.append(clean(value, digits=4))
            else:
                values.append(clean(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def tpfp_markdown_table(rows: list[dict[str, Any]]) -> str:
    columns = ["plot_label", "evidence_level", "split", "tp", "fp", "fn", "tn", "fall_recall", "far", "f20_met", "source_type"]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        values = []
        for column in columns:
            value = row.get(column)
            if column in {"fall_recall", "far"}:
                values.append(clean(value, digits=4))
            else:
                values.append(clean(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_tpfp_summary(rows: list[dict[str, Any]], discrepancies: list[str]) -> None:
    plotted_rows = [row for row in rows if row["plotted"] and row["tp"] is not None and row["fp"] is not None]
    not_plotted = [row for row in rows if not row["plotted"] or row["tp"] is None or row["fp"] is None]
    fallback_rows = [row for row in rows if row["source_type"] == "table_ia3_fallback"]
    target_rows = [row for row in plotted_rows if row["tp"] >= F20_TP and row["fp"] <= F20_FP]

    lines = [
        "# D1-D12 TP vs FP Count Plot Summary",
        "",
        "Generated by `scripts/analysis/plot_d1_d12_recall_far.py`.",
        "",
        "## Files created",
        "",
        f"- `{TPFP_DATA_CSV.relative_to(ROOT).as_posix()}`",
        f"- `{TPFP_PNG.relative_to(ROOT).as_posix()}`",
        f"- `{TPFP_PDF.relative_to(ROOT).as_posix()}`",
        f"- `{TPFP_COMPACT_PNG.relative_to(ROOT).as_posix()}`",
        f"- `{TPFP_COMPACT_PDF.relative_to(ROOT).as_posix()}`",
        f"- `{TPFP_SUMMARY_MD.relative_to(ROOT).as_posix()}`",
        "",
        "## Data sources used",
        "",
        f"- `{INVENTORY_CSV.relative_to(ROOT).as_posix()}` as the upstream artifact-backed inventory CSV.",
        f"- `{PLOT_DATA_CSV.relative_to(ROOT).as_posix()}` as the cleaned D1-D12 plotting table generated from the same pipeline.",
        f"- `{SUMMARY_MD.relative_to(ROOT).as_posix()}` for recall-vs-FAR provenance and fallback/discrepancy context.",
        "- `scripts/analysis/build_defense_attempt_inventory.py` for the upstream inventory-generation convention.",
        "- Attached `internal_defense_experiment_ledger.tex` Table IA.3 values as fallback/cross-check context only.",
        "",
        "## Plotted rows",
        "",
        tpfp_markdown_table(plotted_rows),
        "",
        "## Rows not plotted",
        "",
    ]

    if not_plotted:
        lines += [
            "| id | variant | reason | source_type |",
            "| --- | --- | --- | --- |",
        ]
        for row in not_plotted:
            reason = row["notes"]
            lines.append(f"| {row['id']} | {row['variant']} | {reason} | {row['source_type']} |")
    else:
        lines.append("- None.")

    lines += [
        "",
        "## Target-region definition",
        "",
        f"- TP >= {F20_TP}.",
        f"- FP <= {F20_FP}.",
        f"- This count-space F20 target is based on {TEST_FALL} held-out test fall windows and {TEST_NONFALL} held-out test non-fall windows.",
        "- The shaded target region is the count analog of fall recall >= 80% and FAR <= 20%.",
        "",
        "## Count-space target rows",
        "",
    ]

    if target_rows:
        for row in target_rows:
            evidence_note = "validation-only" if row["evidence_level"] == "validation-only FAR sweep" else row["evidence_level"]
            lines.append(f"- `{row['plot_label']}`: TP={row['tp']}, FP={row['fp']} ({evidence_note}).")
    else:
        lines.append("- No plotted row lands in or on the count-space target region.")

    lines += [
        "",
        "## Fallback usage",
        "",
    ]
    if fallback_rows:
        for row in fallback_rows:
            lines.append(f"- {row['plot_label']} used Table IA.3 fallback values.")
    else:
        lines.append("- No plotted numeric row used Table IA.3 fallback values; all plotted numeric rows were recovered from the inventory CSV/saved result artifacts.")

    lines += [
        "",
        "## Discrepancies vs Table IA.3 fallback values",
        "",
    ]
    if discrepancies:
        lines.extend(f"- {item}" for item in discrepancies)
    else:
        lines.append("- No numeric discrepancies beyond rounding tolerance were found for recovered rows.")

    lines += [
        "",
        "## Short interpretation",
        "",
        f"- D8b AFAC-score reaches the count-space F20 boundary with TP={F20_TP} and FP={F20_FP}.",
        "- D10/D11 validation-only rows may look stronger by counts, but they are not locked held-out test evidence.",
        "- D2 improves TP relative to many fixed/argmax rows, but with a very high FP burden.",
        "- D6b-fixed controls FP better than many alternatives, but TP remains below target.",
        "- Fixed/argmax and post-hoc variants illustrate the central tradeoff between recovering falls and increasing false alarms.",
        "- The count-space view emphasizes that the robustness problem is not merely increasing recall; it is recovering missed falls without creating an unacceptable false-alarm burden.",
    ]

    TPFP_SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def confusion_markdown_table(rows: list[dict[str, Any]]) -> str:
    columns = ["plot_label", "evidence_level", "split", "tp", "fn", "fp", "tn", "tp_gap", "fp_margin", "f20_met", "source_type"]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        values = []
        for column in columns:
            if column == "tp_gap":
                value = row["tp"] - F20_TP
            elif column == "fp_margin":
                value = F20_FP - row["fp"]
            else:
                value = row.get(column)
            values.append(clean(value, digits=4))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_confusion_summary(rows: list[dict[str, Any]], discrepancies: list[str]) -> None:
    ordered_rows = ordered_confusion_rows(rows)
    not_plotted = [row for row in rows if not row["plotted"] or row["tp"] is None or row["fp"] is None]
    fallback_rows = [row for row in rows if row["source_type"] == "table_ia3_fallback"]
    target_rows = [row for row in ordered_rows if row["tp"] >= F20_TP and row["fp"] <= F20_FP]

    lines = [
        "# D1-D12 Confusion-Decomposition Plot Summary",
        "",
        "Generated by `scripts/analysis/plot_d1_d12_recall_far.py`.",
        "",
        "## Files created",
        "",
        f"- `{CONFUSION_DATA_CSV.relative_to(ROOT).as_posix()}`",
        f"- `{CONFUSION_DECOMP_PNG.relative_to(ROOT).as_posix()}`",
        f"- `{CONFUSION_DECOMP_PDF.relative_to(ROOT).as_posix()}`",
        f"- `{TARGET_GAP_PNG.relative_to(ROOT).as_posix()}`",
        f"- `{TARGET_GAP_PDF.relative_to(ROOT).as_posix()}`",
        f"- `{CONFUSION_SUMMARY_MD.relative_to(ROOT).as_posix()}`",
        "",
        "## Data sources used",
        "",
        f"- `{INVENTORY_CSV.relative_to(ROOT).as_posix()}` as the upstream artifact-backed inventory CSV.",
        f"- `{PLOT_DATA_CSV.relative_to(ROOT).as_posix()}` as the cleaned D1-D12 plotting table generated by the same script.",
        f"- `{SUMMARY_MD.relative_to(ROOT).as_posix()}` for recall-vs-FAR provenance and fallback/discrepancy context.",
        "- `scripts/analysis/build_defense_attempt_inventory.py` for the upstream inventory-generation convention.",
        "- Attached `internal_defense_experiment_ledger.tex` Table IA.3 values as fallback/cross-check context only.",
        "",
        "## Plotted rows",
        "",
        confusion_markdown_table(ordered_rows),
        "",
        "## Row ordering used",
        "",
        "Rows are grouped in this order:",
        "1. Held-out test fixed/argmax rows.",
        "2. Held-out test post-hoc FAR sweep rows.",
        "3. Validation-only FAR sweep rows.",
        "4. D0 reference baseline.",
        "",
        "Within each group, rows follow the D1-D12 target order used by the existing recall-vs-FAR pipeline.",
        "",
        "## Rows not plotted",
        "",
    ]

    if not_plotted:
        lines += [
            "| id | variant | reason | source_type |",
            "| --- | --- | --- | --- |",
        ]
        for row in not_plotted:
            reason = row["notes"]
            lines.append(f"| {row['id']} | {row['variant']} | {reason} | {row['source_type']} |")
    else:
        lines.append("- None.")

    lines += [
        "",
        "## Count-target definitions",
        "",
        f"- Total held-out test fall windows = {TEST_FALL}.",
        f"- Total held-out test non-fall windows = {TEST_NONFALL}.",
        f"- Target TP >= {F20_TP}.",
        f"- Target FP <= {F20_FP}.",
        "- In the target-gap plot, `tp_gap = TP - 36` and `fp_margin = 91 - FP`.",
        "",
        "## Rows in or on the count target",
        "",
    ]

    if target_rows:
        for row in target_rows:
            evidence_note = "validation-only" if row["evidence_level"] == "validation-only FAR sweep" else row["evidence_level"]
            lines.append(f"- `{row['plot_label']}`: TP={row['tp']}, FP={row['fp']}, tp_gap={row['tp'] - F20_TP}, fp_margin={F20_FP - row['fp']} ({evidence_note}).")
    else:
        lines.append("- No plotted row lands in or on the count target.")

    lines += [
        "",
        "## Fallback usage",
        "",
    ]
    if fallback_rows:
        for row in fallback_rows:
            lines.append(f"- {row['plot_label']} used Table IA.3 fallback values.")
    else:
        lines.append("- No plotted numeric row used Table IA.3 fallback values; all plotted numeric rows were recovered from the inventory CSV/saved result artifacts.")

    lines += [
        "",
        "## Discrepancies vs Table IA.3 fallback values",
        "",
    ]
    if discrepancies:
        lines.extend(f"- {item}" for item in discrepancies)
    else:
        lines.append("- No numeric discrepancies beyond rounding tolerance were found for recovered rows.")

    lines += [
        "",
        "## Short interpretation",
        "",
        "- Methods that mainly fail by high FN include D1, D8a-lowFA, D3-sweep, D12 val, and D6a fixed/sweep; they keep false alarms relatively controlled but miss too many falls.",
        "- Methods that mainly fail by high FP include D2, D3-fixed, D4-fixed, and the D5/D7 fixed operating point; these create an unacceptable false-alarm burden.",
        "- D5-fixed and D7-fixed recover more falls than many fixed/argmax rows but remain over the FP target, illustrating the fall-recovery vs false-alarm tradeoff.",
        "- D6b-fixed controls FP better than many alternatives, but TP remains below target.",
        "- D8b AFAC-score reaches the count boundary on held-out test with TP=36 and FP=91.",
        "- D10/D11 look strong in count terms but remain validation-only and must not be described as locked held-out test evidence.",
        "- These figures are intended to support judgment statements such as: mainly misses falls, mainly over-predicts falls, balanced but below target, promising but validation-only, or reaches the held-out test boundary.",
    ]

    CONFUSION_SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(rows: list[dict[str, Any]], discrepancies: list[str]) -> None:
    plotted_rows = [row for row in rows if row["plotted"]]
    not_plotted = [row for row in rows if not row["plotted"]]
    fallback_rows = [row for row in rows if row["source_type"] == "table_ia3_fallback"]

    lines = [
        "# D1-D12 Recall vs FAR Plot Summary",
        "",
        "Generated by `scripts/analysis/plot_d1_d12_recall_far.py`.",
        "",
        "## Files created",
        "",
        f"- `{PLOT_DATA_CSV.relative_to(ROOT).as_posix()}`",
        f"- `{FULL_PNG.relative_to(ROOT).as_posix()}`",
        f"- `{FULL_PDF.relative_to(ROOT).as_posix()}`",
        f"- `{ZOOM_PNG.relative_to(ROOT).as_posix()}`",
        f"- `{ZOOM_PDF.relative_to(ROOT).as_posix()}`",
        f"- `{COMPACT_PNG.relative_to(ROOT).as_posix()}`",
        f"- `{COMPACT_PDF.relative_to(ROOT).as_posix()}`",
        f"- `{MIDZOOM_PNG.relative_to(ROOT).as_posix()}`",
        f"- `{MIDZOOM_PDF.relative_to(ROOT).as_posix()}`",
        f"- `{SUMMARY_MD.relative_to(ROOT).as_posix()}`",
        "",
        "## Data sources used",
        "",
        f"- `{INVENTORY_CSV.relative_to(ROOT).as_posix()}`",
        "- `results/defense_attempt_inventory/defense_attempt_results_summary.md` for cross-check context.",
        "- `results/defense_attempt_inventory/defense_attempt_results_summary.tex` for cross-check context.",
        "- `results/defense_attempt_inventory/defense_attempt_artifact_inventory.md` for provenance context.",
        "- `results/defense_attempt_inventory/missing_metrics_todo.md` for missing/validation-only status.",
        "- `scripts/analysis/build_defense_attempt_inventory.py` for the upstream inventory-generation convention.",
        "- Attached `internal_defense_experiment_ledger.tex` Table IA.3 values as fallback only.",
        "",
        "## Plotted rows",
        "",
        markdown_table(plotted_rows),
        "",
        "## Full overview plot",
        "",
        f"- `{FULL_PNG.relative_to(ROOT).as_posix()}` and `{FULL_PDF.relative_to(ROOT).as_posix()}` preserve the original-style full D1-D12 story with full labels.",
        "- This figure keeps the F20 shading, threshold lines, evidence-type legend, D0 reference point, and a D8b F20 callout.",
        "- Manual annotation offsets and light leader lines are used to reduce the worst full-label overlaps.",
        "",
        "## Zoom-only near-F20 plot",
        "",
        f"- `{ZOOM_PNG.relative_to(ROOT).as_posix()}` and `{ZOOM_PDF.relative_to(ROOT).as_posix()}` show only the near-F20 operating region.",
        "- The zoom-only figure labels each visible point with its ID/name plus exact FAR and recall percentages.",
        f"- Zoom window: FAR {ZOOM_XLIM[0]:.2f}-{ZOOM_XLIM[1]:.2f}; fall recall {ZOOM_YLIM[0]:.2f}-{ZOOM_YLIM[1]:.2f}.",
        "- `D10 val`, `D11a val`, and `D11b val` are validation-only triangle points; `D8b AFAC-score` is the held-out test post-hoc point on the F20 boundary.",
        "- Manual zoom offsets place `D10 val` to the right of its triangle, `D11b val` below its triangle, `D11a val` above/right, and `D8b AFAC-score` below/right.",
        "",
        "## Compact overview plot",
        "",
        f"- `{COMPACT_PNG.relative_to(ROOT).as_posix()}` and `{COMPACT_PDF.relative_to(ROOT).as_posix()}` use short labels for a cleaner thesis-style overview.",
        "- Compact notation: `f` = fixed/argmax, `s` = post-hoc FAR sweep, `v` = validation-only, `r` = AFAC-recall, `l` = AFAC-lowFA.",
        "- Only one interpretive callout is kept: `D8b reaches F20`.",
        "",
        "## Medium-range zoom plot",
        "",
        f"- `{MIDZOOM_PNG.relative_to(ROOT).as_posix()}` and `{MIDZOOM_PDF.relative_to(ROOT).as_posix()}` show a medium-range operating region.",
        f"- Window: FAR {MIDZOOM_XLIM[0] * 100:.0f}%-{MIDZOOM_XLIM[1] * 100:.0f}%; fall recall {MIDZOOM_YLIM[0] * 100:.0f}%-{MIDZOOM_YLIM[1] * 100:.0f}%.",
        "- This figure is intended to make the mid-trade-off operating points easier to inspect and show their relation to the F20 target region.",
        "- It uses compact labels and manual offsets for the dense D4-D8 area, including the coincident `D5-f`/`D7-f` point.",
        "",
        "## Manual annotation and residual crowding notes",
        "",
        "- Manual offsets are used for the full-label overview, zoom-only labels, compact labels, and medium-range zoom labels.",
        "- The zoom window was kept at the requested FAR 0.16-0.22 and recall 0.78-0.93.",
        "- The medium-range zoom window was kept at FAR 0.10-0.30 and recall 0.40-1.00.",
        "- The full-label overview intentionally remains text-heavy and has mild crowding around D5-D8 near FAR 0.19-0.21; the compact overview and medium-range zoom are intended as cleaner inspection views.",
        "",
        "## Rows not plotted",
        "",
    ]

    if not_plotted:
        lines += [
            "| id | variant | reason | source_type |",
            "| --- | --- | --- | --- |",
        ]
        for row in not_plotted:
            reason = row["notes"]
            lines.append(f"| {row['id']} | {row['variant']} | {reason} | {row['source_type']} |")
    else:
        lines.append("- None.")

    lines += [
        "",
        "## Fallback usage",
        "",
    ]
    if fallback_rows:
        for row in fallback_rows:
            lines.append(f"- {row['plot_label']} used Table IA.3 fallback values.")
    else:
        lines.append("- No plotted numeric rows used Table IA.3 fallback values; all numeric rows were recovered from the inventory CSV.")

    lines += [
        "",
        "## Discrepancies vs Table IA.3 fallback values",
        "",
    ]
    if discrepancies:
        lines.extend(f"- {item}" for item in discrepancies)
    else:
        lines.append("- No numeric discrepancies beyond rounding tolerance were found for recovered rows.")

    lines += [
        "",
        "## Short interpretation",
        "",
        "- D8b AFAC-score reaches the F20 boundary under a held-out test post-hoc threshold sweep.",
        "- D10/D11 validation-only rows look strong but are not locked held-out test evidence.",
        "- D9 has no usable artifact unless it is recovered or rerun under a documented protocol.",
        "- Fixed/argmax methods generally remain below the F20 target.",
    ]

    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    inventory_rows = read_inventory()
    output_rows: list[dict[str, Any]] = []
    discrepancies: list[str] = []

    for target in TARGETS:
        inventory_row = find_inventory_row(inventory_rows, target)
        output_row = make_output_row(target, inventory_row)
        output_rows.append(output_row)
        discrepancies.extend(compare_to_fallback(output_row, target))

    write_plot_data(output_rows)
    write_tpfp_plot_data(output_rows)
    write_confusion_plot_data(output_rows)
    write_plot(output_rows)
    write_zoom_plot(output_rows)
    write_compact_plot(output_rows)
    write_midzoom_plot(output_rows)
    write_tpfp_plot(output_rows)
    write_tpfp_compact_plot(output_rows)
    write_confusion_decomposition_plot(output_rows)
    write_target_gap_quadrant_plot(output_rows)
    write_summary(output_rows, discrepancies)
    write_tpfp_summary(output_rows, discrepancies)
    write_confusion_summary(output_rows, discrepancies)

    fallback_count = sum(1 for row in output_rows if row["source_type"] == "table_ia3_fallback")
    plotted_count = sum(1 for row in output_rows if row["plotted"])
    print(f"Loaded {len(inventory_rows)} inventory rows from {INVENTORY_CSV.relative_to(ROOT).as_posix()}.")
    print(f"Wrote {len(output_rows)} ledger rows; plotted {plotted_count} numeric rows.")
    print(f"Rows using Table IA.3 fallback: {fallback_count}.")
    print(f"CSV: {PLOT_DATA_CSV.relative_to(ROOT).as_posix()}")
    print(f"TP-FP CSV: {TPFP_DATA_CSV.relative_to(ROOT).as_posix()}")
    print(f"Confusion CSV: {CONFUSION_DATA_CSV.relative_to(ROOT).as_posix()}")
    print(f"Full PNG: {FULL_PNG.relative_to(ROOT).as_posix()}")
    print(f"Full PDF: {FULL_PDF.relative_to(ROOT).as_posix()}")
    print(f"Zoom PNG: {ZOOM_PNG.relative_to(ROOT).as_posix()}")
    print(f"Zoom PDF: {ZOOM_PDF.relative_to(ROOT).as_posix()}")
    print(f"Compact PNG: {COMPACT_PNG.relative_to(ROOT).as_posix()}")
    print(f"Compact PDF: {COMPACT_PDF.relative_to(ROOT).as_posix()}")
    print(f"Midzoom PNG: {MIDZOOM_PNG.relative_to(ROOT).as_posix()}")
    print(f"Midzoom PDF: {MIDZOOM_PDF.relative_to(ROOT).as_posix()}")
    print(f"TP-FP PNG: {TPFP_PNG.relative_to(ROOT).as_posix()}")
    print(f"TP-FP PDF: {TPFP_PDF.relative_to(ROOT).as_posix()}")
    print(f"TP-FP compact PNG: {TPFP_COMPACT_PNG.relative_to(ROOT).as_posix()}")
    print(f"TP-FP compact PDF: {TPFP_COMPACT_PDF.relative_to(ROOT).as_posix()}")
    print(f"Confusion decomposition PNG: {CONFUSION_DECOMP_PNG.relative_to(ROOT).as_posix()}")
    print(f"Confusion decomposition PDF: {CONFUSION_DECOMP_PDF.relative_to(ROOT).as_posix()}")
    print(f"Target-gap quadrant PNG: {TARGET_GAP_PNG.relative_to(ROOT).as_posix()}")
    print(f"Target-gap quadrant PDF: {TARGET_GAP_PDF.relative_to(ROOT).as_posix()}")
    print(f"Summary: {SUMMARY_MD.relative_to(ROOT).as_posix()}")
    print(f"TP-FP summary: {TPFP_SUMMARY_MD.relative_to(ROOT).as_posix()}")
    print(f"Confusion summary: {CONFUSION_SUMMARY_MD.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
