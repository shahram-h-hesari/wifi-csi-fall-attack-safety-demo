# Option A / A1 smoke-only implementation — manual code-review audit

> **Review only.** No code modified, no training/attacks/evaluation/pilot, no A2/A0/H2/H3, no seed 44/45/46,
> no `.tex` edit, no artifact overwrite, no commit. Audits committed `scripts/train_variantH_dual_tail_budget.py`
> (commit `db30d54`) against `OPTION_A_REBALANCED_PREREGISTRATION.md`, the committed A1 smoke artifacts, the
> H1 pilot report, and the reused `train_variantG_targeted_hardneg.py`. Evidence: static inspection +
> read-only git/grep + `python -m py_compile` (syntax). **`--self-check` was NOT re-run** (relied on the
> committed `A1_selfcheck_summary.json`); **smoke was NOT re-run.**

## Decision (see §7): **B — APPROVE WITH ONE REQUIRED FIX FIRST**

The committed **smoke** path is faithful and correct: A1 parameters match the pre-registration, the
`k_abs_min=4` floor is implemented and verified, gates hold, Variant G/H1 behavior is unchanged, and no
`.pt` is produced. **However, the full-pilot path `run_pilot` does NOT thread `fall_k_abs_min` and is
hard-coded H1-only.** Therefore a future A1 *full pilot* would silently run **without** the floor — defeating
the central A1 fix — unless `run_pilot` is updated first. This is the one **required, blocking** fix before
the A1 seed-42 pilot. It is *not* a defect in the committed smoke (which is correct); it is the gate-opening
work that must accompany approval.

---

## 1. Specification compliance

| spec item | status | evidence |
|---|---|---|
| distinct `optionA_rebalanced` namespace | **PASS** | smoke/self-check write under `optionA_rebalanced/_smoke/A1/seed42/` |
| A1 setting present | **PASS** | `SETTINGS["A1"]` (line 65) |
| A1 params exact (λ_b 0.25, λ_r 1.0, k_frac 0.25/0.25, k_abs_min 4, γ 0.5) | **PASS** | `SETTINGS["A1"]` + committed `A1_selfcheck_summary.json` "params" + "A1 params PASSED" |
| A2/A0 defined only if hard-blocked | **PASS** | defined in SETTINGS but `OPTIONA_RUNNABLE={"A1"}`; main() raises for A2/A0 (verified at runtime) |
| H2/H3 still blocked | **PASS** | smoke restricted to H1/A1; `--pilot` H1-only; H2/H3 cannot run |
| seed 44/45/46 blocked | **PASS** | `if args.seed != 42: raise` (verified) |
| full A1 pilot blocked | **PASS** | `--pilot` asserts H1-only → A1 pilot refuses (verified) |
| no architecture changes | **PASS** | LeNet via reused `tvg.load_foundation`; no arch code |
| no Variant G changes | **PASS** | `git diff` clean; `train_variantG_*`/`export_probability_*` unchanged; db30d54 touched only the H script + A1 smoke artifacts |
| smoke output namespace | **PASS** | `variantH_dual_tail_budget/optionA_rebalanced/_smoke/A1/seed42/` (4 artifacts, 0 `.pt`) |
| **full-pilot threads k_abs_min** | **FAIL (blocking for pilot)** | `run_pilot` (line 482) is H1-only and its epoch call (line 513) omits `fall_k_abs_min` → defaults None → **no floor in a full A1 run** |

All *smoke-scope* items PASS; the single **FAIL** concerns the *future pilot* path and is the required fix.

## 2. Mathematical correctness audit

**`fall_rescue_loss(..., k_abs_min=None)` (lines 128–150):**
- ✅ fall-only (`f = y == fall_idx`, `[f]` indexing).
- ✅ `max_{c≠f} z_c − z_f`: `zo[:,fall_idx]=−inf`, `max_nf=zo.max(1)`; `.clone()` protects the graph.
- ✅ hinge `relu(γ_r + max_nf − z_f)`.
- ✅ TopK hardest via `_resolve_k_floor` + `topk_mean(hinge, k_abs=k)`.
- ✅ **k_abs_min correct:** `_resolve_k_floor` → `k = clamp(max(ceil(k_frac·n), k_abs_min), 1, n)`. Verified
  by the committed self-check: **n=10→4, n=3→3, n=0→0 (loss 0), `pass:True`**; selected = largest hinges;
  `rows_with_grad` = selected (4 and 3).
