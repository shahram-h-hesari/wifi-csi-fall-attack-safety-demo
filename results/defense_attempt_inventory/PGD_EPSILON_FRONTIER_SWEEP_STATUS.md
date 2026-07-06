# PGD Epsilon Frontier Sweep — Status (validation-only) — SEARCH COMPLETE

Date: 2026-07-05. Rounds complete: **ε = 0.015, 0.0225, 0.02625, 0.024375**. Validation split
only (496 windows, 44 fall / 452 non-fall). No test file opened; no training; thresholds
selected on validation with the frozen ledger rule (max recall s.t. FAR ≤ cap; tie-break lower
FAR, then higher tau). Attack: PGD-10, α = ε/6, byte-identical frozen pipeline
(`export_probability_predictions.py --split val`).

Targets on validation: **H15** = recall > 0.85 AND FAR < 0.15 (cap-0.15 operating point).
**F20** = recall ≥ 0.80 AND FAR ≤ 0.20 (cap-0.20 point).

## Artifacts exported

- `val_sweep/eps0015/`, `val_sweep/eps00225/`, `val_sweep/eps002625/` (5 models each),
  `val_sweep/eps0024375/` (3 surviving candidates), with per-round analysis CSVs
  `eps*_frontier_results.csv`. D14B_seed44 and GR1_macroF1 were not rerun at 0.024375 (both
  already failed H15 at 0.0225, below this probe).

## Round 4 results — ε = 0.024375 (three surviving candidates)

| Model | recall@FAR≤0.10 | recall@FAR≤0.15 (realized FAR, TP) | recall@FAR≤0.20 | val AUROC | H15 | F20 |
|---|---|---|---|---|---|---|
| AFAC_maxscore | **0.773** | **0.864** (0.142, TP 38/44) | 0.886 | **0.9110** | **PASS** | PASS |
| ST1b6_lowFA | 0.523 | 0.795 (0.142, TP 35) | **0.955** | 0.9035 | fail | PASS |
| SA1_lowFA | 0.636 | 0.795 (0.139, TP 35) | **0.955** | 0.9048 | fail | PASS |

1. **H15 at ε=0.024375:** AFAC_maxscore **PASS** (0.864 > 0.85 at FAR 0.142); ST1b6_lowFA and
   SA1_lowFA FAIL (0.795).
2. **F20 at ε=0.024375:** all three PASS.
3. **Best recall @ FAR≤0.10:** AFAC_maxscore, 0.773.
4. **Best recall @ FAR≤0.15:** AFAC_maxscore, 0.864.
5. **Best recall @ FAR≤0.20:** ST1b6_lowFA / SA1_lowFA, 0.955.
6. **Best candidate at ε=0.024375:** **AFAC_maxscore** — the only H15 pass, plus best @0.10,
   @0.15, and AUROC.

## Frontier state after round 4

| ε | H15 on validation | Source |
|---|---|---|
| 0.000 | PASS (all 24 saved axes) | saved clean exports |
| 0.015 | PASS (all 5 candidates) | round 1 |
| 0.0225 | PASS (3/5: AFAC, ST1b6, SA1) | round 2 |
| **0.024375** | **PASS (1/3: AFAC only)** | **round 4** |
| 0.02625 | FAIL (0/5) | round 3 |
| 0.030 | FAIL (all 24 saved axes) | saved PGD exports |

7. **Updated H15 epsilon brackets (validation):**

| Scope | Bracket (last pass, first fail) |
|---|---|
| **Program-level (= AFAC_maxscore)** | **(0.024375, 0.02625)** |
| AFAC_maxscore | (0.024375, 0.02625) |
| ST1b6_lowFA | (0.0225, 0.024375) |
| SA1_lowFA | (0.0225, 0.024375) |
| D14B_seed44 | (0.015, 0.0225) — from rounds 1–2 |
| GR1_macroF1 | (0.015, 0.0225) — from rounds 1–2 |

## 8. Practical stopping decision — STOP: the frontier is resolved to data resolution

At least one candidate passes at 0.024375, so the H15 validation frontier is
**ε* ≈ 0.024–0.026 for the best model (AFAC_maxscore)**, and ≈ 0.023–0.024 for ST1b6/SA1.

**Another bisection is NOT scientifically useful.** AFAC's pass at 0.024375 is TP = 38/44 —
recall 0.8636 against a bar of >0.85, i.e., **exactly one fall window above the threshold**
(37/44 = 0.841 fails). With 44 validation falls, one window = 0.0227 recall; the bracket width
(0.001875 in ε) now corresponds to sub-window movements in score space. A further probe at
ε = 0.0253125 would measure where one specific window crosses one threshold — attack-strength
quantization noise, not a property of the model. The binomial 95% CI on recall 0.864 at n=44 is
roughly ±0.10, an order of magnitude wider than what further bisection would resolve.

**Frontier conclusion (validation, PGD-10, α=ε/6, LeNet defense family):**
- H15 achievable: ε ≤ ~0.024 (AFAC_maxscore, with ST1b6/SA1 dropping out by ~0.023–0.024).
- Only F20 achievable: ~0.024 < ε ≤ 0.030 (all healthy candidates hold F20 through 0.030 on
  validation; known caveat below).
- Neither: not observed up to 0.030 for F20; beyond 0.030 unmeasured.

9. **Exact next command:** none recommended — the search is complete at data resolution. If a
   fifth probe is nevertheless desired for symmetry, it would be
   (`--epsilon 0.0253125`, out-dir `val_sweep/eps00253125`, AFAC checkpoint) — **DO NOT RUN
   WITHOUT APPROVAL**, and note it cannot change the substantive conclusion above.

Standing caveat (motivation-context, not used for selection): validation success at ε=0.030
previously did not transfer to the held-out test split. Any test-level claim at any chosen ε
(including an H15 claim at ε≈0.024) requires a separately frozen protocol — checkpoint, ε,
threshold rule, and decision bands pre-registered — and one test read. This sweep provides the
validation frontier only.
