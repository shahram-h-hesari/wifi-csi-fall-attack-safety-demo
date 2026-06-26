# Math overclaim audit

Statements to **avoid** when math is inserted, the **reason**, and a **safe alternative**.
This aligns with the thesis's existing non-claim sections (Ch3 threat model; Ch5
"What This Chapter Does Not Claim"). The thesis currently contains **no equations**;
every formula added must inherit these qualifications.

| # | Do NOT say / imply | Why it is an overclaim | Safe alternative |
|---|---|---|---|
| 1 | Perturbations `δ` are RF / over-the-air / channel-spoofing attacks. | All perturbations are applied to the **processed, normalized CSI tensor** (Eq. perturb-domain). No RF waveform, packet, or channel injection was performed. | "Digital-domain, white-box perturbation of the processed CSI tensor; not a physical-layer or over-the-air attack." |
| 2 | The defenses provide **certified** or **provable** robustness. | Variant D/E are empirical adversarial-training recipes; no certificate or bound is computed. Stronger-PGD is a screen, not a proof (Eq. stronger-pgd). | "Experimental adversarial-training recipe; empirical robustness under the evaluated white-box attacks." |
| 3 | The fall detector provides **clinical** safety / validation. | Window-level ML metrics on a benchmark; no clinical study, device, or patient data. The Ch5 filename says "clinical" but its content is safety-proxy. | "Safety-proxy metrics (window-level fall vs non-fall); not clinical validation." Prefer "safety-proxy" over "clinical" in headings. |
| 4 | The system performs **fall-risk prediction** / predicts who will fall. | The task is per-window activity classification (fall vs non-fall), not prospective risk prediction. | "Per-window fall/activity recognition," "fall-alert classification." |
| 5 | Recall differences (e.g., 0.111 vs 0.178 vs 0.289) are **meaningful improvements**. | With `n_f = 45` fall windows these are 5 vs 8 vs 13 windows; 95% Wilson intervals overlap heavily (Eq. wilson). | "Differences in fall recall are within overlapping 95% confidence intervals (n_f=45) and are reported as suggestive, not significant." |
| 6 | Selection-v2 (or Variant E) is a **solved / better defense**. | It is a more conservative, selection-stabilized trade-off operating point; on seed 43 its attacked recall is fragile (collapses to 0 under PGD-20). | "A trade-off operating point that stabilizes clean behavior and false-alarm control at more conservative attacked recall." |
| 7 | **Thresholding** the fall probability can fix the residual false alarms. | Residual walk/run false alarms are **higher** fall-probability than true falls; calibration is poor (ECE ~0.44-0.54). A single threshold cannot separate them. | "A probability threshold cannot separate residual motion false alarms from true falls; a margin-based objective is proposed as future work." |
| 8 | Variant E **eliminates** motion false alarms / fixes the geometry. | It reduces the **count** of motion false alarms; residual ones stay high-confidence (Eq. margin-def geometry). | "Reduces the number of motion-class false alarms; does not guarantee residual false alarms are low-confidence." |
| 9 | The margin loss (Eq. margin-loss-future) **is** part of the method / improved results. | It is **not implemented or evaluated**; only proposed. | "Proposed future-work objective `L_margin` (not implemented in this thesis)." |
| 10 | Results **generalize** across seeds / architectures / datasets from seeds 42–43. | selection-v2's guard was tuned on seeds 42–43; seed 44 is the (not-yet-run) independent test. LeNet + UT-HAR only. | "Demonstrated on seeds 42–43, LeNet, UT-HAR; independent generalization (seed 44, other architectures/datasets) is future work." |
| 11 | `ε = 0.030` is a **small/imperceptible** physical perturbation. | ε is an `ℓ_∞` bound on the **normalized processed tensor**, not a perceptual or physical magnitude. | "ε is an `ℓ_∞` budget on the processed CSI tensor; its physical interpretation is out of scope." |
| 12 | Higher PGD recall = **safer system** without qualification. | Higher recall co-occurs with higher false alarms; the preferred operating point depends on the FN:FP cost ratio (Eq. cost), which is not fixed. | "Operating-point choice depends on the (experimental) FN:FP cost ratio; no single point is uniformly safest." |
| 13 | The cost ratios (10:1, 20:1, …) are **clinical** cost weights. | They are sensitivity-analysis values only. | "Experimental sensitivity ratios, not clinical cost ratios." |
| 14 | "No gradient masking" = the model **is robust**. | The monotonic-recall screen only fails to find masking; it is not a robustness proof. | "No evidence of gradient masking under the evaluated stronger-PGD settings; not a proof of robustness." |

**General rule:** every added equation that touches attacks, defenses, or fall metrics
should be accompanied (in surrounding prose) by the scope tag
"window-level, digital-domain, white-box evaluation on processed CSI; safety-proxy metrics;
not clinical, certified, or over-the-air."
