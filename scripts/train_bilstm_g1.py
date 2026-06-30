"""
Representation pivot -- BiLSTM with the EXACT frozen Variant G G1 objective (seed-42 diagnostic).

After five within-training interventions (DS-SGE, Option B, BASAT Stage 1 TRADES, Stage 2 GAIRAT,
Stage 3 SAT) all hit the same ~0.876 PGD-AUROC separability ceiling on the LeNet representation, this
swaps ONLY the representation (LeNet -> UT_HAR_BiLSTM) and keeps the G1 objective byte-for-byte:

    L_G1 = L_FWCE + lam_s*L_src + lam_f*L_fall + lam_t*L_tgt   (G1 setting lam_s=lam_f=lam_t=1, w_wr=2,
           gammas=0.5, fall weight 3; targeted-to-fall PGD; tvg.train_one_epoch_variantG, unchanged)

Reuses the SAME data loader, FGSM/PGD/targeted attack code, eval PGD-10, clean guard (0.70/0.65), and
selection-v2 checkpoint rule. The only change is the model (BiLSTM accepts the existing (N,1,250,90)
tensors and reshapes internally; verified compatible with pgd_perturb).

DIAGNOSTIC QUESTION: does the BiLSTM val PGD-AUROC of P(fall) envelope clear the 0.906 go/no-go bar
(LeNet G1 = 0.876)? If yes, the representation change is the unlock. If ~0.876, the ceiling is not
LeNet-specific.

Scope: seed 42 ONLY, BiLSTM only, same UT-HAR split, same FGSM/PGD eps=0.030. VALIDATION-only for
selection/go-no-go. NO test set used. Window-level digital-domain white-box; NOT solved/certified/clinical/OTA.

Modes: --self-check (sign check on BiLSTM + finite G1 loss) | --smoke (2 ep) | --pilot.
Commands:
    python scripts/train_bilstm_g1.py --self-check
    python scripts/train_bilstm_g1.py --smoke --epochs 2 --smoke-batches 5
    python scripts/train_bilstm_g1.py --pilot
"""
from __future__ import annotations
from pathlib import Path
import argparse, csv, json, platform, sys, time
from datetime import datetime, timezone
import numpy as np
import torch
import torch.optim as optim


def import_variantG():
    sd = Path(__file__).resolve().parent
    if str(sd) not in sys.path:
        sys.path.insert(0, str(sd))
    import train_variantG_targeted_hardneg as tvg
    return tvg


tvg = import_variantG()
V2_GUARD_ACC, V2_GUARD_F1 = tvg.V2_GUARD_ACC, tvg.V2_GUARD_F1
G1 = tvg.SETTINGS["G1"]          # lam_t=1.0, w_wr=2.0
LAM_T, W_WR = G1["lam_t"], G1["w_wr"]
MODEL_NAME = "bilstm"


