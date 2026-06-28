# Option B seed-42 — Gate-5 held-out test evaluation review

> **Held-out TEST evaluation of existing checkpoints — no training, no new pilot, no seed44/45/46, no
> A1/A2/A0/H2/H3, no `.tex` edit, no A1/G1/H1 change.** Evaluates the three committed Option B seed-42
> validation-selected checkpoints (maxscore / maxrec / minFA) on the held-out test split (n=500: 45 fall /
> 455 non-fall), ε=0.030, via the committed `export_probability_predictions.py` (unmodified). Window-level,
> digital-domain, white-box, processed CSI. **No product / clinical / deployment / certified / over-the-air
> claim.** The joint target (PGD recall > 80% AND FAR < 10%) remains **unmet**.

## Commands and exit codes

For each `cand` in {maxscore, maxrec, minFA} (all exit **0**):
```
.venv\Scripts\python.exe scripts\export_probability_predictions.py \
  --checkpoint checkpoints\...\adaptive_lagrangian_far_constrained\optionB\seed42\seed42_optionB_<cand>_best.pt \
  --model lenet --run-name optionB_<cand> --out-dir results\...\optionB\seed42\test_eval \
  --split test --epsilon 0.03 --pgd-steps 10
```
`last` was **NOT** evaluated (all three primary candidates evaluated; no diagnostic fallback needed).

## Files created (9 per-window CSVs)

`test_eval/optionB_{maxscore,maxrec,minFA}_{clean,fgsm,pgd}_probabilities_test_epsilon_0_03.csv`.
Test split confirmed for every export: **500 windows, 45 fall, 455 non-fall.**

## Held-out test metrics

| checkpoint (epoch) | clean acc | clean mF1 | clean FR | PGD-10 recall | PGD TP/FN | PGD FP | PGD FAR (/455) | FGSM recall | FGSM FP |
|---|---|---|---|---|---|---|---|---|---|
| maxscore (68) | 0.694 | 0.653 | 0.956 (43/45) | 0.422 (19/45) | 19/26 | 59 | 13.0% | 0.644 | 41 |
| maxrec (70) | 0.668 | 0.640 | 0.933 (42/45) | 0.667 (30/45) | 30/15 | 85 | 18.7% | 0.756 | 60 |
| minFA (66) | 0.698 | 0.673 | 0.911 (41/45) | 0.133 (6/45) | 6/39 | 36 | **7.9%** | 0.378 | 23 |

## Classification (pre-registered criteria; three-pronged clean guard acc≥0.70 ∧ mF1≥0.65 ∧ clean FR≥0.90)

| checkpoint | clean guard | verdict | reason |
|---|---|---|---|
| maxscore | **FAIL** (acc 0.694 < 0.70) | **REJECT** | guard fails on test; PGD recall 0.422 < 0.60 |
| maxrec | **FAIL** (acc 0.668 < 0.70, mF1 0.640 < 0.65) | **REJECT** | guard fails; PGD FP 85 > 65 (FAR 18.7%) |
| minFA | **FAIL** (acc 0.698 < 0.70) | **REJECT** | guard fails; PGD recall 0.133 (FP controlled by recall collapse) |

**All three REJECT.** The clean guard that held on *validation* (acc 0.70–0.726) **fails on test** (acc
0.668–0.698) for every checkpoint — the same validation→test generalization gap that rejected A1.

## Comparison (held-out TEST, like-for-like)

| model | clean acc | PGD recall | PGD FP | PGD FAR | clean guard | status |
|---|---|---|---|---|---|---|
| G1 seed42 | 0.716 | 0.689 | 104 | 22.9% | held | validated point |
| G1 seed44 | 0.746 | 0.600 (27/45) | 65 | 14.3% | held | validated point |
| A1 seed42 | 0.678 | 0.556 | 68 | 15.0% | **failed** | REJECT |
| **Option B maxscore** | 0.694 | 0.422 | 59 | 13.0% | **failed** | REJECT |
| **Option B maxrec** | 0.668 | **0.667** | 85 | 18.7% | **failed** | REJECT |
| **Option B minFA** | 0.698 | 0.133 | 36 | **7.9%** | **failed** | REJECT |

## Frontier comparison vs the BEST PRIOR point (the correct baseline)

The right baseline is **not A1** (itself a rejected point) but the **best prior validated frontier**:

> **G1 seed44 — PGD recall 0.600, FP 65/455 (FAR 14.3%), clean guard held.**