- ✅ never selects more than available (`min(k, n)`); empty fall mask → 0 safely.
- ✅ gradients flow only through selected (topk).
- ✅ diagnostics: valid, selected, `k_abs_min`, `floor_active`, mean_fall_margin, mean_selected_hinge.

**`nonfall_budget_loss` (unchanged except A1 weight):**
- ✅ non-fall only; `z_f − z_y`; hinge `relu(r + γ_b)`; source-weighting applied (aligned to nf subset);
  TopK largest; no detach. Identical to the H1-reviewed version (A1 only lowers `λ_b` at the call site).

**`topk_mean` / `_resolve_k_floor`:**
- ✅ deterministic (`torch.topk`); ✅ empty-safe (zeros on input device/dtype); ✅ device/dtype-safe;
  ✅ supports `k_frac`/`k_abs`/floor; ✅ k≥1 when n≥1; ✅ **no off-by-one** — `ceil(k_frac·n)` then floor
  `max(base,k_abs_min)` then clamp; confirmed by n=10→4 (base ceil(2.5)=3, floor 4) and n=3→3 (base 1,
  floor would be 4, clamp to n=3).

## 3. Loss integration audit

Total loss (line ~213): `base_FWCE + 1.0·src_motion + 1.0·fall_margin + 1.0·targeted + λ_b·nonfall_budget +
λ_r·fall_rescue`.
- ✅ FWCE present; Variant G src/motion, fall-margin, targeted reused via `variantH_margin_terms` →
  `tvg.variantG_margin_terms` (unchanged).
- ✅ A1 adds `λ_b·nonfall_budget` and `λ_r·fall_rescue` with **λ_b=0.25, λ_r=1.0** (lower budget, stronger
  rescue) — verified in the committed smoke header and summary.
- ✅ **k_abs_min=4 actually used during A1 smoke** (smoke threads `fall_k_abs_min=kabs`, line 425; summary
  `fall_rescue_k_abs_min: 4`, `floor_active_frac: 1.0`).
- ✅ all components logged; **`budget_to_rescue_loss_ratio` logged** (0.504→0.178).
- ⚠️ **H1 behavior unchanged confirmed:** `run_pilot` (H1) passes no `fall_k_abs_min` → None → committed
  H1/Variant H behavior preserved (k≈1). Good — but this is exactly why the A1 *pilot* needs the fix (§1).

**Risk checks:**
- *Stronger fall-rescue pushing FP back toward Variant F:* **MEDIUM** — λ_r=1.0 + floor raises z_f on hard
  falls; could inflate r_y on motion. The whole point of the pilot is to test this; observable in metrics.
- *Lower budget failing to reduce FP below G1:* **MEDIUM** — λ_b halved may under-suppress FP.
- *Selecting all falls when n<4 makes rescue too broad:* **LOW** — n<4 means at most 3 falls; penalizing all
  is mild and intended (the lower tail is small per batch).
- *Floor interacting badly with small per-batch fall counts:* **LOW–MEDIUM** — the floor *stabilizes* vs H1
  (k≈1 → k=min(4,n)≈2–4), reducing single-sample gradient noise, not increasing it.
- *Accidentally changing H1 behavior:* **LOW** — default None path is byte-equivalent; `run_pilot` H1 omits
  the floor; committed H1 artifacts untouched.

## 4. Gate and leakage audit

- ✅ A1 full pilot blocked (`--pilot` H1-only). ✅ A2/A0 blocked (`OPTIONA_RUNNABLE`). ✅ H2/H3 blocked
  (smoke H1/A1 only; pilot H1 only). ✅ seed 44/45/46 blocked.
- ✅ No test data in self-check (train batches + synthetic) or smoke (`val_loader` only; `_test_loader`
  never used; `test_set_used: false`).
- ✅ No test thresholding/checkpoint selection. ✅ No automatic follow-up. ✅ No `.pt` from smoke (0).
- ✅ Existing H1 results not overwritten (tracked `results/` unchanged vs HEAD).

## 5. Smoke-artifact audit (committed `optionA_rebalanced/_smoke/A1/seed42/`)

- A1 params match pre-registration (`A1 params PASSED`). Self-check **PASS** (class indices, sign check,
  TopK, finite/nonzero, directionality, k_abs_min floor).
