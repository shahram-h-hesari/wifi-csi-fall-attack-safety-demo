# Variant G — math-to-code specification (pre-implementation)

> **Specification / documentation only — Variant G is NOT implemented, trained, or evaluated.** No
> training, no attacks, no script modification, no `.tex` edit, no seeds 45–46, no artifact overwrite.
> This file defines Variant G mathematically, maps every math object to concrete code, and pre-registers
> exactly how a *future* seed-42 pilot would verify whether the defense works. It extends the committed
> `VARIANT_G_DESIGN_MEMO.md` with code-level precision. All references to existing behavior are grounded in
> committed source (file:line cited inline). Window-level, digital-domain, white-box, processed CSI
> tensors; **no certified / clinical / over-the-air / deployment-readiness claim.**

---

## 1. Problem statement (from the Variant F false-alarm diagnostic)

Variant F is the strongest *implemented* defense: it improved the safety-proxy trade-off and passed a
pre-registered independent seed-44 validation (**STRONG SUPPORT** — PGD@0.030 recall 0.622 [0.476,0.749],
FP 112, walk/run 73, residual motion logit margin 0.961, PGD-20 0.511). But the committed diagnostic
(`variantF_false_alarm_diagnostic/`) returned **Diagnosis C — Not filterable**:

- Under PGD@0.030 the residual false alarms exhibit **confidence inversion** — they are *more* fall-confident
  than the true falls Variant F detects: median P(fall) **0.518 vs 0.415** (seed 42) / **0.513 vs 0.392**
  (seed 44); fall-vs-rest logit margin **0.88 vs 0.46** / **0.90 vs 0.42**; entropy **1.30 vs 1.41** / **1.30
  vs 1.40** (lower = more confident).
- No probability / margin / entropy gate met the FP-control targets on **both** seeds; no single threshold
  is cross-seed stable. Post-hoc filtering **fails**.

**Therefore Variant G must change the *learned decision geometry*, not the threshold.** Specifically, it
must lower the model's confidence in the adversarial nonfall→fall direction (concentrated in walk/run, 65–70%
of residual FAs) **without** breaking the clean guard (already at its 0.70 boundary on seed 44) or the
attacked fall recall that Variant F's fall-preservation margin protects.

---

## 2. Mathematical notation

| Symbol | Meaning |
|---|---|
| $x_i \in \mathbb{R}^{1\times 250\times 90}$ | processed CSI input window $i$ (Eq.~\ref{eq:processed-window}) |
| $y_i \in \{0,\dots,6\}$ | true class label of window $i$ |
| $c_f$ | fall class index ( = **1**, see §14.1) |
| $\mathcal{C}_{\mathrm{nf}} = \{0,2,3,4,5,6\}$ | non-fall class set |
| $\mathcal{C}_{\mathrm{wr}} = \{2,4\}$ | walk/run subset ( walk = 2, run = 4 ) |
| $z_\theta(x)\in\mathbb{R}^{7}$ | logits (Eq.~\ref{eq:logits}); $z_f \equiv z_{\theta,c_f}$ |
| $p_\theta(y{=}k\mid x)$ | softmax probability (Eq.~\ref{eq:softmax}) |
| $x_i^{\mathrm{adv}}$ | **untargeted** FGSM/PGD adv example from true label $y_i$ (existing `fgsm_perturb`/`pgd_perturb`) |
| $\hat{x}_i$ | **targeted-to-fall** adv example from a non-fall window ($y_i\in\mathcal{C}_{\mathrm{nf}}$), pushed *toward* $c_f$ (§5) |
| $\gamma_m,\gamma_f,\gamma_t \ge 0$ | margins for motion / fall-preservation / targeted terms |
| $w_c \ge 0$ | source-class weight for class $c$ (heaviest on $\mathcal{C}_{\mathrm{wr}}$) |
| $\lambda_m,\lambda_f,\lambda_t,\lambda_s$ | loss-term weights |
| $\mathcal{B}, \mathcal{B}_{\mathrm{clean}},\mathcal{B}_{\mathrm{fgsm}},\mathcal{B}_{\mathrm{pgd}}$ | batch and its 50/25/25 clean/FGSM/PGD split |
| $n_f = 45$ | test fall windows (val $n_f = 44$) |

