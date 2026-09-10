# D10/D11 Transfer-Failure Diagnosis — Why Validation Success Did Not Transfer to Frozen Held-Out Test

Date: 2026-07-05. Evidence type: **diagnostic re-analysis of already-saved scores and predictions
only.** No new training, no new attack generation, no new held-out-test inference, no checkpoint
loaded, no threshold promoted, no thesis `.tex` touched, nothing committed. All post-hoc test
sweeps below are explicitly diagnostic characterization, not frozen-threshold evidence, and cannot
claim F20.

Script: `scripts/analysis/d10_d11_transfer_failure_diagnosis.py`
Outputs: `results/defense_attempt_inventory/d10_d11_transfer_diagnostics/` (8 CSVs, 4 plots,
`key_numbers.json`).

## Artifact inventory used (all pre-existing)

| Method | Validation scores (PGD eps=0.030) | Test scores (PGD eps=0.030) |
|---|---|---|
| D8b / AFAC (`optionB_maxscore`) | `results/afac_score_frozen_threshold_followup/val_eval/optionB_maxscore_pgd_probabilities_val_epsilon_0_03.csv` | `results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/test_eval/optionB_maxscore_pgd_probabilities_test_epsilon_0_03.csv` |
| D10 (`GR1_v2macroF1`) | `.../boundary_aware_selective_at/gairat/seed42/GR1/val_eval/GR1_v2macroF1_pgd_probabilities_val_epsilon_0_03.csv` | `results/d10_d11_locked_test_followup/test_eval/GR1_v2macroF1_pgd_probabilities_test_epsilon_0_03.csv` |
| D11a (`ST1b6_v2lowFA`) | `.../boundary_aware_selective_at/seed42/beta6p0/val_eval/ST1b6_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv` | `results/d10_d11_locked_test_followup/test_eval/ST1b6_v2lowFA_pgd_probabilities_test_epsilon_0_03.csv` |
| D11b (`SA1_v2lowFA`) | `.../boundary_aware_selective_at/sat/seed42/SA1/val_eval/SA1_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv` | `results/d10_d11_locked_test_followup/test_eval/SA1_v2lowFA_pgd_probabilities_test_epsilon_0_03.csv` |

Frozen thresholds taken verbatim from `d10_d11_threshold_selection_validation.csv` and
`afac_score_threshold_selection_validation.csv`. Split sizes verified in-script: validation 496
(44 fall / 452 non-fall), test 500 (45 fall / 455 non-fall). Score = `fall_probability`, decision
rule `score >= tau`, identical to the committed protocols.

**Missing artifact note:** the directory `provenance/appendices/internal_defense_experiment_ledger/`
does not exist in this working tree (no `provenance/` directory at the repo root). Ledger-level
facts were therefore taken from the committed results summaries
(`d10_d11_locked_test_summary.md`, `afac_score_frozen_threshold_summary.md`,
`d1_d12_*_summary.md`, D13 stage-0 reports). No part of the diagnosis below depends on the missing
directory; it is noted for completeness only.

---

## 1. Score-boundary diagnosis

### 1.1 Validation vs test score distributions (quantiles)

From `diag_score_quantiles_val_vs_test.csv` (fall q10/q25/q50; non-fall q75/q90/q95):

| Method | Split | fall q10 | fall q25 | fall q50 | nf q75 | nf q90 | nf q95 | AUROC |
|---|---|---|---|---|---|---|---|---|
| D8b/AFAC | val | 0.102 | 0.174 | 0.208 | 0.096 | 0.223 | 0.293 | 0.8719 |
| D8b/AFAC | test | 0.101 | 0.160 | 0.200 | 0.112 | 0.245 | 0.296 | 0.8439 |
| D10 | val | 0.068 | 0.086 | 0.171 | 0.034 | 0.223 | 0.358 | 0.8712 |
| D10 | test | **0.039** | **0.075** | 0.167 | 0.038 | 0.235 | 0.344 | 0.8470 |
| D11a | val | 0.052 | 0.066 | 0.099 | 0.023 | 0.160 | 0.261 | 0.8690 |
| D11a | test | **0.025** | **0.049** | 0.099 | **0.035** | **0.206** | 0.268 | 0.8199 |
| D11b | val | 0.043 | 0.068 | 0.125 | 0.031 | 0.121 | 0.208 | 0.8728 |
| D11b | test | **0.030** | **0.054** | 0.109 | 0.033 | **0.148** | **0.244** | 0.8278 |

