"""
Representation pivot Step 1 -- clean BiLSTM baseline (RNN-appropriate training) to convergence.

The from-scratch BiLSTM+G1 adversarial run did NOT converge (clean fall recall 0, no guard-eligible
checkpoints; see representation_bilstm/seed42/G1/NON_CONVERGENCE_DO_NOT_CITE.md). Before any fair
adversarial diagnostic we must show the BiLSTM can learn UT-HAR cleanly. This trains a clean BiLSTM with:
  * plain CrossEntropyLoss (matches the prior LeNet clean baseline; no fall weighting by default),
  * gradient clipping (clip_grad_norm_, RNN-appropriate),
  * a lower/stable learning rate (default 5e-4),
  * early stopping on validation macro-F1,
  * best-checkpoint selection on VALIDATION only (macro-F1, and a guard-eligible best clean fall recall);
  * NO test set use anywhere.

New namespace: results/checkpoints .../representation_bilstm/clean_baseline/seed42/  (does not overwrite
LeNet or the failed from-scratch G1 outputs). Clean AUROC / attacked AUROC (Steps 1-2) are computed
post-hoc on the best checkpoint via export_probability_predictions.py --model bilstm --split val.

Scope: seed 42 ONLY, BiLSTM only, same UT-HAR split. NOT solved/certified/clinical/OTA.

Modes: --self-check | --smoke | --pilot.
"""
from __future__ import annotations
from pathlib import Path
import argparse, csv, json, platform, sys, time
from datetime import datetime, timezone
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim


def import_variantG():
    sd = Path(__file__).resolve().parent
    if str(sd) not in sys.path:
        sys.path.insert(0, str(sd))
    import train_variantG_targeted_hardneg as tvg
    return tvg


tvg = import_variantG()
V2_GUARD_ACC, V2_GUARD_F1 = tvg.V2_GUARD_ACC, tvg.V2_GUARD_F1
MODEL_NAME = "bilstm"


def fall_recall_precision(y_true, y_pred, fall_idx):
    yt = (y_true == fall_idx); yp = (y_pred == fall_idx)
    tp = int((yt & yp).sum()); fn = int((yt & ~yp).sum()); fp = int((~yt & yp).sum())
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    return recall, precision, tp, fn, fp


def train_one_epoch_clipped(model, loader, criterion, optimizer, device, clip):
    model.train()
    tot_loss = tot = 0.0
    for inputs, labels in loader:
        inputs = inputs.to(device).float()
        labels = labels.type(torch.LongTensor).to(device)
        optimizer.zero_grad()
        outputs = model(inputs).float()
        loss = criterion(outputs, labels)
        loss.backward()
        if clip and clip > 0:
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=clip)
        optimizer.step()
        tot_loss += loss.item() * inputs.size(0); tot += inputs.size(0)
    return tot_loss / max(1, tot)


def parse_args():
    p = argparse.ArgumentParser(description="Clean BiLSTM baseline (Step 1 representation recovery).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--patience", type=int, default=20)
    p.add_argument("--min-epochs", type=int, default=30)
    p.add_argument("--lr", type=float, default=5e-4)
    p.add_argument("--clip", type=float, default=5.0, help="grad-norm clip (RNN); 0 disables")
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--fall-weight", type=float, default=1.0, help="1.0 = plain CE (prior-clean-baseline default)")
    p.add_argument("--self-check", action="store_true")
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--smoke-batches", type=int, default=5)
    p.add_argument("--pilot", action="store_true")
    return p.parse_args()


def build(args, F):
    sys.path.insert(0, str(F["exp"] / "third_party" / "WiFi-CSI-Sensing-Benchmark"))
    from model_factory import build_model
    model = build_model(MODEL_NAME).to(F["device"])
    if args.fall_weight != 1.0:
        cw = torch.ones(F["num_classes"], device=F["device"]); cw[F["fall_idx"]] = args.fall_weight
        crit = nn.CrossEntropyLoss(weight=cw)
    else:
        crit = nn.CrossEntropyLoss()
    opt = optim.Adam(model.parameters(), lr=args.lr)
    return model, crit, opt


def evaluate(F, model, crit):
    s1 = F["s1"]
    _, yt, yp, _ = s1.run_inference(model, F["val_loader"], crit, F["device"])
    acc = s1.accuracy_of(yt, yp); mf1 = s1.macro_f1_of(yt, yp)
    rec, prec, tp, fn, fp = fall_recall_precision(yt, yp, F["fall_idx"])
    return {"val_acc": acc, "val_macro_f1": mf1, "val_fall_recall": rec, "val_fall_precision": prec,
            "fall_tp": tp, "fall_fn": fn, "fall_fp": fp, "guard": bool(acc >= V2_GUARD_ACC and mf1 >= V2_GUARD_F1)}


