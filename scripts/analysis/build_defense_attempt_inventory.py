"""
Build an evidence inventory for defense attempts in the WiFi-CSI robustness repo.

Analysis only. This script reads existing CSV/JSON/Markdown/log/figure artifacts,
derives fall-vs-non-fall metrics only from saved per-window predictions or scores,
and writes a new report bundle under results/defense_attempt_inventory/.

It does not train models, run attacks, load checkpoints, edit thesis files, or
modify existing result artifacts.
"""
from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
OUT = RESULTS / "defense_attempt_inventory"
FALL_LABEL = 1
TEST_FALL = 45
TEST_NONFALL = 455
VAL_FALL = 44
VAL_NONFALL = 452
FAR_CAPS = (0.05, 0.10, 0.15, 0.20)

CSV_COLUMNS = [
    "method_internal_name",
    "method_thesis_name",
    "approach_group",
    "seed",
    "split",
    "attack",
    "epsilon",
    "checkpoint_or_threshold_rule",
    "threshold",
    "source_file",
    "source_type",
    "result_status",
    "TP",
    "FN",
    "FP",
    "TN",
    "Rfall",
    "FAR",
    "precision",
    "F1",
    "accuracy",
    "macro_F1",
    "AUROC",
    "Rfall_at_FAR_005",
    "Rfall_at_FAR_010",
    "Rfall_at_FAR_015",
    "Rfall_at_FAR_020",
    "TP_at_FAR_020",
    "FP_at_FAR_020",
    "F20_reached",
    "notes",
]

APPROACHES = [
    ("undefended_lenet_baseline", "Undefended LeNet baseline"),
    ("fgsm_adversarial_training_baseline", "FGSM adversarial-training baseline"),
    ("fall_weighted_training", "Fall-weighted training"),
    ("multi_budget_training", "Multi-budget training"),
    ("motion_margin_loss", "Motion/margin loss"),
    ("g1_hard_negative_margin", "G1 hard-negative/source-aware margin"),
    ("static_dual_tail_budget", "Static dual-tail rescue/budget objective"),
    ("rebalanced_dual_tail_floor", "Rebalanced dual-tail with fall-rescue floor"),
    ("dual_specialist_gate", "Dual-specialist gate"),
    ("afac_fixed_threshold", "AFAC fixed-threshold checkpoints"),
    ("afac_threshold_swept", "AFAC threshold-swept operating point"),
    ("trades_consistency", "TRADES-style fall-probability consistency"),
    ("gairat_boundary_reweighting", "GAIRAT-style boundary reweighting"),
    ("sat_selective_filtering", "SAT-style selective filtering"),
    ("bilstm_representation_pivot", "BiLSTM representation pivot"),
]


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")


def clean_num(value: Any) -> str:
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
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value)


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


def seed_from_path(path: Path, fallback: str = "") -> str:
    m = re.search(r"seed[_-]?(\d+)", rel(path), flags=re.I)
    return m.group(1) if m else fallback


def split_from_path(path: Path, data: dict[str, Any] | None = None) -> str:
    if data:
        for key in ("split", "dataset_split"):
            if data.get(key):
                return str(data[key]).lower()
    text = rel(path).lower()
    name = path.name.lower()
    if "legacy" in name or "_legacy_" in name:
        return "legacy"
    if "val_eval" in text or "_val_" in name or "validation" in text:
        return "val"
    if "test_eval" in text or "_test_" in name or "test_" in name:
        return "test"
    if "clean_metrics_test" in name:
        return "test"
    return "unknown"


def attack_from_path(path: Path, data: dict[str, Any] | None = None) -> str:
    if data and data.get("attack"):
        attack = str(data["attack"]).lower()
        return "clean" if attack in {"none", "clean"} else attack
    if data and data.get("attack_type"):
        attack = str(data["attack_type"]).lower()
        return "clean" if attack in {"none", "clean"} else attack
    if data and data.get("condition"):
        cond = str(data["condition"]).lower()
        if "pgd" in cond:
            return "pgd"
        if "fgsm" in cond:
            return "fgsm"
        if "clean" in cond or "none" in cond:
            return "clean"
    name = path.name.lower()
    if "pgd" in name:
        return "pgd"
    if "fgsm" in name:
        return "fgsm"
    if "clean" in name:
        return "clean"
    return "unknown"


def epsilon_from_path(path: Path, data: dict[str, Any] | None = None) -> float | None:
    attack = attack_from_path(path, data)
    if attack == "clean":
        return 0.0
    if data:
        for key in ("epsilon", "eps"):
            value = as_float(data.get(key))
            if value is not None:
                return value
    m = re.search(r"epsilon_([0-9]+(?:_[0-9]+)?)", path.name, flags=re.I)
    if m:
        return as_float(m.group(1).replace("_", "."))
    m = re.search(r"eps(?:ilon)?[_-]?([0-9]+(?:p[0-9]+)?)", rel(path), flags=re.I)
    if m:
        return as_float(m.group(1).replace("p", "."))
    return None


