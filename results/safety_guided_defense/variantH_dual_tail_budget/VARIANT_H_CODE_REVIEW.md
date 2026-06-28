# Variant H smoke-only implementation — manual code-review audit

> **Review only.** No code modified, no training/attacks/evaluation/pilot run, no new seeds, no `.tex`
> edit, no artifact overwrite, no commit. Audits the committed `scripts/train_variantH_dual_tail_budget.py`
> (commit `c569d3d`) against `VARIANT_H_IMPLEMENTATION_SPEC.md`, the committed smoke artifacts, and the
> reused `scripts/train_variantG_targeted_hardneg.py`. Evidence: static code inspection + read-only
> git/grep + `python -m py_compile` (syntax). **`--self-check` was NOT re-run in this audit** (relied on the
> committed `seed42_variantH_H1_selfcheck.json`); **smoke was NOT re-run.**

## Decision (see §9): **A — APPROVE H1 seed-42 pilot** (with non-blocking transparency notes)

The implementation is faithful to the spec, mathematically correct term-by-term, safely gated (full
training refuses; seeds 44/45/46 blocked; smoke H1-only), leak-free, reuses the frozen Variant G foundation
unchanged, and persists no `.pt`. Two **non-blocking** design choices should be recorded in the pilot
pre-registration (§7 / notes); neither affects safety or correctness.

---

## 1. Specification compliance

| spec item | status | evidence |
|---|---|---|
| `topk_mean` | **PASS** | lines 74–81; deterministic `torch.topk`, empty-safe, k≥1 via `_resolve_k` |
| `nonfall_budget_loss` | **PASS** | lines 85–105; non-fall mask, `z_f−z_y`, hinge, TopK, diagnostics |
| `fall_rescue_loss` | **PASS** | lines 109–128; fall mask, `max_{c≠f}−z_f`, hinge, TopK, diagnostics |
| `variantH_margin_terms` | **PASS** | lines 132–142; returns all 5 components + diags |
| H1/H2/H3 setting defs | **PASS** | lines 60–62; only `(lam_b,lam_r)` vary |
| seed-42-only smoke gate | **PASS** | `main()` `if args.seed != 42: raise SystemExit` |
| seed 44/45/46 block | **PASS** | same gate; verified at runtime (44/45/46 refuse) |
| full-training block | **PASS** | default branch raises SystemExit ("intentionally gated") |
| no architecture changes | **PASS** | `build_model("lenet")` via reused `tvg.load_foundation`; no arch code |
| reuse of Variant G foundation | **PASS** | imports `tvg`; reuses `load_foundation`, `targeted_fall_pgd`, `source_weights`, `variantG_margin_terms`, `targeted_sign_check`; `git diff` shows variantG **UNCHANGED** |
| output namespace `variantH_dual_tail_budget` | **PASS** | `_smoke/seed42/` results; `checkpoints/.../seed42/` reserved (unused in smoke) |
| no `.pt` committed from smoke | **PASS** | smoke saves no checkpoint; 0 `.pt` in repo/commit |
| source-weighting of budget term | **WARNING** (non-blocking) | applied by **default** (lines 138–139), faithful to spec §3 "optional" but deviates from the bare §2 formula; not flag-configurable — see notes |

All required items **PASS**; one **WARNING** is a transparency note, not a failure.

## 2. Mathematical correctness audit

**`nonfall_budget_loss` (lines 85–105):**
- ✅ non-fall only: `nf = y != fall_idx`; all subsequent indexing uses `[nf]`. Fall samples cannot enter.
- ✅ `z_f − z_y`: `zf = zo[:, fall_idx]`, `zy = zo.gather(1, y[nf]...)`, `r = zf − zy`.
- ✅ hinge `max(0, r + γ_b)`: `torch.relu(r + gamma_b)`.
- ✅ top-K largest: `topk_mean(hinge, k_abs=k)` with `k=_resolve_k(...)`.
- ✅ source weighting correct **and aligned**: `source_weights` is computed on the **same `nf` subset**
  (`tvg.source_weights(adv_lab[nf], …)` in `variantH_margin_terms`), applied as `source_weights * hinge`
  before TopK. Element order matches.