- **k_abs_min synthetic: n=10→4, n=3→3, n=0→0** (`pass:True`).
- **Smoke key values** (2 epochs × 6 batches): nonfall_budget **0.456 → 0.180** (nonzero);
  fall_rescue **0.905 → 1.008** (nonzero); fall_selected **2.83 → 2.50** (= min(4, adv-falls/batch));
  **floor_active_frac = 1.00** (engaged every batch); **budget_to_rescue_ratio 0.504 → 0.178** (logged).
- directionality (self-check): nonfall-budget r_y **−0.113 → −0.238** (reduced); fall-rescue m_f
  **−1.123 → −0.998** (increased).
- ✅ smoke report + summary state **smoke-only, no convergence/pilot/scientific claim**; cold-start flags
  explained.

## 6. Risk assessment before an A1 pilot

| risk | level | reasoning |
|---|---|---|
| `run_pilot` omits `k_abs_min` → A1 pilot runs without the floor | **HIGH** (process) | the central A1 fix would not apply; must fix before pilot (§1, §7) |
| stronger fall-rescue increases false alarms (toward F) | **MEDIUM** | λ_r=1.0 + floor raises z_f on hard falls; observable in pilot FP |
| lower budget fails to reduce FP below G1 | **MEDIUM** | λ_b halved may under-suppress the upper tail |
| k_abs_min overemphasizes noisy/atypical falls | **LOW–MEDIUM** | k ≤ 4 small; mild |
| small per-batch fall count → unstable gradients | **LOW–MEDIUM** | floor *reduces* H1's k≈1 instability |
| A1 raises recall but loses the FP gain (ends F-like) | **MEDIUM** | plausible; the recall/FP coupling is the open problem |
| A1 still fails clean guard (as H1 did) | **MEDIUM** | lower λ_b should help vs H1, but unproven on test |
| A1 still far from > 80% recall / < 10% FP | **MEDIUM–HIGH** | one rebalance unlikely to fully close +10 TP / −20 FP |

No latent *code* bug beyond the `run_pilot` threading gap; the MEDIUM items are scientific and observable in
the pilot metrics.

## 7. Pilot-readiness decision

### **B — APPROVE WITH ONE REQUIRED FIX FIRST.**

The committed smoke implementation is faithful and safe. The A1 seed-42 pilot may be approved **provided the
gate-opening commit (a separate, reviewed change) makes exactly these fixes**, then re-runs a quick
self-check/smoke to confirm:

1. **Thread the floor into the full-pilot path:** update `run_pilot` to call
   `train_one_epoch_variantH(..., fall_k_abs_min=cfg.get("k_abs_min"))` (line ~513). Without this, A1's
   full pilot runs with **no floor** (k≈1), silently invalidating the A1 design. *(Required, blocking.)*
2. **Allow A1 in the pilot gate:** the current `--pilot` hard-asserts `setting == "H1"`. Open it to A1
   (e.g., allow `{"H1","A1"}` with an explicit, separately-approved flag), keeping A2/A0/H2/H3 and
   seed 44/45/46 blocked, and keep the numerical stop-conditions. *(Required, blocking.)*
3. After (1)+(2): re-run `--self-check` and a 2-epoch A1 smoke to confirm the **full-pilot path** now reports
   `floor_active` and the threaded k_abs_min, then a code review of the gate-opening diff. *(Required.)*

Once those are in place, the A1 seed-42 pilot is approved under these limits:
- **A1 only**, **seed 42 only**, **no A2/A0**, **no H2/H3**, **no seed 44**, **LeNet only**;
- **no thesis claims** until a full evaluation (clean / FGSM / PGD@0.030 / PGD-20 / 18-ε sweeps /
  confidence-inversion / Wilson) is scored against the pre-registered §8 success tiers;
- the pilot must keep the §7 stop-conditions (NaN/inf; budget/rescue always-zero; **fall selected < 4 when
  n_fall ≥ 4**; post-warmup recall collapse).

*(Decision is B, not A, solely because the committed `run_pilot` would not apply the A1 floor — a real,
blocking gap for the pilot, even though the committed smoke code is correct.)*

### Scope reminder
Review only — no code modified, no training/attacks/pilot/new seeds, no `.tex` edit, no artifact overwrite.
Window-level, digital-domain, white-box; no solved/certified/clinical/over-the-air claim.
