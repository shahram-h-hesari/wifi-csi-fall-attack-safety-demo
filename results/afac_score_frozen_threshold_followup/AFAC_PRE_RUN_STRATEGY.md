# AFAC-Score Frozen Validation-Threshold Follow-Up — Pre-Run Strategy (Advisory Only)

Date: 2026-07-04. Status: **advisory report only — nothing has been run.** No validation export, no
threshold selection, no test application, no training, no thesis edits, no commits.

Purpose: define the most scientifically defensible protocol for promoting D8b (AFAC-score) from
post-hoc test FAR-sweep evidence to frozen validation-selected-threshold held-out-test evidence,
maximizing the chance of a strong result *without* validation/test leakage.

---

## 1. Artifact inventory (D8 / AFAC = "optionB", seed 42)

All under `results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/`
and `checkpoints/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/`.

**Checkpoints (all present):**

| Internal name | Thesis name | Epoch | Checkpoint |
|---|---|---|---|
| optionB maxscore | **AFAC-score (the D8b reference)** | 68 | `optionB/seed42/seed42_optionB_maxscore_best.pt` |
| optionB maxrec | AFAC-recall | 70 | `optionB/seed42/seed42_optionB_maxrec_best.pt` |
| optionB minFA | AFAC-lowFA | 66 | `optionB/seed42/seed42_optionB_minFA_best.pt` |
| optionB last | (not evaluated at Gate 5) | 70 | `optionB/seed42/seed42_optionB_last.pt` |

**Score/metric artifacts:**

| Artifact | Exists? | Notes |
|---|---|---|
| Test per-window scores (clean/FGSM/PGD × 3 variants) | **Yes** | Gate-5 exports via `export_probability_predictions.py --split test --epsilon 0.03 --pgd-steps 10` (alpha = eps/6 default); split verified 500/45/455 in the Gate-5 review. These are the exact saved scores behind the D8b appendix row. |
| **Validation per-window scores** | **NO — none exist for any variant** | This is the single missing piece. Only per-epoch **argmax** validation metrics exist (training log), which cannot be used to select a fall-score threshold. |
| Training log (per-epoch val PGD FAR/recall, lambda_b trace) | Yes | `optionB/seed42/logs/seed42_optionB_training_log.csv` |
| Metadata / provenance | Yes | `seed42_optionB_metadata.json`: `test_set_used: false` at training; selection validation-only; torch 2.12.0+cpu; 70 fixed epochs. |
| Validation pilot review (argmax summary) | Yes | maxscore val PGD argmax recall 0.500 / FAR 12.2%; maxrec 0.614 / 16.8%; minFA 0.205 / 7.3%. |
| Gate-5 test review (argmax) | Yes (historical) | All three checkpoints REJECTED under the pre-registered argmax criteria (clean-accuracy guard failed on test: 0.668–0.698 < 0.70). |
| Test-side diagnostics (frontier sweep, score distributions, val-vs-test, error routing) | Yes (historical) | Test-derived; used below only for disclosure, **not** for protocol design. |
| D8b post-hoc reference row | Yes (historical, in appendix + `results/operating_region_characterization/`) | Rfall 0.8000, FAR 0.2000, TP/FN/FP/TN 36/9/91/364, AUROC ≈ 0.8439, threshold ≈ 0.153246. |

**Evidence classification per variant:** all three variants have test scores (clean/FGSM/PGD),
fixed/argmax test metrics, historical test threshold-sweep metrics, and full metadata — and **none**
has validation scores. Required new artifact: one validation-split export for AFAC-score
(inference-only, ~2–3 min CPU).

## 2. What the D10/D11 failure teaches (the priors we may legitimately use)

The D10/D11 locked-test follow-up (results/d10_d11_locked_test_followup/) is *prior documented
evidence from a different experiment* and is legitimate input to protocol design:

1. **FAR overshoot:** thresholds selected at val FAR ≈ 0.188–0.190 produced test FAR 0.204/0.224/0.215
   — overshoot of +0.004 to +0.024 above the 0.20 cap. Two of three failed the cap on FAR alone.
2. **Recall optimism:** val recall 0.886–0.909 became test recall 0.689–0.756 (drop 0.13–0.22).
3. **Not a threshold artifact:** even post-hoc test sweeps stayed below D8b, so the gap was
   score-separability generalization, not threshold placement.
4. **Statistical floor:** with 455 non-fall test windows, the binomial SD of observed FAR at
   p ≈ 0.20 is √(0.2·0.8/455) ≈ **0.019**. Even a perfectly calibrated threshold has ~50% chance of
   overshooting a boundary-tight cap. Selecting *at* the cap on validation is structurally biased
   toward failure.

