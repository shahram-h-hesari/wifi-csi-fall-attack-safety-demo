# D13 Step 0A/0B — Validation-Only Complementarity + Transfer Audit

Date: 2026-07-04. Diagnostic only. **Cannot claim F20.** Can only authorize, reject, or mark
inconclusive a later, separately pre-registered Stage 1 score-fusion experiment. PGD epsilon =
0.030 throughout. All analysis is validation-only (496 windows: 44 fall, 452 non-fall).

## Input files used

| Model | Source file |
|---|---|
| AFAC-score (`optionB_maxscore`, D8b reference) | `results/afac_score_frozen_threshold_followup/val_eval/optionB_maxscore_pgd_probabilities_val_epsilon_0_03.csv` |
| D10 (GAIRAT `GR1_v2macroF1`) | `results/safety_guided_defense/boundary_aware_selective_at/gairat/seed42/GR1/val_eval/GR1_v2macroF1_pgd_probabilities_val_epsilon_0_03.csv` |
| D11b (SAT `SA1_v2lowFA`) | `results/safety_guided_defense/boundary_aware_selective_at/sat/seed42/SA1/val_eval/SA1_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv` |

Step 0B additionally used the three checkpoints directly (paths in `PROVENANCE.md`) to regenerate
validation-only PGD adversarial examples for the shared-input transfer test.

**Confirmation: no test-split file was opened, read, summarized, or referenced anywhere in this
audit.** Both scripts were grep-checked for test-file references before execution (see
`COMMANDS_RUN.txt`); the only match was a docstring sentence describing the absence of such
references, not an actual usage.

## Step 0A — per-model metrics at FAR caps 0.18 and 0.20

| Model | FAR cap | Threshold | TP | FN | FP | TN | Recall | FAR | Precision | F1 | AUROC | pAUC (McClish, FAR∈[0,0.20]) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AFAC | 0.18 | 0.168743 | 34 | 10 | 71 | 381 | 0.7727 | 0.1571 | 0.3238 | 0.4564 | 0.8719 | 0.7138 |
| AFAC | 0.20 | 0.147489 | 36 | 8 | 88 | 364 | 0.8182 | 0.1947 | 0.2903 | 0.4286 | 0.8719 | 0.7138 |
| D10 | 0.18 | 0.087853 | 32 | 12 | 81 | 371 | 0.7273 | 0.1792 | 0.2832 | 0.4076 | 0.8712 | 0.6742 |
| D10 | 0.20 | 0.074365 | 39 | 5 | 86 | 366 | 0.8864 | 0.1903 | 0.3120 | 0.4615 | 0.8712 | 0.6742 |
| D11b | 0.18 | 0.055186 | 36 | 8 | 80 | 372 | 0.8182 | 0.1770 | 0.3103 | 0.4500 | 0.8728 | 0.7020 |
| D11b | 0.20 | 0.048241 | 39 | 5 | 85 | 367 | 0.8864 | 0.1881 | 0.3145 | 0.4643 | 0.8728 | 0.7020 |

Threshold grid: midpoints between consecutive sorted unique validation scores. This is a
diagnostic-only selection rule; it is not the already-frozen, thesis-committed AFAC-score Stage-1
threshold (see `PROVENANCE.md` for the exact distinction).

**Best single model at FAR<=0.18 (primary gating cap): D11b, recall = 0.8182 (TP = 36).**

## FP/FN overlap (raw counts and Jaccard, at FAR<=0.18 thresholds)

| Set type | Pair | Intersection | Union | Jaccard |
|---|---|---|---|---|
| FP | AFAC & D10 | 56 | 96 | 0.5833 |
| FP | AFAC & D11b | 56 | 95 | 0.5895 |
| FP | D10 & D11b | 69 | 92 | 0.7500 |
| FP | three-way | 52 | 103 | 0.5049 |
| FN | AFAC & D10 | 6 | 16 | 0.3750 |
| FN | AFAC & D11b | 5 | 13 | 0.3846 |
| FN | D10 & D11b | 3 | 17 | 0.1765 |
| FN | three-way | 2 | 18 | 0.1111 |

**Reading:** D10 and D11b share 75% of their false-alarm windows (Jaccard 0.75) — expected, since
both come from the same GAIRAT/SAT boundary-reweighting lineage. AFAC's false alarms are more
distinct from both (Jaccard ~0.58–0.59). Missed-fall sets (FN) are considerably less shared,
especially between D10 and D11b (Jaccard 0.18) and across all three (Jaccard 0.11 — only 2 of the
18 total missed-fall windows are missed by all three models). This asymmetry (FN complementarity
higher than FP complementarity) is the main structural signal behind the Oracle-B gain below.