Two-sided KS distances, validation vs test (`diag_ks_val_vs_test.csv`):

| Method | KS fall (val vs test) | KS non-fall (val vs test) |
|---|---|---|
| D8b/AFAC | 0.140 | 0.052 |
| D10 | 0.155 | 0.078 |
| D11a | **0.220** | 0.073 |
| D11b | 0.167 | 0.066 |

Reading: the validation-to-test shift is **concentrated in the fall-score distribution, not the
non-fall tail**. For D10/D11 the lower fall quantiles (q10/q25) drop by 30–50% from validation to
test — exactly the region where their very low frozen thresholds (0.048–0.075) sit. The non-fall
upper tails also thicken slightly on test (D11a q90: 0.160→0.206; D11b q95: 0.208→0.244),
producing the observed FAR overshoot. D8b/AFAC shows the smallest fall shift near its (much
higher) threshold: fall survival at tau=0.1479 moves only 0.818→0.800.

### 1.2 Recall at FAR caps 0.10 / 0.15 / 0.18 / 0.20 / 0.22

From `diag_recall_at_far_caps.csv`. "Frozen" = validation-selected threshold applied to test
(caps 0.18 and 0.22 use the identical selection rule replicated on saved validation scores;
committed frozen values used where they exist). "Post-hoc" = best-achievable on test at that cap
(diagnostic oracle only).

| Method | Cap | tau (val) | Val recall/FAR | Test frozen recall/FAR (TP/FP) | Test post-hoc recall (TP/FP) |
|---|---|---|---|---|---|
| D8b/AFAC | 0.20 | 0.1479 | 0.818 / 0.195 | 0.800 / 0.209 (36/95) | **0.800 (36/91)** |
| D8b/AFAC | 0.18 | 0.1709 | 0.773 / 0.157 | 0.689 / 0.182 (31/83) | 0.667 (30/79) |
| D10 | 0.20 | 0.0753 | 0.886 / 0.190 | 0.756 / 0.204 (34/93) | 0.711 (32/86) |
| D10 | 0.22 | 0.0558 | 0.955 / 0.219 | 0.800 / 0.226 (36/103) | 0.778 (35/93) |
| D11a | 0.20 | 0.0518 | 0.909 / 0.190 | 0.689 / 0.224 (31/102) | 0.667 (30/91) |
| D11b | 0.20 | 0.0485 | 0.886 / 0.188 | 0.756 / 0.215 (34/98) | 0.667 (30/86) |

(Full 5-cap table including 0.10/0.15 in the CSV.) The decisive column is the last one: **even
with a post-hoc oracle threshold on test — i.e., zero calibration error — D10/D11a/D11b top out at
TP 32/30/30 at FAR<=0.20, below the 36 required for F20.** D8b is the only method whose test
score ranking admits TP=36 at FP<=91 at all.

### 1.3 F20 feasibility window on test (`diag_f20_feasibility_on_test.csv`)

F20 requires TP>=36 and FP<=91, i.e. tau <= (36th-highest fall score) and tau > (92nd-highest
non-fall score):

| Method | 36th fall score (tau upper bound) | 92nd non-fall score (tau lower bound) | Window width | Max TP at FP<=91 | TP shortfall |
|---|---|---|---|---|---|
| D8b/AFAC | 0.153246 | 0.152965 | **+0.000281** (1 candidate tau) | 36 | 0 |
| D10 | 0.057240 | 0.077852 | **−0.0206** (infeasible) | 32 | 4 |
| D11a | 0.039350 | 0.063374 | **−0.0240** (infeasible) | 30 | 6 |
| D11b | 0.046125 | 0.056932 | **−0.0108** (infeasible) | 30 | 6 |

For D10/D11 the 36th-best fall window scores **below** the 92nd-best non-fall window: the F20
operating point does not exist anywhere on their test score axes. For D8b it exists as a
**single-candidate knife edge 0.00028 wide** — the historical D8b F20 point (tau=0.153246) is
literally the only threshold that satisfies it.

### 1.4 TP/FP sensitivity near the frozen FAR-0.20 thresholds

From `diag_threshold_sensitivity_far020.csv` and `diag_fn_fp_distance_from_frozen_tau.csv`:

| Method | Frozen tau | FN dist to tau (median/max) | FN within 0.02 | Excess FPs vs 91 (distance) | tau move to reach TP=36 | FP at that tau (overage) |
|---|---|---|---|---|---|---|
| D8b/AFAC | 0.1479 | 0.052 / 0.140 | 2 of 9 | 4 (all within **0.0051**) | **+0.0054** | **91 (0)** |
| D10 | 0.0753 | 0.031 / 0.070 | 2 of 11 | 2 (within 0.0026) | −0.0180 | 102 (+11) |
| D11a | 0.0518 | 0.021 / 0.049 | 6 of 14 | 11 (within 0.0115) | −0.0125 | 112 (+21) |
| D11b | 0.0485 | 0.011 / 0.046 | 6 of 11 | 7 (within 0.0084) | −0.0024 | 100 (+9) |

Density near the operating point is high: within ±0.01 of the frozen tau, D11b has 9 fall + 19
non-fall test windows (TP swings 30–39, FP swings 90–109 across that ±0.01 band); D11a has 5+13;
D10 4+12. So the operating region sits in a **broadly overlapping score zone**, not a clean margin
with a few stragglers.

Interpretation, split by error type:

- The **FP overshoot** at frozen thresholds is threshold-near: 2–11 marginal non-fall windows
  within ~0.01 of tau. This part is a calibration/threshold-transfer artifact.
- The **recall shortfall is not**: recovering TP=36 by lowering tau costs FP=100–112 (9–21 over
  the cap) for D10/D11, because 4–6 fall windows are interleaved deep inside the non-fall upper
  tail. That is broad distribution overlap, not a few threshold-near windows.
- D8b is the mirror image: its frozen miss is *entirely* 4 threshold-near FPs; moving tau up by
  0.0054 lands exactly on F20 with zero TP loss — but see §4 for why that is not reliably
  selectable from validation.

### 1.5 Recall-drop decomposition at the frozen tau (`diag_recall_drop_decomposition.csv`)

| Method | Fall survival at tau: val → test | Non-fall survival at tau: val → test |
|---|---|---|
| D8b/AFAC | 0.818 → 0.800 (−0.018) | 0.195 → 0.209 (+0.014) |
| D10 | 0.886 → 0.756 (−0.130) | 0.190 → 0.204 (+0.014) |
| D11a | 0.909 → 0.689 (−0.220) | 0.190 → 0.224 (+0.034) |
| D11b | 0.886 → 0.756 (−0.130) | 0.188 → 0.215 (+0.027) |

The transfer failure is dominated by the fall side (recall loss 3–8× larger than the FAR gain).
D10/D11's validation recall advantage over AFAC (0.886–0.909 vs 0.818) was carried by fall windows
scoring barely above very low thresholds; that thin margin is exactly what failed to generalize.

Plots: `fall_vs_nonfall_test_score_distributions.png`, `val_vs_test_score_ecdf.png`,
`tp_fp_vs_threshold_near_far020.png` (F20-feasible tau band shown in green — visible only for
D8b, as a sliver), `nonfall_upper_tail_by_source_class.png`, all under
`d10_d11_transfer_diagnostics/`.

---

## 2. Class-source diagnosis (frozen FAR-0.20 thresholds, held-out test)

From `diag_class_source_breakdown.csv` (counts, with per-class rates in parentheses):

### False-fall-alarm source classes

| Source class (n) | D8b frozen (95 FP) | D10 (93 FP) | D11a (102 FP) | D11b (98 FP) | D8b post-hoc F20 (91 FP) |
|---|---|---|---|---|---|
| run (121) | 38 (.314) | 45 (.372) | 48 (.397) | 44 (.364) | 36 (.298) |
| walk (147) | 27 (.184) | 23 (.157) | 24 (.163) | 22 (.150) | 26 (.177) |
| stand up (31) | 10 (.323) | 10 (.323) | 11 (.355) | 12 (.387) | 10 (.323) |
| lie down (66) | 10 (.152) | 6 (.091) | 8 (.121) | 8 (.121) | 9 (.136) |
| pickup (50) | 8 (.160) | 6 (.120) | 8 (.160) | 7 (.140) | 8 (.160) |
| sit down (40) | 2 (.050) | 3 (.075) | 3 (.075) | 5 (.125) | 2 (.050) |

- run+walk contribute 67–73% of the false-alarm burden for every method. The excess is **not** a
  single-class pathology unique to D10/D11; it is the same run/walk-dominated tail shape as D8b,
  just thicker.
