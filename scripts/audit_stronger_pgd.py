"""
Stronger-PGD sanity check (evaluation-only) for the diagnostic audit.

Loads frozen checkpoints (no training, no weight changes) and evaluates PGD at
eps=0.030 with steps in {10, 20, 40}, fixed-start and random-start, reusing the
frozen attack math (run_converged_attacks.generate_attacked_batch). Reports fall
recall and false-fall alarms on the test split. Writes ONLY under the
diagnostic_audit/stronger_attack_eval/ namespace.

Purpose: check for gradient masking — if fall recall keeps dropping from PGD-10
to PGD-40, the PGD-10 numbers are not artificially robust.

Command: python scripts/audit_stronger_pgd.py
"""
from __future__ import annotations
from pathlib import Path
import csv, sys
import numpy as np
import torch, torch.nn as nn

EXP = Path(__file__).resolve().parents[1]
OUT = EXP / "results" / "safety_guided_defense" / "variantE_motion_hard_negative" / "selection_v2" / "diagnostic_audit" / "stronger_attack_eval"
OUT.mkdir(parents=True, exist_ok=True)
FALL, WALK, RUN = 1, 2, 4
EPS = 0.03


def setup():
    sd = EXP / "scripts"; bench = EXP / "third_party" / "WiFi-CSI-Sensing-Benchmark"
    if str(sd) not in sys.path:
        sys.path.insert(0, str(sd))
    import train_converged_clean_baseline as s1
    s1.patch_sensefi_dataset_loader(bench)
    if str(bench) not in sys.path:
        sys.path.insert(0, str(bench))
    import run_converged_attacks as rca
    from model_factory import build_model
    return s1, rca, build_model, bench


def pgd(model, x, y, crit, eps, steps, alpha, rng_start):
    orig = x.detach()
    adv = orig.clone().detach()
    if rng_start:
        adv = adv + torch.empty_like(adv).uniform_(-eps, eps)
    for _ in range(steps):
        adv.requires_grad = True
        loss = crit(model(adv).float(), y)
        model.zero_grad(); loss.backward()
        with torch.no_grad():
            adv = adv + alpha * adv.grad.sign()
            adv = orig + torch.clamp(adv - orig, -eps, eps)
        adv = adv.detach()
    return adv


def fall_metrics(model, loader, crit, device, steps, alpha, rng_start):
    model.eval(); tp = fp = fn = tn = 0
    for x, y in loader:
        x = x.to(device).float(); y = y.to(device).long()
        if steps == 0:
            adv = x
        else:
            adv = pgd(model, x, y, crit, EPS, steps, alpha, rng_start)
        with torch.no_grad():
            pred = model(adv).float().argmax(1)
        for t, p in zip(y.cpu().numpy(), pred.cpu().numpy()):
            tf = t == FALL; pf = p == FALL
            if tf and pf: tp += 1
            elif (not tf) and pf: fp += 1
            elif tf and (not pf): fn += 1
            else: tn += 1
    rec = tp / (tp + fn) if tp + fn else 0
    return rec, fp, tp, fn


def main():
    s1, rca, build_model, bench = setup()
    s1.set_seed(0)
    data = s1.load_raw_ut_har(bench)
    _, _, test_loader, _ = s1.build_loaders(data, 64)
    device = torch.device("cpu"); crit = nn.CrossEntropyLoss()
    alpha = EPS / 6.0

    ckpts = {}
    for N in (42, 43):
        base = EXP / "checkpoints" / "safety_guided_defense"
        ve = base / "variantE_motion_hard_negative"
        ckpts[f"FGSM_defense_s{N}"] = EXP / "checkpoints" / "converged_defense" / f"defended_fgsm_at_seed{N}_best.pt"
        ckpts[f"D_safety_s{N}"] = base / f"seed{N}" / f"seed{N}_variantD_fgsm_pgd_multieps_at_fw3_50clean_25fgsm_25pgd_bySafetyScore_best.pt"
        ckpts[f"priorE_safety_s{N}"] = ve / f"seed{N}" / f"seed{N}_variantE_motion_hardneg_fw3_lam1p0_50clean_25fgsm_25pgd_bySafetyScore_best.pt"
        ckpts[f"v2safety_s{N}"] = ve / "selection_v2" / f"seed{N}" / f"seed{N}_variantE_selv2_lam1p0_v2safety_best.pt"
        ckpts[f"v2lowFA_s{N}"] = ve / "selection_v2" / f"seed{N}" / f"seed{N}_variantE_selv2_lam1p0_v2lowFA_best.pt"

    rows = []
    settings = [("PGD10_fixed", 10, False), ("PGD20_fixed", 20, False),
                ("PGD40_fixed", 40, False), ("PGD20_random", 20, True)]
    for name, path in ckpts.items():
        if not path.exists():
            print(f"[skip] missing {name}: {path}"); continue
        state = torch.load(path, map_location=device, weights_only=False)
        model = build_model("lenet").to(device)
        model.load_state_dict(state["model_state_dict"], strict=True)
        for sname, steps, rs in settings:
            torch.manual_seed(0)
            rec, fp, tp, fn = fall_metrics(model, test_loader, crit, device, steps, alpha, rs)
            rows.append([name, sname, steps, int(rs), f"{rec:.3f}", tp, fn, fp])
            print(f"{name:18s} {sname:13s} recall={rec:.3f} (tp={tp}) FP={fp}")
    with (OUT / "stronger_pgd_sanity_check.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["checkpoint", "attack", "pgd_steps", "random_start", "fall_recall", "tp", "fn", "false_fall_alarms"])
        w.writerows(rows)
    print(f"[done] -> {OUT / 'stronger_pgd_sanity_check.csv'}")


if __name__ == "__main__":
    main()