### FP source-class / FN destination-class breakdown

| Model | Type | Class/bucket | Count |
|---|---|---|---|
| AFAC | FP source | other | 23 |
| AFAC | FP source | run | 31 |
| AFAC | FP source | walk | 17 |
| AFAC | FN destination | lie down | 3 |
| AFAC | FN destination | pickup | 1 |
| AFAC | FN destination | run | 3 |
| AFAC | FN destination | walk | 3 |
| D10 | FP source | other | 20 |
| D10 | FP source | run | 41 |
| D10 | FP source | walk | 20 |
| D10 | FN destination | lie down | 2 |
| D10 | FN destination | run | 2 |
| D10 | FN destination | walk | 8 |
| D11b | FP source | other | 25 |
| D11b | FP source | run | 39 |
| D11b | FP source | walk | 16 |
| D11b | FN destination | lie down | 1 |
| D11b | FN destination | walk | 7 |

Consistent with every other defense result in this ledger: **run** is the dominant false-alarm
source for all three models (31–41 of 71–81 FPs), followed by **walk**; missed falls are mostly
argmax-routed to **walk**.

## Score-correlation table (Spearman rank correlation)

| Pair | Subset | n | Spearman rho |
|---|---|---|---|
| AFAC & D10 | all validation | 496 | 0.9151 |
| AFAC & D10 | fall + run + walk | 311 | 0.9249 |
| AFAC & D11b | all validation | 496 | 0.9161 |
| AFAC & D11b | fall + run + walk | 311 | 0.9100 |
| D10 & D11b | all validation | 496 | 0.8914 |
| D10 & D11b | fall + run + walk | 311 | 0.8901 |

All three pairs show very high rank correlation (0.89–0.92) on raw fall-probability scores, in both
the full validation set and the fall+run+walk high-risk subset. This indicates the three models'
underlying *scores* are far from independent, even though their post-threshold FP/FN decision sets
show more spread (above) — a reminder that decision-level complementarity is not simply explained
by score-level diversity.

## Vote-pattern table (binary decisions at FAR<=0.18 thresholds)

| AFAC | D10 | D11b | Fall count | Non-fall count | Total | Non-fall source breakdown | Fall destination breakdown | Unstable? |
|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 2 | 349 | 351 | other 150, run 78, walk 121 | lie down 1, pickup 1 | No |
| 0 | 0 | 1 | 4 | 7 | 11 | other 5, run 1, walk 1 | lie down 1, run 2, walk 1 | No |
| 0 | 1 | 0 | 3 | 8 | 11 | other 3, walk 5 | lie down 1, walk 2 | No |
| 0 | 1 | 1 | 1 | 17 | 18 | other 4, run 11, walk 2 | run 1 | No |
| 1 | 0 | 0 | 1 | 11 | 12 | other 6, run 1, walk 4 | walk 1 | No |
| 1 | 0 | 1 | 5 | 4 | 9 | other 4 | fall 3, walk 2 | No |
| 1 | 1 | 0 | 2 | 4 | 6 | other 1, run 3 | fall 1, lie down 1 | No |
| 1 | 1 | 1 | 26 | 52 | 78 | other 12, run 27, walk 13 | fall 18, lie down 1, run 4, walk 3 | No |

All 8 patterns have support >= 3 (minimum support = 6, for pattern (1,1,0)); **no pattern is flagged
UNSTABLE.** The unanimous-reject pattern (0,0,0) covers most non-fall windows (349/452); the
unanimous-accept pattern (1,1,1) covers 26 of 44 fall windows but also 52 non-fall windows (the bulk
of the shared false-alarm burden).

## Oracle bounds

| Oracle | FAR cap | TP | FN | FP | TN | Recall | FAR |
|---|---|---|---|---|---|---|---|
| A — naive set (**OPTIMISTIC / GENERALLY UNATTAINABLE**) | 0.18 | 42 | 2 | 52 | 400 | 0.9545 | 0.1150 |
| B — pattern-level (**DECISION-FUSION BOUND**) | 0.18 | 40 | 4 | 75 | 377 | 0.9091 | 0.1659 |
| A — naive set (**OPTIMISTIC / GENERALLY UNATTAINABLE**) | 0.20 | 42 | 2 | 62 | 390 | 0.9545 | 0.1372 |
| B — pattern-level (**DECISION-FUSION BOUND**) | 0.20 | 40 | 4 | 89 | 363 | 0.9091 | 0.1969 |