- The D10/D11 *extra* FPs relative to D8b's post-hoc F20 point come mostly from **run** (44–48 vs
  36; per-class rate .36–.40 vs .30) plus 1–3 extra sit-down/stand-up windows. Per-class rate is
  actually highest for **stand up** (~.32–.39) in all methods, but at n=31 it contributes few
  absolute FPs.

### Missed-fall destination classes (argmax under PGD)

| Destination | D8b frozen (9 FN) | D10 (11 FN) | D11a (14 FN) | D11b (11 FN) |
|---|---|---|---|---|
| walk | 5 | 9 | 6 | 7 |
| run | 2 | 1 | 6 | 0 |
| lie down | 2 | 1 | 2 | 3 |
| sit down | 0 | 0 | 0 | 1 |

Missed falls are argmax-routed predominantly to **walk** (D10 9/11, D11b 7/11), with D11a
splitting evenly between walk and run. Same destination family as D8b — again a thicker version of
the same confusion, not a new one.

### Why D8b had a better post-hoc operating boundary

D8b's advantage is not a different error pattern — it is a **quantitatively thinner run tail
relative to its fall mass at a higher threshold**. At matched FAR<=0.20 post-hoc points, D8b keeps
36 falls above 91 non-falls; D10/D11 interleave their 33rd–36th falls *below* their 92nd non-fall
(mostly run windows). D8b's higher operating threshold (0.15 vs 0.05–0.08) also sits in a
less-dense score region (1 fall + 4 non-falls within ±0.005, vs up to 4+7 for D11a/b), so its
count boundary is inherently less jittery.

---

## 3. Transfer-failure mechanism (classification)

**Primary: structural ranking/separability failure on held-out test, produced by a
validation-to-test generalization shift concentrated in the fall-score ranks — with a secondary,
genuinely boundary-level false-positive excess.**

Justification against the candidate classes:

- *Calibration/threshold instability* — real but secondary: it explains the FAR overshoot
  (0.204–0.224 vs 0.19 selected; 2–11 threshold-near excess FPs) but cannot explain the recall
  shortfall: post-hoc oracle thresholds (perfect calibration) still leave D10/D11 at TP 32/30/30 < 36 (§1.3).
- *Structural ranking/separability failure* — confirmed: the F20 region is empty on the test
  score axis for all three methods (negative feasibility windows −0.011 to −0.024).
- *Class-specific false-positive tail* — rejected as the primary mechanism: the FP composition is
  the same run/walk-dominated mix as D8b (§2); no single class accounts for the failure.
- *Validation/test generalization shift* — confirmed as the driver of the structural failure:
  KS(fall) 0.155–0.220 vs KS(non-fall) 0.066–0.078; fall survival at the frozen tau drops
  0.13–0.22 while non-fall survival rises only 0.01–0.03 (§1.5). D10/D11's validation win was a
  thin low-threshold fall margin that did not exist on test.
- *Both recall loss and false-positive excess* — descriptively true (both occurred), but the
  recall loss is the binding constraint; fixing the FP excess alone leaves TP maxed at 30–32.
- *Insufficient artifacts* — no: every needed score/prediction artifact existed (only the
  provenance ledger directory was missing, and nothing depended on it).

D8b/AFAC is a distinct sub-case: its frozen-threshold miss (36/95 vs needed 36/91) **is** pure
boundary-level calibration — but its F20 target on test is a single-candidate, 0.00028-wide
threshold window.

---

## 4. Fixability decision

**Chosen: new training objective would be needed — calibration/threshold-stability selection is
provably insufficient on this evidence.** (With the explicit caveat that the ledger's own ceiling
evidence makes new same-family training unpromising; see §5.)

- **Score quantiles / feasibility:** no threshold exists on the D10/D11 test score axes that
  satisfies F20 (window widths −0.011 to −0.024; max TP at FP<=91 is 32/30/30). Calibration
  methods can only pick a point on the existing score axis; they cannot create one. Only a change
  to the score function (i.e., training) could reorder the 4–6 falls currently ranked below the
  92nd non-fall window.
