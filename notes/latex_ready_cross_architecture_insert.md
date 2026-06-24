# LaTeX-Ready Cross-Architecture Results Insert

Drafting aid for the thesis cross-architecture multi-seed result. **Nothing in the
thesis LaTeX is modified by this note** — it only stages copy-pasteable LaTeX plus
recommended placement and wording. All numbers are read from the committed files:

- `results/cross_architecture/cross_architecture_multiseed_summary.csv`
- `notes/priority2_cross_architecture_multiseed_summary.md`

Window-level fall-vs-non-fall safety proxies on the UT-HAR/SenseFi held-out test
split (n = 500 windows; 45 fall / 455 non-fall), matched ε = 0.030 (FGSM
single-step L∞; PGD L∞, 10 steps, α = ε/6). Means ± SD are across the
clean-qualified seeds of each architecture (sample SD, ddof = 1); single-seed
pilots show the point value with "(n=1)".

---

## 1. LaTeX table

```latex
\begin{table}[t]
  \centering
  \caption[Cross-architecture adversarial fall-recall collapse]{%
    Cross-architecture window-level fall recall under matched
    $L_\infty$ FGSM and PGD attacks at $\varepsilon=0.03$ on the UT-HAR/SenseFi
    pipeline (held-out test split, $n=500$ windows, $45$ fall). Values are
    mean~$\pm$~SD over each architecture's clean-qualified training seeds; single
    seed pilots show the point value with $(n{=}1)$. ResNet18 seed~45 is excluded
    as a non-converged divergence. PGD at $\varepsilon=0.03$ drives fall recall to
    exactly $0.000$ in every clean-qualified architecture and seed evaluated.
    These are digital-domain, processed-tensor, window-level safety-proxy results,
    not clinical or over-the-air measurements.}
  \label{tab:cross-architecture-collapse}
  \begin{tabular}{l l c c c c c}
    \toprule
    Architecture & Evidence status & \makecell{Clean-qual.\\seeds}
      & \makecell{Clean\\recall} & \makecell{FGSM$_{0.03}$\\recall}
      & \makecell{PGD$_{0.03}$\\recall} & \makecell{PGD\\collapse} \\
    \midrule
    LeNet       & full five-seed              & 5/5 & $0.978\pm0.016$ & $0.049\pm0.046$ & $0.000\pm0.000$ & 5/5 \\
    GRU         & full five-seed              & 5/5 & $0.920\pm0.012$ & $0.009\pm0.012$ & $0.000\pm0.000$ & 5/5 \\
    ResNet18    & clean-qualified multi-seed  & 4/5 & $0.972\pm0.011$ & $0.011\pm0.013$ & $0.000\pm0.000$ & 4/4 \\
    BiLSTM      & seed-42 pilot               & 1   & $0.889$ \,(n{=}1) & $0.000$ \,(n{=}1) & $0.000$ \,(n{=}1) & 1/1 \\
    Transformer & seed-42 pilot               & 1   & $0.978$ \,(n{=}1) & $0.000$ \,(n{=}1) & $0.000$ \,(n{=}1) & 1/1 \\
    \bottomrule
  \end{tabular}
\end{table}
```

> Notes for insertion: the table uses `booktabs` and `makecell` (both already
> common in thesis preambles). If `makecell` is not loaded, replace the
> `\makecell{...}` headers with plain text (e.g. "Clean recall", "PGD recall").
> ResNet18's 4/5 reflects four clean-qualified seeds (42, 43, 44, 46); seed 45
> diverged and is excluded.

---

## 2. Thesis-ready paragraph

> To test whether the observed missed-fall safety-proxy failure is specific to a
> single network architecture, the converged UT-HAR/SenseFi evaluation was
> repeated across five model families spanning convolutional, recurrent, and
> attention-based designs. Two families were evaluated with a full five-seed sweep
> (seeds 42--46): the LeNet CNN baseline and a GRU recurrent network. A deeper
> ResNet-18 CNN was evaluated over the same five seeds, of which four converged
> and one (seed~45) diverged under the fixed protocol and was excluded as
> non-converged, yielding a four-seed clean-qualified result. A bidirectional LSTM
> and an attention-based Transformer (ViT) were each evaluated as single-seed
> (seed-42) pilots. In every clean-qualified architecture and seed, the clean
> classifier achieved strong window-level fall recall (0.889--0.978), yet a matched
> projected gradient descent (PGD) attack at $\varepsilon=0.03$ reduced fall recall
> to exactly 0.000 --- for the two full five-seed families (LeNet and GRU) with
> zero variance across all five seeds each, and for ResNet18 across all four
> clean-qualified seeds. A single-step FGSM attack at the same budget reduced fall
> recall to near zero (mean 0.000--0.049). Because this collapse reproduces across
> shallow CNN, deep CNN, recurrent, and attention architectures under an identical
> data split, attack configuration, and metric definition, the missed-fall
> safety-proxy failure is not an artifact of one architecture, one architecture
> family, or one training seed. Multi-seed reliability is established for LeNet and
> GRU; ResNet18 provides a four-seed clean-qualified result; the BiLSTM and
> Transformer pilots are consistent with the same failure but are single-seed and
> are not presented as multi-seed evidence.