---

## 3. Baseline: the frozen Variant F objective

Implemented in `scripts/train_variantF_motion_margin.py` (`train_one_epoch_margin`, lines 43–98). Verbatim:

$$
\mathcal{L}_F = \mathcal{L}_{\mathrm{FWCE}}
+ \lambda_m\,\underbrace{\frac{1}{|\mathcal{B}^{\mathrm{adv}}_{\mathrm{wr}}|}\!\!\sum_{i\in\mathcal{B}^{\mathrm{adv}}_{\mathrm{wr}}}\!\!\max\!\big(0,\ \gamma_m + z_f(x_i^{\mathrm{adv}}) - z_{y_i}(x_i^{\mathrm{adv}})\big)}_{\mathcal{L}_{\mathrm{motion}}^{\mathrm{margin}}}
+ \lambda_f\,\underbrace{\frac{1}{|\mathcal{B}^{\mathrm{adv}}_{\mathrm{fall}}|}\!\!\sum_{i\in\mathcal{B}^{\mathrm{adv}}_{\mathrm{fall}}}\!\!\max\!\big(0,\ \gamma_f + \max_{c\neq c_f} z_c(x_i^{\mathrm{adv}}) - z_f(x_i^{\mathrm{adv}})\big)}_{\mathcal{L}_{\mathrm{fall}}^{\mathrm{margin}}}
$$

- $\mathcal{L}_{\mathrm{FWCE}}$: fall-weighted cross-entropy, fall weight $w_{c_f}=3$ (Eq.~\ref{eq:fwce}), on the
  50/25/25 batch-split mix; train $\epsilon\in\{0.005,0.015,0.030\}$.
- $\mathcal{B}^{\mathrm{adv}}_{\mathrm{wr}}$ = adversarial windows whose **true** label is walk or run.
- $\mathcal{B}^{\mathrm{adv}}_{\mathrm{fall}}$ = adversarial windows whose **true** label is fall.
- **Frozen values:** $\lambda_m = 1.0,\ \lambda_f = 1.0,\ \gamma_m = \gamma_f = 0.5$.

Variant F is **not modified** by this spec. Variant G is a **new script** that imports F's helpers.

---

## 4. The Variant G objective

$$
\boxed{\ \mathcal{L}_G \;=\; \mathcal{L}_F \;+\; \lambda_t\,\mathcal{L}_{\mathrm{targeted}} \;+\; \lambda_s\,\mathcal{L}_{\mathrm{src\text{-}motion}}\ }
$$

### A. Targeted nonfall→fall hard-negative term $\mathcal{L}_{\mathrm{targeted}}$
For each non-fall window, generate a **targeted-to-fall** adversarial example $\hat{x}_i$ (§5) and penalize
fall sitting at/above the true non-fall class by margin $\gamma_t$:

$$
\mathcal{L}_{\mathrm{targeted}}
= \frac{1}{|\mathcal{B}^{\mathrm{tgt}}_{\mathrm{nf}}|}\sum_{i\in\mathcal{B}^{\mathrm{tgt}}_{\mathrm{nf}}}
w_{y_i}\,\max\!\big(0,\ \gamma_t + z_f(\hat{x}_i) - z_{y_i}(\hat{x}_i)\big),
\qquad \mathcal{B}^{\mathrm{tgt}}_{\mathrm{nf}} = \{\,i : y_i\in\mathcal{C}_{\mathrm{nf}}\,\}.
$$

This term trains on the *exact worst-case* nonfall→fall directions the diagnostic flagged (untargeted F only
sees whichever motion windows the attack happens to flip). The source weight $w_{y_i}$ (term B) also scales
this term, concentrating it on walk/run.

### B. Source-class-weighted motion margin $\mathcal{L}_{\mathrm{src\text{-}motion}}$
Variant F's motion margin, re-weighted by source class so walk/run get heavier pressure:

$$
\mathcal{L}_{\mathrm{src\text{-}motion}}
= \frac{1}{|\mathcal{B}^{\mathrm{adv}}_{\mathrm{nf}}|}\sum_{i\in\mathcal{B}^{\mathrm{adv}}_{\mathrm{nf}}}
w_{y_i}\,\max\!\big(0,\ \gamma_m + z_f(x_i^{\mathrm{adv}}) - z_{y_i}(x_i^{\mathrm{adv}})\big),
\qquad w_{\mathrm{walk}}=w_{\mathrm{run}}=w_{\mathrm{wr}}\ge 1,\ \ w_{\mathrm{other}}=1.
$$

Setting $w_{\mathrm{wr}}=1$ and restricting the set to $\mathcal{C}_{\mathrm{wr}}$ recovers F's $\mathcal{L}_{\mathrm{motion}}^{\mathrm{margin}}$ exactly (clean ablation anchor). $\mathcal{B}^{\mathrm{adv}}_{\mathrm{nf}}$ = untargeted-adv windows with true label in $\mathcal{C}_{\mathrm{nf}}$.

> **Design choice to avoid double-counting.** In the pilot, term B *replaces* Variant F's
> $\mathcal{L}_{\mathrm{motion}}^{\mathrm{margin}}$ (it is the weighted generalization of the same term), so
> $\mathcal{L}_G = \mathcal{L}_{\mathrm{FWCE}} + \lambda_s\mathcal{L}_{\mathrm{src\text{-}motion}} + \lambda_f\mathcal{L}_{\mathrm{fall}}^{\mathrm{margin}} + \lambda_t\mathcal{L}_{\mathrm{targeted}}$.
> The ablation anchor ($\lambda_s$ with $w_{\mathrm{wr}}=1$, $\lambda_t=0$) is then **numerically identical**
> to Variant F, which is the cleanest possible baseline for attribution.

### C. False-alert-budget — **checkpoint selection, NOT a loss term**
The FP budget is enforced at **selection** (§6 / §9 / Eq.~\ref{eq:v2-guard}), not as a differentiable penalty
(batch FP is noisy and non-differentiable). $\mathcal{L}_G$ contains **no** FP-budget term.

---

## 5. Targeted-to-fall PGD definition

The existing `fgsm_perturb`/`pgd_perturb` (`train_safety_guided_defense.py:165–193`) are **untargeted
ascent** on the *true* label: `adv = x + α·sign(∇_x CE(model(x), y_true))` — they move *away* from the true
class. A targeted-to-fall attack must move *toward* $c_f$. Mathematically:

$$
\hat{x}^{(0)} = x,\qquad
\hat{x}^{(m+1)} = \Pi_{B_\infty(x,\epsilon)}\!\Big(\hat{x}^{(m)} - \alpha\,\operatorname{sign}\!\big(\nabla_{\hat{x}}\,\mathcal{L}_{\mathrm{CE}}(\theta;\hat{x}^{(m)},\,c_f)\big)\Big),
$$

i.e. **gradient *descent* on the cross-entropy to the fall target** $c_f$ — equivalently, ascend $z_f$. The
sign is the **opposite** of the untargeted generators (see §14.2 for the explicit sign-convention check).

- **Applied only to non-fall windows** ($y_i\in\mathcal{C}_{\mathrm{nf}}$), with walk/run the priority via $w$.
- **Budget unchanged:** $\|\hat{x}-x\|_\infty\le\epsilon$, $\epsilon=0.030$, **no** $[0,1]$ clamp (processed
  CSI, matching `pgd_perturb`).
- **Training step count/size (pilot):** $M_{\mathrm{train}}=7$, $\alpha=\epsilon/4$ — identical to the
  committed *training* PGD budget (`--train-pgd-steps` default 7, `train_safety_guided_defense.py:367`), for
  CPU tractability. (Evaluation PGD stays at the thesis protocol $M=10$, $\alpha=\epsilon/6$.)
- **Same threat model as all prior work:** digital-domain $\ell_\infty$ on the processed tensor
  (Eq.~\ref{eq:perturb-domain}); no new attack surface.

---

## 6. Math-to-code mapping

