# Post-closure target-gap analysis — the high-recall / low-FP goal remains unmet

> **Analysis & synthesis only.** No training, attacks, evaluation, H2/H3, seed 44/45/46; no script change,
> no `.tex` edit, no artifact overwrite, no commit until reviewed. Reads committed evidence through
> `61c8d18` (closure) / `737a559` (H1 pilot). Window-level, digital-domain, white-box, processed CSI
> tensors; test n=500 (45 fall / 455 non-fall), ε=0.030. **No product / clinical / deployment / certified /
> over-the-air claim.**

## Why this memo exists

The committed `FINAL_DEFENSE_LINE_CLOSURE.md` correctly records the *current* validated operating points
(Variant F, Variant G G1) and the rejected pilot (Variant H H1). **It is a record of the line as run — not
a statement that the defense is good enough.** The overall target I care about — **PGD fall recall > 80%
AND attacked false-alarm rate < 10% together** — is **still unmet**. This memo makes the residual gap
explicit and frames the next research decision *before* any Chapter 6 finalization. **It does not start any
experiment.**

## 1. What is still insufficient

| model (committed) | PGD recall | PGD FP (rate) | clean guard | status |
|---|---|---|---|---|
| Variant F seed44 | **0.622** | 112 (24.6%) | holds (acc 0.700) | validated higher-recall, **but high FP** |
| Variant G G1 seed44 | **0.600** | **65 (14.3%)** | holds (acc 0.746) | validated lower-FP, **but recall ~0.60 and FP still > 10%** |
| Variant H H1 seed42 | 0.489 | 94 (20.7%) | **fails** (acc 0.662, mF1 0.591) | **REJECT** (recall < 0.60, FP only by recall loss) |

- **Attacked fall recall is only ~0.60–0.622** — far below a strong fall-detection defense; under PGD, ~38–40%
  of falls are still missed.
- **Best attacked false-alarm rate is Variant G G1 at 65/455 = 14.3%** — close to the < 10% goal but **still
  above it**.
