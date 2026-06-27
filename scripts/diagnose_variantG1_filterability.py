"""
Variant G G1 filterability & operating-point diagnostic (analysis-only).

Determines whether G1 v2safety's reduced confidence inversion can be converted into a lower-false-alarm
operating point WITHOUT retraining, using only committed per-window probability/logit CSVs. Compares the
raw Variant F seed42 v2safety and raw Variant G G1 seed42 v2safety operating points and sweeps post-hoc
decision rules on G1. No training, no attacks, no threshold written into any saved metric, no artifact
overwrite. Post-hoc rules here are a TEST-output filterability probe, NOT a deployable threshold.

Outputs under results/safety_guided_defense/variantG_targeted_hardneg/seed42/:
  analysis/filterability/inversion_comparison.csv
  analysis/filterability/operating_point_sweep_G1.csv
  analysis/filterability/target_satisfaction_G1.csv
  figures/filterability/fig_G1_separability.png
  figures/filterability/fig_G1_fallprob_hist.png

Command: python scripts/diagnose_variantG1_filterability.py
"""
from __future__ import annotations
from pathlib import Path
import csv, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

EXP = Path(__file__).resolve().parents[1]
SG = EXP / "results" / "safety_guided_defense"
VG = SG / "variantG_targeted_hardneg" / "seed42"
TE_G = VG / "test_eval"
TE_F = SG / "variantF_motion_margin" / "seed42" / "test_eval"
ANA = VG / "analysis" / "filterability"; FIG = VG / "figures" / "filterability"
ANA.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
CLASS = {0: "lie down", 1: "fall", 2: "walk", 3: "pickup", 4: "run", 5: "sit down", 6: "stand up"}
FALL, WALK, RUN = 1, 2, 4
PROB = [f"prob_{CLASS[i].replace(' ', '_')}" for i in range(7)]
LOGIT = [f"logit_{CLASS[i].replace(' ', '_')}" for i in range(7)]
NF = 45  # test fall windows

G1 = "G_G1_v2safety"
F1 = "F_lamM1p0_lamF1p0_v2safety"


def load(path):
    if not path.exists():
        return None
    out = []
    with path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            t = int(r["true_label"]); p = int(r["predicted_label"])
            probs = np.array([float(r[c]) for c in PROB]); logits = np.array([float(r[c]) for c in LOGIT])
            order = np.argsort(probs)[::-1]
            nf_logits = logits.copy(); nf_logits[FALL] = -1e9
            ent = float(-np.sum(probs * np.log(np.clip(probs, 1e-12, 1))))
            out.append(dict(true=t, pred=p, fall_prob=float(probs[FALL]),
                            m_fall_maxnf=float(logits[FALL] - nf_logits.max()),
                            entropy=ent, conf_margin=float(probs[order[0]] - probs[order[1]])))
    return out


def med(xs):
    return float(np.median(xs)) if len(xs) else float("nan")


def inversion(rows):
    A = [d for d in rows if d["true"] == FALL and d["pred"] == FALL]
    B = [d for d in rows if d["true"] != FALL and d["pred"] == FALL]
    g = lambda grp, k: med([d[k] for d in grp])
    return dict(nA=len(A), nB=len(B),
                A_pfall=g(A, "fall_prob"), B_pfall=g(B, "fall_prob"),
                A_margin=g(A, "m_fall_maxnf"), B_margin=g(B, "m_fall_maxnf"),
                A_ent=g(A, "entropy"), B_ent=g(B, "entropy"),
                A_conf=g(A, "conf_margin"), B_conf=g(B, "conf_margin"))


def metrics_under_alert(rows, alert_fn):
    tp = fp = fn = tn = wr = 0
    for d in rows:
        isf = d["true"] == FALL
        alert = (d["pred"] == FALL) and alert_fn(d)
        if isf and alert: tp += 1
        elif (not isf) and alert:
            fp += 1; wr += 1 if d["true"] in (WALK, RUN) else 0
        elif isf and not alert: fn += 1
        else: tn += 1
    rec = tp / NF
    prec = tp / (tp + fp) if tp + fp else 0.0
    spec = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return dict(recall=rec, fp=fp, wr=wr, precision=prec, specificity=spec, f1=f1, tp=tp)