| Math object | Python variable / function | Tensor shape / subset | Expected behavior | Failure check |
|---|---|---|---|---|
| logits $z_\theta(x)$ | `logits = model(x)` | `(B,7)` | finite, requires_grad in train | `assert torch.isfinite(logits).all()` |
| probs $p_\theta(x)$ | `probs = logits.softmax(1)` | `(B,7)` | rows sum to 1 | `assert torch.allclose(probs.sum(1),1)` |
| fall index $c_f$ | `fall_idx = tsg.FALL_CLASS_INDEX` | scalar `=1` | read from module, not literal | `assert fall_idx == 1` (§14.1) |
| walk/run idx $\mathcal{C}_{\mathrm{wr}}$ | `WALK, RUN = 2, 4` | scalars | from F script line 30 | `assert {WALK,RUN}=={2,4}` |
| nonfall mask | `nf = labels != fall_idx` | `(B,)` bool | True for $y\in\mathcal{C}_{\mathrm{nf}}$ | `assert nf.sum()==(labels!=1).sum()` |
| walk/run mask | `wr = (labels==WALK)|(labels==RUN)` | `(B,)` bool | subset of `nf` | `assert (wr & ~nf).sum()==0` |
| untargeted adv | `x_adv = tsg.pgd_perturb(model,xs,ys,crit,eps,7,eps/4)` | `(B,1,250,90)` | $\|x_{adv}-x\|_\infty\le\epsilon$ | `assert (x_adv-xs).abs().max()<=eps+1e-5` |
| **targeted adv** $\hat{x}$ | `x_tgt = targeted_fall_pgd(model,x_nf,fall_idx,eps,7,eps/4)` | `(B_nf,1,250,90)` | raises $z_f$ on nonfall | median $z_f(\hat{x}) > z_f(x_{nf})$ (§14.2) |
| $\mathcal{L}_{\mathrm{FWCE}}$ | `fwce = F.cross_entropy(logits, y, weight=class_w)` | scalar | fall weight 3 | `assert class_w[fall_idx]==3` |
| F motion margin | `relu(gm + zf - zt)[wr_adv].mean()` | scalar≥0 | 0 when $z_t>z_f+\gamma_m$ | `assert L_motion>=0` |
| F fall margin | `relu(gf + max_nonfall - zf)[fall_adv].mean()` | scalar≥0 | applies to true falls only | `assert fall_adv_mask.equal(y_adv==fall_idx)` |
| **G targeted loss** | `(src_w * relu(gt + zf_t - zt_t))[nf].mean()` | scalar≥0 | nonzero on targeted nonfall | `assert L_targeted.item()>0` early (§14.2) |
| **source weights** $w_c$ | `src_w = torch.where(wr, w_wr, 1.0)` | `(B_nf,)` | walk/run > others | `assert src_w[wr].min()>=src_w[~wr].max()` |
| total loss $\mathcal{L}_G$ | `loss = fwce + lam_s*L_src + lam_f*L_fall + lam_t*L_tgt` | scalar | finite | `assert torch.isfinite(loss)` |
| selection-v2 guard | `acc>=0.70 and macroF1>=0.65` (val) | bool | Eq.~\ref{eq:v2-guard} | guard computed on **val**, not test (§14.3) |
| FP-budget selection | `keep = argmax R_pgd^val s.t. guard ∧ FP_pgd^val<=B_fp ∧ wr_pgd^val<=B_wr` | ckpt | val-only | `assert split=='val'` in selector (§14.3) |

---

## 7. PyTorch pseudocode (NOT implementation)

