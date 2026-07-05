"""
D14 shared constants and helpers (partial-AUC / low-FAR ranking-loss fine-tuning).

This module centralizes every pre-registered D14 value so the training script, the
validation-gate script, and the locked-test stub all read the SAME frozen numbers from
one place. It performs NO training, NO evaluation, and reads NO data at import time.

Pre-registration (thesis repo):
  provenance/appendices/internal_defense_experiment_ledger/decision_memos/
    20260704_d14_partial_auc_low_far_preregistration.md
  commit 7ee228369052461682741a372a1ac2c3209fecb1
Preflight (this repo):
  results/d14_partial_auc_low_far_ranking/D14_PREFLIGHT_CHECK.md
  commit 67efeda578db53ae4eab0ca82dccb0d5c9373f23

Score convention (locked by preflight and by every existing AFAC/D10/D11/D13 script):
  s(x) = softmax(model(x), dim=1)[:, FALL_CLASS_INDEX], FALL_CLASS_INDEX = 1.
  Higher s(x) = more fall-like. Validation thresholds are selected from this same score.
"""

from __future__ import annotations

from pathlib import Path
import math
import sys

# ---------------------------------------------------------------------------
# Provenance anchors (recorded into every D14 metadata file).
# ---------------------------------------------------------------------------
# Thesis-repo D14 memo commits: original pre-registration and the subsequent clarification
# (full-batch PGD-only training; paired-bootstrap primary Gate-3, fixed 36/44 as sensitivity only).
D14_PREREG_COMMIT = "7ee228369052461682741a372a1ac2c3209fecb1"
D14_CLARIFICATION_COMMIT = "06c93abb635b3bcaf2e5591f214bd57d00faf831"
# Backward-compatible alias (earlier scripts referenced THESIS_PREREG_COMMIT).
THESIS_PREREG_COMMIT = D14_PREREG_COMMIT
PREFLIGHT_COMMIT = "67efeda578db53ae4eab0ca82dccb0d5c9373f23"

REPO = Path(__file__).resolve().parents[2]
BENCH_DIR = REPO / "third_party" / "WiFi-CSI-Sensing-Benchmark"
D14_RESULTS_ROOT = REPO / "results" / "d14_partial_auc_low_far_ranking"

# ---------------------------------------------------------------------------
# Locked design (pre-registered; do not edit without a written memo amendment).
# ---------------------------------------------------------------------------
ALLOWED_SEEDS = (42, 43, 44)

CONFIGS = {
    "A": {"lambda_ce": 1.00, "lambda_rank": 0.50},
    "B": {"lambda_ce": 1.00, "lambda_rank": 1.00},
}

FALL_CLASS_INDEX = 1
NUM_CLASSES = 7

# PGD (training AND evaluation): the full evaluation convention, per the preflight
# recommendation to keep D14's training-time attack identical to what it is judged on.
PGD_EPSILON = 0.030
PGD_STEPS = 10
PGD_ALPHA = PGD_EPSILON / 6.0          # == 0.005
PGD_RANDOM_START = False               # no random start
# L-infinity projection each step; NO [0,1] value clamp (processed CSI tensors);
# untargeted cross-entropy loss on the true label.

# Ranking loss.
RANK_MARGIN = 0.10                     # m
RANK_TAIL_FRACTION = 0.20             # top-k non-fall tail = ceil(0.20 * N_nonfall_batch)

# Threshold selection.
PRIMARY_FAR_CAP = 0.17                 # primary (buffered) validation FAR cap
SECONDARY_FAR_CAP = 0.20              # secondary comparison only

# Clean-collapse guard (validation).
CLEAN_GUARD = {
    "min_clean_accuracy": 0.70,
    "min_clean_macro_f1": 0.65,
    "min_clean_fall_recall": 0.90,
}

# Validation gate numeric bars.
VAL_FALL_WINDOWS = 44                  # falls in the 496-window validation split
VAL_NONFALL_WINDOWS = 452
GATE_MIN_MEDIAN_RECALL_TP = 38         # >= 38/44 = 0.8636 at cap 0.17
GATE_MIN_MEDIAN_RECALL = GATE_MIN_MEDIAN_RECALL_TP / VAL_FALL_WINDOWS
BOOTSTRAP_N = 2000                     # >= 2000 (pre-registered minimum)
BOOTSTRAP_SEED = 1337
GATE_RECALL_FLOOR = 0.80               # bootstrap recall >= 0.80 ...
GATE_RECALL_FLOOR_FRACTION = 0.75      # ... in >= 75% of resamples
GATE_GAIN_TP = 2                       # gain >= +2 TP over AFAC reference ...
GATE_GAIN_FRACTION = 0.70              # ... in >= 70% of resamples

# AFAC validation reference (36/44 at the pre-registered cap-0.20 operating point).
AFAC_REF_TP = 36
AFAC_REF_FALL_WINDOWS = 44

# ---------------------------------------------------------------------------
# Checkpoints (from the committed D14 preflight report).
# ---------------------------------------------------------------------------
AFAC_SCORE_CHECKPOINT = (
    REPO / "checkpoints" / "safety_guided_defense" / "variantH_dual_tail_budget"
    / "adaptive_lagrangian_far_constrained" / "optionB" / "seed42"
    / "seed42_optionB_maxscore_best.pt"
)
D10_FALLBACK_CHECKPOINT = (
    REPO / "checkpoints" / "safety_guided_defense" / "boundary_aware_selective_at"
    / "gairat" / "seed42" / "GR1" / "seed42_basat_gairat_GR1_v2macroF1_best.pt"
)