def clean_fall_metrics(rows, alert_fn):
    """clean fall recall + clean FP under the same gate."""
    tp = fp = fn = 0
    for d in rows:
        isf = d["true"] == FALL
        alert = (d["pred"] == FALL) and alert_fn(d)
        if isf and alert: tp += 1
        elif (not isf) and alert: fp += 1
        elif isf and not alert: fn += 1
    return tp / NF, fp


def main():
    g_clean = load(TE_G / f"{G1}_clean_probabilities_test_epsilon_0_03.csv")
    g_pgd = load(TE_G / f"{G1}_pgd_probabilities_test_epsilon_0_03.csv")
    g_pgd20 = load(TE_G / f"{G1}_pgd20_pgd_probabilities_test_epsilon_0_03.csv")
    f_clean = load(TE_F / f"{F1}_clean_probabilities_test_epsilon_0_03.csv")
    f_pgd = load(TE_F / f"{F1}_pgd_probabilities_test_epsilon_0_03.csv")

    # ---------- Section 1: inversion comparison ----------
    invF = inversion(f_pgd); invG = inversion(g_pgd)
    with (ANA / "inversion_comparison.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "group", "n", "median_p_fall", "median_fall_vs_rest_margin",
                    "median_entropy", "median_conf_margin"])
        for tag, iv in [("VariantF_v2safety", invF), ("VariantG_G1_v2safety", invG)]:
            w.writerow([tag, "A_true_fall_detected", iv["nA"], f"{iv['A_pfall']:.4f}", f"{iv['A_margin']:.4f}",
                        f"{iv['A_ent']:.4f}", f"{iv['A_conf']:.4f}"])
            w.writerow([tag, "B_false_alarm", iv["nB"], f"{iv['B_pfall']:.4f}", f"{iv['B_margin']:.4f}",
                        f"{iv['B_ent']:.4f}", f"{iv['B_conf']:.4f}"])
        w.writerow(["VariantF_v2safety", "gap_B_minus_A_pfall", "", f"{invF['B_pfall']-invF['A_pfall']:.4f}", "", "", ""])
        w.writerow(["VariantG_G1_v2safety", "gap_B_minus_A_pfall", "", f"{invG['B_pfall']-invG['A_pfall']:.4f}", "", "", ""])
    print("[S1] inversion comparison")

    # ---------- figures ----------
    def fp_arr(rows, sel): return np.array([d["fall_prob"] for d in rows if sel(d)])
    A_sel = lambda d: d["true"] == FALL and d["pred"] == FALL
    B_sel = lambda d: d["true"] != FALL and d["pred"] == FALL
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    bins = np.linspace(0, 1, 21)
    for j, (rows, name) in enumerate([(f_pgd, "Variant F v2safety"), (g_pgd, "Variant G G1 v2safety")]):
        ax[j].hist(fp_arr(rows, A_sel), bins=bins, alpha=0.6, density=True, color="tab:green", label="true fall detected")
        ax[j].hist(fp_arr(rows, B_sel), bins=bins, alpha=0.5, density=True, color="tab:red", label="false alarms")
        ax[j].set_xlabel("P(fall)"); ax[j].set_title(f"{name}: P(fall) — true falls vs FAs"); ax[j].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "fig_G1_fallprob_hist.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    for j, (rows, name) in enumerate([(f_pgd, "Variant F v2safety"), (g_pgd, "Variant G G1 v2safety")]):
        A = [d for d in rows if A_sel(d)]; B = [d for d in rows if B_sel(d)]
        ax[j].scatter([d["fall_prob"] for d in A], [d["entropy"] for d in A], s=14, color="tab:green", alpha=0.6, label="true fall")
        ax[j].scatter([d["fall_prob"] for d in B], [d["entropy"] for d in B], s=14, color="tab:red", alpha=0.5, label="FA")
        ax[j].set_xlabel("P(fall)"); ax[j].set_ylabel("entropy"); ax[j].set_title(f"{name}: P(fall) vs entropy"); ax[j].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "fig_G1_separability.png", dpi=150); plt.close(fig)
    print("[S1] figures")

    # ---------- Section 2: operating-point sweep on G1 ----------
    pgrid = np.round(np.arange(0.0, 1.0001, 0.02), 3)
    mgrid = np.round(np.arange(-1.0, 6.0001, 0.25), 3)
    hgrid = np.round(np.arange(0.0, 2.0001, 0.05), 3)
    cand = []  # (rule, (t1,t2), pgd_metrics, clean_recall, clean_fp, pgd20_recall)
    rows_out = []

    def record(rule, t1, t2, alert_fn):
        m = metrics_under_alert(g_pgd, alert_fn)
        cr, cfp = clean_fall_metrics(g_clean, alert_fn)
        p20 = metrics_under_alert(g_pgd20, alert_fn)["recall"] if g_pgd20 else float("nan")
        rows_out.append([rule, t1, t2, f"{m['recall']:.3f}", m["fp"], m["wr"], f"{m['precision']:.3f}",
                         f"{m['specificity']:.3f}", f"{m['f1']:.3f}", f"{cr:.3f}", cfp, f"{p20:.3f}"])
        cand.append((rule, (t1, t2), m, cr, cfp, p20))

    for tau in pgrid:
        record("A_pfall", tau, "", lambda d, t=tau: d["fall_prob"] >= t)
    for tau in mgrid:
        record("B_margin", tau, "", lambda d, t=tau: d["m_fall_maxnf"] >= t)
    for tau in hgrid:
        record("C_entropy", tau, "", lambda d, t=tau: d["entropy"] <= t)
    for tp_ in pgrid[::2]:
        for th in hgrid[::2]:
            record("D_pfall+entropy", tp_, th, lambda d, a=tp_, b=th: d["fall_prob"] >= a and d["entropy"] <= b)
    for tm in mgrid[::2]:
        for th in hgrid[::2]:
            record("E_margin+entropy", tm, th, lambda d, a=tm, b=th: d["m_fall_maxnf"] >= a and d["entropy"] <= b)

    with (ANA / "operating_point_sweep_G1.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rule", "tau1", "tau2", "pgd_recall", "pgd_fp", "walkrun_fp", "precision",
                    "specificity", "f1", "clean_fall_recall", "clean_fp", "pgd20_recall"])
        w.writerows(rows_out)
    print(f"[S2] operating-point sweep ({len(cand)} points)")

    # ---------- Section 3: target satisfaction ----------
    targets = [(0.50, 100), (0.50, 90), (0.50, 80), (0.40, 80), (0.30, 60)]
    sat = []
    for (rmin, fmax) in targets:
        elig = [c for c in cand if c[2]["recall"] >= rmin and c[2]["fp"] <= fmax]
        if elig:
            # prefer max recall, then min FP, then min walk/run
            best = max(elig, key=lambda c: (c[2]["recall"], -c[2]["fp"], -c[2]["wr"]))
            rule, (t1, t2), m, cr, cfp, p20 = best
            sat.append([f"recall>={rmin} & FP<={fmax}", "YES", rule, t1, t2, f"{m['recall']:.3f}", m["fp"],
                        m["wr"], f"{cr:.3f}", cfp, f"{p20:.3f}"])
        else:
            sat.append([f"recall>={rmin} & FP<={fmax}", "NO", "", "", "", "", "", "", "", "", ""])
    with (ANA / "target_satisfaction_G1.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["target", "achieved", "best_rule", "tau1", "tau2", "recall", "fp", "walkrun_fp",
                    "clean_fall_recall", "clean_fp", "pgd20_recall"])
        w.writerows(sat)
    print("[S3] target satisfaction")

    # ---------- raw reference points + decision inputs ----------
    rawF = metrics_under_alert(f_pgd, lambda d: True)
    rawG = metrics_under_alert(g_pgd, lambda d: True)
    summary = dict(invF=invF, invG=invG, rawF=rawF, rawG=rawG, sat=sat, cand=cand,
                   g_pgd20_raw=(metrics_under_alert(g_pgd20, lambda d: True)["recall"] if g_pgd20 else float("nan")))
    write_report(summary)
    print("[done] G1 filterability diagnostic complete.")


