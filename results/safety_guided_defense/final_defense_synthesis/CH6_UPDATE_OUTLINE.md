# Chapter 6 update outline — designed-framework structure

> **Outline only — no `.tex` edited.** Specifies how to update the committed Chapter 6 draft
> (`defense_line_synthesis/CH6_DEFENSE_DRAFT.md`) so the chapter reads as a **designed defense framework**
> (mathematical objective → code → evidence → interpretation), **not** a story reverse-engineered after
> seeing good tables. After commit `656cd50`, Variant G is no longer future work — it is an **implemented,
> two-seed-validated lower-false-alarm operating point**. Scope unchanged: window-level, processed CSI
> tensor, digital-domain, white-box; no solved/certified/clinical/over-the-air claim.

## Required section order (every defense subsection follows this)

The chapter — and each defense variant within it — must be written in this fixed order:

**1. Problem / failure mode (from earlier chapters) → 2. Mathematical objective formulation → 3. Mechanistic
expectation → 4. Algorithm / code mapping → 5. Experimental protocol → 6. Results tables / figures → 7.
Safety-proxy interpretation → 8. Scope boundaries.**

The mathematical objective and the code mapping are written **before** any table. In short, the mandated flow
is: **objective formulation → algorithm/code mapping → experimental evidence → safety-proxy interpretation.**

## A. Chapter-claim revision (§6.1)

Revise to: **"Two safety-proxy-aware defenses are *designed*, *implemented*, and *validated* as distinct
operating points on a safety-relevant attacked recall / false-alarm frontier — Variant F (higher attacked
recall) and Variant G G1 (lower false alarms) — each with two-seed evidence."** Keep the trade-off framing;
do not claim a single dominant defense. State up front that objectives were formalized *before* evaluation.

## B. Section plan (each in the 8-step order above)

| § | Title | Notes |
|---|---|---|
| 6.1 | Overview & chapter claim | designed-framework framing (§A) |
| 6.2 | Threat model, classifier, safety-proxy metrics | unchanged |
| 6.3 | Failure modes & the objective family | **new emphasis:** present notation + objectives (1)–(6) from `FINAL_DEFENSE_SYNTHESIS.md` *before* any result; each failure mode → its term |
| 6.4 | Variant D / E / selection-v2 | objective → code → evidence for each |
| 6.5 | **Variant F** | written in the 4-step order (§C) |
| 6.6 | Residual false-alarm diagnostic | confidence inversion (Diagnosis C); motivates §6.7 — keep visible |
| 6.7 | **Variant G** (was "future work") | written in the 4-step order (§C); promote from future work to implemented |
| 6.7.1 | Seed-42 pilot + ablation | targeted term = active ingredient; MINIMUM USEFUL |
| 6.7.2 | Filterability re-test | Diagnosis A; test-output probe that justifies seed-44 |
| 6.7.3 | Seed-44 pre-registered validation | validation-only gate; STRONG VALIDATION |
| 6.8 | Conclusions: two validated operating points | §G wording |

## C. How to write Variant F and Variant G (mandatory 4-step order)

For **each** of Variant F and Variant G, write strictly in this order:

1. **Define the objective mathematically** — give $\mathcal{L}_F$ (eq. 5) / $\mathcal{L}_G$ (eq. 6) and the
   terms (1)–(4), with the targeted-PGD sign convention for $x^{tgt}$. State the *expected mechanism* first.
2. **Show how the objective appears in code** — the math-to-code mapping table: `variantG_margin_terms()`,
   `targeted_fall_pgd()`, `source_weights()`, selection-v2 in `run_full`, the `--split val` export, and the
   validation-selected gate in `analyze_variantG_g1_seed44.py`. (Reuse the table in
   `FINAL_DEFENSE_SYNTHESIS.md`.)
3. **Present tables/figures** — only now: clean/PGD/PGD-20 tables, the inversion table, the frontier figure.
4. **Interpret whether the mechanism was supported** — say the evidence *supports / fails to support* the
   intended behavior; never that the math *proved* it.

## D. Tables to add

1. **Objective family table** (eqs. 1–6) — in §6.3, before results.
2. **Math-to-code mapping table** — in §6.5 and §6.7, before results.
3. **Final frontier table** (from `FINAL_DEFENSE_SYNTHESIS.md`): clean acc / macro-F1 / clean fall recall /
   PGD recall / FP / walk/run→fall / PGD-20 / inversion gap / decision, for the 6 required rows (+ D-seed44,
   FGSM-seed44 floor).