# Existing AFAC-score VALIDATION PGD scores (used only by the gate script's paired
# bootstrap reference; a pre-existing artifact, not a new evaluation).
AFAC_VAL_PGD_SCORES = (
    REPO / "results" / "afac_score_frozen_threshold_followup" / "val_eval"
    / "optionB_maxscore_pgd_probabilities_val_epsilon_0_03.csv"
)

# ---------------------------------------------------------------------------
# Training-loop settings. ADV_FRACTION is now LOCKED by the D14 clarification commit
# (D14_CLARIFICATION_COMMIT): D14 uses full-batch PGD adversarial fine-tuning, no 50/50
# clean/PGD mixture. The schedule knobs below remain identical across BOTH configs and ALL
# seeds so only lambda_rank ever differs.
# See results/d14_partial_auc_low_far_ranking/D14_IMPLEMENTATION_NOTES.md.
# ---------------------------------------------------------------------------
ADV_FRACTION = 1.0                     # LOCKED: full-batch PGD-AT (whole minibatch attacked);
                                       # no 50/50 clean/PGD mixture (clarification commit)
DEFAULT_EPOCHS = 40                    # fine-tune schedule (short; from a strong ckpt)
DEFAULT_LR = 3e-4                      # Adam LR for fine-tuning
DEFAULT_BATCH_SIZE = 64


def validate_seed(seed: int) -> int:
    if int(seed) not in ALLOWED_SEEDS:
        raise SystemExit(
            f"REFUSED: seed {seed} is not a pre-registered D14 seed {ALLOWED_SEEDS}. "
            "No seed 45/46 extension is authorized without a written memo amendment."
        )
    return int(seed)


def validate_config(config: str) -> str:
    if config not in CONFIGS:
        raise SystemExit(
            f"REFUSED: config '{config}' is not a pre-registered D14 config "
            f"{sorted(CONFIGS)}. Configs differ only in lambda_rank."
        )
    return config


def refuse_if_test_path(path) -> None:
    """Hard stop if a path looks test-related. D14 phase-1 scripts never touch test."""
    p = str(path).lower().replace("\\", "/")
    for token in ("test_eval", "/test", "_test_", "y_test", "x_test"):
        if token in p:
            raise SystemExit(f"REFUSED: path looks test-related, blocked in this script: {path}")


def import_pipeline():
    """Import the shared Stage-1 pipeline, the attack module, and the model factory.

    Adds the SenseFi clone to sys.path and patches its loader, exactly as every other
    training/eval script in this repo does. Does NOT load data by itself.
    """
    scripts_dir = REPO / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import train_converged_clean_baseline as s1
    s1.patch_sensefi_dataset_loader(BENCH_DIR)
    if str(BENCH_DIR) not in sys.path:
        sys.path.insert(0, str(BENCH_DIR))
    import run_converged_attacks as rca
    from model_factory import build_model
    return s1, rca, build_model


# ---------------------------------------------------------------------------
# Score / threshold helpers (pure; no I/O). Shared by training + gate scripts so
# the exact same midpoint-grid rule and tie-break are used everywhere.
# ---------------------------------------------------------------------------
def threshold_grid(nonfall_scores):
    """Midpoints between sorted unique non-fall scores, plus two outer sentinels."""
    uniq = sorted(set(float(v) for v in nonfall_scores))
    if not uniq:
        return [0.0]
    mids = [(uniq[i] + uniq[i + 1]) / 2.0 for i in range(len(uniq) - 1)]
    return [uniq[0] - 1e-9] + mids + [uniq[-1] + 1e-9]


def confusion_at(y, s, tau):
    tp = fn = fp = tn = 0
    for yi, si in zip(y, s):
        pred = si >= tau
        if yi == 1:
            tp += pred
            fn += not pred
        else:
            fp += pred
            tn += not pred
    return tp, fn, fp, tn


def rates(tp, fn, fp, tn):
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    far = fp / (fp + tn) if (fp + tn) else float("nan")
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return recall, far, precision, f1


def select_threshold(y, s, far_cap):
    """Max validation recall s.t. FAR <= far_cap on the MIDPOINT grid built from
    non-fall scores. Tie-break: lower FAR, then higher threshold. Returns None if
    no threshold satisfies the cap."""
    nonfall_scores = [si for yi, si in zip(y, s) if yi == 0]
    grid = threshold_grid(nonfall_scores)
    best = None
    for tau in grid:
        tp, fn, fp, tn = confusion_at(y, s, tau)
        recall, far, _, _ = rates(tp, fn, fp, tn)
        if far > far_cap:
            continue
        key = (recall, -far, tau)
        if best is None or key > best[0]:
            best = (key, tau, tp, fn, fp, tn, recall, far)
    if best is None:
        return None
    _, tau, tp, fn, fp, tn, recall, far = best
    return {"threshold": tau, "TP": tp, "FN": fn, "FP": fp, "TN": tn,
            "recall": recall, "FAR": far}


def auroc(y, s):
    pairs = sorted(zip(s, y))
    n = len(pairs)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    n_pos = sum(yy for _, yy in pairs)
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    rank_sum_pos = sum(r for r, (_, yy) in zip(ranks, pairs) if yy == 1)
    u = rank_sum_pos - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * n_neg)


def tail_k(n_nonfall_batch: int) -> int:
    """k = max(1, ceil(0.20 * N_nonfall_batch)) -- the high-risk non-fall tail size."""
    return max(1, math.ceil(RANK_TAIL_FRACTION * n_nonfall_batch))