**Oracle-B gain over best single model (D11b, TP=36) at FAR<=0.18: +4 TP.** Oracle A is reported
only as an upper-bound sanity check and is explicitly not attainable by any real decision rule (it
requires simultaneously using the most permissive OR-rule for detection and the most restrictive
AND-rule for false alarms).

## P0 — zero-parameter saved-score feasibility probe

Equal-weight mean of validation-ECDF-normalized fall scores (each model's raw score mapped to its
own empirical CDF rank on the 496-window validation set, then averaged 1/3-1/3-1/3; ECDF mapping
frozen and documented in the script, no fitted weights).

| FAR cap | Threshold (on ECDF-mean) | TP | FN | FP | TN | Recall | FAR | AUROC | pAUC (McClish) |
|---|---|---|---|---|---|---|---|---|---|
| 0.18 | 0.758861 | 34 | 10 | 75 | 377 | 0.7727 | 0.1659 | 0.8801 | 0.7117 |
| 0.20 | 0.721234 | 40 | 4 | 90 | 362 | 0.9091 | 0.1991 | 0.8801 | 0.7117 |

**Caveat (required):** P0 combines scores that were each computed under a *different, independently
crafted* PGD adversarial example per model. It is a **saved-score feasibility probe only, not a
deployment-equivalent fusion result** — a real fused rule would act on one shared attacked input,
which is exactly what Step 0B tests separately.

**P0 gain over best single model (D11b, TP=36) at the primary FAR<=0.18 cap: −2 TP** (P0
underperforms the best single model at this cap). Notably, at the FAR<=0.20 cap, P0 reaches TP=40,
matching Oracle-B exactly at that cap — but the primary gating cap for this audit is FAR<=0.18, per
the pre-registered protocol, where P0 does not help.

## Bootstrap (stratified by class, 2,000 resamples, seed 1337)

**Documented choice: 2,000 resamples, not 10,000**, to keep full-audit runtime reasonable given
that each resample recomputes per-model recall, Oracle-B's pattern reassignment (256-way exhaustive
search), and the P0 gain — all under already-frozen (not re-selected) per-model thresholds, so the
bootstrap describes evaluation/sampling variability under the fixed Step 0A rule, with the single
explicit exception of Oracle-B's pattern assignment, which is re-optimized inside every resample per
the audit specification.

| Metric | Median | 95% CI |
|---|---|---|
| AFAC recall @ FAR<=0.18 | 0.7727 | [0.6364, 0.8864] |
| D10 recall @ FAR<=0.18 | 0.7273 | [0.5909, 0.8636] |
| D11b recall @ FAR<=0.18 | 0.8182 | [0.7045, 0.9318] |
| Oracle-B TP gain over best single | 4.0 | [−1.0, 8.0] |
| P0 TP gain over best single | −2.0 | [−7.0, 1.0] |

**Fraction of resamples with Oracle-B gain >= 2 TP: 0.8205.**
**Fraction of resamples with P0 gain >= 2 TP: 0.0080** (P0 essentially never matches this bar).

### Optional 2-fold cross-fit of Oracle-B (NOISE-DOMINATED — not used for gating)

Fold sizes: 22 fall / 226 non-fall per fold. Assignment learned on fold A, applied to fold B:
TP=18/22 (FAR=0.1593). Assignment learned on fold B, applied to fold A: TP=17/22 (FAR=0.1770).
Both meaningfully below the full-sample Oracle-B recall (0.9091), as expected with half the fall
windows (22 vs 44) — reported for context only, explicitly not used in the gate decision.

## Step 0B — shared-input transfer matrix (3x3, FAR<=0.18 thresholds)

Rows = evaluated model; columns = source model the adversarial example was crafted against.

| Eval model \ Source | AFAC | D10 | D11b |
|---|---|---|---|
| **AFAC** | TP34/FN10/FP71/TN381, R=0.7727 (diag) | TP37/FN7/FP57/TN395, R=0.8409 | TP38/FN6/FP46/TN406, R=0.8636 |
| **D10** | TP43/FN1/FP89/TN363, R=0.9773 | TP32/FN12/FP81/TN371, R=0.7273 (diag) | TP42/FN2/FP71/TN381, R=0.9545 |
| **D11b** | TP42/FN2/FP104/TN348, R=0.9545 | TP41/FN3/FP91/TN361, R=0.9318 | TP36/FN8/FP80/TN372, R=0.8182 (diag) |

