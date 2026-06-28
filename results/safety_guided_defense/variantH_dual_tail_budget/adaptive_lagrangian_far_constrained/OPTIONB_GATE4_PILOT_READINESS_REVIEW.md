# Option B (adaptive-Lagrangian FAR-constrained) — Gate-4 seed-42 pilot readiness review

> **READINESS REVIEW ONLY — the pilot is NOT run by this document.** No training, no pilot, no held-out test
> evaluation, no checkpoints, no `.tex` edit, no A1/G1/H1 change, no commit performed here. Reviews readiness
> to launch the single pinned seed-42 Option B pilot, against committed evidence through `2c6f5d2` (Gate-3
> smoke). Window-level, digital-domain, white-box, processed CSI; test n=500 (45 fall / 455 non-fall),
> validation n=496 (44 falls), ε=0.030. **No product / clinical / deployment / certified / over-the-air
> claim.** The joint target (PGD recall > 80% AND FAR < 10%) remains **unmet**.

## 1. Why Option B is worth one seed-42 pilot despite A1 failing

A1 (static dual-tail, rejected) was an **informative negative**, not a dead end: its `k_abs_min=4`
fall-rescue floor worked mechanically (≈2.6 falls/batch vs H1's k≈1), recall rose to 0.556 (> H1's 0.489),
and FP fell to 68 (15.0%, < H1's 94). What A1 proved is that a **constant** budget weight `λ_b` cannot hold
both tails: a fixed `λ_b` either under-cuts FP (recall preserved, FAR > 10%) or over-suppresses recall
(FAR down, clean guard breaks). A1 sat in the former regime on test (FAR 15.0%, clean acc 0.678 — guard
fails). Option B changes **the one thing A1 could not do**: it makes `λ_b` a feedback-controlled Lagrange
multiplier that *rises only while FAR > 10% and relaxes once FAR ≤ 10%*, so the model is pushed toward the
constraint boundary rather than toward a fixed, mis-calibrated penalty. This is a single, cheap (~1 seed-42
run, like A1), pre-registered test of a *different mechanism*, with an explicit FAR constraint and a
target-aligned selection score — the cheapest disciplined way to learn whether the two tails can be
separated by feedback control. An honest negative is still publishable as future work; a positive would
materially strengthen the defense chapter.

## 2. What Option B changes mathematically vs static dual-tail A1

| aspect | A1 (static, rejected) | Option B (adaptive) |
|---|---|---|
| FAR handling | implicit: fixed `λ_b=0.25` penalty on the budget term | **explicit constraint** FAR ≤ 0.10 enforced by a dual variable |
| `λ_b` | constant 0.25 for all epochs | **adaptive** `λ_b(t+1)=clip(λ_b(t)+0.10·(FAR_val_PGD10(t)−0.10),0,1.0)` |
| feedback signal | none | **validation PGD-10 FAR** measured once per epoch (never test) |
| checkpoint selection | selection-v2 SafetyScore (recall/PGD/FGSM/NFAB blend) | **target-aligned score** `PGDRecall − 4·max(0,FAR−0.10) − 2·max(0,0.90−CleanFR) − 2·max(0,0.70−Acc)` with a three-pronged clean guard |
| objective form | `L = base + λ_s·src + λ_f·fall + λ_t·tgt + λ_b·budget + λ_r·rescue` (λ_b fixed) | same objective; **only λ_b becomes time-varying**; rescue floor `k_abs_min=4` retained |

The base (Variant G G1) terms, the two TopK tail terms, and the fall-rescue floor are **unchanged** — the
sole new dynamic is the epoch-level adaptive `λ_b` and the constraint-aligned selection. This isolates the
mechanism under test.

## 3. Pinned pilot target (must match the committed implementation)

| knob | pinned value |
|---|---|
| seed | **42 only** |
| architecture | **LeNet only** |
| dataset | **UT-HAR only** |
| train epsilons | **`{0.005, 0.015, 0.03}`** |
| `λ_r` (rescue, fixed) | **1.0** |
| `λ_b(0)` | **0.25** |
| `η` (step size) | **0.10** |
| `λ_b,max` (cap) | **1.0** |
| `k_abs_min` (fall-rescue floor) | **4** |
| update cadence | **once per epoch**, after validation, applied to next epoch |
| FAR signal | **validation PGD-10 FAR = FP/N_val_nonfall**, `N_val_nonfall` computed from labels (expect 452) |
| test-set use during train/selection | **none** |

These match `train_optionB_adaptive_lagrangian.py` constants (verified at Gate 2/3): `LAM_R=1.0`,
`LAM_B0=0.25`, `ETA=0.10`, `LAM_B_MAX=1.0`, `K_ABS_MIN=4`, `EXPECTED_VAL_NONFALL=452`, train-eps gate.

## 4. Success / failure criteria (pre-registered; evaluated on seed-42 test, separate Gate-5)

- **Strong success:** PGD recall ≥ 0.80 ∧ PGD FP ≤ 45 ∧ clean guard holds (acc ≥ 0.70, mF1 ≥ 0.65,
  clean fall recall ≥ 0.90) ∧ PGD-20 durability holds (if produced).
- **Promising:** PGD recall ≥ 0.70 ∧ PGD FP ≤ 65 ∧ clean guard holds.
- **Minimum useful:** PGD recall ≥ 0.60 ∧ PGD FP ≤ 65 ∧ clean guard holds (acc ≥ 0.70, mF1 ≥ 0.65,
  clean fall recall ≥ 0.90).
- **Reject:** clean-guard failure; or PGD recall < 0.60; or FP controlled **only** by recall collapse; or the
  result is dominated by G1 (seed42 0.689/104 or seed44 0.600/65) or by A1 (0.556/68).

Selection is **validation-only**; the test evaluation (and these test-based verdicts) happen at Gate 5 after
the pilot, reusing `export_probability_predictions.py --split test` unmodified — exactly as the A1 kill-check.

## 5. Early monitoring rules (during a future pilot)

- All loss components **finite** every epoch.
- **budget and rescue terms nonzero** (TopK terms engaged; floor active).
- **`N_val_nonfall == 452`** (split-integrity guard; computed from validation labels).
- **`λ_b(t)` stays within `[0, 1.0]`** every epoch.
- **exactly one λ_b update per epoch** (cadence guard `assert updates == epochs`).
- **no test-set access** (val loader only; `_test_loader` never referenced).
- **clean guard eventually eligible** (acc/mF1/clean-fall-recall floors reached after warmup, not stuck at 0).
- **recall recovery not permanently collapsed** (cold-start recall 0 expected early; must recover, as in
  G/G1/H1/A1 ~epoch 27–61).
- **λ_b trajectory sane** (moves toward the FAR boundary; logged each epoch with `far_val_pgd10`).

## 6. Stop conditions (halt and report)

- **NaN/inf** in total loss or any term.
- **Missing validation PGD metrics** (no FAR signal can be formed).
- **Split mismatch** (`N_val_nonfall != 452`).
- **All-zero budget or rescue term** despite valid examples.
- **Unauthorized seed/setting** starts (anything ≠ optionB / seed 42).
- **Accidental test-set access** during training or selection.
- **Full-pilot gate not exactly restricted to optionB + seed 42** (the gate-opening patch must not widen
  scope beyond this single configuration).
- Do **not** stop for epoch-1/2 cold-start alone.

## 7. Current gate status — the script still refuses `--pilot`

The committed `train_optionB_adaptive_lagrangian.py` (Gate-2/3) **intentionally refuses the pilot**:
- `enforce_gate(setting, seed, pilot)` raises `SystemExit` when `pilot=True` ("requires explicit Gate-4
  approval"); verified at runtime (`--pilot` → **exit 1**).
- `run_pilot(args, F)` is a stub that raises `SystemExit` ("run_pilot is gated").
- `main()` has no path that reaches a full training loop; the default branch raises.

Therefore a **minimal Gate-4 gate-opening patch is required before launch**, scope-limited to:
1. allow `--pilot` only for `--setting optionB --seed 42`;
2. implement `run_pilot` as the full-epoch version of the already-reviewed `_adaptive_train` loop (no
   `max_batches`), running a **fixed 70 epochs with NO early stopping** (see §7a), writing to the
   `optionB/seed42` namespace and saving the three selection-candidate `.pt` checkpoints
   (max-score / max-recall-within-guard / min-FAR-within-guard);
3. keep all stop conditions, the once-per-epoch update, the split guard, and the no-test-access invariant
   **unchanged**;
4. **not** widen the gate to any other setting/seed and **not** touch the test set.
This patch must itself pass a small code review + a re-smoke (gate-fix pattern, as done for A1) before the
pilot runs.

## 7a. Exact future pilot command and output namespace

> Reference only — **not runnable today** (the script refuses `--pilot`, §7). These become valid **after** the
> separate Gate-4 gate-opening patch is approved, reviewed, and re-smoked.

**Exact future pilot command:**
```
.venv\Scripts\python.exe scripts\train_optionB_adaptive_lagrangian.py --setting optionB --seed 42 --pilot
```

**Expected output (results) namespace:**
```
results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/
```

**Expected checkpoint namespace (if checkpoints are saved):**
```
checkpoints/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/
```
(Saved candidates would be max-score / max-recall-within-guard / min-FAR-within-guard, mirroring selection-v2.)

**Intended full-pilot schedule (DECISION): fixed 70 epochs, validation-based checkpoint selection, NO early
stopping** for the first Option B pilot.

Reasoning:
- A1 was a rejected result, so the first Option B pilot should **not** copy A1-style early-stopping/defense
  behavior. The part worth preserving from prior variants is the **disciplined validation-only checkpoint
  selection and full per-epoch logging**, not A1's static-weight mechanism or its stopping policy.
- Option B's whole point is the **adaptive `λ_b`**: stopping early could interrupt the feedback process
  before the budget weight settles at a useful FAR boundary. A fixed schedule gives the controller time to
  converge.
- Prior variants recovered attacked recall **late** (≈ epoch 27–61), so a **fixed 70-epoch** run gives the
  adaptive mechanism a fair test rather than cutting it off during cold-start.
- The pilot **verdict must come from the saved validation-selected checkpoints**, not from where an
  early-stop rule happened to halt.

**Schedule pinning (must be fixed by the gate-opening patch).** The committed script exposes `--epochs 70`,
`--min-epochs 35`, `--patience 15` as argparse **defaults**, and the reviewed `_adaptive_train` loop iterates
`range(1, epochs+1)` only (no early-stop logic). For the first Option B pilot:
- run **fixed 70 epochs**; **no early stopping**;
- `--patience` and `--min-epochs` **must not remain as unused, active-looking controls.** The Gate-4
  gate-opening patch must EITHER (1) remove/ignore `--patience` and `--min-epochs` from the Option B pilot
  path and clearly log `early_stopping=false`, OR (2) keep them only as **inactive metadata** with an
  explicit warning/log field stating they are **not used** for the first fixed-70 pilot.

**Checkpoint selection remains validation-only** (test never used): max target-aligned score · max PGD recall
within the clean guard · min FAR within the clean guard. **Test evaluation remains a separate Gate 5 only.**

**This review does not approve the pilot by itself.** Listing the command, namespaces, and schedule here is
documentation, not authorization. The pilot remains gated; this review only recommends **preparing the
minimal gate-opening patch + re-smoke**, which must be separately reviewed before any run.

## 8. Recommendation

**Proceed to prepare the minimal Gate-4 gate-opening patch** (a separate, reviewed change), then launch the
**single pinned seed-42 Option B pilot** only after that patch is reviewed and re-smoked. Rationale: the
mechanism is scientifically distinct from A1, the cost is one seed-42 run, the criteria and stop conditions
are pre-registered, and the implementation already passed Gate-2 static audit and Gate-3 smoke. Do **not**
open the gate and launch in one step; keep the patch minimal and re-reviewed (the A1 gate-fix taught us that
the pilot path is exactly where a silent threading/scope bug would invalidate the run).

**The Gate-4 gate-opening patch should implement a fixed-70-epoch pilot with validation-based checkpoint
selection; it should not implement A1-style early stopping for the first Option B pilot.**

### Scope reminder
Readiness review only — no training/pilot/test evaluation/checkpoints; no `.tex`/A1/G1/H1 change. Confirms
the pinned target, criteria, monitoring, and stop conditions, and recommends a **separate minimal
gate-opening patch + re-smoke** before the seed-42 pilot. Starts nothing.