Option B must be judged against that point. Held-out test, per checkpoint vs G1 seed44:

| Option B ckpt | recall vs 0.600 | FP vs 65 | clean guard | net vs G1 seed44 |
|---|---|---|---|---|
| maxscore | 0.422 (**worse**, −0.178) | 59 (slightly lower) | **fails** (acc 0.694) | **worse** — recall drops far more than the small FP gain; guard breaks |
| maxrec | 0.667 (**higher**, +0.067) | 85 (**much worse**, +20) | **fails** (acc 0.668, mF1 0.640) | **worse** — recall gain bought with +20 FP and a broken guard |
| minFA | 0.133 (**collapse**) | 36 (lower, FAR 7.9%) | **fails** (acc 0.698) | **worse** — sub-10% FAR only via recall collapse |

**Interpretation (the key rule — not celebrating one metric):**
- **Option B does not beat the best prior frontier (G1 seed44).** No checkpoint matches *both* recall ≥ 0.600
  *and* FP ≤ 65 with the clean guard intact.
- **maxrec** improves recall over G1 seed44 (0.667 vs 0.600) **but with much higher FP (85 vs 65) and a failed
  clean guard** — a dominated trade, not a frontier gain.
- **maxscore** lowers FP slightly vs G1 seed44 (59 vs 65) **but recall drops too much (0.422) and the clean
  guard fails.**
- **minFA** reaches sub-10% FAR (7.9%) **but only by recall collapse (0.133).**
- **No checkpoint approaches the final target (recall ≥ 0.80 ∧ FP ≤ 45).** Best test recall is 0.667, at FP 85.

**Therefore Option B is REJECT / informative negative — NOT minimum useful.** The adaptive FAR controller can
reach low FAR on test, but only by collapsing recall; the two tails still trade and the clean guard does not
generalize from validation to test. The best prior frontier (G1 seed44) is **not** advanced.

## Final Option B verdict

**REJECT — informative-negative / partial result.** The adaptive-Lagrangian mechanism worked mechanically
(λ_b tracked FAR, stayed bounded in ≈0.21–0.26, never hit the cap) and produced a within-guard sub-10% FAR
point *on validation*, but on the **held-out test**: (1) the clean guard fails for all three checkpoints
(acc < 0.70), and (2) no checkpoint reaches even minimum-useful (recall ≥ 0.60 ∧ FP ≤ 65 ∧ guard). Measured
against the **best prior frontier (G1 seed44: 0.600 / FP 65, guard held)**, Option B does **not** advance it —
every checkpoint is dominated (lower recall, or much higher FP, and a broken guard). The joint
> 80%-recall / < 10%-FAR target remains **unmet**. Feedback control of `λ_b` did not, on its own, separate the
two tails.

## Diagnostic recommendation (analysis-only; uses the existing test_eval CSVs)

Before abandoning the line, run an **analysis-only** diagnostic on the already-created
`optionB_{maxscore,maxrec,minFA}_{clean,fgsm,pgd}_*_test_*.csv` files (no training, no new attacks, no new
checkpoints):

1. **Threshold / frontier sweep** on the PGD test probabilities (`fall_probability` column) for each
   checkpoint: sweep the fall-decision threshold and trace the (TP, FP) curve.
2. **Target reachability:** determine whether *any* threshold on *any* checkpoint yields **TP ≥ 37/45 AND
   FP ≤ 45/455** simultaneously (the joint target), and report the closest achievable (TP, FP) point.
3. **Distribution overlap:** summarize the attacked **fall-score** distribution (P(fall) on adv fall windows)
   vs the attacked **non-fall fall-score** distribution (P(fall) on adv non-fall windows) — quantify the
   overlap that bounds any threshold (e.g. medians/IQRs, and FP at the threshold achieving TP=37).
4. **Validation vs test gap:** tabulate clean acc, PGD recall, FP, FAR on validation (from the committed
   training log) vs test (these CSVs) for each checkpoint, to quantify the clean-guard generalization gap.
5. **Error-routing analysis:** for missed falls, tabulate the predicted class (where falls are misrouted
   under PGD); for false alarms, tabulate the true source class (which non-fall classes become fall) — using
   `predicted_label` / `true_label` in the CSVs.

This is purely post-hoc analysis of committed outputs; it **cannot** create true positives or change the
verdict, but it tells us *why* the frontier is stuck and whether post-hoc thresholding could ever reach the
target.