- **Threshold sensitivity:** for D8b/AFAC, where the gap *is* boundary-level, the F20-feasible
  window is one candidate threshold wide (0.000281). The saved Stage-1 bootstrap
  (`afac_score_bootstrap_stability_validation.csv`) puts the 95% CI of the validation-selected
  FAR-0.20 threshold at **[0.113, 0.177]** — the sampling uncertainty of the selection rule is
  ~230× wider than the target window. A "stability-aware" selection cannot reliably hit it; the
  pre-registered 0.18-buffered attempt already demonstrated the failure mode (buffering overshot
  to tau=0.171, dropping test TP from 36 to 31).
- **False-positive source classes:** the FP tail is the same run/walk mix in all methods; there is
  no isolatable class whose removal by a calibration-side rule would legitimately recover the cap
  (and per-class decision rules would be new-model territory anyway, with 4–6 TPs still missing).
- **Missed-fall destinations:** the missing falls are argmax-routed to walk/run with scores
  0.01–0.07 below the frozen thresholds and interleaved with dozens of non-fall windows — they are
  not recoverable by any threshold move at acceptable FP cost (FP 100–112 at TP=36).
- **Distance of failing windows:** FP excess = threshold-near (fixable in principle); recall
  shortfall = distributed through the overlap zone (not fixable by thresholding). The binding
  failure is the second one.

---

## 5. One next-action recommendation

**Recommendation: stop the F20 chase before the proposal defense.** (Do not open AFAC-plus
calibration/stability, D10b, D11c, a class-source-aware penalty, or calibrated fusion.)

- **Why it targets the diagnosed failure:** the diagnosis shows F20 was never achievable on the
  locked test split for D10/D11 at *any* threshold, and that the only F20-bearing score axis
  (D8b/AFAC) admits it only on a 0.00028-wide knife edge that validation-side selection cannot
  reliably target (threshold CI ±0.032). The failure is in test-split score geometry at a target
  sitting exactly on the count boundary (TP=36/45, FP=91/455) — at n=500 this operating point is
  at the resolution limit of the split itself. No calibration procedure fixes geometry, and the
  geometry-side fix (training) is already frontier-capped in this ledger.
- **Why better than the alternatives:**
  - *AFAC-plus calibration/stability* — targets a single-candidate threshold window; the
    pre-registered buffered variant already failed in exactly the predicted direction; a second
    calibration attempt is a coin flip dressed as a protocol.
  - *D10b FP-tail penalty / class-source-aware false-alarm penalty / D11c SAT-BASAT rerun* — all
    are new training against the documented representation-spanning frontier ceiling
    (~0.876 PGD-AUROC; TRADES/GAIRAT/SAT all NO-GO; BiLSTM pivot worse; D14 low-FAR-ranking runs
    failed their validation health gates on seeds 43/44). The diagnosed deficit (4–6 fall windows
    interleaved in the run/walk tail) is precisely what those objectives already tried to move.
  - *Calibrated fusion* — D13 Stage-0 shared-input transfer veto **failed** under its
    pre-registered rule (gap 0.1478 < 0.15); opening fusion now would override the project's own
    evidence discipline.
- **Timing: before the proposal defense.** This is a stopping decision, not an experiment; it
  costs nothing and removes the risk of walking into the defense with another fresh negative.
  Present D8b post-hoc F20 + the frozen near-miss (36/95) + this diagnosis as the operating-region
  characterization story. Any reopening should be post-proposal, advisor-authorized, and
  pre-registered — plausibly only for a genuinely different representation family, per the
  capstone.
- **Success gate (for the stop decision):** the appendix/proposal presents the F20 chase as closed
  with this diagnosis as the mechanism evidence, and the committee accepts the
  frozen-vs-post-hoc evidence distinction without requiring a new F20 attempt.
- **Failure gate (what would reopen the chase):** the committee explicitly requires
  frozen-threshold F20 evidence, **and** a new pre-registered candidate exists that clears a
  pre-declared validation bar strictly stronger than D10/D11's (e.g., validation pAUC(FAR<=0.20)
  materially above the 0.71 AFAC level and a positive projected F20 feasibility window under a
  D14-style health gate) — otherwise the chase stays closed even post-proposal.

*(Per instructions, no new experiment protocol is written here.)*

---

## Reproduction

```
python scripts/analysis/d10_d11_transfer_failure_diagnosis.py
```

Reads only the eight saved probability CSVs and the two frozen-threshold selection CSVs; writes
only under `results/defense_attempt_inventory/d10_d11_transfer_diagnostics/`. Deterministic (no
sampling anywhere).
