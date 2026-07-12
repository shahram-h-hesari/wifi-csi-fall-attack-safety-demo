"""Task 3 — validation-only PGD eps=0.015 false-positive audit and operating-point
feasibility library.

Pure functions only (no file I/O of production paths here; the driver script
`eps015_validation_feasibility_audit.py` supplies real paths). This separation lets
`test_eps015_feasibility_lib.py` exercise every safety and correctness rule against
synthetic fixtures only, never against real validation or test artifacts.

Split-safety discipline (per the project's own documented standard split, see
`results/d10_d11_locked_test_followup/PROVENANCE.md`): train 3977 / val 496 (44 fall,
452 non-fall) / held-out test 500 (45 fall, 455 non-fall). An artifact is accepted as
validation only if its filename encodes "_val_" (never "_test_" or "TESTREAD"), AND its
row count is exactly 496, AND its fall-positive count is exactly 44. Any artifact that
fails any one of these checks is rejected, never guessed into place.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

VAL_TOTAL = 496
VAL_FALL = 44
VAL_NONFALL = 452
TEST_TOTAL = 500
TEST_FALL = 45
TEST_NONFALL = 455

TARGET_RECALL = 0.90   # strict: Rfall > 0.90
TARGET_FAR = 0.10      # strict: FAR < 0.10

_TEST_MARKERS = ("_test_", "testread", "_test.", "test_epsilon")
_VAL_MARKERS = ("_val_", "val_epsilon")


class SplitRejection(ValueError):
    """Raised when an artifact cannot be proven to be the validation split."""


@dataclass(frozen=True)
class SplitCheckResult:
    accepted: bool
    reason: str
    row_count: Optional[int] = None
    fall_count: Optional[int] = None


def check_split_is_validation(filename: str, row_count: int, fall_count: int) -> SplitCheckResult:
    """Deterministically decide whether an artifact may be treated as validation evidence.

    Rejects: filenames naming the test split; row/fall counts matching the test split's
    shape (500/45) instead of validation's (496/44); row/fall counts matching neither
    shape (ambiguous -- never guessed as validation).
    """
    lower = filename.lower()
    if any(marker in lower for marker in _TEST_MARKERS):
        return SplitCheckResult(False, f"filename '{filename}' names the test split", row_count, fall_count)
    if not any(marker in lower for marker in _VAL_MARKERS):
        return SplitCheckResult(False, f"filename '{filename}' does not explicitly name the validation split", row_count, fall_count)
    if row_count == TEST_TOTAL and fall_count == TEST_FALL:
        return SplitCheckResult(False, "row/fall counts match the held-out test split shape (500/45), not validation (496/44)", row_count, fall_count)
    if row_count != VAL_TOTAL or fall_count != VAL_FALL:
        return SplitCheckResult(
            False,
            f"row/fall counts ({row_count}/{fall_count}) match neither the documented "
            f"validation shape ({VAL_TOTAL}/{VAL_FALL}) nor test shape ({TEST_TOTAL}/{TEST_FALL}) "
            f"-- ambiguous, rejected rather than guessed",
            row_count, fall_count,
        )
    return SplitCheckResult(True, "matches documented validation split shape (496 windows, 44 fall)", row_count, fall_count)


@dataclass(frozen=True)
class Confusion:
    TP: int
    FN: int
    FP: int
    TN: int

    def __post_init__(self):
        if min(self.TP, self.FN, self.FP, self.TN) < 0:
            raise ValueError("confusion counts must be non-negative")

    @property
    def n_fall(self) -> int:
        return self.TP + self.FN

    @property
    def n_nonfall(self) -> int:
        return self.FP + self.TN

    @property
    def recall(self) -> float:
        return self.TP / self.n_fall if self.n_fall else float("nan")

    @property
    def far(self) -> float:
        return self.FP / self.n_nonfall if self.n_nonfall else float("nan")

    @property
    def specificity(self) -> float:
        return self.TN / self.n_nonfall if self.n_nonfall else float("nan")

    @property
    def precision(self) -> float:
        denom = self.TP + self.FP
        return self.TP / denom if denom else float("nan")

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        if p != p or r != r or (p + r) == 0:  # NaN-safe
            return float("nan")
        return 2 * p * r / (p + r)

    @property
    def balanced_accuracy(self) -> float:
        return (self.recall + self.specificity) / 2

    def meets_target(self, target_recall: float = TARGET_RECALL, target_far: float = TARGET_FAR) -> bool:
        return self.recall > target_recall and self.far < target_far


def confusion_at_threshold(scores, labels, threshold: float) -> Confusion:
    """Decision rule: fall alarm iff score >= threshold (matches the project's frozen
    decision-rule convention). `labels` are 1 for fall, 0 for non-fall."""
    if len(scores) != len(labels):
        raise ValueError("scores and labels must be the same length")
    TP = FN = FP = TN = 0
    for s, y in zip(scores, labels):
        pred = 1 if s >= threshold else 0
        if y == 1 and pred == 1:
            TP += 1
        elif y == 1 and pred == 0:
            FN += 1
        elif y == 0 and pred == 1:
            FP += 1
        else:
            TN += 1
    return Confusion(TP=TP, FN=FN, FP=FP, TN=TN)


def candidate_thresholds(scores) -> list:
    """Deterministic candidate threshold set: every distinct score value, sorted
    ascending, plus one value above the maximum (so the all-non-fall point is reachable).
    Sweeping exactly these thresholds is sufficient to enumerate every distinct
    confusion matrix achievable by the `score >= tau` decision rule."""
    uniq = sorted(set(scores))
    if not uniq:
        return []
    return uniq + [uniq[-1] + 1e-9]


@dataclass(frozen=True)
class SweepRow:
    threshold: float
    confusion: Confusion


def sweep_thresholds(scores, labels) -> list:
    """Deterministic full sweep (see `candidate_thresholds`). Same inputs -> identical
    output every time (no randomness, no unordered set iteration in the output order)."""
    rows = []
    for t in candidate_thresholds(scores):
        rows.append(SweepRow(threshold=t, confusion=confusion_at_threshold(scores, labels, t)))
    return rows


@dataclass(frozen=True)
class FeasibilitySummary:
    feasible_rows: list  # list[SweepRow] meeting both strict targets
    best_feasible: Optional[SweepRow]  # tie-break: max recall, then min FAR, then max tau
    highest_recall_under_far_target: Optional[SweepRow]  # best recall among FAR < target rows
    lowest_far_at_recall_target: Optional[SweepRow]  # best (lowest) FAR among recall > target rows
    nearest_to_target: SweepRow  # minimizes shortfall distance to the (recall>0.90, FAR<0.10) region


def _shortfall_distance(row: SweepRow) -> float:
    c = row.confusion
    recall_shortfall = max(0.0, TARGET_RECALL - c.recall) if c.recall == c.recall else 1.0
    far_shortfall = max(0.0, c.far - TARGET_FAR) if c.far == c.far else 1.0
    return recall_shortfall + far_shortfall


def summarize_feasibility(rows: list) -> FeasibilitySummary:
    feasible = [r for r in rows if r.confusion.meets_target()]

    def _feasible_key(r: SweepRow):
        c = r.confusion
        return (-c.recall, c.far, -r.threshold)

    best_feasible = min(feasible, key=_feasible_key) if feasible else None

    under_far = [r for r in rows if r.confusion.far == r.confusion.far and r.confusion.far < TARGET_FAR]
    highest_recall_under_far = max(under_far, key=lambda r: (r.confusion.recall, -r.confusion.far)) if under_far else None

    above_recall = [r for r in rows if r.confusion.recall == r.confusion.recall and r.confusion.recall > TARGET_RECALL]
    lowest_far_at_recall = min(above_recall, key=lambda r: (r.confusion.far, -r.confusion.recall)) if above_recall else None

    nearest = min(rows, key=lambda r: (_shortfall_distance(r), -r.confusion.recall, r.confusion.far)) if rows else None

    return FeasibilitySummary(
        feasible_rows=feasible,
        best_feasible=best_feasible,
        highest_recall_under_far_target=highest_recall_under_far,
        lowest_far_at_recall_target=lowest_far_at_recall,
        nearest_to_target=nearest,
    )


def false_positive_source_breakdown(rows: list) -> dict:
    """rows: iterable of (true_class_name, true_fall_binary, predicted_fall_binary).
    Returns {class_name: count} for rows that are actual non-fall but predicted fall
    (false positives) at whatever threshold the caller already applied to produce
    `predicted_fall_binary`. Aggregate counts only -- no per-example identifiers."""
    counts: dict = {}
    for true_class, true_fall, pred_fall in rows:
        if true_fall == 0 and pred_fall == 1:
            counts[true_class] = counts.get(true_class, 0) + 1
    return counts


def score_margin_buckets(scores, labels, threshold: float, near_band: float = 0.05) -> dict:
    """For predicted false positives at `threshold`, bucket by |score - threshold|:
    'near' (<= near_band) vs 'far' (> near_band). Aggregate counts only."""
    near = far = 0
    for s, y in zip(scores, labels):
        if y == 0 and s >= threshold:
            if abs(s - threshold) <= near_band:
                near += 1
            else:
                far += 1
    return {"near_threshold": near, "far_from_threshold": far}


@dataclass(frozen=True)
class OverlapSummary:
    shared_tp: int
    shared_fp: int
    unique_fp_a: int
    unique_fp_b: int
    unique_recovered_fall_a: int
    unique_recovered_fall_b: int
    disagreement_count: int


def compare_axis_predictions(joined_rows: list) -> OverlapSummary:
    """joined_rows: iterable of (true_fall_binary, pred_a, pred_b) for the SAME
    sample_id set (already joined by the caller). Aggregate overlap counts only."""
    shared_tp = shared_fp = unique_fp_a = unique_fp_b = 0
    unique_recovered_fall_a = unique_recovered_fall_b = 0
    disagreement = 0
    for y, pa, pb in joined_rows:
        if pa != pb:
            disagreement += 1
        if y == 1:
            if pa == 1 and pb == 1:
                shared_tp += 1
            elif pa == 1 and pb == 0:
                unique_recovered_fall_a += 1
            elif pa == 0 and pb == 1:
                unique_recovered_fall_b += 1
        else:
            if pa == 1 and pb == 1:
                shared_fp += 1
            elif pa == 1 and pb == 0:
                unique_fp_a += 1
            elif pa == 0 and pb == 1:
                unique_fp_b += 1
    return OverlapSummary(
        shared_tp=shared_tp, shared_fp=shared_fp,
        unique_fp_a=unique_fp_a, unique_fp_b=unique_fp_b,
        unique_recovered_fall_a=unique_recovered_fall_a, unique_recovered_fall_b=unique_recovered_fall_b,
        disagreement_count=disagreement,
    )
