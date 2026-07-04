# D13 Step 0A/0B — Validation-Only Complementarity + Transfer Audit

Diagnostic-only audit deciding whether AFAC-score, D10 (GAIRAT GR1_v2macroF1), and D11b (SAT
SA1_v2lowFA) have enough validation-only complementarity to justify a later, separately
pre-registered Stage 1 score-fusion experiment. **Cannot claim F20.** Validation-only throughout;
no test-split file was opened at any point (grep-verified before each script ran).

**GATE RESULT: FAIL.** The mandatory shared-input transfer veto (mean off-diagonal fall recall must
exceed mean diagonal fall recall by >= 0.15) narrowly failed (observed gap 0.1478, short of 0.15 by
0.0022, roughly one fall window out of 44), which per the pre-registered rule fails the entire gate
regardless of the otherwise-favorable Oracle-B complementarity signal (+4 TP gain, 82% bootstrap
stability). **No Stage 1 score-fusion experiment is authorized on this evidence.**

## Contents

| File | What it is |
|------|-----------|
| `D13_STAGE0_COMPLEMENTARITY_AUDIT.md` | Full report: inputs, per-model metrics, overlap, correlations, vote patterns, oracles, P0 probe, bootstrap, transfer matrix, gate result, interpretation |
| `d13_stage0_model_metrics.csv` | Per-model TP/FN/FP/TN/recall/FAR/precision/F1/AUROC/pAUC at FAR caps 0.18 and 0.20 |
| `d13_stage0_overlap_metrics.csv` | Pairwise + three-way FP/FN Jaccard overlap and raw intersection/union counts |
| `d13_stage0_fp_fn_breakdown.csv` | FP true-class source and FN argmax-destination breakdown per model |
| `d13_stage0_rank_correlations.csv` | Spearman score correlations (all validation; fall+run+walk subset) |
| `d13_stage0_vote_patterns.csv` | 8-pattern binary-decision table with support, source/destination breakdowns, UNSTABLE flag |
| `d13_stage0_oracle_bounds.csv` | Oracle A (naive, unattainable) and Oracle B (pattern-level, decision-fusion bound) at both FAR caps |
| `d13_stage0_p0_probe.csv` | Zero-parameter equal-weight ECDF-mean score-fusion probe |
| `d13_stage0_bootstrap_summary.csv` | Stratified bootstrap (2,000 resamples) CIs and gain-stability fractions |
| `d13_stage0_transfer_matrix.csv` | 3x3 shared-input transfer matrix (eval model x source-of-adversarial-example model) |
| `d13_stage0_transfer_validity_summary.json` | Diagonal validity check detail + transfer veto computation |
| `d13_stage0_fp_fn_sets.json` | Raw FP/FN window-ID sets per model + 2-fold cross-fit detail (NOISE-DOMINATED, not used for gating) |
| `PROVENANCE.md` | Input files, checkpoints, protocol, threshold-rule distinction, explicit non-actions |
| `COMMANDS_RUN.txt` | Exact commands executed, including pre-execution test-file self-checks |
| `d13_stage0_ledger_entry.md` | Short ledger-style entry summarizing this diagnostic for future reference |
| `scripts/d13_stage0_complementarity_audit.py` | Step 0A script (copy, unmodified) |
| `scripts/d13_stage0_transfer_audit.py` | Step 0B script (copy, unmodified) |

## Key numbers

- Best single model at FAR<=0.18: **D11b**, recall 0.8182 (TP 36/44).
- Oracle-B (pattern-level decision-fusion bound) gain over best single: **+4 TP**, stable in 82.05%
  of bootstrap resamples.
- P0 (zero-parameter score-fusion probe) gain over best single at FAR<=0.18: **−2 TP** (P0 does not
  realize the oracle's gain via naive averaging at this cap).
- Shared-input transfer veto: mean diagonal recall 0.7727, mean off-diagonal recall 0.9205, gap
  0.1478 — **fails** the required >= 0.15 bar by 0.0022.
- Diagonal validity check: **exact match** (diff = 0 in every cell) — Step 0B is valid, not
  `STEP0B_INVALID`.

## Evidence-type note

Every number in this folder is validation-only diagnostic evidence. Nothing here is held-out test
evidence, and nothing here authorizes a Stage 1 fusion experiment on the held-out test split.
