# Undefended Baseline vs Frozen AFAC at PGD ε=0.015 — Held-Out Test Comparison

Date: 2026-07-05. Evidence type: **re-analysis of existing saved artifacts only.** No new test
inference was run: the undefended numbers come from the existing Chapter-4 converged epsilon-sweep
summary (`results/converged_attacks/converged_seed42_pgd_epsilon_sweep_test.csv`), and the AFAC
numbers are the already-committed frozen single-read result (`frozen_test_read/`, commit
`2a5c1a0`). No thresholds tuned; the undefended baseline uses its standard argmax
fall-vs-non-fall prediction; the AFAC frozen result is untouched.

Machine-readable twin: `undefended_vs_afac_eps0015_comparison.csv` (this folder).

## 1. Why this comparison is necessary

The frozen H15 pass certifies AFAC at ε=0.015. That claim carries thesis weight only if the
undefended baseline does *not* already satisfy H15 at the same attack strength — otherwise the
defense would be taking credit for an operating point the attack never threatened. This memo
pins the exact ε=0.015 undefended row from existing artifacts.

## 2. Existing thesis evidence: undefended PGD collapses before ε=0.015

Confirmed from the same Chapter-4 sweep artifact: at **ε=0.0075** the undefended seed-42
baseline is already at **fall recall 0.000** (TP 0/45, FN 45, FP 34, TN 421; accuracy 0.112).
The ε=0.015 row is therefore beyond the collapse point, consistent with the thesis's existing
claim that undefended PGD reaches zero fall recall by ε=0.0075.

## 3. Exact undefended ε=0.015 result (existing artifact — no new run needed)

Row `epsilon=0.015000`, `split=test`, `converged_seed42_pgd_epsilon_sweep_test.csv`
(500 windows: 45 fall / 455 non-fall; PGD-10, α=ε/6; argmax decision rule):

| Quantity | Value |
|---|---|
| 7-class accuracy | **0.008** |
| TP / FN / FP / TN | **0 / 45 / 47 / 408** |
| Fall recall | **0.000** |
| Missed-fall rate | **1.000** |
| FAR (false-positive rate) | **0.1033** |
| H15 | **FAIL** (TP 0 ≪ 39) — total collapse |

Cross-seed footnote (same artifact family): seed43 0/45/63/392 (FAR 0.139), seed44 0/45/51/404
(FAR 0.112) — recall 0.000 at ε=0.015 for all three undefended seeds. Clean reference (ε=0,
seed42): 43/2/0/455 — recall 0.956, FAR 0.000, accuracy 0.970.

## 4. Frozen AFAC ε=0.015 result (single pre-registered read; unchanged)

| Quantity | Value |
|---|---|
| TP / FN / FP / TN | 41 / 4 / 60 / 395 |
| Fall recall | 0.9111 (Wilson 95% CI 0.793–0.965) |
| FAR | 0.1319 (Wilson 95% CI 0.104–0.166) |
| H15 | **PASS** (TP 41 ≥ 39, FP 60 ≤ 68), frozen tau 0.168754 |
| Clean at same tau | 44/1/41/414 — recall 0.978, FAR 0.090 |

## 5. Direct safety-proxy improvement at PGD ε=0.015 (held-out test, seed42)

| Delta (undefended argmax → AFAC frozen threshold) | Value |
|---|---|
| TP gain | **+41** (0 → 41 of 45) |
| FN reduction | **−41** (45 → 4); missed-fall rate 1.000 → 0.089 |
| Recall improvement | **+0.9111** (0.000 → 0.9111) |
| FP / FAR change | +13 FP (47 → 60); FAR 0.1033 → 0.1319 (both < 0.15) |
| H15 status | **FAIL → PASS** |

The defense converts a total detection collapse into an H15-satisfying operating point at the
cost of +13 false alarms per 455 non-fall windows, with FAR remaining under the 0.15 bar.

## 6. Thesis-safe wording

- "At PGD ε=0.015 (PGD-10, α=ε/6, white-box, digital-domain, window-level, held-out 500-window
  test split), the undefended converged seed-42 baseline's argmax rule detects 0 of 45 fall
  windows (recall 0.000, FAR 0.103, accuracy 0.008), while the AFAC-score defense with its
  pre-registered frozen validation-selected threshold (tau = 0.168754) detects 41 of 45
  (recall 0.911, FAR 0.132), meeting the H15 operating target (recall > 0.85, FAR < 0.15) in a
  single pre-registered test read."
- "The undefended baseline is already at zero fall recall by ε=0.0075; ε=0.015 lies beyond its
  collapse point (recall 0.000 for all three undefended seeds)."
- Required accompanying disclosures wherever the claim appears: (a) ε=0.015 was selected by a
  validation-only epsilon frontier search; H15 remains unmet at ε=0.030, where the ledger's F20
  evidence stands unchanged; (b) the comparison pairs the baseline's argmax rule against the
  defense's score-threshold rule — it is a system-level (model + decision rule) comparison, and
  the baseline has no comparable validation-calibrated threshold protocol; (c) Gate-5 argmax
  caveat for the AFAC checkpoint (clean 7-class accuracy 0.694 < 0.70); (d) single seed (42),
  LeNet family, not clinical, not deployment-validated, not certified.

## 7. Forbidden wording

- Any claim that AFAC is "adversarially robust", "solves" or "defeats" PGD, or is "certified" —
  the result is one operating point at one epsilon under one attack configuration.
- Any H15 claim at ε=0.030, or wording implying the ε=0.030 story changed — it did not.
- Omitting that ε=0.015 was chosen by a validation-only search (silently presenting it as the
  study's canonical evaluation point).
- "The defense improves recall by 91 percentage points under attack" *without* stating the
  argmax-vs-threshold decision-rule difference and the FAR cost.
- Any generalization across seeds, architectures, datasets, physical/over-the-air settings, or
  clinical deployment.
- Calling the undefended FAR (0.103) "safe" or "acceptable" — with recall 0.000 the undefended
  system misses every fall while still raising false alarms; its FAR is not a virtue.

---

### Final printed summary

1. Undefended PGD ε=0.015 TP/FN/FP/TN: **0 / 45 / 47 / 408** (existing Chapter-4 artifact,
   seed42; seeds 43/44 also at recall 0.000).
2. Undefended PGD ε=0.015 recall and FAR: **recall 0.000, FAR 0.1033** (accuracy 0.008).
3. Undefended H15: **FAIL** (total collapse; already at recall 0.000 by ε=0.0075).
4. AFAC PGD ε=0.015 TP/FN/FP/TN: **41 / 4 / 60 / 395** (frozen tau 0.168754, single
   pre-registered read).
5. AFAC recall and FAR: **0.9111 and 0.1319**.
6. Claim allowed: **YES** — with the §6 disclosures (validation-selected ε, decision-rule
   difference, Gate-5 caveat, single-seed/claim-boundary limits); forbidden wordings in §7.