**Diagonal validity check:** each diagonal cell (model evaluated on adversarial examples crafted
against itself) was required to reproduce Step 0A's saved-score confusion counts within ±2 per
cell. **Actual result: exact match, diff = 0 in every TP/FN/FP/TN cell, for all three models.**
`step0b_valid = True`. Transfer-dependent gates below are therefore valid, not `STEP0B_INVALID`.

**Mean diagonal fall recall: 0.7727. Mean off-diagonal fall recall: 0.9205.**

Required transfer-veto condition: mean off-diagonal recall >= mean diagonal recall + 0.15
(>= 0.9227). **Actual: 0.9205 < 0.9227 — the transfer veto FAILS, by a margin of 0.0022 (roughly
one fall window out of 44).**

**Interpretation:** every model detects *more* falls under adversarial examples crafted against a
different model than under its own adversarial examples — i.e., attacks do not transfer perfectly,
and each model has a genuinely distinct point of weakness. This is the expected direction for
"real" complementarity. However, the pre-registered bar requires this gap to reach 0.15, and the
observed gap (0.1478) falls just short of it. The complementarity measured in Step 0A is therefore
real in direction but does not clear the threshold set for authorizing fusion under a shared,
single attacked input.

## Gates

**Best single model at FAR<=0.18: D11b (recall = 0.8182, TP = 36).**

- **Transfer veto: FAIL** (mean off-diagonal recall 0.9205 < required 0.9227).
- Oracle-B gain over best single = +4 TP (>= +3 required) — satisfied in isolation.
- P0 gain over best single = −2 TP (fails the +2 alternative) — not satisfied.
- Bootstrap P(Oracle-B gain >= 2 TP) = 0.8205 (>= 0.70 required) — satisfied in isolation.
- Step 0B validity: **valid** (diagonal exact match) — so the transfer veto's failure is a clean,
  reportable result, not an `INCONCLUSIVE_FOR_TRANSFER` case.

**Per the pre-registered rule, a failed transfer veto is a necessary-condition failure: the final
result is FAIL for fusion purposes regardless of the Oracle-B or P0 gains.**

### GATE RESULT: **FAIL**

(For transparency only, not as a basis for action: absent the transfer veto, the Oracle-B path
alone — gain +4 >= +3, bootstrap stability 0.8205 >= 0.70 — would have numerically satisfied the
STRICT PASS conditions. The transfer veto exists precisely to catch this case, and it did.)

No fusion fitting was performed. No test-split data was touched at any point. No recommendation
beyond this factual gate status is made.

## Interpretation

The saved-score audit (Step 0A) shows real, structurally interesting complementarity between
AFAC-score, D10, and D11b: their missed-fall (FN) sets barely overlap (three-way Jaccard 0.11),
their false-alarm (FP) sets overlap only partially (three-way Jaccard 0.50), and a pattern-level
decision oracle recovers 4 more true positives than the best single model, a gain that is stable
across 82% of stratified bootstrap resamples. A simple, unfitted equal-weight score-fusion probe
(P0), however, does not realize this gain at the primary FAR<=0.18 cap (it ties the weakest model
rather than approaching the oracle bound), showing that the complementarity visible at the
decision level does not trivially translate into a naive score-averaging rule. The shared-input
transfer audit (Step 0B) — which regenerates adversarial examples against each model individually
and cross-evaluates all three, with an exact diagonal validity match confirming the regeneration
was faithful — shows that each model is indeed harder to fool with its own adversarial examples
than with another model's (mean off-diagonal recall 0.92 vs mean diagonal recall 0.77), consistent
with genuine, non-trivial diversity. But this gap (0.1478) falls just short of the pre-registered
0.15 bar meant to guard against mistaking artifacts of independently-crafted attacks for durable,
shared-input-robust diversity. Taken together, D13 Step 0A/0B finds **real but insufficient**
evidence of complementarity: the gate result is FAIL, and no Stage 1 score-fusion experiment is
authorized on this evidence. A materially larger or more reliably estimated transfer gap — for
example from a fourth, more architecturally distinct candidate model, or from re-running this exact
protocol after any of the three checkpoints is retrained — would be the natural precondition for
revisiting this audit before any Stage 1 is considered.
