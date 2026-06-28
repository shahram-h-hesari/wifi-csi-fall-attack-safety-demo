# Option B seed-42 pilot — validation-only interim result

> **VALIDATION-ONLY interim result — NOT a held-out test verdict.** No held-out test evaluation, no additional
> training, no seed 44/45/46, no A1/A2/A0/H2/H3, no `.tex` edit, no A1/G1/H1 change. All metrics below are on
> the **validation** split (496 windows, 44 falls / 452 non-fall); the pre-registered success criteria are
> **test-based** and remain **pending a separate Gate-5 approval**. Window-level, digital-domain, white-box,
> processed CSI; ε=0.030. **No product / clinical / deployment / certified / over-the-air claim.** The joint
> target (PGD recall > 80% AND FAR < 10%) remains **unmet**.

## 1. Exact command

```
.venv\Scripts\python.exe scripts\train_optionB_adaptive_lagrangian.py --setting optionB --seed 42 --pilot
```

## 2. Exit code and runtime

- Exit code **0**.
- **70/70 fixed epochs** completed.
- ≈ **6098 seconds** (~1.7 h, CPU).
- **No stop condition** (no NaN/inf, no missing PGD metrics, no split mismatch, no all-zero term, no
  unauthorized seed/setting, no test access, no sign-check failure).

## 3. Pinned configuration (confirmed in metadata)

| knob | value |
|---|---|
| setting | optionB |
| seed | 42 only |
| schedule | **fixed 70 epochs** |
| early_stopping | **false** |
| patience / min_epochs | **inactive (not used)** |
| train epsilons | `{0.005, 0.015, 0.03}` |
| `lambda_b0` | 0.25 |
| `eta` | 0.10 |
| `lambda_b_max` | 1.0 |
| `lambda_r` | 1.0 |
| `k_abs_min` | 4 |
| `target_far` | 0.10 |
| `N_val_nonfall` | 452 |
| `test_set_used` | **false** |

## 4. Files created

- `logs/seed42_optionB_training_log.csv` (per-epoch: λ_b current/next, FAR, N_val_nonfall, PGD FP/recall,
  clean acc/mF1/clean-FR, budget/rescue losses + ratio, fall-selected count, floor-active fraction, guard
  eligibility, selection score).
- `analysis/seed42_optionB_selection_candidates.csv` (selected epochs for maxscore / maxrec / minFA).
- `metadata/seed42_optionB_metadata.json`.
- **Checkpoints (gitignored, not committed):** `seed42_optionB_maxscore_best.pt`,
  `seed42_optionB_maxrec_best.pt`, `seed42_optionB_minFA_best.pt`, `seed42_optionB_last.pt`.

## 5. Validation-selected checkpoint summary (validation; 44 falls / 452 non-fall)

| candidate | epoch | PGD recall | FP | FAR | clean acc | mF1 | clean FR | guard | score |
|---|---|---|---|---|---|---|---|---|---|
| maxscore | 68 | 0.500 (22/44) | 55 | 12.2% | 0.726 | 0.712 | 0.955 | pass | 0.413 |
| maxrec | 70 | 0.614 (27/44) | 76 | 16.8% | 0.718 | 0.711 | 0.932 | pass | 0.341 |
| minFA | 66 | 0.205 (9/44) | 33 | **7.3%** | 0.704 | 0.709 | 0.909 | pass | 0.205 |

All three pass the three-pronged clean guard (acc ≥ 0.70, mF1 ≥ 0.65, clean fall recall ≥ 0.90) on validation.

## 6. Adaptive lambda_b behaviour

- Started at **0.25**, drifted to ≈ **0.21** mid-training, ended ≈ **0.257**.
- Stayed in a narrow **≈ 0.21–0.26** band; **never approached the cap (1.0)**.
- Tracked the validation FAR around the 0.10 boundary as designed (rose when FAR > 0.10, relaxed when
  FAR < 0.10), keeping budget pressure modest rather than over-suppressing recall.

## 7. Interpretation

- The **adaptive controller worked mechanically**: λ_b moved with FAR once per epoch, stayed bounded, and the
  **clean guard held** for the selected checkpoints (eligible repeatedly from ~epoch 59 on; clean acc up to
  0.742).
- **minFA achieved a sub-10% validation FAR (7.3%) within the clean guard** — an operating regime A1 never
  reached within guard.
- **maxrec reached validation recall above 0.60 (0.614)** — but at **FAR 16.8%**.
- **No single checkpoint achieved PGD recall ≥ 0.60 AND FAR ≤ 10% together** on validation (the two tails
  still trade: low FAR ⇒ low recall; high recall ⇒ high FAR).
- **Therefore Option B is not a validation-level success yet.** The mechanism is better-controlled than A1
  (clean guard held; a within-guard sub-10% FAR point exists) but does not separate the tails enough to meet
  the joint target.
- **The held-out test verdict is pending and must be Gate 5.** These validation numbers are selection
  signals, not the pre-registered test outcome.

## 8. Comparison (⚠️ Option B = validation; A1/G1 = committed TEST — not directly interchangeable)

| model | recall | FP | FAR | clean guard | basis |
|---|---|---|---|---|---|
| A1 seed42 | 0.556 | 68 | 15.0% | **failed** (acc 0.678) | test |
| G1 seed44 | 0.600 (27/45) | 65 | 14.3% | held | test |
| **Option B val maxrec (ep70)** | 0.614 (27/44) | 76 | 16.8% | pass | **validation** |
| **Option B val minFA (ep66)** | 0.205 (9/44) | 33 | **7.3%** | pass | **validation** |

**Validation and test metrics are not directly interchangeable** (different split, n=496 vs 500, 44 vs 45
falls; the clean guard A1 passed on validation but failed on test). Option B's apparent edge — a within-guard
sub-10% FAR point and a recall-0.61 within-guard point — must be confirmed on the held-out test before any
comparison to A1/G1 is meaningful.

## 9. No-claim boundary

- **No thesis claim.**
- **No clinical claim.**
- **No deployment / product claim.**
- **No certified-robustness claim.**
- **No over-the-air (OTA) claim.**
- **No held-out test evaluation has been run.**
- Window-level, digital-domain, white-box, research-stage; the joint > 80%-recall / < 10%-FAR target is
  **unmet**.

## 10. Recommended next step

- A **separate Gate-5 held-out test evaluation** of the validation-selected checkpoints (e.g. a minimal
  kill-check on `maxscore`/`maxrec`, mirroring the A1 kill-check, or the fuller suite incl. PGD-20 +
  confidence inversion), reusing `export_probability_predictions.py --split test` unmodified.
- **Do NOT run it until separately approved.** This interim review records the validation pilot only.

### Scope reminder
Validation-only interim result — no held-out test evaluation / additional training / seed44-46 / A-variants /
`.tex` / A1-G1-H1 change. Records the Option B seed-42 pilot validation outcome; the test verdict awaits a
separate Gate-5 approval. Starts nothing further.
