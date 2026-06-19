# Multi-Seed Runtime Log (Priority 1 Reliability Study)

Runtime / reproducibility record for the Priority 1 multi-seed converged
UT-HAR/SenseFi LeNet pipeline (clean baseline + FGSM/PGD attacks + FGSM-AT
defense). These are **wall-clock timings only**, for the thesis reproducibility
section — not experimental results and not safety-proxy metrics.

## Environment
- Device: **CPU** (`torch.cuda.is_available() == False`)
- Interpreter for stages: repo venv `.venv\Scripts\python.exe`, torch `2.12.0+cpu`
- Orchestrator launched with global Python 3.10 via
  `scripts/run_multiseed_converged_pipeline.py --python-exe .venv\Scripts\python.exe`
- Split sizes: train 3977 / val 496 / test 500 (fall = 45 in test)
- Hyperparameters: clean & defense max-epochs 200, patience 20; FGSM-AT
  train-epsilon 0.03, loss weights clean=0.5 adv=0.5; PGD attack steps 10,
  alpha = epsilon/6; 18-point epsilon sweep.
- Source of timings: per-stage `*_metadata.json` `elapsed_seconds` (clean,
  defense) and orchestrator `done in …s` log lines (attacks, where captured).

## Clean baseline training (precise — metadata `elapsed_seconds`)
| Seed | Time | Epochs run | ~s/epoch |
|---|---|---|---|
| 42 | 6.5 min (391 s) | 61 | ~6.4 |
| 43 | 7.5 min (447 s) | 65 | ~6.9 |
| 44 | 11.5 min (689 s) | 102 | ~6.8 |
| 45 | 12.7 min (763 s) | 75 | ~10.2 |
| 46 | 10.0 min (602 s) | 86 | ~7.0 |

## FGSM-AT defense training (precise — metadata `elapsed_seconds`) — dominant cost
| Seed | Time | Best epoch | ~s/epoch |
|---|---|---|---|
| 42 | 31.8 min (1906 s) | 72 | ~21 |
| 43 | 52.0 min (3120 s) | 97 | ~27 |
| 44 | 2 h 41 m (9649 s) | 182 | ~48 |
| 45 | 1 h 59 m (7150 s) | 56 | ~94 |
| 46 | 38.7 min (2319 s) | 80 | ~23 |

## Attack stages (short, except sweeps)
| Stage | Representative time |
|---|---|
| Matched ε=0.03 attacks (FGSM+PGD, test+legacy) | ~40–45 s (seed 43 undef 41 s; seed 45 def 42 s) |
| Undefended epsilon sweep (18 pts × FGSM+PGD × test+legacy) | seed 43: 570 s (~10 min); seed 46: 3147 s (~52 min) |
| Defended epsilon sweep | seed 43: 1087 s (~18 min); seed 45: 3160 s (~53 min); seed 46: 591 s (~10 min) |

Note: exact seed-44 sweep durations are unavailable — the large 44–46 batch's
per-step `done in` log lines were not flushed before that batch process died;
only the inner-script `Elapsed:` lines (clean, defense) survived.

**Sweep timing is contention-dominated, not work-dominated.** The same 18-point
sweep ranged from ~10 min to ~53 min depending purely on when it ran: seed 46's
*undefended* sweep took 52 min while its *defended* sweep (same machine, ~1 h
later) took 10 min — the reverse of seed 45. Nominal sweep cost is ~10 min;
inflation is CPU contention / thermal throttling during busy windows.

## Approx total wall-clock per completed seed
| Seed | Approx total |
|---|---|
| 42 | ~45 min |
| 43 | ~89 min |
| 44 | ~3 h 20 m |
| 45 | ~3 h 25 m |
| 46 | 1 h 52 m (6743 s, exact: 602+41+3147+2319+43+591) |

## Observed per-epoch slowdown across the session
Defense-training per-epoch time tracked machine load, not the seed: seed 42 ≈
21 s/epoch → 43 ≈ 27 → 44 ≈ 48 → 45 ≈ 94 s/epoch during the contended batch,
then **back down to ≈ 23 s/epoch for seed 46 run solo**. So the slowdown was
CPU contention / thermal throttling while multiple stages overlapped, not an
intrinsic property of any seed. Practical implication: run seeds one-at-a-time
(lets the machine clear between runs and checkpoints each seed), or run on GPU,
to keep per-seed time near the seed-42/43/46 figures (~45–110 min/seed) rather
than the contended ~3.5 h.

## Provenance / completion status
- Seeds 42, 43: complete, committed and pushed.
- Seed 44: complete, committed locally (`6057696`).
- Seed 45: complete, committed locally (`882adc0`). Its undefended PGD epsilon
  sweep was backfilled separately after the original batch stopped mid-sweep.
- Seed 46: complete, committed locally (`5f94267`).

All 5 seeds (42–46) complete. Final 5-seed aggregate written to
`results/multiseed_robustness/` and `figures/multiseed_robustness/`.