- **Variant H H1** (the attempt to push both) was **rejected**: it lost recall and broke the clean guard.
- **Conclusion:** the line shows **partial robustness recovery** (recall up from the FGSM floor 0.044, FP
  down from Variant D's 167), **not** a strong high-recall / low-FP result. No single defense is near the
  joint target.

## 2. Remaining target gap (anchored to Variant G G1 seed44, the closest point)

- **Recall target > 80% ⇒ ≥ 37/45 detected falls.** G1 seed44 detects **27/45** ⇒ **needs +10 true positives.**
- **False-alarm target < 10% ⇒ FP ≤ 45/455.** G1 seed44 has **FP = 65** ⇒ **needs −20 false positives.**
- **Both must improve simultaneously**, and the committed feasibility analysis showed they are **coupled** at
  the fall↔motion boundary: post-hoc gating **cannot** reach the target (gating cannot create true positives;
  max recall at FP ≤ 45 is 0.356), and the one training attempt at joint pressure (H1) traded recall for a
  small FP cut. **The gap is a two-tail separation problem that remains open.**

For Variant F (the higher-recall point), the gap is even wider on FP: recall 0.622 (still < 0.80, needs
+8 TP from 28/45) **and** FP 112 (needs −67 to reach ≤ 45).

## 3. Why not move directly to Chapter 6

- Chapter 6 *can* eventually report **Variant F and Variant G G1 as partial validated operating points** —
  that is honest and defensible.
- **But** before finalizing Chapter 6, a decision is needed on whether to attempt **one more targeted
  experiment**, because **0.60 recall is too low** and **14.3% FP is not yet below target**. Finalizing now
  risks locking in a weaker result than one more disciplined experiment might achieve.
- **Framing discipline:** the closure must be read as *"current line closed; target gap remains,"* **not**
  *"the defense is good enough."* Chapter 6, whenever written, must carry the same framing (partial
  operating points; joint target unmet → future work).

## 4. Plausible next research paths

**Option A — rebalanced dual-tail design (a *new* design, NOT the committed H2/H3).**
Motivated directly by the H1 failure analysis (committed): H1 over-suppressed recall and its fall-rescue was
under-powered (k ≈ 1 fall/batch). A rebalanced design would: **lower `lambda_b`** (less FP-suppression
pressure), **raise `lambda_r`** (stronger fall rescue), and **add a `k_abs` floor for the fall-rescue term**
so it covers more than one fall window per batch. *Note:* the committed H2/H3 keep `lambda_r = 0.5` and do
**not** address the under-power, so they are unlikely to fix the recall collapse — this Option A is a
**different** setting, requiring a new pre-registration.

**Option B — architecture-controlled defense study.**
Hold the defense objective fixed and test whether **LeNet capacity** limits fall↔motion separability.
Candidate architectures: ResNet18, GRU, BiLSTM. Must be **separately pre-registered**, **no random
architecture search**, everything else fixed (same loss, same protocol) so the architecture effect is
isolated.

**Option C — temporal / event-level aggregation analysis.**
Window-level metrics may be harsher than event-level fall-alarm behavior; aggregating adjacent windows could
suppress **isolated** false alarms and recover **event-level** sensitivity. Must be framed as
**benchmark/event-level post-processing**, an *orthogonal* (non-window-level) route — **not** clinical
validation, and not a substitute for the training fix.

**Option D — stop experiments and write Chapter 6 honestly.**
Report Variant F / Variant G G1 as **partial operating points**, state plainly that the joint target
(> 80% recall AND < 10% FP) **remains unmet**, and place it as **future work**.

## 5. Option ranking

| option | expected benefit | risk | compute cost | thesis value | recommendation |
|---|---|---|---|---|---|
| **A — rebalanced dual-tail** | directly targets the H1 failure mode; best chance to move *both* tails (recall + FP) at once | may still over/under-suppress; coupled tails may not separate; single-seed pilot only | **medium** (~1 seed-42 pilot ≈ 2–3 h CPU + eval, like H1) | **high** — a *positive* dual-tail result would materially strengthen Chapter 6; an honest negative still informs future work | **Recommended first** (as a pre-registered seed-42 pilot, not an auto-run) |
| **B — architecture study** | tests whether capacity, not the loss, is the ceiling; could lift the whole frontier | confounds objective vs architecture if not isolated; larger models = longer runs; may not help | **high** (multiple architectures × train + eval; ≫ Option A) | medium-high — valuable but a larger, separate study; better *after* A clarifies whether the loss can reach the target on LeNet | Defer; pre-register only if A stalls |
| **C — event-level aggregation** | cheap; may cut isolated FAs and raise event sensitivity without retraining | risks overclaiming if framed as deployment/clinical; changes the evaluation unit (must be stated) | **low** (analysis only on committed outputs) | medium — a useful complementary framing, but changes the metric definition; not a window-level defense result | Optional complement; pre-register the protocol first |
| **D — stop & write Chapter 6** | locks in an honest partial result now; zero risk | freezes a weaker result; forgoes a plausible improvement from A | **none** | medium — defensible but leaves recall 0.60 / FP 14.3% as the headline | Fallback if no further compute is available |

## 6. Recommended next action

**Recommended: create a *new* pre-registration for a rebalanced dual-tail design (Option A)** — lower
`lambda_b`, higher `lambda_r`, and a `k_abs` floor for fall-rescue — to be run as a **single seed-42 pilot
only after the pre-registration is reviewed and committed.** This is the cheapest path that *directly*
targets the documented H1 failure mode and has the best chance of moving recall and FP together.

- **Do NOT** auto-run any training. The next deliverable is a **pre-registration document**, not a run.
- **Do NOT** run the committed H2/H3 (they do not address the under-power and are unlikely to help).
- If Option A's seed-42 pilot fails to reach the pilot bar, **fall back to Option D** (write Chapter 6 as a
  partial result) and consider Option B / C as separately pre-registered future studies.
- Event-level aggregation (Option C) may be pre-registered in parallel as a cheap complementary analysis.

**Decision owner: the user.** This memo recommends Option A (new pre-registration) but starts nothing.

## 7. No-claim boundary

> **NO-CLAIM BOUNDARY.** The current work does **NOT**:
> - achieve **> 80% PGD fall recall with < 10% false alarms** (this joint target **remains unmet**);
> - claim deployment readiness;
> - claim clinical performance / clinical validation;
> - claim certified robustness;
> - claim product readiness;
> - claim over-the-air attack resistance or a universal defense.
>
> All results are window-level, processed-CSI-tensor, digital-domain, white-box, benchmark-level,
> research-stage, with quantified uncertainty (Wilson intervals, n_f = 45). The committed defenses are
> **partial** safety-proxy operating points; the high-recall / low-FP goal is **future work**.

### Scope reminder
Analysis/synthesis only — no training/attacks/evaluation/H2/H3/seed44-46/script change/`.tex` edit/artifact
overwrite. Recommends a pre-registration (Option A); starts no experiment.