4. **Variant G seed-42 ablation table** (G1/G2/G3) — isolates the targeted term.
5. **Confidence-inversion before/after table** (Variant F vs G1, both seeds): +0.103/+0.121 → +0.012/+0.043.
6. **Seed-44 validation table** (raw + gated G1 vs F / D / FGSM floor).

## E. Figures to add

1. **Recall-vs-FP frontier scatter** marking Variant F (both seeds) and Variant G G1 (both seeds) as two
   labelled operating points (Variant D + FGSM floor for context) — the chapter's key figure.
2. **Seed-44 Pareto** (`variantG.../seed44/figures/fig_G1_seed44_pareto.png`).
3. **Confidence-inversion plots** side by side (Variant F `fig_separability` vs G1 `fig_G1_separability`) —
   the mechanism figure.
4. **PGD ε-sweep** for Variant G G1 seed-44 (`fig_G1_seed44_epsilon_sweep.png`).

## F. Where / how to frame Variant F vs Variant G G1

- Introduce them as **two validated operating points** on the frontier.
- **Variant F** = higher-attacked-recall reference defense; **Variant G G1** = lower-false-alarm validated
  defense (seed-44 FP 65 vs 112), achieved by the inversion-reducing objective.
- State plainly: on seed 44, **G1 is not strictly Pareto-dominant** — PGD recall ~1 fall window lower (0.600
  vs 0.622), Wilson intervals overlap; the gain is **lower false alarms at matched recall** with better clean
  accuracy and durability. Present as **operating-point selection**, not a winner.

## Avoid Reverse-Engineering Language

The chapter must not read as a post-hoc story. **Do not write:**

- "After seeing the results, we explain…"
- "The model proves…"
- "This solves false alarms…"
- "This is clinically validated…"

**Use instead:**

- "The objective is designed to…"
- "The implemented term corresponds to…"
- "The empirical results support…" / "…fail to support…"
- "The evidence suggests…"
- "Within the window-level digital-domain evaluation…"

Additional discipline:
- Math **defines / motivates / constrains**; experiments **validate / support / fail to support**. Never say
  math *proves* behavior.
- Pair every recall number with its **Wilson interval** and note overlap where it exists.
- Call seed-42 filterability thresholds **diagnostic / test-tuned**; the seed-44 gate **validation-selected**.
  Never present a test-tuned threshold as final.
- Keep the §6.6 limitation visible — Variant F's residual false alarms *motivated* Variant G.
- Report the **clean-accuracy cost** honestly.

## Safety wording (keep)

- "**safety-relevant**" is acceptable.
- "**clinically meaningful**" must be avoided.
- "**clinical validation**" must not be claimed.
- No "solved," "deployable," "certified," or "over-the-air" claims; keep "window-level, digital-domain,
  white-box, processed CSI tensor."

## G. Final chapter conclusion (suggested wording)

> Chapter 6 **designs** a family of safety-proxy-aware adversarial-training objectives for WiFi-CSI fall
> detection, **implements** them, and **evaluates** whether they move the classifier along a safety-relevant
> attacked recall / false-alarm frontier under white-box PGD on processed CSI tensors. Each objective is
> motivated by a named failure mode and **defines** an intended behavior; the experiments then **support or
> fail to support** that behavior. The endpoint is **two validated operating points**, each with two-seed
> evidence: **Variant F**, the higher-attacked-recall margin-aware defense (recall 0.62–0.67), and **Variant
> G G1**, a targeted hard-negative defense **designed to** reduce the residual confidence inversion, which on
> an independent pre-registered seed **cuts false fall alarms ~42% at matched recall** with higher clean
> accuracy and more durable recall. Variant G G1 is **not** strictly dominant over Variant F — its attacked
> recall is marginally (non-significantly) lower — so the two are reported as a **recall-vs-false-alarm
> choice**, not a single solution. The contribution is methodological: a measurable failure mode can be
> **diagnosed, formalized as a training objective, implemented, and validated**, with the effect replicating
> across seeds. All results are window-level, digital-domain, white-box evaluations on processed CSI tensors
> with quantified uncertainty; none constitutes solved, certified, clinical, or over-the-air robustness.

## H. Process note (do NOT do yet)

Editing the live thesis/Overleaf `.tex` is **out of scope** until explicitly authorized. When authorized,
apply A–G to the committed `CH6_DEFENSE_DRAFT.md` first, review, *then* transfer to `.tex`. Promote the
math-package `eq:margin-loss-future` note: the Variant F margin loss **and** the Variant G targeted term are
now implemented and validated (Variant G was the only "future work" objective in the original draft).
