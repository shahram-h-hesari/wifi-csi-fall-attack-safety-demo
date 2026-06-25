# Priority 2 — Cross-Architecture Multi-Seed Summary (Final)

Thesis-ready roll-up of the adversarial window-level safety-proxy collapse across
**five architecture configurations** — spanning shallow CNN, deep CNN, recurrent,
bidirectional recurrent, and attention-based designs — on the UT-HAR/SenseFi
pipeline. Built **only** from already-committed result files (no experiment rerun;
no raw file modified). **Final state: all five configurations now have full
five-seed clean-qualified evidence.**

> Note on "architecture configurations": LeNet and ResNet18 are **both CNN-family**
> models (shallow vs deep), so this is **not** five distinct model families. It is
> **five architecture configurations** spanning shallow CNN (LeNet), deep CNN
> (ResNet18), recurrent (GRU), bidirectional recurrent (BiLSTM), and attention-based
> (Transformer/ViT) designs.

All quantities are window-level fall-vs-non-fall safety proxies on the held-out
test split (n = 500 windows; 45 fall / 455 non-fall), at matched ε = 0.030
(FGSM single-step L∞; PGD L∞, 10 steps, α = ε/6). Means are across each
configuration's **clean-qualified** seeds; SD is sample SD (ddof=1).

## Evidence tiers
All five configurations are **full five-seed clean-qualified** results:
1. **LeNet (shallow CNN)** — seeds 42–46. PGD@0.03 exact collapse 5/5.
2. **GRU (recurrent)** — seeds 42–46. PGD@0.03 exact collapse 5/5.
3. **BiLSTM (bidirectional recurrent)** — seeds 42–46. PGD@0.03 exact collapse 4/5;
   all 5/5 reach PGD 0.000 by ε ≤ 0.035 (seed-45 caveat below).
4. **Transformer (attention/ViT)** — seeds 42–46. PGD@0.03 exact collapse 5/5
   (seed-45 FGSM caveat below).
5. **ResNet18 (deep CNN)** — five clean-qualified seeds (42, 43, 44, 46, 48), with
   **two excluded divergent attempts (seeds 45, 47)**. PGD@0.03 exact collapse 5/5.

## Cross-architecture table
| Architecture | Type | Clean-qual. seeds | Clean fall recall | FGSM@0.03 fall recall | PGD@0.03 fall recall | Exact 0.000 @ε=0.03 (FGSM / PGD) | Evidence status |
|---|---|---|---|---|---|---|---|
| LeNet | shallow CNN | 5/5 (42–46) | 0.978 ± 0.016 | 0.049 ± 0.046 | **0.000 ± 0.000** | 2/5 / **5/5** | full five-seed |
| GRU | recurrent | 5/5 (42–46) | 0.920 ± 0.012 | 0.009 ± 0.012 | **0.000 ± 0.000** | 3/5 / **5/5** | full five-seed |
| BiLSTM | bidirectional recurrent | 5/5 (42–46) | 0.884 ± 0.043 | 0.022 ± 0.050 | 0.004 ± 0.010 | 4/5 / **4/5** † | full five-seed |
| Transformer | attention (ViT) | 5/5 (42–46) | 0.947 ± 0.049 | 0.004 ± 0.010 | **0.000 ± 0.000** | 4/5 / **5/5** ‡ | full five-seed |
| ResNet18 | deep CNN | 5/5 (42,43,44,46,48) | 0.978 ± 0.016 | 0.009 ± 0.012 | **0.000 ± 0.000** | 3/5 / **5/5** | full five clean-qualified (2 excluded) §|

All clean-qualified seeds of all five configurations reach exactly 0.000 PGD fall
recall **by ε ≤ 0.035** (LeNet ≤0.0125, GRU ≤0.025, BiLSTM ≤0.035, Transformer
≤0.030, ResNet18 ≤0.010).

† **BiLSTM seed 45** is the exception at ε=0.03: FGSM@0.03 = **0.111**, PGD@0.03 =
**0.022**; its FGSM fall recall never reaches exactly 0.000 within the 0.0–0.075
grid (bottoms at 0.022), and its PGD fall recall reaches exactly 0.000 at ε=0.035.
The other four BiLSTM seeds reach exactly 0.000 under both attacks at ε=0.03.

