"""
Variant F seed-42 pilot: margin-aware motion hard-negative + true-fall margin preservation.

Per VARIANT_F_DESIGN_MEMO.md (Candidate F3). Reuses the frozen Variant E batch-split
adversarial-training machinery (50% clean / 25% FGSM / 25% PGD, multi-eps {0.005,0.015,0.030},
fall-weighted CE) and the frozen selection-v2 checkpoint rule (guard val clean acc >= 0.70 AND
macro-F1 >= 0.65; candidates v2safety / v2maxrec / v2lowFA / v2macroF1). The committed Variant D /
Variant E / selection-v2 scripts are NOT modified; this is a NEW script.

Objective:
    L_F = L_FWCE
        + lambda_m * mean_{i in adv walk/run} max(0, gamma_m + z_fall(x_i^adv) - z_true(x_i^adv))
        + lambda_f * mean_{i in adv true-fall} max(0, gamma_f + max_{c != fall} z_c(x_i^adv) - z_fall(x_i^adv))
Fixed margins gamma_m = gamma_f = 0.5. Pilot lambda settings (ONLY these three):
    (lambda_m, lambda_f) in {(1.0,0.5), (1.0,1.0), (0.5,1.0)}.

Scope: seed 42 only, LeNet only, same UT-HAR/SenseFi split. Window-level, digital-domain,
white-box; NOT solved/certified/clinical/over-the-air.

Command:
    python scripts/train_variantF_motion_margin.py --lambda-m 1.0 --lambda-f 1.0 --seed 42
"""
from __future__ import annotations
from pathlib import Path
import argparse, csv, json, platform, sys, time
from datetime import datetime, timezone
import numpy as np
import torch, torch.nn as nn, torch.optim as optim

WALK, RUN = 2, 4
V2_GUARD_ACC, V2_GUARD_F1 = 0.70, 0.65
LOWFA_RECALL_FLOOR = 0.10


def import_variantE():
    sd = Path(__file__).resolve().parent
    if str(sd) not in sys.path:
        sys.path.insert(0, str(sd))
    import train_variantE_motion_hard_negative as tve
    return tve


def train_one_epoch_margin(model, loader, train_criterion, atk_criterion, optimizer, device,
                           train_epsilons, train_pgd_steps, rng, tsg, lam_m, lam_f, gamma_m, gamma_f, fall_idx):
    """Variant E batch-split FGSM+PGD adversarial training + two margin terms."""
    model.train()
    tot_loss = tot = 0.0
    mm_sum = fm_sum = 0.0; mm_b = fm_b = 0
    for inputs, labels in loader:
        inputs = inputs.to(device).float()
        labels = labels.type(torch.LongTensor).to(device)
        bs = labels.size(0)
        eps = float(rng.choice(train_epsilons)); pgd_alpha = eps / 4.0
        n_clean = bs // 2; n_fgsm = (bs - n_clean) // 2
        clean_x = inputs[:n_clean]
        fgsm_src, fgsm_lbl = inputs[n_clean:n_clean + n_fgsm], labels[n_clean:n_clean + n_fgsm]
        pgd_src, pgd_lbl = inputs[n_clean + n_fgsm:], labels[n_clean + n_fgsm:]
        model.eval()
        fgsm_adv = tsg.fgsm_perturb(model, fgsm_src, fgsm_lbl, atk_criterion, eps)
        pgd_adv = tsg.pgd_perturb(model, pgd_src, pgd_lbl, atk_criterion, eps, train_pgd_steps, pgd_alpha)
        model.train()
        batch_x = torch.cat([clean_x, fgsm_adv, pgd_adv], dim=0)
        batch_y = labels
        n_clean = clean_x.size(0)

        optimizer.zero_grad()
        outputs = model(batch_x).float()
        base = train_criterion(outputs, batch_y)

        adv_out = outputs[n_clean:]; adv_lab = batch_y[n_clean:]
        # motion margin: push true walk/run logit above fall logit
        mmask = (adv_lab == WALK) | (adv_lab == RUN)
        if mmask.any():
            zo = adv_out[mmask]
            zf = zo[:, fall_idx]
            zt = zo.gather(1, adv_lab[mmask].unsqueeze(1)).squeeze(1)
            L_motion = torch.relu(gamma_m + zf - zt).mean()
            mm_sum += float(L_motion.item()); mm_b += 1
        else:
            L_motion = torch.zeros((), device=device)
        # fall margin: keep fall logit above max non-fall logit on adversarial true falls
        fmask = (adv_lab == fall_idx)
        if fmask.any():
            zo = adv_out[fmask].clone()
            zf2 = zo[:, fall_idx].clone()
            zo[:, fall_idx] = float("-inf")
            max_nonfall = zo.max(dim=1).values
            L_fall = torch.relu(gamma_f + max_nonfall - zf2).mean()
            fm_sum += float(L_fall.item()); fm_b += 1
        else:
            L_fall = torch.zeros((), device=device)

        loss = base + lam_m * L_motion + lam_f * L_fall
        loss.backward(); optimizer.step()
        tot_loss += loss.item() * bs; tot += bs
    return {"train_loss": tot_loss / tot,
            "mean_motion_margin": mm_sum / mm_b if mm_b else 0.0,
            "mean_fall_margin": fm_sum / fm_b if fm_b else 0.0}