def parse_args():
    p = argparse.ArgumentParser(description="BiLSTM + frozen G1 objective (seed-42 representation diagnostic).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=70)
    p.add_argument("--patience", type=int, default=15)
    p.add_argument("--min-epochs", type=int, default=35)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--train-pgd-steps", type=int, default=7)
    p.add_argument("--fall-weight", type=float, default=3.0)
    p.add_argument("--self-check", action="store_true")
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--smoke-batches", type=int, default=5)
    p.add_argument("--pilot", action="store_true")
    return p.parse_args()


def swap_to_bilstm(F, args):
    """Replace the LeNet model+optimizer in the foundation with a BiLSTM (same data/criteria/attacks)."""
    sys.path.insert(0, str(F["exp"] / "third_party" / "WiFi-CSI-Sensing-Benchmark"))
    from model_factory import build_model
    model = build_model(MODEL_NAME).to(F["device"])
    F["model"] = model
    F["optimizer"] = optim.Adam(model.parameters(), lr=args.lr)
    return F


def run_self_check(args, F):
    print("=" * 78); print(f"BiLSTM + G1 --self-check  model={type(F['model']).__name__}")
    assert F["fall_idx"] == 1 and F["num_classes"] == 7
    nparams = sum(p.numel() for p in F["model"].parameters())
    print(f"  class indices OK (FALL=1, NUM=7); BiLSTM params={nparams}")
    # targeted-PGD sign check on the BiLSTM (must raise fall logit/P(fall) on nonfall windows)
    sc, ok = tvg.targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], F["fall_idx"], F["device"])
    print(f"  targeted-PGD sign check (BiLSTM): clean P(fall)={sc['clean_median_p_fall']:.4f} -> "
          f"targeted={sc['targeted_median_p_fall']:.4f}  increased={sc['increased']}")
    if not ok:
        raise SystemExit("SIGN CHECK FAILED on BiLSTM: targeted PGD did not raise fall logit/P(fall).")
    # one-batch G1 loss decomposition (finite; L_tgt>0)
    F["model"].train()
    inputs, labels = next(iter(F["train_loader"]))
    inputs = inputs.to(F["device"]).float(); labels = labels.type(torch.LongTensor).to(F["device"])
    bs = labels.size(0); eps = float(F["rng"].choice(F["train_epsilons"])); a = eps / 4.0
    n_clean = bs // 2; n_fgsm = (bs - n_clean) // 2
    fgsm = F["tsg"].fgsm_perturb(F["model"], inputs[n_clean:n_clean + n_fgsm], labels[n_clean:n_clean + n_fgsm], F["atk_criterion"], eps)
    pgd = F["tsg"].pgd_perturb(F["model"], inputs[n_clean + n_fgsm:], labels[n_clean + n_fgsm:], F["atk_criterion"], eps, args.train_pgd_steps, a)
    nf = labels != F["fall_idx"]
    tgt_adv = tvg.targeted_fall_pgd(F["model"], inputs[nf], F["fall_idx"], F["atk_criterion"], eps, args.train_pgd_steps, a)
    outputs = F["model"](torch.cat([inputs[:n_clean], fgsm, pgd], 0)).float()
    base = F["train_criterion"](outputs, labels)
    L_src, L_fall, L_tgt = tvg.variantG_margin_terms(outputs[n_clean:], labels[n_clean:], F["model"](tgt_adv).float(),
                                                     labels[nf], W_WR, F["fall_idx"], F["device"])
    total = base + L_src + L_fall + LAM_T * L_tgt
    for nm, v in (("FWCE", base), ("L_src", L_src), ("L_fall", L_fall), ("L_tgt", L_tgt), ("total", total)):
        print(f"    {nm:6s} = {v.item():.5f}"); assert np.isfinite(v.item())
    assert L_tgt.item() > 0, "L_tgt must be > 0 on targeted nonfall examples"
    print("  PASS: BiLSTM builds, sign check holds, G1 loss finite, L_tgt>0.")
    print("=" * 78)