- ✅ no detach / gradient-safe: operates on live `logits_adv`; no `.detach()`.

**`fall_rescue_loss` (lines 109–128):**
- ✅ fall only: `f = y == fall_idx`; `[f]` indexing.
- ✅ `max_{c≠f} z_c − z_f`: `zo[:, fall_idx] = −inf` then `max_nf = zo.max(1)`; **fall excluded correctly**
  (the `.clone()` of `zo` and `zf` protects the graph/values, mirroring Variant G's fall margin).
- ✅ hinge `max(0, γ_r + max_other − z_f)`: `torch.relu(gamma_r + (max_nf − zf))`.
- ✅ top-K hardest: TopK on the hinge selects the largest = most-negative-`m_f` falls.
- ✅ no detach / gradient-safe.

**`topk_mean` (lines 67–81):**
- ✅ deterministic (`torch.topk`, `largest=True`); ✅ empty-safe (returns `torch.zeros((), device=…, dtype=…)`
  from the input tensor); ✅ k≥1 when valid (`_resolve_k` clamps to `[1, n]`); ✅ selects **largest** not
  smallest; ✅ gradient flows only through the K selected values (topk returns selected entries with grad);
  ✅ both `k_frac` and `k_abs` supported (`k_abs` takes precedence); ✅ no device/dtype bug (zeros derive
  device/dtype from `values`).

**Note (intended, not a bug):** `γ_b = γ_r = 0.5` equal `γ_m = γ_f = 0.5` (Variant G). Therefore
`nonfall_budget` is the **same hinge form as `src_motion`** and `fall_rescue` is the **same hinge form as
`fall_margin`** — each new term is a **TopK re-emphasis of an existing mean term on the worst windows**.
This is exactly the spec's "mean moved the bulk, TopK moves the tail" design (§5). It is intended emphasis,
not harmful double-counting (see §3).

## 3. Loss integration audit

Total loss (line 187–188):
`loss = base_FWCE + 1.0·src_motion + 1.0·fall_margin + 1.0·targeted + lam_b·nonfall_budget + lam_r·fall_rescue`.

- ✅ base FWCE present (`train_criterion(outputs, batch_y)`, fall weight 3 via reused foundation).
- ✅ Variant G terms reused via `variantH_margin_terms` → `tvg.variantG_margin_terms` (source/motion,
  fall-margin, targeted) — **unchanged**.
- ✅ new terms added with correct weights (`lam_b`, `lam_r` from the setting).
- ✅ H1/H2/H3 vary only `(lam_b, lam_r)`; base $\lambda$/$w_{wr}$/$\gamma$ fixed (`BASE_LAM_*`, `BASE_W_WR`).
- ✅ default smoke uses H1 only (`if args.setting != "H1": raise` in smoke branch).
- ✅ H2/H3 cannot run in smoke (same guard); ✅ full pilot cannot launch (default branch raises).
- ✅ component-by-component logging: epoch dict accumulates all six means + TopK selected counts.

**Double-counting / compatibility:**
- `L_fall_rescue` vs `L_fall`: **intended double-emphasis.** Same hinge (γ identical); `L_fall` is the mean
  over all adversarial falls, `L_fall_rescue` is the TopKMean over the hardest. The hardest falls receive
  the sum of both gradients — *exactly* the intended lower-tail pressure. Not harmful.
- `L_nonfall_budget` vs `L_src`: **compatible / intended double-emphasis** (same relationship on the upper
  tail of non-fall risk). Both source-weighted.
- `L_tgt` source: train loop generates `tgt_adv` via `targeted_fall_pgd` (targeted-to-fall) and feeds
  `tgt_out`; the two budget terms operate on `adv_out` (the untargeted FGSM/PGD sub-batch). ✅ Matches spec
  §3: budget terms use untargeted PGD examples; `L_tgt` uses targeted-to-fall. No source mixing.

## 4. Data-leakage and split audit

- ✅ self-check uses `train_loader` + a synthetic directionality probe only; the summary records
  `no_test_leakage` explicitly. No test access.
- ✅ smoke selection/metrics use `compute_validation_bundle` on `val_loader` (validation); `test_loader` is
  bound as `_test_loader` and **never referenced**.
- ✅ no threshold/gate is selected on test (none is selected at all in smoke).
- ✅ seed 44 cannot run (seed gate).
- ✅ no evaluation artifact is mislabeled as a final result; smoke summary `stage: "variantH_smoke"`,
  `test_set_used: false`.
- ✅ smoke artifacts clearly state no scientific conclusion (see §6 note).

## 5. Reproducibility and safety-gates audit

- ✅ deterministic seed handling: reused `load_foundation` calls `s1.set_seed(args.seed)` +
  `rng = np.random.default_rng(args.seed)`.
- ✅ output paths include `_smoke/seed42`.
- ✅ no existing artifacts overwritten (`git status` additions only; Variant G **UNCHANGED** vs HEAD).
- ✅ no `.pt` persisted or staged (smoke saves none; 0 `.pt` in commit).
- ✅ script refuses unsafe modes (full training raises; smoke H1-only).
- ✅ script refuses unsupported seeds (44/45/46 raise).
- ✅ full training refuses unless intentionally unlocked in a future commit (default branch is a hard
  `SystemExit`).
- ✅ no accidental change to Variant G files (`git diff --quiet HEAD` clean).
- Minor: no try/except anywhere (no silent exception handling); no hardcoded absolute paths.

## 6. Smoke-artifact audit (committed `_smoke/seed42/*`)

**Self-check (`seed42_variantH_H1_selfcheck.json`):**
- targeted-PGD sign check **PASSED**: clean median fall logit **0.0095 → 0.0270** (targeted); clean median
  P(fall) **0.1414 → 0.1441**; `increased=True`; n_nonfall=55.
- TopK correctness **PASSED**: `select_mean_top2_is_4.0=True`, `grad_only_selected=True`,
  `empty_returns_zero=True`, `k_at_least_1=True`.
- directionality **PASSED**: nonfall-budget `r_y` **−0.1126 → −0.2376** (reduced ✅); fall-rescue `m_f`
  **−1.1227 → −0.9977** (increased ✅).
- one-batch loss values: FWCE 1.945, src 0.769, fall 0.573, targeted 0.793, **nonfall_budget 0.982**,
  **fall_rescue 0.574** (all finite; both new losses **> 0**). budget_diag valid 30 / selected 8 / mean raw
  margin −0.008; rescue_diag valid 2 / selected 1 / mean fall margin −0.073.

**Smoke (`seed42_variantH_H1_smoke_log.csv` / `_summary.json`):**
- epoch 1: loss 4.437, base 2.008, src 0.291, fall 1.088, tgt 0.300, **budget 0.405**, **rescue 1.094**,
  ksel(b/r) 7.4/1.2, acc 0.244, cleanFR 0.000, pgd_fr 0.000, pgd_FP 0.
- epoch 2: loss 3.884, base 1.972, src 0.139, fall 1.016, tgt 0.145, **budget 0.203**, **rescue 1.020**,
  ksel(b/r) 8.0/1.0, acc 0.294, cleanFR 0.000, pgd_fr 0.000, pgd_FP 0.
- all losses finite; both new terms nonzero each epoch.
- summary `note` explicitly states: **code-correctness only; the epoch-2 recall collapse is the EXPECTED
  cold-start (Variant G/G1 began identically, recovering ~epoch 27) and is NOT a convergence conclusion; no
  full-training/pilot conclusion may be drawn; no scientific claim is made.**

## 7. Failure-risk analysis (before a full H1 pilot)

| risk | level | reasoning |
|---|---|---|
| fall-rescue increases FP by raising $z_f$ too broadly | **MEDIUM** | raising $z_f$ on hard falls can spill onto motion neighbours; bounded by TopK (k≈1 fall/batch) and γ_r=0.5, but this is the exact tension the pilot tests — watch FP vs recall jointly. |
| nonfall-budget suppresses true fall recall | **MEDIUM** | lowering $z_f$ on worst non-fall could globally depress $z_f$; countered by `L_fall`+`L_fall_rescue`. The pilot's recall floor + PGD-20 criteria are the guardrail. |
| TopK overfits hardest noisy examples | **MEDIUM** | k_frac=0.25 on a small per-batch fall count → **k≈1 fall/batch** for rescue; gradient driven by a single (possibly noisy) hardest fall → potential instability/under-power. |
| source weighting overemphasizes walk/run vs fall | **LOW–MEDIUM** | $w_{wr}=2$ on the budget term focuses motion; balanced by fall terms; defensible per the diagnosis (73.8% motion FAs). |
| k_frac=0.25 too aggressive/weak | **MEDIUM** | reasonable for non-fall (~8/batch) but yields k≈1 for fall — **fall-rescue may be under-powered per batch**; consider k_abs floor for the fall term in a later iteration. |
| early clean-recall collapse = instability vs cold-start | **LOW** | identical to Variant G/G1 cold-start which recovered; 2-epoch smoke can't distinguish, but the pattern matches the validated baseline. |
| implementation hides gradient masking / apparent robustness | **LOW** | no masking mechanism added; the reused PGD-20 screen + pilot non-collapse criteria detect it at eval time. |

No risk is **HIGH**; the two MEDIUM items most worth watching are the **per-batch fall-rescue under-power
(k≈1)** and the **joint recall/FP tension** — both are *observable in the pilot metrics*, not latent code
bugs.

## 8. Code-quality audit

- ✅ clear function names (`topk_mean`, `nonfall_budget_loss`, `fall_rescue_loss`, `variantH_margin_terms`).
- ✅ readable diagnostics (`budget_diag`/`rescue_diag`: valid/selected/mean-margin/selected-hinge).
- ⚠️ **one dead variable**: `pct = None` (run_self_check, line 277) is assigned and never used — harmless,
  cosmetic; recommend removal in a future tidy-up (not a blocker).
- ✅ no misleading copied dead code paths.
- ✅ no hardcoded absolute paths (all via `Path(__file__).resolve().parents[...]`).
- ✅ no silent exception handling (no `try/except`).
- ✅ no hidden default that launches training (default branch hard-raises).
- ✅ device handling consistent (`F["device"]` throughout; synthetic probes on the same device); no CPU/GPU
  mixing risk in practice.
- ✅ JSON/CSV schema unambiguous; component-wise logs are sufficient to interpret a future pilot.

## 9. Pilot-readiness decision

### **A — APPROVE H1 seed-42 pilot.**

The script is faithful to `VARIANT_H_IMPLEMENTATION_SPEC.md` and safe to run **H1 only**. The math is
correct term-by-term, gradients are intact, gates hold, there is no leakage, Variant G is unchanged, and no
`.pt` is persisted. Conditions on the approval:

- **H1 only** (H2/H3 defined but not run).
- **seed 42 only** (seeds 44/45/46 blocked; seed-44 needs a separate committed pre-registration).
- **No thesis claims** until a full evaluation (clean / PGD@0.030 / 18-ε sweeps / PGD-20 / confidence
  inversion) is complete and scored against the pre-registered §7 pilot criteria.

**Non-blocking transparency notes to record in the pilot pre-registration (do NOT require a code change to
run H1):**
1. The **nonfall-budget term is source-weighted by default** (faithful to spec §3-optional; differs from
   the bare §2 formula). Document it as `TopKMean[s_y·relu(r_y+γ_b)]`; if an unweighted ablation is wanted
   later, add a flag.
2. **γ_b = γ_r = γ_m = γ_f = 0.5**, so each new term is a **TopK re-emphasis** of an existing Variant G mean
   term on the worst windows (intended tail pressure). State this explicitly so the pilot is interpreted as
   *tail re-weighting*, not a new geometric target.
3. **Per-batch fall-rescue selects k≈1** (k_frac=0.25 × small fall count) — watch for under-powered or
   noisy rescue; consider a `k_abs` floor for the fall term in a later iteration if recall does not move.
4. Trivial: remove the dead `pct = None` (line 277) in a future tidy-up.

*(Decision is A, not B: items 1–4 are documentation/observability, not correctness or safety blockers; H1
can run as committed.)*

### Scope reminder
Review only — no code modified, no training/attacks/pilot/new seeds, no `.tex` edit, no artifact overwrite.
Window-level, digital-domain, white-box; no solved/certified/clinical/over-the-air claim.