def parse_args():
    p = argparse.ArgumentParser(description="Variant F margin-aware defense (seed-42 pilot).")
    p.add_argument("--lambda-m", type=float, required=True)
    p.add_argument("--lambda-f", type=float, required=True)
    p.add_argument("--gamma-m", type=float, default=0.5)
    p.add_argument("--gamma-f", type=float, default=0.5)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=70)
    p.add_argument("--patience", type=int, default=15)
    p.add_argument("--min-epochs", type=int, default=35)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--train-pgd-steps", type=int, default=7)
    p.add_argument("--fall-weight", type=float, default=3.0)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def safety_score(vb):
    return (0.35 * vb["val_clean_fall_recall"] + 0.45 * vb["val_pgd_fall_recall"]
            + 0.10 * vb["val_fgsm_fall_recall"] - 0.10 * vb["val_normalized_false_alarm_burden"])


def main():
    args = parse_args()
    if args.seed not in (42, 44):
        raise SystemExit("Variant F: only seed 42 (pilot) and seed 44 (frozen independent "
                         "validation) are permitted. Eligibility relaxed for the pre-registered "
                         "seed-44 validation; loss/lambda/margins/guard unchanged.")
    if (args.lambda_m, args.lambda_f) not in {(1.0, 0.5), (1.0, 1.0), (0.5, 1.0)}:
        raise SystemExit(f"Disallowed lambda setting {(args.lambda_m, args.lambda_f)}; "
                         "pilot permits only (1.0,0.5),(1.0,1.0),(0.5,1.0).")
    tve = import_variantE()
    tsg = tve.import_variantD()
    s1 = tsg.import_stage1()

    preset = tsg.VARIANT_PRESETS["D"]
    train_epsilons = list(preset["train_epsilons"])
    fall_idx = tsg.FALL_CLASS_INDEX; num_classes = tsg.NUM_CLASSES

    exp = Path(__file__).resolve().parents[1]
    benchmark = exp / "third_party" / "WiFi-CSI-Sensing-Benchmark"
    seed_tag = f"seed{args.seed}"
    base = exp / "results" / "safety_guided_defense" / "variantF_motion_margin" / seed_tag
    ck_dir = exp / "checkpoints" / "safety_guided_defense" / "variantF_motion_margin" / seed_tag
    logs_dir = base / "logs"; ana_dir = base / "analysis"; meta_dir = base / "metadata"

    s1.patch_sensefi_dataset_loader(benchmark)
    if str(benchmark) not in sys.path:
        sys.path.insert(0, str(benchmark))
    from model_factory import build_model

    s1.set_seed(args.seed)
    data = s1.load_raw_ut_har(benchmark)
    train_loader, val_loader, test_loader, split_sizes = s1.build_loaders(data, args.batch_size)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model("lenet").to(device)
    class_weights = torch.ones(num_classes, device=device); class_weights[fall_idx] = args.fall_weight
    train_criterion = nn.CrossEntropyLoss(weight=class_weights)
    atk_criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    rng = np.random.default_rng(args.seed)

    lmtag = f"lamM{str(args.lambda_m).replace('.', 'p')}_lamF{str(args.lambda_f).replace('.', 'p')}"
    run = f"{seed_tag}_variantF_margin_{lmtag}_gm0p5_gf0p5"
    ck = {k: ck_dir / f"{run}_{k}_best.pt" for k in ("v2safety", "v2maxrec", "v2lowFA", "v2macroF1")}
    ck_last = ck_dir / f"{run}_last.pt"
    log_path = logs_dir / f"{run}_training_log.csv"
    cand_path = ana_dir / f"{run}_selection_candidates.csv"
    meta_path = logs_dir / f"{run}_metadata.json"

    print("Variant F (margin-aware) seed-42 pilot")
    print("-" * 70)
    print(f"Run: {run}")
    print(f"lambda_m={args.lambda_m} lambda_f={args.lambda_f} gamma_m={args.gamma_m} gamma_f={args.gamma_f}")
    print(f"Guard: clean_acc>={V2_GUARD_ACC} AND clean_macro_f1>={V2_GUARD_F1}")
    print(f"Train eps {train_epsilons} fw{args.fall_weight} | epochs {args.epochs} patience {args.patience} min {args.min_epochs}")
    print("-" * 70)
    if args.dry_run:
        for k, v in ck.items():
            print(f"  {k}: {v}")
        return

    for d in (ck_dir, logs_dir, ana_dir, meta_dir):
        d.mkdir(parents=True, exist_ok=True)

    history = []
    best = {"v2safety": (-1e9, -1), "v2maxrec": ((-1e9, 1e9), -1),
            "v2lowFA": ((1e9, -1e9), -1), "v2macroF1": (-1e9, -1)}
    best_rec = {}
    no_improve = 0
    start = time.time()

    for epoch in range(1, args.epochs + 1):
        tr = train_one_epoch_margin(model, train_loader, train_criterion, atk_criterion, optimizer,
                                    device, train_epsilons, args.train_pgd_steps, rng, tsg,
                                    args.lambda_m, args.lambda_f, args.gamma_m, args.gamma_f, fall_idx)
        vb = tsg.compute_validation_bundle(s1, model, val_loader, atk_criterion, device)
        sc = safety_score(vb)
        acc = vb["val_clean_accuracy"]; f1 = vb["val_clean_macro_f1"]
        rec = vb["val_pgd_fall_recall"]; fpv = vb["val_pgd_false_fall_alarms"]
        eligible = (acc >= V2_GUARD_ACC and f1 >= V2_GUARD_F1)

        def save(key):
            torch.save({"epoch": epoch, "model_state_dict": model.state_dict(), "selection_method": key,
                        "val_bundle": vb, "safety_score": sc, "run_name": run, "args": vars(args)}, ck[key])

        flags = {k: 0 for k in ck}
        if eligible:
            if sc > best["v2safety"][0]:
                best["v2safety"] = (sc, epoch); best_rec["v2safety"] = vb; save("v2safety"); flags["v2safety"] = 1; no_improve = 0
            if (rec, -fpv) > best["v2maxrec"][0]:
                best["v2maxrec"] = ((rec, -fpv), epoch); best_rec["v2maxrec"] = vb; save("v2maxrec"); flags["v2maxrec"] = 1
            if rec >= LOWFA_RECALL_FLOOR and (fpv, -rec) < best["v2lowFA"][0]:
                best["v2lowFA"] = ((fpv, -rec), epoch); best_rec["v2lowFA"] = vb; save("v2lowFA"); flags["v2lowFA"] = 1
        if not flags["v2safety"] and best["v2safety"][1] > 0:
            no_improve += 1
        if f1 > best["v2macroF1"][0]:
            best["v2macroF1"] = (f1, epoch); best_rec["v2macroF1"] = vb; save("v2macroF1"); flags["v2macroF1"] = 1

        history.append({"epoch": epoch, "train_loss": tr["train_loss"],
                        "mean_motion_margin": tr["mean_motion_margin"], "mean_fall_margin": tr["mean_fall_margin"],
                        "val_clean_accuracy": acc, "val_clean_macro_f1": f1,
                        "val_clean_fall_recall": vb["val_clean_fall_recall"],
                        "val_fgsm_fall_recall": vb["val_fgsm_fall_recall"], "val_pgd_fall_recall": rec,
                        "val_fgsm_false_fall_alarms": vb["val_fgsm_false_fall_alarms"],
                        "val_pgd_false_fall_alarms": fpv,
                        "val_normalized_false_alarm_burden": vb["val_normalized_false_alarm_burden"],
                        "safety_score": sc, "v2_eligible": int(eligible),
                        "sel_v2safety": flags["v2safety"], "sel_v2maxrec": flags["v2maxrec"],
                        "sel_v2lowFA": flags["v2lowFA"], "sel_v2macroF1": flags["v2macroF1"]})
        print(f"Epoch {epoch:03d}/{args.epochs} | loss={tr['train_loss']:.3f} "
              f"mMar={tr['mean_motion_margin']:.3f} fMar={tr['mean_fall_margin']:.3f} | "
              f"acc={acc:.3f} f1={f1:.3f} pgd_fr={rec:.3f} pgd_FP={fpv} score={sc:.3f} "
              f"v2elig={int(eligible)} [{'S' if flags['v2safety'] else '.'}{'L' if flags['v2lowFA'] else '.'}{'F' if flags['v2macroF1'] else '.'}]")
        if args.patience > 0 and epoch >= args.min_epochs and no_improve >= args.patience:
            print(f"Early stopping at epoch {epoch} (best v2safety epoch {best['v2safety'][1]})."); break

    elapsed = time.time() - start
    last_epoch = history[-1]["epoch"]
    torch.save({"epoch": last_epoch, "model_state_dict": model.state_dict(),
                "selection_method": "last", "run_name": run, "args": vars(args)}, ck_last)

    fields = list(history[0].keys())
    with log_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in history:
            w.writerow({k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]) for k in fields})
    with cand_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["selection", "selected_epoch", "val_clean_acc", "val_clean_macro_f1",
                    "val_pgd_recall", "val_pgd_false_alarms", "safety_score"])
        for k in ck:
            ep = best[k][1]; vb = best_rec.get(k, {})
            w.writerow([k, ep, f"{vb.get('val_clean_accuracy', float('nan')):.4f}",
                        f"{vb.get('val_clean_macro_f1', float('nan')):.4f}",
                        f"{vb.get('val_pgd_fall_recall', float('nan')):.4f}",
                        vb.get('val_pgd_false_fall_alarms', ''), f"{safety_score(vb):.4f}" if vb else ""])
    meta = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "stage": "variantF_margin_seed42_pilot",
            "run_name": run, "seed": args.seed, "lambda_m": args.lambda_m, "lambda_f": args.lambda_f,
            "gamma_m": args.gamma_m, "gamma_f": args.gamma_f, "fall_weight": args.fall_weight,
            "objective": "L_FWCE + lam_m*relu(gm+z_fall-z_true)[adv walk/run] + lam_f*relu(gf+max_nonfall-z_fall)[adv fall]",
            "v2_guard": {"min_clean_accuracy": V2_GUARD_ACC, "min_clean_macro_f1": V2_GUARD_F1},
            "train_epsilons": train_epsilons, "epochs_run": last_epoch, "split_sizes": split_sizes,
            "selected_epochs": {k: best[k][1] for k in ck}, "checkpoints": {k: str(v) for k, v in ck.items()},
            "claim_boundary": "window-level digital-domain white-box; seed42/LeNet only; not solved/certified/clinical/OTA",
            "device": str(device), "python_version": platform.python_version(), "torch_version": torch.__version__,
            "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(exp)), "elapsed_seconds": elapsed}
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("-" * 70)
    print(f"Done in {elapsed:.1f}s ({last_epoch} epochs). selected epochs: " +
          ", ".join(f"{k}={best[k][1]}" for k in ck))


if __name__ == "__main__":
    main()