**Diagnostic run** (analysis-only): `python scripts/analyze_optionB_test_frontier.py` — reads the 9 test
CSVs + the committed training log; outputs under `test_eval/diagnostics/`
(`optionB_threshold_frontier_sweep.csv`, `optionB_score_distribution_summary.csv`,
`optionB_val_vs_test.csv`, `optionB_error_routing.csv`, `optionB_frontier_diagnostic_summary.md`). No torch,
no attacks, no checkpoint loading.

### Diagnostic findings

**(1) Post-hoc thresholding CANNOT reach the joint target.** A one-vs-rest threshold sweep on the PGD
`P(fall)` finds **no threshold on any checkpoint** giving TP ≥ 37 *and* FP ≤ 45:

| ckpt | FP needed to reach TP=37 | best recall at FP ≤ 45 |
|---|---|---|
| maxscore | **FP = 95** | TP 12/45 (0.27) |
| maxrec | **FP = 107** | TP 15/45 (0.33) |
| minFA | **FP = 122** | TP 11/45 (0.24) |

To detect 37/45 falls under PGD, **every** checkpoint must accept ≥ 95 false alarms (2–3× the 45 budget);
holding FP ≤ 45 caps recall at ~0.24–0.33. **The failure is representation / frontier-level, not
checkpoint-selection or threshold choice.**

**(2) Cause = score-distribution overlap.** Under PGD the attacked **fall** `P(fall)` is dragged down
(median 0.20 / 0.27 / 0.13 for maxscore / maxrec / minFA) into the **upper tail of the attacked non-fall**
`P(fall)` (non-fall q3 = 0.11 / 0.15 / 0.066). The true-fall and non-fall fall-score masses overlap heavily,
so no single threshold separates them — exactly the two-tail-overlap problem.

**(3) Validation operating points generalize poorly to test.** Clean acc drops val→test for all three
(0.726→0.694, 0.718→0.668, 0.704→0.698), pushing every checkpoint **below the 0.70 clean guard on test**;
PGD FP rises val→test (55→59, 76→85, 33→36). The validation-selected points do **not** transfer.

**(4) Error routing confirms the fall↔motion boundary.** Missed falls under PGD are predicted mostly as
**walk / run** (e.g. minFA: 21 run, 6 walk; maxscore: 12 walk, 10 run); false alarms originate mostly from
**run / walk** (e.g. maxrec: 33 run, 24 walk). The confusion is concentrated at the fall↔walk/run boundary,
as in prior variants — not spread across unrelated classes.

**Bottom line:** Option B is **representation-frontier-limited**. Post-hoc thresholding cannot rescue it, the
clean guard does not generalize, and Option B remains **dominated by G1 seed44**. The diagnostic does not
change the **REJECT** verdict.

## No-claim boundary

- **No thesis claim. No clinical claim. No deployment / product claim. No certified-robustness claim. No
  over-the-air (OTA) claim. The held-out test verdict is a REJECT.**
- Window-level, digital-domain, white-box, benchmark-level, research-stage.

## Recommendation

**Commit as an informative-negative / partial result** (the honest record: validation-selected Option B
checkpoints fail the clean guard and minimum-useful on held-out test, and the frontier diagnostic shows
post-hoc thresholding cannot reach the target). Do **not** present Option B as a success or minimum-useful
result.

The diagnostic sharpens the root cause: the limit is **representation / frontier-level**, not
checkpoint-selection — under PGD the attacked fall-score collapses into the non-fall upper tail, so **no
threshold reaches TP ≥ 37 ∧ FP ≤ 45** (TP=37 costs FP ≥ 95). Combined with the **validation→test clean-guard
generalization gap**, this means **further reweighting the same two TopK tails on LeNet is unlikely to help**.
Candidate future directions (each separately pre-registered) should target the *representation*: e.g.
architecture/capacity changes (ResNet/GRU/BiLSTM) or temporal/event-level aggregation at the fall↔walk/run
boundary, and addressing clean-guard generalization (regularization) — **not** another static/adaptive
loss-reweighting on the current LeNet frontier.

### Scope reminder
Held-out test evaluation of existing checkpoints only — no training / new pilot / seed44-46 / A-variants /
`.tex` / A1-G1-H1 change. Records the Gate-5 REJECT verdict for Option B seed-42; recommends committing it as
an informative negative. Starts nothing further.
