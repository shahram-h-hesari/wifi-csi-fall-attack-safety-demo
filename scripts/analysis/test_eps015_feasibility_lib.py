"""Task 3 safety/correctness tests for eps015_feasibility_lib. Synthetic fixtures only --
no real validation or test artifact is read here."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eps015_feasibility_lib as lib  # noqa: E402


# --------------------------------------------------------------------- split safety

def test_validation_shaped_artifact_is_accepted():
    result = lib.check_split_is_validation("AFAC_maxscore_eps0015_pgd_probabilities_val_epsilon_0_015.csv", 496, 44)
    assert result.accepted is True


def test_test_named_filename_is_rejected_even_with_val_shaped_counts():
    result = lib.check_split_is_validation("AFAC_maxscore_eps0015_TESTREAD_pgd_probabilities_test_epsilon_0_015.csv", 496, 44)
    assert result.accepted is False
    assert "test split" in result.reason


def test_test_shaped_counts_rejected_even_with_val_style_filename():
    # adversarial fixture: filename says "val" but the shape matches test (500/45)
    result = lib.check_split_is_validation("suspicious_val_epsilon_0_015.csv", 500, 45)
    assert result.accepted is False
    assert "500/45" in result.reason


def test_ambiguous_shape_is_rejected_not_guessed():
    result = lib.check_split_is_validation("some_val_epsilon_0_015.csv", 123, 7)
    assert result.accepted is False
    assert "ambiguous" in result.reason


def test_filename_without_val_or_test_marker_is_rejected():
    result = lib.check_split_is_validation("mystery_epsilon_0_015.csv", 496, 44)
    assert result.accepted is False


# --------------------------------------------------------------------- confusion / metrics

def test_confusion_metrics_are_correct():
    c = lib.Confusion(TP=41, FN=4, FP=60, TN=395)
    assert c.n_fall == 45
    assert c.n_nonfall == 455
    assert abs(c.recall - 41 / 45) < 1e-9
    assert abs(c.far - 60 / 455) < 1e-9


def test_confusion_rejects_negative_counts():
    import pytest
    with pytest.raises(ValueError):
        lib.Confusion(TP=-1, FN=4, FP=60, TN=395)


def test_meets_target_uses_strict_inequalities():
    # exactly at the boundary must NOT count as meeting the (strict) target
    at_boundary = lib.Confusion(TP=90, FN=10, FP=100, TN=900)  # recall=0.90 exactly, FAR=0.10 exactly
    assert at_boundary.recall == 0.90
    assert at_boundary.far == 0.10
    assert at_boundary.meets_target() is False
    just_over = lib.Confusion(TP=91, FN=9, FP=99, TN=901)  # recall=0.91>0.90, FAR=0.099<0.10
    assert just_over.meets_target() is True


# --------------------------------------------------------------------- sweep determinism

def test_sweep_thresholds_is_deterministic():
    scores = [0.1, 0.9, 0.5, 0.5, 0.3, 0.7]
    labels = [0, 1, 1, 0, 0, 1]
    rows1 = lib.sweep_thresholds(scores, labels)
    rows2 = lib.sweep_thresholds(scores, labels)
    assert [(r.threshold, r.confusion) for r in rows1] == [(r.threshold, r.confusion) for r in rows2]


def test_sweep_covers_all_and_none_predicted_extremes():
    scores = [0.2, 0.4, 0.6]
    labels = [0, 1, 1]
    rows = lib.sweep_thresholds(scores, labels)
    # lowest threshold -> everything predicted fall
    assert rows[0].confusion.TP + rows[0].confusion.FP == 3
    # threshold above max -> nothing predicted fall
    assert rows[-1].confusion.TP == 0 and rows[-1].confusion.FP == 0


# --------------------------------------------------------------------- feasibility summary

def test_summarize_feasibility_finds_a_feasible_point_when_one_exists():
    # 44 fall / 452 non-fall synthetic axis with a clean separable region
    scores = [0.9] * 42 + [0.4] * 2 + [0.1] * 442 + [0.6] * 10
    labels = [1] * 44 + [0] * 452
    rows = lib.sweep_thresholds(scores, labels)
    summary = lib.summarize_feasibility(rows)
    assert len(summary.feasible_rows) > 0
    assert summary.best_feasible is not None
    assert summary.best_feasible.confusion.meets_target()


def test_summarize_feasibility_reports_nearest_when_infeasible():
    # heavily overlapping distributions: no threshold can hit both targets
    scores = [0.5] * 44 + [0.5] * 452
    labels = [1] * 44 + [0] * 452
    rows = lib.sweep_thresholds(scores, labels)
    summary = lib.summarize_feasibility(rows)
    assert summary.feasible_rows == []
    assert summary.best_feasible is None
    assert summary.nearest_to_target is not None


def test_highest_recall_under_far_and_lowest_far_at_recall_are_reported_independently():
    scores = [0.9] * 40 + [0.5] * 4 + [0.05] * 452
    labels = [1] * 44 + [0] * 452
    rows = lib.sweep_thresholds(scores, labels)
    summary = lib.summarize_feasibility(rows)
    assert summary.highest_recall_under_far_target is not None
    assert summary.highest_recall_under_far_target.confusion.far < 0.10


# --------------------------------------------------------------------- source-class aggregation

def test_false_positive_source_breakdown_counts_only_actual_non_fall_predicted_fall():
    rows = [
        ("walk", 0, 1),
        ("walk", 0, 1),
        ("run", 0, 1),
        ("walk", 0, 0),   # correctly rejected, not a FP
        ("lie down", 1, 1),  # true positive, not a FP
    ]
    counts = lib.false_positive_source_breakdown(rows)
    assert counts == {"walk": 2, "run": 1}


def test_false_positive_breakdown_never_returns_per_example_identifiers():
    rows = [("walk", 0, 1)] * 5
    counts = lib.false_positive_source_breakdown(rows)
    # aggregate dict keyed by class name only -- no sample_id-shaped keys
    assert set(counts.keys()) == {"walk"}
    assert all(isinstance(v, int) for v in counts.values())


# --------------------------------------------------------------------- score-margin buckets

def test_score_margin_buckets_split_near_and_far_false_positives():
    scores = [0.52, 0.9, 0.3]
    labels = [0, 0, 1]
    result = lib.score_margin_buckets(scores, labels, threshold=0.5, near_band=0.05)
    assert result["near_threshold"] == 1  # 0.52 is within 0.05 of 0.5
    assert result["far_from_threshold"] == 1  # 0.9 is far from 0.5


# --------------------------------------------------------------------- axis overlap

def test_compare_axis_predictions_counts_shared_and_unique_correctly():
    joined = [
        (1, 1, 1),  # shared TP
        (1, 1, 0),  # axis a recovers a fall axis b misses
        (1, 0, 1),  # axis b recovers a fall axis a misses
        (0, 1, 1),  # shared FP
        (0, 1, 0),  # unique FP to axis a
        (0, 0, 1),  # unique FP to axis b
        (0, 0, 0),  # both correct, no disagreement
    ]
    overlap = lib.compare_axis_predictions(joined)
    assert overlap.shared_tp == 1
    assert overlap.unique_recovered_fall_a == 1
    assert overlap.unique_recovered_fall_b == 1
    assert overlap.shared_fp == 1
    assert overlap.unique_fp_a == 1
    assert overlap.unique_fp_b == 1
    assert overlap.disagreement_count == 4


def test_no_forbidden_imports_or_execution_in_library():
    src = Path(__file__).resolve().parent.joinpath("eps015_feasibility_lib.py").read_text(encoding="utf-8")
    for forbidden in ("subprocess", "torch", "checkpoint", "os.system", "eval(", "exec("):
        assert forbidden not in src, forbidden