‡ **Transformer seed 45** is the FGSM exception at ε=0.03: FGSM@0.03 = **0.022**
(one residual TP), reaching exactly 0.000 at ε=0.040; PGD@0.03 = **0.000**. The
other four Transformer seeds reach exactly 0.000 under both attacks at ε=0.03;
all five reach FGSM 0.000 by ε ≤ 0.040 and PGD 0.000 by ε ≤ 0.030.

§ **ResNet18 required seven fixed-protocol runs (seeds 42–48) to obtain five
clean-qualified seeds.** Seeds 45 and 47 each diverged to walk-only predictors
(clean accuracy 0.294, clean fall recall 0.000, val loss ~10¹⁵ / ~8.6×10⁶) and were
**excluded before attack evaluation** — they are **not** in any clean-qualified
robustness statistic. The exclusions are training-stability observations, not
adversarial-robustness evidence. No protocol/lr/optimizer change was made to rescue
them.

## What is consistent across all five configurations
- Every clean-qualified configuration is a clean classifier with meaningful fall
  recall beforehand (clean fall recall 0.884–0.978; BiLSTM weakest, LeNet/ResNet18
  strongest).
- **Matched PGD at ε=0.03 drives window-level fall recall to exactly 0.000 in every
  clean-qualified seed of LeNet, GRU, Transformer, and ResNet18 (5/5 each), and in
  4/5 BiLSTM seeds.** Counting all clean-qualified seeds across all five
  configurations, PGD@0.03 reaches exactly 0.000 in **24/25 seed-runs** — the lone
  exception is BiLSTM seed 45 (PGD@0.03 = 0.022), which still reaches exactly 0.000
  by ε=0.035.
- **Every clean-qualified seed of every configuration reaches exactly 0.000 PGD fall
  recall by ε ≤ 0.035.**
- FGSM at ε=0.03 is severe but **less uniformly exact**: exact-0.000 counts are
  LeNet 2/5, GRU 3/5, BiLSTM 4/5, Transformer 4/5, ResNet18 3/5. FGSM should be
  described as "severe/near-total," **not** "universal exact collapse," at the
  matched budget.

## Thesis-ready table text (LaTeX; not yet inserted into any .tex)
```latex
% Final cross-architecture multi-seed safety-proxy collapse (UT-HAR, eps=0.03).
% Window-level fall recall, mean +/- SD over clean-qualified seeds (5 per config).
\begin{tabular}{l l c c c c c l}
\toprule
Architecture & Type & cq seeds & Clean recall & FGSM$_{0.03}$ & PGD$_{0.03}$
  & FGSM/PGD exact @0.03 & Evidence \\
\midrule
LeNet       & shallow CNN             & 5/5 & $0.978\pm0.016$ & $0.049\pm0.046$ & $0.000\pm0.000$ & 2/5 / 5/5 & full five-seed \\
GRU         & recurrent               & 5/5 & $0.920\pm0.012$ & $0.009\pm0.012$ & $0.000\pm0.000$ & 3/5 / 5/5 & full five-seed \\
BiLSTM      & bidirectional recurrent & 5/5 & $0.884\pm0.043$ & $0.022\pm0.050$ & $0.004\pm0.010$ & 4/5 / 4/5 & full five-seed \\
Transformer & attention (ViT)         & 5/5 & $0.947\pm0.049$ & $0.004\pm0.010$ & $0.000\pm0.000$ & 4/5 / 5/5 & full five-seed \\
ResNet18    & deep CNN                & 5/5 & $0.978\pm0.016$ & $0.009\pm0.012$ & $0.000\pm0.000$ & 3/5 / 5/5 & full five-seed (2 excl.) \\
\bottomrule
\end{tabular}
% ResNet18: 5 clean-qualified of 7 runs (seeds 45, 47 diverged, excluded).
% BiLSTM seed 45 / Transformer seed 45 retain small FGSM residual at eps=0.03;
% all clean-qualified seeds of all five configs reach PGD 0.000 by eps<=0.035.
```

