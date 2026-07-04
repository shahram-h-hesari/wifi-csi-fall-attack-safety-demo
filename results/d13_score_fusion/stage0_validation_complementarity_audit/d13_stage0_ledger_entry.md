## D13 — Score-fusion complementarity/transfer audit (Step 0A/0B)

**Evidence level:** Validation-only diagnostic (not test evidence; not a defense result; cannot
claim F20).

**Models audited:** AFAC-score (`optionB_maxscore`, D8b reference), D10 (GAIRAT `GR1_v2macroF1`),
D11b (SAT `SA1_v2lowFA`). PGD epsilon = 0.030.

**Purpose:** decide whether these three models have enough validation-only complementarity to
justify a later, separately pre-registered Stage 1 score-fusion experiment.

**Result:** best single model at FAR<=0.18 is D11b (recall 0.8182). Pattern-level decision oracle
(Oracle B) gains +4 TP over the best single model, stable across 82.05% of stratified bootstrap
resamples — a favorable complementarity signal on its own. However, the mandatory shared-input
transfer veto (mean off-diagonal fall recall must exceed mean diagonal fall recall by >= 0.15, to
guard against complementarity that is an artifact of independently-crafted per-model adversarial
examples rather than genuine, shared-input-robust diversity) **narrowly failed**: observed gap
0.1478 against a required 0.15 (short by 0.0022, ~1 fall window out of 44). The diagonal validity
check (each model's own regenerated adversarial examples must reproduce its saved-score confusion
counts within +/-2) passed exactly (diff = 0 in every cell), so this is a clean, valid failure, not
an inconclusive one.

**GATE RESULT: FAIL.** Per the pre-registered rule, a failed transfer veto fails the gate
regardless of Oracle-B's or the zero-parameter P0 probe's gains. **No Stage 1 score-fusion
experiment is authorized on this evidence.**

**Full report:** `D13_STAGE0_COMPLEMENTARITY_AUDIT.md` in this folder
(`results/d13_score_fusion/stage0_validation_complementarity_audit/`).

**Lesson:** the three candidate models show real decision-level complementarity (especially in
their missed-fall sets, three-way Jaccard 0.11) and their scores correlate highly (Spearman
0.89-0.92), but this complementarity does not clear the bar required to trust it against a shared
adversarial input, which is the realistic threat model for any deployed fused rule. Revisiting this
audit would need either a materially larger transfer gap or a fourth, more architecturally distinct
candidate model.