def _run(args, F, smoke):
    tsg, s1 = F["tsg"], F["s1"]; device = F["device"]
    tag = "smoke" if smoke else "pilot"
    run = f"seed{args.seed}_bilstm_g1{'_smoke' if smoke else ''}"
    nsroot = F["exp"] / "results" / "safety_guided_defense" / "representation_bilstm"
    base = (nsroot / "_smoke" / f"seed{args.seed}" / "G1") if smoke else (nsroot / f"seed{args.seed}" / "G1")
    ck_dir = F["exp"] / "checkpoints" / "safety_guided_defense" / "representation_bilstm" / f"seed{args.seed}" / "G1"
    logs_dir = base / "logs"; ana_dir = base / "analysis"; meta_dir = base / "metadata"
    dirs = [base, logs_dir] if smoke else [ck_dir, logs_dir, ana_dir, meta_dir]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    ck = {k: ck_dir / f"{run}_{k}_best.pt" for k in ("v2safety", "v2maxrec", "v2lowFA", "v2macroF1")}

    print("=" * 78)
    print(f"BiLSTM + G1 {tag.upper()}  model={type(F['model']).__name__}  run={run}")
    print(f"  G1: lam_s={tvg.LAM_S} lam_f={tvg.LAM_F} lam_t={LAM_T} w_wr={W_WR} fw={args.fall_weight} | "
          f"guard acc>={V2_GUARD_ACC} mF1>={V2_GUARD_F1} | epochs={args.epochs} eps={F['train_epsilons']}")
    print("=" * 78)

    history = []
    best = {"v2safety": (-1e9, -1), "v2maxrec": ((-1e9, 1e9), -1), "v2lowFA": ((1e9, -1e9), -1), "v2macroF1": (-1e9, -1)}
    best_rec = {}; no_improve = 0; start = time.time()
    mb = args.smoke_batches if smoke else None

    for epoch in range(1, args.epochs + 1):
        tr = tvg.train_one_epoch_variantG(F["model"], F["train_loader"], F["train_criterion"], F["atk_criterion"],
                                          F["optimizer"], device, F["train_epsilons"], args.train_pgd_steps,
                                          F["rng"], tsg, LAM_T, W_WR, F["fall_idx"], max_batches=mb)
        for k in ("train_loss", "mean_base", "mean_src_motion", "mean_fall_margin", "mean_targeted"):
            if not np.isfinite(tr[k]):
                raise SystemExit(f"STOP (numerical): {k} not finite at epoch {epoch}.")
        vb = tsg.compute_validation_bundle(s1, F["model"], F["val_loader"], F["atk_criterion"], device)
        sc = tvg.safety_score(vb)
        acc = vb["val_clean_accuracy"]; f1 = vb["val_clean_macro_f1"]
        rec = vb["val_pgd_fall_recall"]; fpv = vb["val_pgd_false_fall_alarms"]
        eligible = (acc >= V2_GUARD_ACC and f1 >= V2_GUARD_F1)

        def save(key):
            if smoke:
                return
            torch.save({"epoch": epoch, "model_state_dict": F["model"].state_dict(), "selection_method": key,
                        "val_bundle": vb, "safety_score": sc, "run_name": run, "model_name": MODEL_NAME,
                        "args": vars(args)}, ck[key])

        flags = {k: 0 for k in ck}
        if eligible:
            if sc > best["v2safety"][0]:
                best["v2safety"] = (sc, epoch); best_rec["v2safety"] = vb; save("v2safety"); flags["v2safety"] = 1; no_improve = 0
            if (rec, -fpv) > best["v2maxrec"][0]:
                best["v2maxrec"] = ((rec, -fpv), epoch); best_rec["v2maxrec"] = vb; save("v2maxrec"); flags["v2maxrec"] = 1
            if rec >= tvg.LOWFA_RECALL_FLOOR and (fpv, -rec) < best["v2lowFA"][0]:
                best["v2lowFA"] = ((fpv, -rec), epoch); best_rec["v2lowFA"] = vb; save("v2lowFA"); flags["v2lowFA"] = 1
        if not flags["v2safety"] and best["v2safety"][1] > 0:
            no_improve += 1
        if f1 > best["v2macroF1"][0]:
            best["v2macroF1"] = (f1, epoch); best_rec["v2macroF1"] = vb; save("v2macroF1"); flags["v2macroF1"] = 1

        history.append({"epoch": epoch, "train_loss": tr["train_loss"], "mean_base": tr["mean_base"],
                        "mean_src_motion": tr["mean_src_motion"], "mean_fall_margin": tr["mean_fall_margin"],
                        "mean_targeted": tr["mean_targeted"], "val_clean_accuracy": acc, "val_clean_macro_f1": f1,
                        "val_clean_fall_recall": vb["val_clean_fall_recall"], "val_fgsm_fall_recall": vb["val_fgsm_fall_recall"],
                        "val_pgd_fall_recall": rec, "val_fgsm_false_fall_alarms": vb["val_fgsm_false_fall_alarms"],
                        "val_pgd_false_fall_alarms": fpv, "val_normalized_false_alarm_burden": vb["val_normalized_false_alarm_burden"],
                        "safety_score": sc, "v2_eligible": int(eligible), "sel_v2safety": flags["v2safety"],
                        "sel_v2maxrec": flags["v2maxrec"], "sel_v2lowFA": flags["v2lowFA"], "sel_v2macroF1": flags["v2macroF1"]})
        print(f"Epoch {epoch:03d}/{args.epochs} | loss={tr['train_loss']:.3f} base={tr['mean_base']:.3f} "
              f"src={tr['mean_src_motion']:.3f} fall={tr['mean_fall_margin']:.3f} tgt={tr['mean_targeted']:.3f} | "
              f"acc={acc:.3f} f1={f1:.3f} cFR={vb['val_clean_fall_recall']:.3f} pgd_fr={rec:.3f} pgd_FP={fpv} "
              f"score={sc:.3f} v2elig={int(eligible)} "
              f"[{'S' if flags['v2safety'] else '.'}{'R' if flags['v2maxrec'] else '.'}"
              f"{'L' if flags['v2lowFA'] else '.'}{'F' if flags['v2macroF1'] else '.'}]")
        if not smoke and args.patience > 0 and epoch >= args.min_epochs and no_improve >= args.patience:
            print(f"Early stopping at epoch {epoch} (best v2safety epoch {best['v2safety'][1]})."); break

    elapsed = time.time() - start
    last_epoch = history[-1]["epoch"]
    fields = list(history[0].keys())
    if not smoke:
        torch.save({"epoch": last_epoch, "model_state_dict": F["model"].state_dict(), "selection_method": "last",
                    "run_name": run, "model_name": MODEL_NAME, "args": vars(args)}, ck_dir / f"{run}_last.pt")
    with (logs_dir / f"{run}_training_log.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in history:
            w.writerow({k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]) for k in fields})
    if not smoke:
        with (ana_dir / f"{run}_selection_candidates.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["selection", "selected_epoch", "val_clean_acc", "val_clean_macro_f1", "val_pgd_recall", "val_pgd_false_alarms", "safety_score"])
            for k in ck:
                ep = best[k][1]; vbk = best_rec.get(k, {})
                w.writerow([k, ep, f"{vbk.get('val_clean_accuracy', float('nan')):.4f}", f"{vbk.get('val_clean_macro_f1', float('nan')):.4f}",
                            f"{vbk.get('val_pgd_fall_recall', float('nan')):.4f}", vbk.get('val_pgd_false_fall_alarms', ''),
                            f"{tvg.safety_score(vbk):.4f}" if vbk else ""])
        meta = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "stage": "representation_bilstm_g1_seed42_pilot",
                "method": "BiLSTM + frozen Variant G G1 objective (representation pivot)", "namespace": "representation_bilstm",
                "run_name": run, "model_name": MODEL_NAME, "model_params": sum(p.numel() for p in F["model"].parameters()),
                "seed": args.seed, "lam_s": tvg.LAM_S, "lam_f": tvg.LAM_F, "lam_t": LAM_T, "w_wr": W_WR, "fall_weight": args.fall_weight,
                "objective": "L_FWCE + lam_s*L_src + lam_f*L_fall + lam_t*L_tgt (G1, unchanged); only the model changed LeNet->BiLSTM",
                "v2_guard": {"min_clean_accuracy": V2_GUARD_ACC, "min_clean_macro_f1": V2_GUARD_F1},
                "train_epsilons": F["train_epsilons"], "train_pgd_steps": args.train_pgd_steps,
                "epochs_run": last_epoch, "split_sizes": F["split_sizes"], "test_set_used": False,
                "selected_epochs": {k: best[k][1] for k in ck}, "checkpoints": {k: str(v) for k, v in ck.items()},
                "go_no_go_ref": "results/safety_guided_defense/boundary_aware_selective_at/seed42/g1_baseline_val_frontier.json",
                "claim_boundary": "window-level digital-domain white-box; seed42/BiLSTM only; not solved/certified/clinical/OTA",
                "device": str(device), "python_version": platform.python_version(), "torch_version": torch.__version__,
                "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(F["exp"])), "elapsed_seconds": elapsed}
        with (meta_dir / f"{run}_metadata.json").open("w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
    print("-" * 78)
    print(f"{tag} done in {elapsed:.1f}s ({last_epoch} epochs)." + ("" if smoke else
          " selected epochs: " + ", ".join(f"{k}={best[k][1]}" for k in ck)))
    if not smoke:
        print("  NEXT: export val PGD probabilities (--model bilstm) for selected checkpoints; val PGD AUROC vs 0.906 bar.")
    print("=" * 78)


def main():
    args = parse_args()
    if args.seed != 42:
        raise SystemExit(f"BiLSTM G1 diagnostic is seed-42 ONLY for now (got seed {args.seed}).")
    F = tvg.load_foundation(args)
    F = swap_to_bilstm(F, args)
    if args.self_check:
        run_self_check(args, F); return
    if args.smoke:
        _, ok = tvg.targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], F["fall_idx"], F["device"])
        if not ok:
            raise SystemExit("SIGN CHECK FAILED on BiLSTM before smoke.")
        _run(args, F, smoke=True); return
    if args.pilot:
        _, ok = tvg.targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], F["fall_idx"], F["device"])
        if not ok:
            raise SystemExit("SIGN CHECK FAILED on BiLSTM before pilot.")
        _run(args, F, smoke=False); return
    raise SystemExit("Gated: pass --self-check, --smoke, or --pilot.")


if __name__ == "__main__":
    main()