def read_csv_rows(path: Path, limit: int | None = None) -> tuple[list[str], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                return [], []
            for i, row in enumerate(reader):
                if limit is not None and i >= limit:
                    break
                rows.append({k: (v if v is not None else "") for k, v in row.items()})
            return list(reader.fieldnames), rows
    except Exception:
        return [], []


def is_metric_value_csv(columns: list[str]) -> bool:
    return len(columns) >= 2 and norm(columns[0]) == "metric" and norm(columns[1]) == "value"


def metric_value_dict(rows: list[dict[str, str]], columns: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    if not is_metric_value_csv(columns):
        return out
    metric_col, value_col = columns[0], columns[1]
    for row in rows:
        key = norm(row.get(metric_col, ""))
        if key:
            out[key] = row.get(value_col, "")
    return out


def find_col(columns: list[str], names: list[str]) -> str | None:
    lookup = {norm(c): c for c in columns}
    for name in names:
        hit = lookup.get(norm(name))
        if hit:
            return hit
    return None


LABEL_COLUMNS = [
    "fall_true_binary",
    "true_binary",
    "y_true_binary",
    "is_fall",
    "true_label",
    "y_true",
    "label",
]
PRED_COLUMNS = [
    "fall_pred_binary",
    "attacked_fall_pred_binary",
    "clean_fall_pred_binary",
    "predicted_label",
    "attacked_predicted_label",
    "clean_predicted_label",
    "prediction",
    "pred",
]
SCORE_COLUMNS = [
    "fall_probability",
    "prob_fall",
    "p_fall",
    "fall_prob",
    "score_fall",
    "fall_score",
    "logit_fall",
]


def label_value(value: Any, col: str) -> int | None:
    iv = as_int(value)
    if iv is None:
        return None
    ncol = norm(col)
    if ncol in {"fall_true_binary", "true_binary", "y_true_binary", "is_fall"}:
        return 1 if iv == 1 else 0
    if ncol in {"true_label", "y_true", "label"}:
        return 1 if iv == FALL_LABEL else 0
    if iv in {0, 1}:
        return iv
    return 1 if iv == FALL_LABEL else 0


def pred_value(value: Any, col: str) -> int | None:
    iv = as_int(value)
    if iv is None:
        return None
    ncol = norm(col)
    if "binary" in ncol or ncol in {"prediction", "pred"} and iv in {0, 1}:
        return 1 if iv == 1 else 0
    return 1 if iv == FALL_LABEL else 0


def counts_from_binary(y: list[int], pred: list[int]) -> dict[str, int]:
    tp = sum(1 for a, b in zip(y, pred) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(y, pred) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(y, pred) if a == 0 and b == 1)
    tn = sum(1 for a, b in zip(y, pred) if a == 0 and b == 0)
    return {"TP": tp, "FN": fn, "FP": fp, "TN": tn}


def enrich_metrics(row: dict[str, Any]) -> dict[str, Any]:
    tp = as_int(row.get("TP"))
    fn = as_int(row.get("FN"))
    fp = as_int(row.get("FP"))
    tn = as_int(row.get("TN"))
    if tp is None or fn is None or fp is None or tn is None:
        return row
    pos = tp + fn
    neg = fp + tn
    total = pos + neg
    row["Rfall"] = tp / pos if pos else None
    row["FAR"] = fp / neg if neg else None
    row["precision"] = tp / (tp + fp) if (tp + fp) else None
    row["F1"] = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else None
    if not row.get("accuracy"):
        row["accuracy"] = (tp + tn) / total if total else None
    rfall = row.get("Rfall")
    far = row.get("FAR")
    row["F20_reached"] = bool(rfall is not None and far is not None and rfall >= 0.80 and far <= 0.20)
    return row


def auc_from_scores(y: list[int], scores: list[float]) -> float | None:
    n_pos = sum(y)
    n_neg = len(y) - n_pos
    if n_pos == 0 or n_neg == 0:
        return None
    pairs = sorted(zip(scores, y), key=lambda item: item[0])
    ranks = [0.0] * len(pairs)
    i = 0
    while i < len(pairs):
        j = i + 1
        while j < len(pairs) and pairs[j][0] == pairs[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j
    rank_sum_pos = sum(rank for rank, (_, label) in zip(ranks, pairs) if label == 1)
    return (rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def threshold_curve(y: list[int], scores: list[float]) -> list[dict[str, Any]]:
    if not y:
        return []
    thresholds = sorted(set(scores), reverse=True)
    if thresholds:
        thresholds = [math.nextafter(thresholds[0], math.inf)] + thresholds
    rows: list[dict[str, Any]] = []
    n_fall = sum(y)
    n_nonfall = len(y) - n_fall
    for threshold in thresholds:
        pred = [1 if score >= threshold else 0 for score in scores]
        counts = counts_from_binary(y, pred)
        rec = counts["TP"] / n_fall if n_fall else None
        far = counts["FP"] / n_nonfall if n_nonfall else None
        rows.append({**counts, "threshold": threshold, "Rfall": rec, "FAR": far})
    return rows


def best_at_far(curve: list[dict[str, Any]], cap: float) -> dict[str, Any] | None:
    feasible = [row for row in curve if row.get("FAR") is not None and row["FAR"] <= cap]
    if not feasible:
        return None
    return sorted(
        feasible,
        key=lambda row: (
            -(row.get("Rfall") or 0.0),
            row.get("FP") or 10**9,
            -(row.get("threshold") or -10**9),
        ),
    )[0]


@dataclass(frozen=True)
class MethodInfo:
    internal: str
    thesis: str
    group: str
    notes: str = ""


def method_from_path(path: Path, row: dict[str, Any] | None = None, for_sweep: bool = False) -> MethodInfo:
    rpath = rel(path)
    text = rpath.lower().replace("\\", "/")
    name = path.name
    row = row or {}
    row_method = str(
        row.get("checkpoint")
        or row.get("model_defense")
        or row.get("model_type")
        or row.get("run_name")
        or ""
    )
    combined = f"{text} {row_method.lower()}"

    if "trades" in combined:
        return MethodInfo("trades_consistency", "TRADES-style fall-probability consistency", "TRADES-style fall-probability consistency")
    if "variantg_bilstm_representation_test" in combined or "representation_bilstm" in combined or "bilstm_g1" in combined:
        return MethodInfo("bilstm_g1_representation_pivot", "BiLSTM representation pivot", "BiLSTM representation pivot")
    if "/gairat/" in combined or "gairat" in combined or "gr1_" in combined:
        return MethodInfo("gairat_gr1", "GAIRAT-style boundary reweighting", "GAIRAT-style boundary reweighting")
    if "/sat/" in combined or "sat-style" in combined or "sa1_" in combined or "basat_sat" in combined:
        return MethodInfo("sat_sa1", "SAT-style selective filtering", "SAT-style selective filtering")
    if "boundary_aware_selective_at" in combined or "basat" in combined or "stage1" in combined or "st1" in combined:
        return MethodInfo("basat_stage1", "SAT-style selective filtering (Stage-1/BASAT pilot)", "SAT-style selective filtering")
    if "optiona_rebalanced" in combined or "optiona" in combined or "a1_v2" in combined:
        return MethodInfo("optionA_A1", "Rebalanced dual-tail with fall-rescue floor", "Rebalanced dual-tail with fall-rescue floor")
    if "dual_specialist_safety_gate" in combined or "gate_dual_specialist" in combined or re.search(r"(^|[/_])(b_|r_).*g1", combined):
        return MethodInfo("dual_specialist_gate_A1", "Dual-specialist gate", "Dual-specialist gate")
    if "optionb" in combined or "adaptive_lagrangian_far_constrained" in combined:
        thesis = "AFAC"
        if "maxscore" in combined:
            thesis = "AFAC-score"
        elif "maxrec" in combined:
            thesis = "AFAC-recall"
        elif "minfa" in combined:
            thesis = "AFAC-lowFA"
        group = "AFAC threshold-swept operating point" if for_sweep else "AFAC fixed-threshold checkpoints"
        return MethodInfo("optionB_AFAC", thesis, group)
    if "varianth_dual_tail_budget" in combined or "variant_h" in combined:
        return MethodInfo("variantH_H1", "Static dual-tail rescue/budget objective", "Static dual-tail rescue/budget objective")
    if "variantg_targeted_hardneg" in combined or re.search(r"\bg_g1\b", combined) or "variant g" in combined or "g1" in row_method.lower():
        return MethodInfo("variantG_G1", "G1 hard-negative/source-aware margin", "G1 hard-negative/source-aware margin")
    if "variantf_motion_margin" in combined or "variant f" in combined or "motion_margin" in combined or "variantf" in combined:
        return MethodInfo("variantF_motion_margin", "Motion/margin loss", "Motion/margin loss")
    if "varianted" in combined or "variantd" in combined or "multi_eps" in combined or "multieps" in combined or "multi-budget" in combined:
        return MethodInfo("safety_guided_variantD", "Multi-budget training", "Multi-budget training")
    if "variantb" in combined or "variantc" in combined or "fw3" in combined or "fall-weight" in combined or "fall_weight" in combined:
        if "variantc" in combined:
            return MethodInfo("safety_guided_variantC", "Fall-weighted training (FGSM+PGD)", "Fall-weighted training")
        return MethodInfo("safety_guided_variantB", "Fall-weighted training", "Fall-weighted training")
    if "varianta" in combined or "safety_guided_defense/seed" in combined:
        return MethodInfo("safety_guided_variantA", "Safety-guided PGD AT reference", "Fall-weighted training")
    if "defended_fgsm_at" in combined or "fgsm_adversarial_training" in combined or "existing fgsm defense" in combined or "fgsm_defense" in combined or "defended_" in combined:
        return MethodInfo("fgsm_adv_training", "FGSM adversarial-training baseline", "FGSM adversarial-training baseline")
    if "converged_seed" in combined or "clean lenet baseline" in combined or "clean_baseline" in combined or "undefended" in combined:
        return MethodInfo("undefended_lenet", "Undefended LeNet baseline", "Undefended LeNet baseline")
    return MethodInfo("unknown", "unknown", "unknown")


def result_row_base(path: Path, info: MethodInfo, source_type: str, status: str) -> dict[str, Any]:
    return {
        "method_internal_name": info.internal,
        "method_thesis_name": info.thesis,
        "approach_group": info.group,
        "seed": seed_from_path(path),
        "split": split_from_path(path),
        "attack": attack_from_path(path),
        "epsilon": epsilon_from_path(path),
        "checkpoint_or_threshold_rule": "",
        "threshold": "",
        "source_file": rel(path),
        "source_type": source_type,
        "result_status": status,
        "TP": "",
        "FN": "",
        "FP": "",
        "TN": "",
        "Rfall": "",
        "FAR": "",
        "precision": "",
        "F1": "",
        "accuracy": "",
        "macro_F1": "",
        "AUROC": "",
        "Rfall_at_FAR_005": "",
        "Rfall_at_FAR_010": "",
        "Rfall_at_FAR_015": "",
        "Rfall_at_FAR_020": "",
        "TP_at_FAR_020": "",
        "FP_at_FAR_020": "",
        "F20_reached": "",
        "notes": info.notes,
    }


COUNT_KEYS = {
    "TP": ["fall_true_positive", "true_positive_fall_detected", "tp_detected_falls", "tp"],
    "FN": ["fall_false_negative", "false_negative_missed_falls", "fn_missed_falls", "fn"],
    "FP": ["fall_false_positive", "false_fall_alarm_count", "fp_false_fall_alarms", "fp"],
    "TN": ["fall_true_negative", "true_negative_non_falls", "tn_correct_non_falls", "tn"],
}


def first_present(data: dict[str, Any], names: list[str]) -> Any:
    for name in names:
        key = norm(name)
        if key in data and str(data[key]) != "":
            return data[key]
    return None


def counts_from_metric_data(data: dict[str, Any]) -> dict[str, int] | None:
    out: dict[str, int] = {}
    for key, names in COUNT_KEYS.items():
        value = as_int(first_present(data, names))
        if value is None:
            return None
        out[key] = value
    return out


def direct_metric_rows(path: Path, columns: list[str], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if is_metric_value_csv(columns):
        data = metric_value_dict(rows, columns)
        counts = counts_from_metric_data(data)
        if counts:
            info = method_from_path(path, data)
            row = result_row_base(path, info, "reported_metrics_csv", "direct_reported_counts")
            row.update(counts)
            row["split"] = split_from_path(path, data)
            row["attack"] = attack_from_path(path, data)
            row["epsilon"] = epsilon_from_path(path, data)
            row["checkpoint_or_threshold_rule"] = "reported fixed argmax/checkpoint"
            attack = row["attack"]
            if attack in {"fgsm", "pgd"}:
                row["accuracy"] = as_float(data.get("attack_accuracy"))
                row["macro_F1"] = as_float(data.get("attack_macro_f1"))
            else:
                row["accuracy"] = as_float(data.get("accuracy") or data.get("clean_accuracy"))
                row["macro_F1"] = as_float(data.get("macro_f1") or data.get("clean_macro_f1"))
            row["Rfall"] = as_float(data.get("fall_recall") or data.get("recall_sensitivity"))
            row["precision"] = as_float(data.get("fall_precision") or data.get("precision"))
            row["F1"] = as_float(data.get("fall_f1") or data.get("f1_score"))
            row = enrich_metrics(row)
            out.append(row)
        return out

    ncols = {norm(c): c for c in columns}
    has_counts = any(norm(name) in ncols for names in COUNT_KEYS.values() for name in names)
    if not has_counts:
        return out

    for raw in rows:
        data = {norm(k): v for k, v in raw.items()}
        counts = counts_from_metric_data(data)
        if not counts:
            continue
        info = method_from_path(path, raw)
        row = result_row_base(path, info, "reported_metrics_table", "direct_reported_counts")
        row.update(counts)
        row["split"] = split_from_path(path, raw)
        row["attack"] = attack_from_path(path, raw)
        row["epsilon"] = epsilon_from_path(path, raw)
        condition = raw.get("condition") or raw.get("checkpoint") or raw.get("selection_method") or ""
        row["checkpoint_or_threshold_rule"] = condition or "reported fixed argmax/checkpoint"
        row["accuracy"] = as_float(raw.get("accuracy") or raw.get("seven_class_accuracy") or raw.get("binary_accuracy"))
        row["macro_F1"] = as_float(raw.get("macro_f1") or raw.get("attack_macro_f1") or raw.get("clean_macro_f1"))
        row["Rfall"] = as_float(raw.get("fall_recall") or raw.get("recall_sensitivity"))
        row["precision"] = as_float(raw.get("fall_precision") or raw.get("precision"))
        row["F1"] = as_float(raw.get("fall_f1") or raw.get("f1_score") or raw.get("binary_f1"))
        row = enrich_metrics(row)
        out.append(row)
    return out


def group_rows_for_conditions(rows: list[dict[str, str]], columns: list[str]) -> list[list[dict[str, str]]]:
    condition_col = find_col(columns, ["condition"])
    epsilon_col = find_col(columns, ["epsilon"])
    if not condition_col and not epsilon_col:
        return [rows]
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row.get(condition_col, "")) if condition_col else "",
            str(row.get(epsilon_col, "")) if epsilon_col else "",
        )
        groups[key].append(row)
    return list(groups.values())


def condition_data_from_group(group: list[dict[str, str]], path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if group:
        first = group[0]
        for key in ("condition", "epsilon", "attack", "attack_type", "split"):
            if key in first:
                data[key] = first[key]
    if "condition" in data:
        cond = str(data["condition"]).lower()
        if cond == "clean":
            data["attack"] = "clean"
            data["epsilon"] = "0"
        elif "fgsm" in cond:
            data["attack"] = "fgsm"
        elif "pgd" in cond:
            data["attack"] = "pgd"
    if not data.get("attack"):
        data["attack"] = attack_from_path(path)
    if not data.get("epsilon"):
        eps = epsilon_from_path(path, data)
        if eps is not None:
            data["epsilon"] = eps
    return data


def prediction_columns_for_group(columns: list[str], group: list[dict[str, str]], attack: str) -> tuple[str | None, str | None]:
    label_col = find_col(columns, LABEL_COLUMNS)
    if attack == "clean":
        pred_col = find_col(columns, ["fall_pred_binary", "clean_fall_pred_binary", "predicted_label", "clean_predicted_label"])
    else:
        pred_col = find_col(columns, ["fall_pred_binary", "attacked_fall_pred_binary", "predicted_label", "attacked_predicted_label"])
    if pred_col is None:
        pred_col = find_col(columns, PRED_COLUMNS)
    return label_col, pred_col


def score_columns_for_group(columns: list[str]) -> tuple[str | None, str | None]:
    return find_col(columns, LABEL_COLUMNS), find_col(columns, SCORE_COLUMNS)


def per_window_rows(path: Path, columns: list[str], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not rows:
        return out
    for group in group_rows_for_conditions(rows, columns):
        data = condition_data_from_group(group, path)
        attack = attack_from_path(path, data)
        # Fixed argmax/hard-prediction result.
        label_col, pred_col = prediction_columns_for_group(columns, group, attack)
        if label_col and pred_col:
            y: list[int] = []
            pred: list[int] = []
            for raw in group:
                yl = label_value(raw.get(label_col), label_col)
                pr = pred_value(raw.get(pred_col), pred_col)
                if yl is not None and pr is not None:
                    y.append(yl)
                    pred.append(pr)
            if y and len(y) == len(pred):
                info = method_from_path(path, data)
                row = result_row_base(path, info, "per_window_predictions_csv", "derived_from_per_window_predictions")
                row.update(counts_from_binary(y, pred))
                row["split"] = split_from_path(path, data)
                row["attack"] = attack
                row["epsilon"] = epsilon_from_path(path, data)
                row["checkpoint_or_threshold_rule"] = f"fixed argmax via {pred_col}"
                row["notes"] = f"Derived using fall-positive class 1 from {label_col}/{pred_col}."
                row = enrich_metrics(row)
                out.append(row)

        # Post-hoc threshold-swept result from scores.
        score_label_col, score_col = score_columns_for_group(columns)
        if score_label_col and score_col:
            y = []
            scores: list[float] = []
            for raw in group:
                yl = label_value(raw.get(score_label_col), score_label_col)
                score = as_float(raw.get(score_col))
                if yl is not None and score is not None:
                    y.append(yl)
                    scores.append(score)
            if y and len(y) == len(scores) and len(set(y)) == 2:
                info = method_from_path(path, data, for_sweep=True)
                curve = threshold_curve(y, scores)
                auroc = auc_from_scores(y, scores)
                row = result_row_base(path, info, "per_window_score_csv", "post_hoc_threshold_sweep_from_saved_scores")
                row["split"] = split_from_path(path, data)
                row["attack"] = attack
                row["epsilon"] = epsilon_from_path(path, data)
                row["checkpoint_or_threshold_rule"] = f"post-hoc fall-score threshold sweep via {score_col}"
                row["AUROC"] = auroc
                notes = [f"Score column {score_col}; fall-positive class 1."]
                for cap in FAR_CAPS:
                    best = best_at_far(curve, cap)
                    suffix = f"{int(round(cap * 100)):03d}"
                    if best:
                        row[f"Rfall_at_FAR_{suffix}"] = best.get("Rfall")
                        notes.append(
                            f"FAR<={cap:.2f}: thr={best.get('threshold'):.6g}, "
                            f"TP/FN/FP/TN={best.get('TP')}/{best.get('FN')}/{best.get('FP')}/{best.get('TN')}"
                        )
                        if abs(cap - 0.20) < 1e-12:
                            row["threshold"] = best.get("threshold")
                            row["TP"] = best.get("TP")
                            row["FN"] = best.get("FN")
                            row["FP"] = best.get("FP")
                            row["TN"] = best.get("TN")
                            row["TP_at_FAR_020"] = best.get("TP")
                            row["FP_at_FAR_020"] = best.get("FP")
                row = enrich_metrics(row)
                row["F20_reached"] = bool(as_float(row.get("Rfall_at_FAR_020")) is not None and as_float(row.get("Rfall_at_FAR_020")) >= 0.80)
                row["notes"] = " ".join(notes)
                out.append(row)
    return out


def candidate_files() -> list[Path]:
    exts = {".csv", ".md", ".json", ".log", ".txt", ".png", ".jpg", ".jpeg"}
    roots = [RESULTS, ROOT / "notes", ROOT / "scripts", ROOT]
    seen: set[Path] = set()
    files: list[Path] = []
    for start in roots:
        if not start.exists():
            continue
        if start == ROOT:
            iterable = [p for p in start.glob("*.log")] + [p for p in start.glob("*.md")]
        else:
            iterable = start.rglob("*")
        for path in iterable:
            if not path.is_file() or path.suffix.lower() not in exts:
                continue
            r = rel(path)
            low = r.lower()
            if any(part in low for part in ["/.git/", "/.venv/", "results/defense_attempt_inventory/"]):
                continue
            info = method_from_path(path)
            if info.group == "unknown":
                continue
            rp = path.resolve()
            if rp not in seen:
                seen.add(rp)
                files.append(path)
    return sorted(files, key=lambda p: rel(p).lower())


def inspect_artifact(path: Path) -> dict[str, Any]:
    info = method_from_path(path)
    row: dict[str, Any] = {
        "path": rel(path),
        "file_type": path.suffix.lower().lstrip(".") or "unknown",
        "likely_method_internal_name": info.internal,
        "thesis_facing_name": info.thesis,
        "approach_group": info.group,
        "split": split_from_path(path),
        "seed": seed_from_path(path),
        "attack": attack_from_path(path),
        "epsilon": clean_num(epsilon_from_path(path)),
        "contains_hard_predictions": "no",
        "contains_fall_scores_probabilities_logits": "no",
        "contains_TP_FN_FP_TN": "no",
        "AUROC_can_be_computed": "no",
        "threshold_swept_recall_at_FAR_cap_can_be_computed": "no",
        "notes": "",
    }
    if path.suffix.lower() == ".csv":
        columns, rows = read_csv_rows(path, limit=None)
        if columns:
            ncols = {norm(c) for c in columns}
            label_col = find_col(columns, LABEL_COLUMNS)
            score_col = find_col(columns, SCORE_COLUMNS)
            pred_col = find_col(columns, PRED_COLUMNS)
            has_count_cols = any(norm(name) in ncols for names in COUNT_KEYS.values() for name in names)
            has_metric_counts = False
            if is_metric_value_csv(columns):
                data = metric_value_dict(rows, columns)
                has_metric_counts = counts_from_metric_data(data) is not None
            row["contains_hard_predictions"] = "yes" if pred_col else "no"
            row["contains_fall_scores_probabilities_logits"] = "yes" if score_col else "no"
            row["contains_TP_FN_FP_TN"] = "yes" if has_count_cols or has_metric_counts else "no"
            row["AUROC_can_be_computed"] = "yes" if label_col and score_col else "no"
            row["threshold_swept_recall_at_FAR_cap_can_be_computed"] = "yes" if label_col and score_col else "no"
            row["notes"] = f"columns={len(columns)}, rows={len(rows)}"
    elif path.suffix.lower() == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            text = json.dumps(data).lower()
            if all(k in text for k in ["true_positive", "false_negative", "false_positive", "true_negative"]):
                row["contains_TP_FN_FP_TN"] = "yes"
            if "smoke" in text:
                row["notes"] = "smoke/metadata artifact; not a standalone evaluation unless paired with CSVs"
        except Exception:
            pass
    elif path.suffix.lower() in {".md", ".log", ".txt"}:
        try:
            sample = path.read_text(encoding="utf-8", errors="replace")[:20000].lower()
            if re.search(r"\btp\b.*\bfp\b|\bpgd fp\b|\bfall_true_positive\b", sample):
                row["contains_TP_FN_FP_TN"] = "possibly"
            if "probabilities" in sample or "p(fall)" in sample or "auroc" in sample:
                row["contains_fall_scores_probabilities_logits"] = "possibly referenced"
            if "validation only" in sample or "val " in sample:
                row["notes"] = "text/report artifact; inspect cited CSVs for exact computable metrics"
        except Exception:
            pass
    return row


def dedupe_result_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Prefer direct reported metrics over per-window derivations for the same source family,
    # but keep score-sweep rows because they answer a different operating-point question.
    priority = {
        "direct_reported_counts": 0,
        "derived_from_per_window_predictions": 1,
        "post_hoc_threshold_sweep_from_saved_scores": 2,
        "not_found": 9,
    }
    best: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        if row["result_status"] == "post_hoc_threshold_sweep_from_saved_scores":
            key = (
                row["method_internal_name"],
                row["method_thesis_name"],
                row["approach_group"],
                row["seed"],
                row["split"],
                row["attack"],
                clean_num(row["epsilon"]),
                row["checkpoint_or_threshold_rule"],
                row["source_file"],
            )
        else:
            # Collapse metrics/predictions that report the same fixed checkpoint result.
            source_stem = re.sub(r"_(predictions|probabilities|safety_metrics).*", "", Path(str(row["source_file"])).name)
            key = (
                row["method_internal_name"],
                row["method_thesis_name"],
                row["approach_group"],
                row["seed"],
                row["split"],
                row["attack"],
                clean_num(row["epsilon"]),
                source_stem,
            )
        old = best.get(key)
        if old is None or priority.get(row["result_status"], 5) < priority.get(old["result_status"], 5):
            best[key] = row
    return sorted(
        best.values(),
        key=lambda r: (
            r.get("approach_group", ""),
            r.get("method_thesis_name", ""),
            str(r.get("seed", "")),
            r.get("split", ""),
            r.get("attack", ""),
            clean_num(r.get("epsilon")),
            r.get("result_status", ""),
            r.get("source_file", ""),
        ),
    )


def add_missing_rows(rows: list[dict[str, Any]], artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    present_groups = {row["approach_group"] for row in rows if row.get("TP") != "" or row.get("AUROC") != ""}
    artifact_groups = {a["approach_group"] for a in artifacts}
    for key, thesis in APPROACHES:
        if thesis in present_groups:
            continue
        info = MethodInfo(key, thesis, thesis)
        row = {col: "" for col in CSV_COLUMNS}
        row.update(
            {
                "method_internal_name": info.internal,
                "method_thesis_name": info.thesis,
                "approach_group": info.group,
                "result_status": "not_found" if thesis not in artifact_groups else "no_standalone_result",
                "source_type": "inventory_gap",
                "notes": "No usable standalone metric row found in existing artifacts."
                if thesis not in artifact_groups
                else "Artifacts exist, but no standalone TP/FN/FP/TN or saved-score operating point was found.",
            }
        )
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: clean_num(row.get(col, "")) for col in columns})


def md_table(rows: list[dict[str, Any]], columns: list[str], max_rows: int | None = None) -> str:
    use_rows = rows if max_rows is None else rows[:max_rows]
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in use_rows:
        vals = [clean_num(row.get(col, "")).replace("|", "\\|") for col in columns]
        out.append("| " + " | ".join(vals) + " |")
    if max_rows is not None and len(rows) > max_rows:
        out.append(f"| ... | {len(rows) - max_rows} additional rows omitted here; see CSV. |" + " |" * (len(columns) - 2))
    return "\n".join(out)


def summarize(rows: list[dict[str, Any]], artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["approach_group"]].append(row)
    exact = []
    score_groups = []
    val_only = []
    auroc_only = []
    no_usable = []
    for _, group_name in APPROACHES:
        grows = groups.get(group_name, [])
        usable = [r for r in grows if r.get("TP") != "" and r.get("FN") != "" and r.get("FP") != "" and r.get("TN") != ""]
        scores = [r for r in grows if r.get("result_status") == "post_hoc_threshold_sweep_from_saved_scores"]
        has_test = any(r.get("split") == "test" and r.get("TP") != "" for r in grows)
        has_val = any(r.get("split") == "val" and r.get("TP") != "" for r in grows)
        has_auroc = any(r.get("AUROC") not in {"", None} for r in grows)
        if usable:
            exact.append(group_name)
        if scores:
            score_groups.append(group_name)
        if has_val and not has_test:
            val_only.append(group_name)
        if has_auroc and not usable:
            auroc_only.append(group_name)
        if not usable and not has_auroc:
            no_usable.append(group_name)
    return {
        "groups": groups,
        "exact": exact,
        "score_groups": score_groups,
        "val_only": val_only,
        "auroc_only": auroc_only,
        "no_usable": no_usable,
        "artifact_count": len(artifacts),
        "result_count": len(rows),
    }


def best_test_pgd(rows: list[dict[str, Any]], swept: bool | None = None) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        if row.get("split") != "test" or row.get("attack") != "pgd":
            continue
        eps = as_float(row.get("epsilon"))
        if eps is None or abs(eps - 0.03) > 1e-9:
            continue
        if swept is True and row.get("result_status") != "post_hoc_threshold_sweep_from_saved_scores":
            continue
        if swept is False and row.get("result_status") == "post_hoc_threshold_sweep_from_saved_scores":
            continue
        rfall = as_float(row.get("Rfall_at_FAR_020") if swept else row.get("Rfall"))
        far = as_float(row.get("FAR"))
        fp = as_int(row.get("FP"))
        if rfall is None:
            continue
        out.append({**row, "_rank_rfall": rfall, "_rank_far": far if far is not None else 9.0, "_rank_fp": fp if fp is not None else 10**9})
    return sorted(out, key=lambda r: (-r["_rank_rfall"], r["_rank_fp"], r.get("method_thesis_name", "")))


def write_artifact_inventory(path: Path, artifacts: list[dict[str, Any]]) -> None:
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for art in artifacts:
        by_group[art["approach_group"]].append(art)
    lines = [
        "# Defense Attempt Artifact Inventory",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "Scope: existing local artifacts only. No model training, new attacks, checkpoint loading, thesis edits, or commits.",
        "Fall-positive convention used for derivations: UT-HAR class 1 is fall.",
        "",
        f"Classified candidate artifacts: {len(artifacts)}.",
        "",
    ]
    cols = [
        "path",
        "file_type",
        "likely_method_internal_name",
        "thesis_facing_name",
        "split",
        "seed",
        "attack",
        "epsilon",
        "contains_hard_predictions",
        "contains_fall_scores_probabilities_logits",
        "contains_TP_FN_FP_TN",
        "AUROC_can_be_computed",
        "threshold_swept_recall_at_FAR_cap_can_be_computed",
        "notes",
    ]
    for _, group_name in APPROACHES:
        group_rows = by_group.get(group_name, [])
        lines += [f"## {group_name}", ""]
        if group_rows:
            lines.append(md_table(group_rows, cols))
        else:
            lines.append("_No classified artifact found._")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary(path: Path, rows: list[dict[str, Any]], artifacts: list[dict[str, Any]]) -> None:
    summary = summarize(rows, artifacts)
    fixed_best = best_test_pgd(rows, swept=False)[:12]
    swept_best = best_test_pgd(rows, swept=True)[:12]
    lines = [
        "# Defense Attempt Results Summary",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        f"Artifact inventory rows: {summary['artifact_count']}. Result rows: {summary['result_count']}.",
        "",
        "## Availability by approach",
        "",
        "- Exact TP/FN/FP/TN available: " + (", ".join(summary["exact"]) if summary["exact"] else "none"),
        "- AUROC only: " + (", ".join(summary["auroc_only"]) if summary["auroc_only"] else "none"),
        "- Validation-only usable rows: " + (", ".join(summary["val_only"]) if summary["val_only"] else "none"),
        "- Saved scores allow threshold sweeps: " + (", ".join(summary["score_groups"]) if summary["score_groups"] else "none"),
        "- No usable standalone result artifact: " + (", ".join(summary["no_usable"]) if summary["no_usable"] else "none"),
        "",
        "## Best fixed PGD test rows",
        "",
        md_table(
            fixed_best,
            ["method_thesis_name", "approach_group", "seed", "Rfall", "FAR", "TP", "FN", "FP", "TN", "source_file"],
            max_rows=12,
        )
        if fixed_best
        else "_No fixed PGD test rows._",
        "",
        "## Best post-hoc PGD test rows at FAR <= 0.20",
        "",
        md_table(
            swept_best,
            [
                "method_thesis_name",
                "approach_group",
                "seed",
                "Rfall_at_FAR_020",
                "TP_at_FAR_020",
                "FP_at_FAR_020",
                "AUROC",
                "threshold",
                "F20_reached",
                "source_file",
            ],
            max_rows=12,
        )
        if swept_best
        else "_No post-hoc PGD test rows._",
        "",
        "## Interpretation",
        "",
        "- Fixed-threshold/argmax test evidence still favors the validated G1 and Variant F operating points for lower false-alarm burden at nonzero PGD recall.",
        "- Post-hoc score thresholding changes the operating point: AFAC-score reaches the F20 criterion on test at FAR <= 0.20 from saved PGD scores.",
        "- SAT/BASAT and GAIRAT have strong validation-score operating points, but the classified artifacts here do not provide matching test-score rows for those pilots.",
        "- TRADES-style consistency has no classified local result artifact in this inventory.",
        "- Existing CSVs are enough for many thesis rows, but not enough to fill a complete all-approach table without marking TRADES as not found and SAT/GAIRAT/BiLSTM pilots as validation-only.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def latex_escape(text: Any) -> str:
    s = clean_num(text)
    for old, new in [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]:
        s = s.replace(old, new)
    return s


def write_latex(path: Path, rows: list[dict[str, Any]]) -> None:
    fixed_best = best_test_pgd(rows, swept=False)[:10]
    swept_best = best_test_pgd(rows, swept=True)[:10]
    lines = [
        "% Auto-generated by scripts/analysis/build_defense_attempt_inventory.py",
        "% Analysis-only inventory from existing artifacts.",
        "\\begin{tabular}{llllrrrr}",
        "\\toprule",
        "Mode & Method & Group & Seed & $R_{fall}$ & FAR & TP & FP \\\\",
        "\\midrule",
    ]
    for row in fixed_best:
        lines.append(
            "Fixed & "
            + " & ".join(
                [
                    latex_escape(row.get("method_thesis_name")),
                    latex_escape(row.get("approach_group")),
                    latex_escape(row.get("seed")),
                    latex_escape(row.get("Rfall")),
                    latex_escape(row.get("FAR")),
                    latex_escape(row.get("TP")),
                    latex_escape(row.get("FP")),
                ]
            )
            + r" \\"
        )
    for row in swept_best:
        lines.append(
            "Swept & "
            + " & ".join(
                [
                    latex_escape(row.get("method_thesis_name")),
                    latex_escape(row.get("approach_group")),
                    latex_escape(row.get("seed")),
                    latex_escape(row.get("Rfall_at_FAR_020")),
                    "$\\leq 0.20$",
                    latex_escape(row.get("TP_at_FAR_020")),
                    latex_escape(row.get("FP_at_FAR_020")),
                ]
            )
            + r" \\"
        )
    lines += [
        "\\bottomrule",
        "\\end{tabular}",
        "",
        "% Note: Swept rows are post-hoc fall-score thresholds from saved scores, not fixed argmax checkpoints.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_missing(path: Path, rows: list[dict[str, Any]], artifacts: list[dict[str, Any]]) -> None:
    summary = summarize(rows, artifacts)
    groups = summary["groups"]
    lines = [
        "# Missing Metrics TODO",
        "",
        "This file lists missing or non-derivable rows from existing local artifacts. It is not a request to train or attack.",
        "",
    ]
    for _, group_name in APPROACHES:
        grows = groups.get(group_name, [])
        usable = [r for r in grows if r.get("TP") != "" or r.get("AUROC") != ""]
        has_test = any(r.get("split") == "test" and r.get("TP") != "" for r in grows)
        has_val = any(r.get("split") == "val" and r.get("TP") != "" for r in grows)
        art_count = sum(1 for art in artifacts if art["approach_group"] == group_name)
        lines.append(f"## {group_name}")
        if not usable:
            if art_count:
                lines.append("- only qualitative, metadata, smoke, or non-standalone artifacts found")
                lines.append("- cannot compute TP/FN/FP/TN because matching per-window predictions or score exports are missing")
            else:
                lines.append("- not found")
        elif has_val and not has_test:
            lines.append("- validation only")
            lines.append("- test split not touched by classified usable metric artifacts")
        elif not has_test:
            lines.append("- test split not touched")
        else:
            lines.append("- usable test metrics found")
        if group_name == "TRADES-style fall-probability consistency":
            lines.append("- TRADES-named result artifacts were not found in the local classified inventory")
        if group_name == "Static dual-tail rescue/budget objective" and not has_test:
            lines.append("- smoke metadata exists, but no converged standalone validation/test result was found")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = candidate_files()
    artifacts = [inspect_artifact(path) for path in files]
    result_rows: list[dict[str, Any]] = []
    for path in files:
        if path.suffix.lower() != ".csv":
            continue
        columns, rows = read_csv_rows(path, limit=None)
        if not columns or not rows:
            continue
        result_rows.extend(direct_metric_rows(path, columns, rows))
        result_rows.extend(per_window_rows(path, columns, rows))
    result_rows = dedupe_result_rows(result_rows)
    result_rows = add_missing_rows(result_rows, artifacts)

    write_artifact_inventory(OUT / "defense_attempt_artifact_inventory.md", artifacts)
    write_csv(OUT / "defense_attempt_results_long.csv", result_rows, CSV_COLUMNS)
    write_summary(OUT / "defense_attempt_results_summary.md", result_rows, artifacts)
    write_latex(OUT / "defense_attempt_results_summary.tex", result_rows)
    write_missing(OUT / "missing_metrics_todo.md", result_rows, artifacts)

    print(f"Wrote {OUT}")
    print(f"Artifacts: {len(artifacts)}")
    print(f"Result rows: {len(result_rows)}")


if __name__ == "__main__":
    main()