Implication: the rule must include a **pre-registered FAR transfer buffer**, and expectations for
recall must be conservative.

## 3. Leakage boundaries observed in this design

- The known D8b post-hoc threshold (≈0.1532) and every historical test-side number are used **only**
  for disclosure and expectation-setting. The selection rule below is derived exclusively from
  (a) validation evidence to be generated, (b) the D10/D11 transfer measurements, and (c) binomial
  reasoning. **Pre-commitment: the validation-selected threshold will not be adjusted based on its
  proximity to 0.1532 or to any other test-derived quantity.**
- The existing Gate-5 **test scores will be reused, not regenerated** — regeneration is unnecessary
  (protocol is deterministic and already byte-identical: same tool, `--epsilon 0.03 --pgd-steps 10`,
  alpha = eps/6) and reuse preserves provenance continuity with the D8b appendix row.
- Test files will be read **only** in the single-shot application step, after thresholds are frozen.

## 4. Threshold-selection strategy comparison

| Rule | Verdict |
|---|---|
| (a) Max val recall s.t. val FAR ≤ 0.20 | Precedented (exact D10/D11 rule) but boundary-tight: D10/D11 showed it overshoots the cap on test ~2/3 of the time. Keep as a **secondary comparability row**, not the headline. |
| (b) Max val recall s.t. **conservative cap (0.18)** | **Recommended primary.** The 0.02 buffer ≈ max observed D10/D11 overshoot (+0.024, rounded) ≈ 1 binomial SD of test FAR at n=455. Simple to state, simple to defend: "0.20 target minus a pre-registered transfer buffer derived from measured validation-to-test FAR overshoot in the immediately preceding locked-test experiment." Cost: some recall if the val frontier is steep — which is why Stage 1 inspects the frontier *before* the buffer is finalized (validation-only tuning, fully legitimate). |
| (c) Non-fall val-score quantile | Mathematically identical to (a)/(b) — a FAR cap of c places the threshold at the ⌈(1−c)·452⌉-th order statistic of non-fall val scores. Not a separate option; mention the equivalence in the writeup for rigor. |
| (d) Bootstrap stability | Valuable as a **diagnostic**, not as the headline rule: stratified bootstrap of the 496 val windows → distribution of selected thresholds and of predicted FAR at each candidate threshold. Use it to (i) quantify threshold uncertainty with only 44 fall windows, and (ii) sanity-check the buffer size. Making it the primary rule would complicate the committee story for little gain. |
| (e) Recall-minus-FAR-penalty score | Ad hoc; penalty weight is an unjustifiable free parameter; weakest defensibility. Rejected. |
| (f) Partial-AUC / low-FAR behavior | A metric, not a selection rule; report validation partial behavior descriptively. Rejected as a rule. |

**Tie-breaking** (pre-registered, identical to the D10/D11 script): among thresholds meeting the cap,
maximize val recall; then minimize val FAR; then take the highest threshold.

## 5. Variant-selection strategy

**Use AFAC-score (optionB maxscore) only, as the pre-committed headline. Do not select among
variants.** Three reasons, in order of importance:

1. **Any "fresh" variant selection is unavoidably test-informed.** Held-out test results for all
   three variants are already documented (Gate-5 argmax review; operating-region sweep rows). We
   already know maxscore's post-hoc test frontier dominates maxrec's and minFA's at FAR ≤ 0.20. A
   validation-based selection run *now* cannot be un-contaminated by that knowledge — whichever
   variant "wins on validation," the choice was made knowing the test answer. The only clean
   position is that the variant was **pre-committed historically**: the appendix D8b row and the
   2026-07-04 decision memo both designate AFAC-score, and both predate this analysis.
2. Selecting among 3 variants multiplies the validation-optimism problem D10/D11 just quantified.
3. The claim being tested is precise — "does the D8b operating point survive frozen
   validation-threshold selection?" — and only maxscore answers it.

Optional: also export validation scores for maxrec/minFA, **labeled diagnostics-only**, with a
pre-registered commitment that the headline cannot be switched to them regardless of outcome.

## 6. Recommended primary protocol (two-stage, approval-gated)

**Stage 1 — validation only (no test contact):**
1. Export AFAC-score validation per-window scores:
   checkpoint `seed42_optionB_maxscore_best.pt`, `export_probability_predictions.py --split val
   --epsilon 0.03 --pgd-steps 10` (identical settings to the Gate-5 test exports).
   Verify 496 windows / 44 fall / 452 non-fall.