```python
# ---- 0. setup (NEW script: scripts/train_variantG_targeted_margin.py) ----
assert args.seed == 42, "Variant G pilot is seed-42 only"          # §14.1 / §8
tsg  = tve.import_variantD()
fall_idx, K = tsg.FALL_CLASS_INDEX, tsg.NUM_CLASSES                # read, don't hardcode
assert fall_idx == 1 and K == 7                                    # §14.1 assertion
WALK, RUN = 2, 4
class_w = torch.ones(K); class_w[fall_idx] = 3.0                   # FWCE weights

def targeted_fall_pgd(model, x, fall_idx, eps, steps, alpha):      # §5, §14.2
    x0 = x.detach(); adv = x0.clone().detach()
    tgt = torch.full((x.size(0),), fall_idx, dtype=torch.long, device=x.device)
    for _ in range(steps):
        adv.requires_grad_(True)
        loss_to_fall = F.cross_entropy(model(adv).float(), tgt)
        model.zero_grad(); loss_to_fall.backward()
        with torch.no_grad():
            adv = adv - alpha * adv.grad.sign()                    # MINUS: descend CE-to-fall
            adv = x0 + torch.clamp(adv - x0, -eps, eps)            # project to L-inf ball
        adv = adv.detach()
    return adv                                                     # no [0,1] clamp (processed CSI)

# ---- per-batch training step ----
for xb, yb in train_loader:
    # 1. batch split  (reuse F/D 50% clean / 25% FGSM / 25% PGD indexing)
    idx_clean, idx_fgsm, idx_pgd = batch_split(len(xb))
    eps = sample_train_eps()  # {0.005,0.015,0.030}

    # 2. clean loss
    logits_clean = model(xb[idx_clean])
    fwce = F.cross_entropy(logits_clean.float(), yb[idx_clean], weight=class_w)

    # 3. untargeted FGSM/PGD adv  (existing helpers, true-label ascent)
    x_fgsm = tsg.fgsm_perturb(model, xb[idx_fgsm], yb[idx_fgsm], crit, eps)
    x_pgd  = tsg.pgd_perturb (model, xb[idx_pgd ], yb[idx_pgd ], crit, eps, 7, eps/4)
    x_adv  = cat(x_fgsm, x_pgd); y_adv = cat(yb[idx_fgsm], yb[idx_pgd])
    z_adv  = model(x_adv)

    # 4. targeted nonfall->fall adv (nonfall windows in the batch)
    nf = yb != fall_idx
    x_tgt = targeted_fall_pgd(model, xb[nf], fall_idx, eps, 7, eps/4)
    z_tgt = model(x_tgt); y_tgt = yb[nf]

    # source weights (heavier on walk/run)
    def src_w(labels): return torch.where((labels==WALK)|(labels==RUN),
                                          torch.tensor(args.w_wr), torch.tensor(1.0))

    # 5. targeted hard-negative loss  (G term A)
    zf_t = z_tgt[:, fall_idx]; zt_t = z_tgt.gather(1, y_tgt[:,None]).squeeze(1)
    L_tgt = (src_w(y_tgt) * relu(args.gamma_t + zf_t - zt_t)).mean()

    # 6. source-weighted motion-margin loss  (G term B; replaces F motion term)
    nfa = y_adv != fall_idx
    zf_a = z_adv[nfa, fall_idx]; zt_a = z_adv[nfa].gather(1, y_adv[nfa,None]).squeeze(1)
    L_src = (src_w(y_adv[nfa]) * relu(args.gamma_m + zf_a - zt_a)).mean()

    # 7. fall-preservation loss  (UNCHANGED from F; true-fall adv only)
    fa = y_adv == fall_idx
    if fa.any():
        zo = z_adv[fa].clone(); zo[:, fall_idx] = -inf
        L_fall = relu(args.gamma_f + zo.max(1).values - z_adv[fa, fall_idx]).mean()
    else:
        L_fall = zeros(())

    # 8. combine
    loss = fwce + args.lam_s*L_src + args.lam_f*L_fall + args.lam_t*L_tgt
    assert torch.isfinite(loss)
    optimizer.zero_grad(); loss.backward(); optimizer.step()

# ---- 9. checkpoint selection (selection-v2 + FP budget; VAL ONLY, §14.3) ----
# among saved candidates (v2safety/v2maxrec/v2lowFA/v2macroF1):
#   eligible = guard(acc>=0.70, macroF1>=0.65) AND FP_pgd_val<=B_fp AND wr_pgd_val<=B_wr
#   keep     = argmax_eligible  R_pgd_val
```

---

## 8. Code sanity checks before any full run