---

## 3. Boundary language (include verbatim near the table)

> All quantities are **window-level safety-proxy** metrics computed on the
> **UT-HAR** dataset only, under a **processed-CSI-tensor, digital white-box**
> attack setting (gradients taken on software feature tensors). They are **not**
> clinical fall-detection or clinical-deployment evidence, **not** over-the-air or
> physical-layer/packet-level validation, and **not** certified or provable
> robustness. "Fall recall" here is a window-level activity-recognition proxy on
> the UT-HAR protocol, not a validated clinical fall-detection outcome. Multi-seed
> reliability is demonstrated for LeNet and GRU only; ResNet18 is a four-seed
> clean-qualified result (one excluded divergence); BiLSTM and Transformer are
> single-seed (seed-42) pilots.

---

## 4. Suggested placement

**Recommendation: place the table and paragraph in Chapter 4, with a one-line
cross-reference from Chapter 5.**

Rationale, grounded in the existing artifact layout:
- **Chapter 4** already holds the *attack/robustness results* artifacts
  (`ch04_table_4_2_fall_safety_proxy_confusion_metrics`,
  `ch04_table_4_3_epsilon_sweep_attack_metrics`,
  `ch04_table_4_5_attack_impact_delta_summary`). This cross-architecture table is
  fundamentally an **empirical robustness result** — "the collapse reproduces
  across architectures and seeds" — so it belongs alongside the other Chapter 4
  attack-result tables, extending them from single-architecture to
  cross-architecture and from single-seed to multi-seed.
- **Chapter 5** holds the *safety-proxy interpretation* artifacts
  (`ch05_table_5_1_robustness_failure_thresholds`,
  `ch05_table_5_3_attack_induced_safety_risk_amplification`). The **interpretation**
  — "therefore the missed-fall safety-proxy failure is architecture-general" — is
  best stated in Chapter 5, citing this table by its `\ref{}` rather than
  duplicating it.

So: put `tab:cross-architecture-collapse` and paragraph (2) in Chapter 4 as a
results subsection (e.g. "Cross-architecture and multi-seed robustness"); in
Chapter 5, add a single sentence referencing Table~\ref{tab:cross-architecture-collapse}
when arguing the safety-proxy failure generalizes. This mirrors how the existing
`tables/chapter_cross_architecture_seed42_table.tex` (seed-42 pilot) was handled
and avoids double-counting the same numbers across chapters.

---

## 5. Committee-safe wording

**What we CAN claim**
- The clean classifiers are strong across all five architectures (clean fall
  recall 0.889--0.978).
- Under matched PGD at $\varepsilon=0.03$, window-level fall recall collapses to
  **exactly 0.000 in every clean-qualified architecture and seed evaluated**.
- For **LeNet and GRU**, this is a **full five-seed** result with **zero variance**
  in the PGD collapse — reproducible, not a single-seed artifact.
- For **ResNet18**, the same collapse holds across **four clean-qualified seeds**
  (seed 45 excluded as a documented non-convergence).
- The failure is **architecture-general** across the families tested (shallow CNN,
  deep CNN, recurrent, attention).
- FGSM at the same budget is near-total but more seed/architecture-variable.

**What we CANNOT claim yet**
- **Not** full multi-seed reliability for **BiLSTM or Transformer** — these are
  **single-seed (seed-42) pilots**; do not state "five-seed" or "reliable" for
  them, and do not aggregate them with the multi-seed families.
- **Not** a clinical claim — no clinical fall-risk prediction, patient outcome, or
  medical-device/deployment validity.
- **Not** an over-the-air / physical-layer result — the attack is digital,
  white-box, on processed CSI tensors, not transmitted RF or packet/preamble-level.
- **Not** certified or provable robustness — these are empirical attack results at
  specific budgets, not robustness certificates.
- **Not** an exhaustive architecture sweep — five families, not all model
  families, depths, or Transformer variants.
- **Not** event-level or session-level clinical fall detection — "fall recall" is
  a window-level UT-HAR activity-recognition proxy.

See [[project_overview]], `notes/priority2_cross_architecture_multiseed_summary.md`,
`notes/thesis_ready_multiseed_summary.md`, `notes/priority2_gru_5seed_aggregate.md`,
and `notes/priority2_resnet18_multiseed_summary.md` for full per-family detail.