2. Compute the validation PGD recall–FAR frontier and the bootstrap threshold-stability diagnostic.
3. Freeze thresholds at four caps: **0.18 (primary)**, 0.20, 0.15, 0.10 — rule: max val recall
   s.t. val FAR ≤ cap; ties per §4. If the frontier is pathologically steep at 0.18 (e.g., large
   recall cliff), the buffer may be revisited **only with documented justification and Shahram's
   approval, still before any test contact**.
4. Present the frozen thresholds + validation metrics to Shahram. **Hard stop for approval.**

**Stage 2 — single-shot test application (after approval):**
5. Apply each frozen threshold exactly once to the **existing** Gate-5 test PGD scores
   (`optionB_maxscore_pgd_probabilities_test_epsilon_0_03.csv`). No regeneration, no re-selection,
   no second look.
6. Also apply the primary frozen threshold once to the existing **clean** test scores, to report
   clean-condition thresholded recall/FAR (pre-registered here; addresses the Gate-5 clean-guard
   caveat at the operating level actually used).
7. Report per cap: threshold, val recall/FAR at threshold, test TP/FN/FP/TN, recall, FAR,
   precision, F1, AUROC, F20 and R90F10 flags; FP source classes; FN destination classes.

**Attack setting:** PGD, epsilon = 0.030, eval PGD-10 (alpha = eps/6) — matching D8b, D10/D11, and
all committed evals. **Main target:** F20 at the 0.20 cap, pursued via the 0.18-buffered selection.

**Success/failure judged on the primary (0.18-buffered) row only.** The 0.20-cap row exists for
like-for-like comparison with the D10/D11 protocol; the 0.15/0.10 rows characterize the path toward
R90F10. Reporting all rows is mandatory regardless of outcome (no selective reporting).

## 7. Recommended secondary diagnostics (all labeled non-headline)

- FAR caps 0.20 / 0.15 / 0.10 frozen-threshold rows (as above).
- Post-hoc test characterization row (labeled) — reproduces/confirms the historical D8b 0.800@0.200
  reference for a same-footing table; no new information, symmetry with the D10/D11 outputs.
- False-alarm source breakdown and missed-fall destination breakdown at each frozen threshold
  (run/walk dominance check, comparison to D10/D11 error structure).
- Validation-vs-test calibration gap: val recall/FAR at τ vs test recall/FAR at τ — the direct
  transfer measurement for AFAC, comparable to the D10/D11 gaps.
- Score-distribution summary (val vs test, clean vs PGD, fall vs non-fall).
- Binomial 95% CIs on test recall (n=45) and FAR (n=455) for honest uncertainty display.
- Comparison table: this result vs D8b post-hoc reference vs D10/D11 locked rows.
- Optional: maxrec/minFA validation exports (diagnostics-only, headline locked to maxscore).

## 8. How this maximizes the chance of a strong result without cheating

- The **0.02 FAR buffer** converts the known dominant failure mode (cap overshoot) from ~2-in-3
  (D10/D11 observed) to unlikely, at a bounded recall cost that is inspected on validation first.
- **All tuning lives on validation** (buffer choice, frontier inspection, bootstrap) — that is
  explicitly permitted and documented; the freeze happens before any test read.
- **One variant, one primary rule, one test shot.** No variant shopping, no threshold shopping, no
  post-test adjustment, no "try 0.19 if 0.18 fails."
- **Approval gate between selection and application** creates an auditable freeze point.
- Post-hoc rows stay in a separately labeled table, never mixed with frozen-threshold evidence.
- Full archive: commands, scripts, score files, PROVENANCE.md, split-count assertions (496/44/452
  val; 500/45/455 test) enforced in code; the analysis script reads test files only in the
  application function, verifiable by inspection.

## 9. Honest expectation and decision rule

**Expectation (disclosure, not protocol input):** the historical post-hoc optimum on these exact
test scores is recall 0.800 at FAR 0.200 — the F20 boundary, reached at exactly TP=36/FP=91. A
frozen threshold can only match that if it lands in the same narrow optimal region. Given D10/D11
showed recall optimism of 0.13–0.22, the realistic central outcome is the **near-success band**,
not a clean F20 pass. This should be priced in now so the result is not oversold or spun later.
Additional disclosure for the writeup: Gate 5 rejected this checkpoint under the argmax clean-guard
criteria (test clean accuracy 0.694 < 0.70); the follow-up must present the frozen-threshold result
as operating-point evidence for the thresholded fall-alert rule, alongside that caveat, not as a
reversal of the Gate-5 argmax verdict.