1. **Seed gate:** the new G script asserts `args.seed == 42`; seeds 43/44/45/46 are rejected for the pilot
   (frozen F's `seed not in (42,44)` gate is **not** reused or modified).
2. **Variant G accepts seed 42 only** (assertion above) — no other seed runs in the pilot.
3. **Targeted attack works:** on a frozen Variant F checkpoint, before any G training, median $z_f(\hat{x})$
   and median $P(\mathrm{fall})(\hat{x})$ on targeted non-fall windows **increase** vs clean non-fall
   (§14.2). If not, the targeted sign is wrong → fix before proceeding.
4. **Targeted loss nonzero:** `L_tgt > 0` on the first batch of targeted non-fall examples (else the term is
   inert).
5. **Source weights:** `src_w[walk|run] == w_wr > 1 == src_w[other nonfall]`; assert ordering.
6. **Fall-preservation subset:** `L_fall` mask equals `y_adv == fall_idx` exactly (true falls only).
7. **Subset correctness:** motion/source term applies only to non-fall adv; targeted term only to non-fall
   targeted; no term touches the wrong subset (assert mask cardinalities).
8. **Gradient flow:** gradients flow through `loss` to model params; attack-generation tensors are
   `.detach()`-ed (no graph leak through PGD bookkeeping) — assert `x_tgt.requires_grad is False` after gen.
9. **Finiteness:** a 2-epoch `--dry-run` smoke test yields finite `loss` every batch.
10. **Hygiene:** no `.pt` and no large logs staged by the smoke test (`git status` clean of binaries).

---

## 9. Seed-42 pilot design (exactly 3 settings — NOT run)

Fixed across all: $\lambda_m\!\to\!\lambda_s$ base = 1.0, $\lambda_f = 1.0$, $\gamma_m=\gamma_f=\gamma_t=0.5$,
fall weight 3, train $\epsilon\{0.005,0.015,0.030\}$, train PGD/targeted $M=7,\alpha=\epsilon/4$ — identical to
F except the two new ingredients. **Only the (λ_t, w_wr) pair varies**, so attribution is clean (§14.5).

| # | Setting | $\lambda_t$ | $w_{\mathrm{wr}}$ | $\gamma_m$ | $\gamma_f$ | Hypothesis tested |
|---|---|---|---|---|---|---|
| G1 | **Balanced A+B** | 1.0 | 2.0 | 0.5 | 0.5 | targeted HN **and** source weighting together improve the trade-off |
| G2 | **Targeted-heavy** | 2.0 | 1.0 | 0.5 | 0.5 | isolates **A** (targeted HN) — source weighting off |
| G3 | **Source-weighted / ablation anchor** | 0.0 | 2.0 | 0.5 | 0.5 | isolates **B**; with $\lambda_t{=}0,w_{wr}{=}2$. ($w_{wr}{=}1$ here would be numerically identical to Variant F.) |

Comparing G1 vs G2 vs G3 attributes the effect to A, B, or their combination. **Baselines reused, not
retrained:** Variant F seed-42 v2safety (115/80) and Variant D seed-42 are the references. **No seed
44/45/46** until a seed-42 setting meets pilot-success (§11).

---

## 10. Evaluation outputs (for the future pilot)

**Tables:** (1) Variant F vs G **clean** metrics (acc, macro-F1, fall recall, **clean FP, clean walk/run→fall,
clean precision, clean specificity** — §14.6); (2) Variant F vs G **PGD@0.030** safety metrics (recall+Wilson,
FP, walk/run→fall, specificity, precision, F1); (3) false-alarm **source anatomy** (per source class, reusing
`diagnose_variantF_false_alarms.py` style); (4) **confidence inversion before/after** (median P(fall),
fall-vs-rest margin, entropy for detected true falls vs FAs); (5) **PGD-20 durability**; (6) **success/failure
scorecard** vs §11/§12.

**Figures:** (1) recall-vs-FP **Pareto** (F vs G1/G2/G3); (2) **walk/run false-alarm breakdown**; (3)
**P(fall) distribution** true falls vs FAs; (4) **logit-margin distribution before/after**; (5) **PGD ε-sweep**
(18-point); (6) **PGD-10 vs PGD-20** durability.

---

## 11. Success criteria (pre-registered)

**Minimum useful:** clean acc ≥ 0.70 ∧ clean macro-F1 ≥ 0.65 ∧ clean fall recall ≥ 0.90 ∧ PGD recall ≥ 0.50
∧ PGD FP < 115 ∧ walk/run→fall < 80 ∧ PGD-20 recall > 0.

**Pilot success (gates seed-44):** PGD recall ≥ 0.50 ∧ PGD FP ≤ 90 ∧ walk/run→fall ≤ 60 ∧ PGD-20 recall ≥ 50%
of PGD-10 ∧ confidence inversion **reduced** (FA median P(fall) gap over detected-true-fall median shrinks).

**Strong success:** PGD recall ≥ 0.50 ∧ PGD FP ≤ 80 ∧ walk/run→fall ≤ 60 ∧ PGD-20 recall ≥ 75% of PGD-10 ∧
false alarms **no longer** have higher median P(fall) than detected true falls (inversion removed or
substantially reduced).

---

## 12. Failure criteria (pre-registered)

Variant G **fails** if any: clean guard fails; clean fall recall < 0.90; PGD recall drops below the 0.50 useful
floor; **FP reduction only by destroying recall** (FP<115 only at recall below floor — same inverted frontier
as the diagnostic); **confidence inversion unchanged**; PGD-20 collapses (≈0 or <50% of PGD-10, or recall
*increases* PGD-10→20); **no setting** improves F's recall/FP trade-off; or the improvement is too small
(within Wilson/run-to-run noise) to justify seed-44 validation.

---

## 13. Advisor recommendation

- **Implement Variant G after this spec is approved?** **Yes — a bounded seed-42 pilot is the right next
  research step**, *if* the user wants to push past Variant F. The spec is now unambiguous; implementation is
  a new ~1-file script reusing F's helpers, 3 runs (~one F-pilot of compute). The pilot directly tests the
  diagnostic's central hypothesis (is the confidence inversion *trainable away?*) — high information value.
- **Keep the Chapter 6 draft parked?** **Yes, parked but not discarded.** Chapter 6 already stands on
  committed evidence (Variant F + diagnostic). If the G pilot succeeds, promote G into Ch6 as the new final
  result; if it fails, Ch6 is already correct (F final, G future work). Either way the draft is not edited
  into Overleaf until the G outcome is known.
- **Seeds 45–46?** **Wait.** They add confirmatory breadth to F but no new mechanism; the G pilot outranks
  them on value-per-compute. Run 45–46 only if neither G nor further mechanism work is pursued.
- **What would make Variant G a thesis result (not future work)?** It must clear **pilot-success on seed 42**
  *and* pass a pre-registered **seed-44** independent validation — i.e. an improvement that is (a) a genuine
  Pareto move over Variant F (not recall-for-FP or FP-for-recall), (b) accompanied by **reduced confidence
  inversion**, (c) PGD-20 durable, and (d) reproduced on the held-out seed. Short of that, Variant F remains
  the final implemented defense and Variant G stays future work (§14.9).

---

## 14. Critical correctness requirements

### 14.1 Class-index verification (read from repo, not memory)
- **Fall class index = `tsg.FALL_CLASS_INDEX = 1`** — `scripts/train_safety_guided_defense.py:111`.
- **Num classes = `tsg.NUM_CLASSES = 7`** — `scripts/train_safety_guided_defense.py:112`.
- **Walk = 2, Run = 4** — `scripts/train_variantF_motion_margin.py:30` (`WALK, RUN = 2, 4`).
- **Non-fall set = {0,2,3,4,5,6}** (all classes except `fall_idx`). Human-readable order used by the export /
  diagnostic tooling: `0 lie down, 1 fall, 2 walk, 3 pickup, 4 run, 5 sit down, 6 stand up` (UT-HAR/SenseFi
  benchmark label order, as used in `diagnose_variantF_false_alarms.py`).
- **Implementation must assert at startup** (do not hardcode): `assert tsg.FALL_CLASS_INDEX == 1 and
  tsg.NUM_CLASSES == 7 and (WALK, RUN) == (2, 4)`. If the benchmark exposes a label list, additionally assert
  `labels[1]=="fall"`, `labels[2]=="walk"`, `labels[4]=="run"` before training.

### 14.2 Targeted-PGD sign convention
The existing generators **ascend** CE on the *true* label (`adv = x + α·sign(∇CE(·,y_true))`,
`train_safety_guided_defense.py:174,190`) — they push **away** from the true class. Targeted-to-fall is the
**opposite sign**: the implementation **descends** CE toward the fall target (`adv = x − α·sign(∇CE(·,c_f))`),
equivalently **ascends** $z_f$. The spec mandates **descent on CE-to-fall** (pseudocode §7).
- **Failure check (mandatory pre-train, §8.3):** on a frozen F checkpoint, median $z_f(\hat{x})$ and median
  $P(\mathrm{fall})(\hat{x})$ over targeted non-fall windows must **increase** vs the clean non-fall windows.
  If they do **not** increase, the sign is wrong (likely the untargeted `+` was used) — **halt and fix**.

### 14.3 No validation/test leakage
- **Train split:** training + all adversarial generation (untargeted and targeted) during training.
- **Validation split:** checkpoint selection **and** false-alert-budget selection (guards, $B_{fp}$, $B_{wr}$,
  SafetyScore) — Eq.~\ref{eq:v2-guard}/\ref{eq:safetyscore}.
- **Test split:** used **once** for final reporting only.
- **No checkpoint, threshold, margin, or operating-point may be chosen using the test set.** The selector
  asserts it reads `split=='val'`; test metrics are computed only after selection is frozen.

### 14.4 Split & seed reproducibility logging
Each run must log to its `metadata.json`: random seed; train/val/test split identifiers + sizes; **git commit
hash**; exact Python command; all hyperparameters ($\lambda_t,\lambda_s,\lambda_f,w_{wr},\gamma_{m,f,t}$, train
ε, PGD steps/α); environment summary (Python/torch/numpy versions, device); checkpoint-selection criteria
($B_{fp},B_{wr}$, guard); timestamp (UTC); and whether Comet/online logging is disabled (it must be, for
offline determinism — matching prior runs).

### 14.5 Ablation requirement
The three settings (§9) are an ablation by construction: **G2 isolates A** (targeted HN, source off), **G3
isolates B** (source-weighted, targeted off — and equals Variant F when $w_{wr}=1$), **G1 is the combination**.
Only the $(\lambda_t, w_{wr})$ pair changes between settings — never multiple ingredients at once — so the
pilot is interpretable.

### 14.6 Clean false-alarm burden
Evaluation must report **clean** alongside attacked: clean false fall alarms, clean walk/run→fall, clean
precision, clean specificity (Table 1, §10). **A setting that lowers PGD FP but raises clean FP is rejected** —
clean FP must not exceed Variant F's clean FP by more than a small pre-set tolerance (record F's clean FP as
the reference at eval time).