## Generated package files
- `results/cross_architecture/cross_architecture_multiseed_summary.csv` (this roll-up)
- Per-architecture aggregates / sources (all five-seed):
  - LeNet: `results/multiseed_robustness/multiseed_summary_stats.csv` (+ `notes/thesis_ready_multiseed_summary.md`)
  - GRU: `results/cross_architecture/gru/gru_clean_qualified_summary.csv` (+ `notes/priority2_gru_5seed_aggregate.md`)
  - BiLSTM: `results/cross_architecture/bilstm/bilstm_clean_qualified_summary.csv` (+ `notes/priority2_bilstm_5seed_aggregate.md`)
  - Transformer: `results/cross_architecture/transformer/transformer_clean_qualified_summary.csv` (+ `notes/priority2_transformer_5seed_aggregate.md`)
  - ResNet18: `results/cross_architecture/resnet/resnet18_clean_qualified_summary.csv` (+ `notes/priority2_resnet18_multiseed_summary.md`)

## Thesis-safe interpretation
Holding the dataset, split, preprocessing, attack settings, and metric definitions
fixed, the adversarial window-level safety-proxy collapse reproduces across five
architecture configurations — a shallow CNN (LeNet), a deep CNN (ResNet18), a
recurrent network (GRU), a bidirectional recurrent network (BiLSTM), and an
attention-based network (Transformer/ViT) — each with a full five-seed
clean-qualified evaluation. Matched PGD at ε=0.030 drives window-level fall recall
to exactly 0.000 in every clean-qualified seed of LeNet, GRU, Transformer, and
ResNet18 (5/5 each) and in four of five BiLSTM seeds; the lone exception, BiLSTM
seed 45, still reaches exactly 0.000 by ε=0.035. Thus **every clean-qualified seed
of every configuration reaches total PGD fall-recall collapse by ε ≤ 0.035**,
despite high-to-moderate clean fall recall beforehand (0.884–0.978). FGSM at the
same budget is severe but less uniformly exact (exact-0.000 at ε=0.03 in 2/5–4/5
seeds per configuration), so PGD is the consistent worst-case attack. Because the
collapse reproduces across shallow CNN, deep CNN, recurrent, bidirectional-recurrent,
and attention configurations under an identical data split, attack configuration,
and metric definition — and across five seeds each — the missed-fall safety-proxy
failure is not an artifact of one architecture configuration or one training seed.

A secondary observation: **ResNet18 was the most training-unstable configuration**,
requiring seven fixed-protocol runs to yield five clean-qualified seeds (seeds 45
and 47 diverged to walk-only predictors and were excluded). This is a
training-stability property of the deep CNN under the fixed protocol, separate from
the adversarial result.

## Boundary language (must accompany any use of these numbers)
- **Full five-seed clean-qualified evidence now exists for all five configurations**
  (LeNet, GRU, BiLSTM, Transformer, ResNet18). For ResNet18, "five clean-qualified
  seeds" means seeds 42, 43, 44, 46, 48; **seeds 45 and 47 are excluded
  divergences** and must never be counted in robustness statistics.
- **Do not overstate FGSM as universal exact collapse at ε=0.03.** PGD is the
  consistent worst case (exact 0.000 at ε=0.03 in 24/25 clean-qualified seed-runs;
  all by ε ≤ 0.035). FGSM exact-0.000 at ε=0.03 holds in only 2/5–4/5 seeds per
  configuration. Preserve the BiLSTM seed-45 and Transformer seed-45 FGSM caveats.
- These are **UT-HAR**, **processed-tensor**, **digital white-box** adversarial
  results — **window-level safety-proxy** metrics on software CSI feature tensors.
  They are **not** clinical fall-risk prediction, clinical deployment evidence,
  over-the-air / physical-layer / packet-level attacks, or certified robustness.
- See [[project_overview]], `notes/priority2_seed42_cross_architecture_pilot.md`,
  `notes/thesis_ready_multiseed_summary.md`, `notes/priority2_gru_5seed_aggregate.md`,
  `notes/priority2_bilstm_5seed_aggregate.md`,
  `notes/priority2_transformer_5seed_aggregate.md`, and
  `notes/priority2_resnet18_multiseed_summary.md` for full per-configuration detail.