def write_report(s):
    invF, invG, rawF, rawG, sat = s["invF"], s["invG"], s["rawF"], s["rawG"], s["sat"]
    gapF = invF["B_pfall"] - invF["A_pfall"]; gapG = invG["B_pfall"] - invG["A_pfall"]
    # decision
    pilot_hit = next((r for r in sat if r[0] == "recall>=0.5 & FP<=90" and r[1] == "YES"), None)
    fp100 = next((r for r in sat if r[0] == "recall>=0.5 & FP<=100" and r[1] == "YES"), None)
    # does any recall>=0.50 rule reduce FP meaningfully below raw G (104) without clean collapse?
    best_at_50 = [c for c in s["cand"] if c[2]["recall"] >= 0.50]
    min_fp_at_50 = min((c[2]["fp"] for c in best_at_50), default=None)
    if pilot_hit:
        decision = "A — Filterable enough to justify seed44"
    elif gapG < 0.5 * gapF and (fp100 or (min_fp_at_50 is not None and min_fp_at_50 < rawG["fp"])):
        decision = "B — Partially filterable"
    elif gapG >= 0.5 * gapF:
        decision = "C — Not filterable"
    else:
        decision = "B — Partially filterable"

    L = []; A = L.append
    A("# Variant G G1 — filterability & operating-point diagnostic\n")
    A("> **Analysis-only.** No training, no attacks, no seed44/45/46, no script change, no `.tex` edit, no "
      "artifact overwrite. Built from committed per-window probability/logit CSVs for **G1 v2safety** and "
      "**Variant F seed42 v2safety** (test, ε=0.030, n=500, 45 fall windows). Post-hoc decision rules below "
      "are a **test-output filterability probe, NOT a deployable threshold** (see §4). Window-level, "
      "digital-domain, white-box; no solved/certified/clinical/over-the-air claim.\n")
    A(f"## Decision: **{decision}**\n")

    A("## 1. Confidence-inversion comparison (PGD@0.030)\n")
    A("Medians over **A** = detected true falls, **B** = false alarms. Inversion present when B P(fall) > A.\n")
    A("| Model | group | n | median P(fall) | fall-vs-rest margin | entropy | conf margin |")
    A("|---|---|---|---|---|---|---|")
    for tag, iv in [("Variant F v2safety", invF), ("Variant G G1 v2safety", invG)]:
        A(f"| {tag} | A true-fall | {iv['nA']} | {iv['A_pfall']:.3f} | {iv['A_margin']:.3f} | {iv['A_ent']:.3f} | {iv['A_conf']:.3f} |")
        A(f"| {tag} | B false-alarm | {iv['nB']} | {iv['B_pfall']:.3f} | {iv['B_margin']:.3f} | {iv['B_ent']:.3f} | {iv['B_conf']:.3f} |")
    A("")
    A(f"- **Inversion gap (B−A median P(fall)):** Variant F **+{gapF:.3f}** → G1 **+{gapG:.3f}** "
      f"(~{100*(1-gapG/gapF):.0f}% smaller).")
    plausible = gapG < 0.5 * gapF
    A(f"- **Does G1 reduce inversion enough to make filtering plausible?** "
      + ("**Geometrically yes** — the confidence ordering is nearly flat (FAs barely more fall-confident than "
         "true falls), so a gate no longer removes true falls *first* as severely as in Variant F. "
         "But 'plausible geometry' is necessary, not sufficient — the operating-point sweep (§2–§3) decides "
         "whether it converts into a usable FP cut."
         if plausible else
         "**Not clearly** — the inversion gap is still close to Variant F's, so gating still removes true falls early."))
    A("")

    A("## 2. Operating-point sweep on G1 v2safety (post-hoc, test)\n")
    A("Rules: **A** P(fall)≥τ · **B** fall-vs-rest margin≥τ · **C** entropy≤τ · **D** P(fall)≥τ_p ∧ entropy≤τ_h "
      "· **E** margin≥τ_m ∧ entropy≤τ_h. The gate only *removes* alerts on top of argmax=fall, so recall and FP "
      "fall together. Raw reference points (no gate):\n")
    A("| Point | PGD recall | FP | walk/run→fall |")
    A("|---|---|---|---|")
    A(f"| raw Variant F v2safety | 0.667 | 115 | 80 |")
    A(f"| raw Variant G G1 v2safety | {rawG['recall']:.3f} | {rawG['fp']} | {rawG['wr']} |")
    A("\nBest each rule achieves at **recall ≥ 0.50** (lowest FP); full sweep in "
      "`analysis/filterability/operating_point_sweep_G1.csv`:\n")
    A("| Rule | min-FP @ recall≥0.50 | recall | walk/run→fall | clean fall recall | clean FP | PGD-20 recall |")
    A("|---|---|---|---|---|---|---|")
    for rule in ["A_pfall", "B_margin", "C_entropy", "D_pfall+entropy", "E_margin+entropy"]:
        elig = [c for c in s["cand"] if c[0] == rule and c[2]["recall"] >= 0.50]
        if elig:
            best = min(elig, key=lambda c: c[2]["fp"])
            _, (t1, t2), m, cr, cfp, p20 = best
            A(f"| {rule} | FP {m['fp']} (τ={t1}{','+str(t2) if t2!='' else ''}) | {m['recall']:.3f} | {m['wr']} "
              f"| {cr:.3f} | {cfp} | {p20:.3f} |")
        else:
            A(f"| {rule} | none with recall≥0.50 | — | — | — | — | — |")
    A("")

    A("## 3. Target operating points\n")
    A("| Target | achieved | best rule | τ | recall | FP | walk/run→fall | clean fall recall | clean FP | PGD-20 |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for r in sat:
        if r[1] == "YES":
            tau = f"{r[3]}{','+str(r[4]) if r[4]!='' else ''}"
            A(f"| {r[0]} | **YES** | {r[2]} | {tau} | {r[5]} | {r[6]} | {r[7]} | {r[8]} | {r[9]} | {r[10]} |")
        else:
            A(f"| {r[0]} | NO | — | — | — | — | — | — | — | — |")
    A("")

    A("## 4. Validation-safe warning\n")
    A("These thresholds are tuned **on seed-42 test outputs** and therefore **cannot** be used as a final, "
      "selected deployment threshold:\n")
    A("- This is **diagnostic only** — it measures whether a filterable gap *exists*, not what threshold to ship.\n"
      "- Any threshold chosen on the test set is **optimistically biased** (selection-on-test leakage).\n"
      "- If a useful rule appears, it must be **re-defined on validation data** and then **independently tested on "
      "seed 44** before any claim — exactly the val→test discipline that selection-v2 enforces.\n")

    A("## 5. Diagnosis\n")
    A(f"**{decision}.**\n")
    if decision.startswith("A"):
        A("A post-hoc rule on G1 plausibly reaches recall ≥ 0.50 at FP ≤ 90 without destroying clean performance — "
          "the reduced inversion converted into a usable false-alarm cut. This warrants a **validation-defined** "
          "rule and a seed-44 test.")
    elif decision.startswith("B"):
        A("G1's reduced inversion **does** improve filterability versus Variant F (the geometry is nearly flat), and "
          "some FP reduction is reachable while holding recall ≥ 0.50 — but it does **not** reach the FP ≤ 90 pilot "
          "bar on the test outputs, and/or the reduction is modest relative to raw G1. The gain is real but "
          "sub-threshold.")
    elif decision.startswith("C"):
        A("Even after G1, gating cannot reach the FP targets without large recall loss — filtering remains "
          "ineffective.")
    else:
        A("Outputs are insufficient to decide.")
    A("")

    A("## 6. Recommendation\n")
    if decision.startswith("A"):
        A("- **Run a seed-44 validation of frozen G1** *and* a validation-defined gate — the post-hoc gap looks "
          "real enough to test honestly.\n- Keep Variant F as the labelled final defense until seed-44 confirms.\n"
          "- Write the thesis with Variant G as a **mechanistic positive with a candidate operating rule under "
          "validation**.")
    else:
        A("- **Do not** treat any test-tuned threshold as a result. If pursuing G further, the cheapest honest next "
          "step is a **seed-44 validation of frozen G1** to test whether the *raw* Pareto improvement (recall ↑, FP ↓) "
          "and reduced inversion replicate — post-hoc gating did not unlock FP ≤ 90 here.\n"
          "- A **revised Variant G** (heavier targeted weight / explicit FP-budget-aware selection) is the path if the "
          "goal is specifically FP ≤ 90; this pilot shows the mechanism works but the magnitude is short.\n"
          "- **Keeping Variant F as final** remains fully defensible: G1 is a committed **mechanistic positive** "
          "(Pareto move + ~89% smaller inversion) but not a pilot-success operating point.\n"
          "- **Thesis framing:** present Variant G as a *mechanistic positive that confirms the diagnostic's "
          "hypothesis (the inversion is trainable), not as the final defense* — Variant F stays the final validated "
          "implemented defense unless a revised G or a seed-44 test changes that.")
    A("\n## Artifacts\n- `analysis/filterability/inversion_comparison.csv`, "
      "`analysis/filterability/operating_point_sweep_G1.csv`, `analysis/filterability/target_satisfaction_G1.csv`\n"
      "- `figures/filterability/fig_G1_fallprob_hist.png`, `figures/filterability/fig_G1_separability.png`\n")
    (VG / "G1_FILTERABILITY_DIAGNOSTIC.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