**Decision rule (pre-registered, judged on the primary 0.18-buffered row):**

| Outcome | Criterion (held-out test) | Thesis meaning |
|---|---|---|
| **Success** | recall ≥ 0.80 AND FAR ≤ 0.20 | AFAC-score F20 becomes the headline **frozen validation-threshold** defense result — the strongest defensible claim in the defense chapter; D8b post-hoc row becomes supporting characterization. |
| **Near success** | recall 0.72–0.80 AND FAR ≤ 0.20 | Report as near-F20 locked evidence beside the D8b post-hoc characterization; thesis states that F20 is *characterized* on held-out test scores and *approached but not met* under frozen threshold transfer. |
| **Failure** | recall < 0.72 OR FAR > 0.20 | Thesis states plainly that F20 is reachable only as post-hoc operating-region characterization, not as frozen-threshold transfer — the same honest boundary applied to D10/D11. The negative result is still publishable evidence discipline. |

R90F10: the 0.10-cap row is characterization only; no realistic path expects it here (historical
post-hoc recall at FAR ≤ 0.10 on these scores was ≈ 0.27). Every outcome is reported with exact
counts regardless of band.

## 10. Exact run plan (NOT executed — pending approval)

**Stage 1 (validation only):**
```
.venv/Scripts/python.exe scripts/export_probability_predictions.py \
  --checkpoint checkpoints/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/seed42_optionB_maxscore_best.pt \
  --model lenet --epsilon 0.03 --pgd-steps 10 --run-name optionB_maxscore \
  --out-dir results/afac_score_frozen_threshold_followup/val_eval --split val
```
Then a selection-only analysis script (adapted from
`scripts/analysis/d10_d11_locked_test_followup.py`) that reads ONLY
`val_eval/optionB_maxscore_pgd_probabilities_val_epsilon_0_03.csv`, asserts 496/44/452, and writes
`afac_threshold_selection_validation.csv` (caps 0.18/0.20/0.15/0.10) + bootstrap stability CSV.

**Stage 2 (after Shahram approves the frozen thresholds):**
Application step reads the frozen-selection CSV + the existing test scores at
`results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/test_eval/optionB_maxscore_pgd_probabilities_test_epsilon_0_03.csv`
(and the matching `_clean_` file for the clean-condition check), asserts 500/45/455, applies each
frozen threshold once, and writes: `afac_frozen_threshold_test_metrics.csv`, summary MD/CSV,
FP-source and FN-destination breakdowns, PROVENANCE.md, COMMANDS_RUN.txt, README.md — all under
`results/afac_score_frozen_threshold_followup/`.

**Runtime:** Stage 1 ≈ 3–5 minutes (one CPU inference pass over 496 windows × 3 conditions +
analysis seconds). Stage 2 ≈ seconds (pure score analysis).

**Risk points:** (i) recall cliff at the 0.18 cap on validation → handled at the Stage-1 approval
gate; (ii) temptation to compare the frozen threshold with the known 0.1532 post-hoc value →
pre-committed against; (iii) accidental test regeneration → prohibited, existing Gate-5 files are
the single source; (iv) split mix-ups → hard assertions on window/fall counts in both stages.

**No-test-tuning verification:** the selection script contains no test-file path; the application
script contains no selection logic; both are archived; the frozen thresholds are recorded in the
Stage-1 CSV (and in the approval message to Shahram) *before* Stage 2 runs; single execution of
Stage 2, outputs immutable thereafter.

---

**Recommended primary protocol:** AFAC-score (optionB maxscore, the pre-committed D8b checkpoint),
validation PGD-10 scores at epsilon 0.030, threshold = max validation recall subject to validation
FAR ≤ 0.18 (0.20 target minus a pre-registered 0.02 transfer buffer justified by the measured
D10/D11 validation-to-test FAR overshoot and the binomial SD of FAR on 455 test windows; ties →
lower FAR, then higher threshold), frozen at a documented approval gate, then applied exactly once
to the existing Gate-5 test PGD scores; success judged only on this row per the §9 decision rule.

**Recommended secondary diagnostics:** frozen rows at FAR caps 0.20/0.15/0.10; labeled post-hoc
test characterization for same-footing comparison with the D8b reference; FP-source and
FN-destination breakdowns; validation-vs-test calibration gap; score-distribution summary; binomial
CIs; comparison table vs D8b and D10/D11; optional diagnostics-only maxrec/minFA validation exports
with the headline locked to maxscore.

**Do not run final test until Shahram approves this protocol.**