def run_self_check(args, F):
    model, crit, opt = build(args, F)
    print("=" * 78); print(f"Clean BiLSTM baseline --self-check  model={type(model).__name__}")
    nparams = sum(p.numel() for p in model.parameters())
    print(f"  params={nparams}  lr={args.lr}  clip={args.clip}  fall_weight={args.fall_weight} (1.0=plain CE)")
    inputs, labels = next(iter(F["train_loader"]))
    inputs = inputs.to(F["device"]).float(); labels = labels.type(torch.LongTensor).to(F["device"])
    out = model(inputs).float(); loss = crit(out, labels)
    print(f"  forward {tuple(inputs.shape)} -> {tuple(out.shape)}; CE={loss.item():.4f}")
    assert out.shape[1] == F["num_classes"] and np.isfinite(loss.item())
    loss.backward()
    gn = nn.utils.clip_grad_norm_(model.parameters(), max_norm=args.clip)
    print(f"  pre-clip grad-norm={float(gn):.3f} (clip={args.clip})")
    ev = evaluate(F, model, crit)
    print(f"  untrained val: acc={ev['val_acc']:.3f} mF1={ev['val_macro_f1']:.3f} fallRec={ev['val_fall_recall']:.3f}")
    print("  PASS: BiLSTM builds, forward+CE finite, grad clip works, eval runs.")
    print("=" * 78)