### 14.7 Stronger-attack sanity beyond PGD-20
PGD-20 stays required for every candidate. **If a selected candidate looks unusually strong** (e.g. PGD-20 ≥
75% of PGD-10 with low FP), run a **PGD-40 and/or multiple-random-start** check **on that candidate only**
(Eq.~\ref{eq:stronger-pgd}). This is a **gradient-masking sanity check, not tuning** — recall must remain
non-increasing PGD-10→20→40; any *increase* signals masking and disqualifies the result.

### 14.8 Runtime & stop rules
- Seed-42 pilot **only**; **exactly 3 settings**; **no extra settings without a new written addendum**.
- **Stop** if all three settings fail the clean guard (the targeted pressure is over-suppressing fall).
- **Do not proceed to seed 44** unless ≥1 setting meets the pre-registered **pilot-success** criteria (§11).
- Approximate budget: 3 training runs + eval ≈ one Variant F pilot (CPU). No background sweeps.

### 14.9 Thesis promotion rule
Variant G is promoted from *future work* to *implemented thesis result* **only if all** hold: (1) a seed-42
setting meets **at least pilot-success**; (2) the improvement is a **genuine Pareto move** over Variant F (not
recall traded for FP or FP traded for recall); (3) **confidence inversion is reduced**; (4) **PGD-20 does not
collapse** (and passes the §14.7 masking check if triggered); and (5) the result is strong enough to justify a
**pre-registered seed-44 independent validation** — which it must then **pass**. Otherwise **Variant G remains
future work and Variant F remains the final implemented defense.**

---

## Scope reminder
Specification only — Variant G is **not** implemented, trained, attacked, or evaluated. No script modified, no
`.tex` edited, no seeds 45–46, no artifact overwritten. Window-level, digital-domain, white-box, processed CSI
tensors; **not** solved, **not** certified, **not** clinical, **not** over-the-air.