def _run(args, F, smoke):
    model, crit, opt = build(args, F); s1 = F["s1"]
    tag = "smoke" if smoke else "pilot"
    run = f"seed{args.seed}_bilstm_clean{'_smoke' if smoke else ''}"
    nsroot = F["exp"] / "results" / "safety_guided_defense" / "representation_bilstm" / "clean_baseline"
    base = (nsroot / "_smoke" / f"seed{args.seed}") if smoke else (nsroot / f"seed{args.seed}")
    ck_dir = F["exp"] / "checkpoints" / "safety_guided_defense" / "representation_bilstm" / "clean_baseline" / f"seed{args.seed}"
    logs_dir = base / "logs"; meta_dir = base / "metadata"
    for d in ([base, logs_dir] if smoke else [ck_dir, logs_dir, meta_dir]):
        d.mkdir(parents=True, exist_ok=True)
    ck_f1 = ck_dir / f"{run}_best_macroF1.pt"; ck_rec = ck_dir / f"{run}_best_fallrecall.pt"; ck_last = ck_dir / f"{run}_last.pt"

    print("=" * 78); print(f"Clean BiLSTM baseline {tag.upper()}  model={type(model).__name__}  run={run}")
    print(f"  plain CE (fw={args.fall_weight})  lr={args.lr}  clip={args.clip}  guard acc>={V2_GUARD_ACC} mF1>={V2_GUARD_F1}  "
          f"epochs={args.epochs} patience={args.patience} min={args.min_epochs}")
    print("=" * 78)

    history = []; best_f1 = (-1.0, -1); best_rec = (-1.0, -1); best_f1_rec = None; no_improve = 0; start = time.time()
    mb_loader = F["train_loader"]
    for epoch in range(1, args.epochs + 1):
        if smoke:
            # tiny: just a few batches
            model.train()
            for bi, (inputs, labels) in enumerate(mb_loader):
                if bi >= args.smoke_batches:
                    break
                inputs = inputs.to(F["device"]).float(); labels = labels.type(torch.LongTensor).to(F["device"])
                opt.zero_grad(); loss = crit(model(inputs).float(), labels); loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), max_norm=args.clip); opt.step()
            tl = float(loss.item())
        else:
            tl = train_one_epoch_clipped(model, mb_loader, crit, opt, F["device"], args.clip)
        ev = evaluate(F, model, crit)
        assert np.isfinite(tl) and np.isfinite(ev["val_macro_f1"]), "non-finite at epoch %d" % epoch
        improved = ev["val_macro_f1"] > best_f1[0]
        if improved:
            best_f1 = (ev["val_macro_f1"], epoch); best_f1_rec = ev; no_improve = 0
            if not smoke:
                torch.save({"epoch": epoch, "model_state_dict": model.state_dict(), "selection": "macroF1",
                            "metrics": ev, "run_name": run, "model_name": MODEL_NAME, "args": vars(args)}, ck_f1)
        else:
            no_improve += 1
        if ev["guard"] and ev["val_fall_recall"] > best_rec[0]:
            best_rec = (ev["val_fall_recall"], epoch)
            if not smoke:
                torch.save({"epoch": epoch, "model_state_dict": model.state_dict(), "selection": "fallrecall_guarded",
                            "metrics": ev, "run_name": run, "model_name": MODEL_NAME, "args": vars(args)}, ck_rec)
        history.append({"epoch": epoch, "train_loss": tl, **ev})
        print(f"Epoch {epoch:03d}/{args.epochs} | train_loss={tl:.3f} | val_acc={ev['val_acc']:.3f} "
              f"mF1={ev['val_macro_f1']:.3f} fallRec={ev['val_fall_recall']:.3f} fallPrec={ev['val_fall_precision']:.3f} "
              f"guard={int(ev['guard'])}{' *bestF1' if improved else ''}")
        if not smoke and args.patience > 0 and epoch >= args.min_epochs and no_improve >= args.patience:
            print(f"Early stopping at epoch {epoch} (best macro-F1 epoch {best_f1[1]})."); break

    elapsed = time.time() - start; last_epoch = history[-1]["epoch"]
    if not smoke:
        torch.save({"epoch": last_epoch, "model_state_dict": model.state_dict(), "selection": "last",
                    "run_name": run, "model_name": MODEL_NAME, "args": vars(args)}, ck_last)
    with (logs_dir / f"{run}_training_log.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(history[0].keys())); w.writeheader()
        for r in history:
            w.writerow({k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]) for k in history[0]})
    if not smoke:
        meta = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "stage": "representation_bilstm_clean_baseline_seed42",
                "method": "clean BiLSTM baseline (plain CE, grad clip, lower LR)", "namespace": "representation_bilstm/clean_baseline",
                "run_name": run, "model_name": MODEL_NAME, "model_params": sum(p.numel() for p in model.parameters()),
                "seed": args.seed, "lr": args.lr, "clip": args.clip, "fall_weight": args.fall_weight,
                "selection": "best val macro-F1 (primary); best guard-eligible clean fall recall (secondary)",
                "v2_guard": {"min_clean_accuracy": V2_GUARD_ACC, "min_clean_macro_f1": V2_GUARD_F1},
                "best_macroF1_epoch": best_f1[1], "best_macroF1_metrics": best_f1_rec,
                "best_fallrecall_epoch": best_rec[1], "epochs_run": last_epoch,
                "split_sizes": F["split_sizes"], "test_set_used": False,
                "checkpoints": {"best_macroF1": str(ck_f1), "best_fallrecall": str(ck_rec), "last": str(ck_last)},
                "claim_boundary": "clean baseline; window-level; seed42/BiLSTM only; not solved/certified/clinical/OTA",
                "device": str(F["device"]), "python_version": platform.python_version(), "torch_version": torch.__version__,
                "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(F["exp"])), "elapsed_seconds": elapsed}
        with (meta_dir / f"{run}_metadata.json").open("w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, default=str)
    print("-" * 78)
    bm = best_f1_rec or {}
    print(f"{tag} done in {elapsed:.1f}s ({last_epoch} ep). BEST macro-F1 epoch {best_f1[1]}: "
          f"acc={bm.get('val_acc', float('nan')):.4f} mF1={bm.get('val_macro_f1', float('nan')):.4f} "
          f"fallRec={bm.get('val_fall_recall', float('nan')):.4f} fallPrec={bm.get('val_fall_precision', float('nan')):.4f} "
          f"guard={'PASS' if bm.get('guard') else 'FAIL'}")
    if not smoke:
        print(f"  best guard-eligible clean fall recall: epoch {best_rec[1]} (recall {best_rec[0]:.4f})")
        print("  NEXT: export val clean/fgsm/pgd probs (--model bilstm) for best checkpoint; clean & PGD AUROC.")
    print("=" * 78)


def main():
    args = parse_args()
    if args.seed != 42:
        raise SystemExit(f"Clean BiLSTM baseline is seed-42 ONLY for now (got seed {args.seed}).")
    F = tvg.load_foundation(args)
    if args.self_check:
        run_self_check(args, F); return
    if args.smoke:
        _run(args, F, smoke=True); return
    if args.pilot:
        _run(args, F, smoke=False); return
    raise SystemExit("Gated: pass --self-check, --smoke, or --pilot.")


if __name__ == "__main__":
    main()
