"""
Representation pivot Step 3 -- BiLSTM G1 adversarial fine-tune FROM a clean-qualified checkpoint.

The from-scratch BiLSTM+G1 run did not converge (NON_CONVERGENCE_DO_NOT_CITE.md). The committed
cross-architecture study already produced five clean-qualified BiLSTM checkpoints (seeds 42-46, strict
clean gate PASS, identical UT-HAR split, strict=True load-compatible with build_model("bilstm")). Per the
user's instruction and the pre-registration's convergence-failure allowance (validation-only budget
tuning), this initializes the BiLSTM from the clean checkpoint and fine-tunes with the EXACT frozen G1
objective (no loss/lambda/gamma/fall_weight change), adding only RNN-appropriate optimization knobs:
gradient clipping and a lower LR.

DEVIATION (documented): LeNet G1 was trained from scratch; this BiLSTM G1 is clean-initialized. The
backbone is still the scientific variable; the clean init is a budget accommodation (from-scratch
adversarial training did not converge on the recurrent backbone). Logged in metadata.

Objective: L_FWCE + lam_s*L_src + lam_f*L_fall + lam_t*L_tgt (G1: lam_s=lam_f=lam_t=1, w_wr=2, gammas=0.5,
fall_weight=3; targeted-to-fall PGD; tvg.variantG_margin_terms unchanged). Protocol: 50/25/25 batch split,
multi-eps {0.005,0.015,0.030}, train PGD 7 steps a=eps/4, batch 64. NEW: grad-norm clip, lower LR.

Eval (post-hoc, validation-only for go/no-go): export_probability_predictions.py --model bilstm --split val;
val PGD-10 AUROC of P(fall) vs LeNet G1 bar 0.876 / recall@FAR<=10% 0.477. Pre-reg decision criteria are on
the held-out TEST split, touched once only after a validation GO. Selection-v2 + clean guard (0.70/0.65).

Scope: seed 42 ONLY, BiLSTM only, same split. NO test set in training/selection. Not solved/certified/clinical/OTA.

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
G1 = tvg.SETTINGS["G1"]
LAM_T, W_WR = G1["lam_t"], G1["w_wr"]
MODEL_NAME = "bilstm"
DEFAULT_INIT = "checkpoints/cross_architecture/bilstm/bilstm_seed42_best.pt"


def train_one_epoch_g1_clipped(model, loader, train_criterion, atk_criterion, optimizer, device,
                               train_epsilons, train_pgd_steps, rng, tsg, lam_t, w_wr, fall_idx, clip,
                               max_batches=None):
    """EXACT tvg.train_one_epoch_variantG logic + gradient clipping before optimizer.step()."""
    model.train()
    tot_loss = tot = 0.0; s = {"base": 0.0, "src": 0.0, "fall": 0.0, "tgt": 0.0}; nb = 0; gnsum = 0.0
    for bi, (inputs, labels) in enumerate(loader):
        if max_batches is not None and bi >= max_batches:
            break
        inputs = inputs.to(device).float(); labels = labels.type(torch.LongTensor).to(device); bs = labels.size(0)
        eps = float(rng.choice(train_epsilons)); pgd_alpha = eps / 4.0
        n_clean = bs // 2; n_fgsm = (bs - n_clean) // 2
        clean_x = inputs[:n_clean]
        fgsm_src, fgsm_lbl = inputs[n_clean:n_clean + n_fgsm], labels[n_clean:n_clean + n_fgsm]
        pgd_src, pgd_lbl = inputs[n_clean + n_fgsm:], labels[n_clean + n_fgsm:]
        model.eval()
        fgsm_adv = tsg.fgsm_perturb(model, fgsm_src, fgsm_lbl, atk_criterion, eps)
        pgd_adv = tsg.pgd_perturb(model, pgd_src, pgd_lbl, atk_criterion, eps, train_pgd_steps, pgd_alpha)
        nf_mask = labels != fall_idx
        if lam_t > 0 and nf_mask.any():
            tgt_adv = tvg.targeted_fall_pgd(model, inputs[nf_mask], fall_idx, atk_criterion, eps, train_pgd_steps, pgd_alpha)
            tgt_lab = labels[nf_mask]
        else:
            tgt_adv, tgt_lab = None, labels[:0]
        model.train()
        batch_x = torch.cat([clean_x, fgsm_adv, pgd_adv], dim=0); batch_y = labels; n_clean = clean_x.size(0)
        optimizer.zero_grad()
        outputs = model(batch_x).float()
        base = train_criterion(outputs, batch_y)
        adv_out, adv_lab = outputs[n_clean:], batch_y[n_clean:]
        tgt_out = model(tgt_adv).float() if (tgt_adv is not None and tgt_adv.numel() > 0) else None
        L_src, L_fall, L_tgt = tvg.variantG_margin_terms(adv_out, adv_lab, tgt_out, tgt_lab, w_wr, fall_idx, device)
        loss = base + tvg.LAM_S * L_src + tvg.LAM_F * L_fall + lam_t * L_tgt
        loss.backward()
        gn = nn.utils.clip_grad_norm_(model.parameters(), max_norm=clip) if clip and clip > 0 else 0.0
        optimizer.step()
        tot_loss += loss.item() * bs; tot += bs; nb += 1; gnsum += float(gn)
        s["base"] += float(base.item()); s["src"] += float(L_src.item())
        s["fall"] += float(L_fall.item()); s["tgt"] += float(L_tgt.item())
    d = max(1, nb)
    return {"train_loss": tot_loss / max(1, tot), "mean_base": s["base"] / d, "mean_src_motion": s["src"] / d,
            "mean_fall_margin": s["fall"] / d, "mean_targeted": s["tgt"] / d, "mean_grad_norm": gnsum / d, "batches": nb}


def parse_args():
    p = argparse.ArgumentParser(description="BiLSTM G1 fine-tune from clean checkpoint (seed-42 representation diagnostic).")
    p.add_argument("--init-checkpoint", default=DEFAULT_INIT, help="clean-qualified BiLSTM checkpoint to initialize from")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=70)
    p.add_argument("--patience", type=int, default=15)
    p.add_argument("--min-epochs", type=int, default=20)
    p.add_argument("--lr", type=float, default=3e-4, help="lower than LeNet G1 1e-3 (RNN fine-tune)")
    p.add_argument("--clip", type=float, default=5.0, help="grad-norm clip (RNN); 0 disables")
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--train-pgd-steps", type=int, default=7)
    p.add_argument("--fall-weight", type=float, default=3.0)
    p.add_argument("--self-check", action="store_true")
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--smoke-batches", type=int, default=5)
    p.add_argument("--pilot", action="store_true")
    return p.parse_args()


def swap_to_bilstm_init(F, args):
    sys.path.insert(0, str(F["exp"] / "third_party" / "WiFi-CSI-Sensing-Benchmark"))
    from model_factory import build_model
    model = build_model(MODEL_NAME).to(F["device"])
    ckp = Path(args.init_checkpoint)
    if not ckp.is_absolute():
        ckp = F["exp"] / ckp
    if not ckp.exists():
        raise SystemExit(f"init checkpoint not found: {ckp}")
    state = torch.load(ckp, map_location=F["device"], weights_only=False)
    sd = state["model_state_dict"] if isinstance(state, dict) and "model_state_dict" in state else state
    model.load_state_dict(sd, strict=True)   # verified strict-compatible
    F["model"] = model
    F["optimizer"] = optim.Adam(model.parameters(), lr=args.lr)
    F["init_checkpoint"] = str(ckp)
    F["init_val_macro_f1"] = state.get("val_macro_f1") if isinstance(state, dict) else None
    return F


def run_self_check(args, F):
    print("=" * 80); print(f"BiLSTM G1 fine-tune --self-check  init={Path(F['init_checkpoint']).name}")
    assert F["fall_idx"] == 1 and F["num_classes"] == 7
    nparams = sum(p.numel() for p in F["model"].parameters())
    # confirm the clean init actually loaded -> the model should already classify clean falls well
    s1 = F["s1"]; _, yt, yp, _ = s1.run_inference(F["model"], F["val_loader"], F["atk_criterion"], F["device"])
    acc = s1.accuracy_of(yt, yp); mf1 = s1.macro_f1_of(yt, yp)
    yt1 = (yt == F["fall_idx"]); yp1 = (yp == F["fall_idx"])
    frec = (yt1 & yp1).sum() / max(1, yt1.sum())
    print(f"  clean-init loaded: params={nparams}  val acc={acc:.3f} mF1={mf1:.3f} fallRec={frec:.3f} "
          f"(init val mF1 in ckpt={F.get('init_val_macro_f1')})")
    assert acc >= 0.70 and frec > 0.5, "clean init should already classify; load may have failed"
    sc, ok = tvg.targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], F["fall_idx"], F["device"])
    print(f"  targeted-PGD sign check (BiLSTM): clean P(fall)={sc['clean_median_p_fall']:.4f} -> "
          f"targeted={sc['targeted_median_p_fall']:.4f}  increased={sc['increased']}")
    if not ok:
        raise SystemExit("SIGN CHECK FAILED on BiLSTM.")
    # one-batch clipped G1 loss finite + L_tgt>0 + grad-norm reported
    tr = train_one_epoch_g1_clipped(F["model"], F["train_loader"], F["train_criterion"], F["atk_criterion"],
                                    F["optimizer"], F["device"], F["train_epsilons"], args.train_pgd_steps,
                                    F["rng"], F["tsg"], LAM_T, W_WR, F["fall_idx"], args.clip, max_batches=2)
    print(f"  2-batch clipped G1: loss={tr['train_loss']:.4f} base={tr['mean_base']:.4f} src={tr['mean_src_motion']:.4f} "
          f"fall={tr['mean_fall_margin']:.4f} tgt={tr['mean_targeted']:.4f} grad_norm={tr['mean_grad_norm']:.3f}")
    for k in ("train_loss", "mean_base", "mean_src_motion", "mean_fall_margin", "mean_targeted"):
        assert np.isfinite(tr[k])
    assert tr["mean_targeted"] > 0
    print("  PASS: clean init loaded & classifies, sign check holds, clipped G1 loss finite, L_tgt>0.")
    print("=" * 80)


def _run(args, F, smoke):
    tsg, s1 = F["tsg"], F["s1"]; device = F["device"]
    tag = "smoke" if smoke else "pilot"
    run = f"seed{args.seed}_bilstm_g1_finetune{'_smoke' if smoke else ''}"
    nsroot = F["exp"] / "results" / "safety_guided_defense" / "variantG_bilstm_representation_test" / "seed42" / "g1_finetune_cleaninit"
    base = (nsroot / "_smoke") if smoke else nsroot
    ck_dir = F["exp"] / "checkpoints" / "safety_guided_defense" / "variantG_bilstm_representation_test" / "seed42" / "g1_finetune_cleaninit"
    logs_dir = base / "logs"; ana_dir = base / "analysis"; meta_dir = base / "metadata"
    dirs = [base, logs_dir] if smoke else [ck_dir, logs_dir, ana_dir, meta_dir]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    ck = {k: ck_dir / f"{run}_{k}_best.pt" for k in ("v2safety", "v2maxrec", "v2lowFA", "v2macroF1")}

    print("=" * 80)
    print(f"BiLSTM G1 fine-tune {tag.upper()}  init={Path(F['init_checkpoint']).name}  run={run}")
    print(f"  G1: lam_s={tvg.LAM_S} lam_f={tvg.LAM_F} lam_t={LAM_T} w_wr={W_WR} fw={args.fall_weight} | "
          f"NEW lr={args.lr} clip={args.clip} | guard acc>={V2_GUARD_ACC} mF1>={V2_GUARD_F1} | "
          f"epochs={args.epochs} patience={args.patience} min={args.min_epochs} eps={F['train_epsilons']}")
    print("=" * 80)

    history = []
    best = {"v2safety": (-1e9, -1), "v2maxrec": ((-1e9, 1e9), -1), "v2lowFA": ((1e9, -1e9), -1), "v2macroF1": (-1e9, -1)}
    best_rec = {}; no_improve = 0; start = time.time(); mb = args.smoke_batches if smoke else None

    for epoch in range(1, args.epochs + 1):
        tr = train_one_epoch_g1_clipped(F["model"], F["train_loader"], F["train_criterion"], F["atk_criterion"],
                                        F["optimizer"], device, F["train_epsilons"], args.train_pgd_steps,
                                        F["rng"], tsg, LAM_T, W_WR, F["fall_idx"], args.clip, max_batches=mb)
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
                        "init_checkpoint": F["init_checkpoint"], "args": vars(args)}, ck[key])

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
                        "mean_targeted": tr["mean_targeted"], "mean_grad_norm": tr["mean_grad_norm"],
                        "val_clean_accuracy": acc, "val_clean_macro_f1": f1, "val_clean_fall_recall": vb["val_clean_fall_recall"],
                        "val_fgsm_fall_recall": vb["val_fgsm_fall_recall"], "val_pgd_fall_recall": rec,
                        "val_fgsm_false_fall_alarms": vb["val_fgsm_false_fall_alarms"], "val_pgd_false_fall_alarms": fpv,
                        "val_normalized_false_alarm_burden": vb["val_normalized_false_alarm_burden"], "safety_score": sc,
                        "v2_eligible": int(eligible), "sel_v2safety": flags["v2safety"], "sel_v2maxrec": flags["v2maxrec"],
                        "sel_v2lowFA": flags["v2lowFA"], "sel_v2macroF1": flags["v2macroF1"]})
        print(f"Epoch {epoch:03d}/{args.epochs} | loss={tr['train_loss']:.3f} base={tr['mean_base']:.3f} "
              f"src={tr['mean_src_motion']:.3f} fall={tr['mean_fall_margin']:.3f} tgt={tr['mean_targeted']:.3f} gnorm={tr['mean_grad_norm']:.2f} | "
              f"acc={acc:.3f} f1={f1:.3f} cFR={vb['val_clean_fall_recall']:.3f} pgd_fr={rec:.3f} pgd_FP={fpv} "
              f"score={sc:.3f} v2elig={int(eligible)} "
              f"[{'S' if flags['v2safety'] else '.'}{'R' if flags['v2maxrec'] else '.'}"
              f"{'L' if flags['v2lowFA'] else '.'}{'F' if flags['v2macroF1'] else '.'}]")
        if not smoke and args.patience > 0 and epoch >= args.min_epochs and no_improve >= args.patience:
            print(f"Early stopping at epoch {epoch} (best v2safety epoch {best['v2safety'][1]})."); break

    elapsed = time.time() - start; last_epoch = history[-1]["epoch"]; fields = list(history[0].keys())
    if not smoke:
        torch.save({"epoch": last_epoch, "model_state_dict": F["model"].state_dict(), "selection_method": "last",
                    "run_name": run, "model_name": MODEL_NAME, "init_checkpoint": F["init_checkpoint"], "args": vars(args)},
                   ck_dir / f"{run}_last.pt")
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
        meta = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "stage": "bilstm_g1_finetune_cleaninit_seed42_pilot",
                "method": "BiLSTM G1 fine-tune from clean-qualified checkpoint (representation pivot)",
                "namespace": "variantG_bilstm_representation_test/seed42/g1_finetune_cleaninit", "run_name": run,
                "model_name": MODEL_NAME, "model_params": sum(p.numel() for p in F["model"].parameters()), "seed": args.seed,
                "init_checkpoint": F["init_checkpoint"], "init_val_macro_f1": F.get("init_val_macro_f1"),
                "deviation_note": "DEVIATION from pre-reg single-variable from-scratch framing: BiLSTM is CLEAN-INITIALIZED "
                                  "(from-scratch G1 did not converge on the recurrent backbone; see NON_CONVERGENCE_DO_NOT_CITE.md). "
                                  "Backbone remains the scientific variable; clean init + grad clip + lower LR are budget "
                                  "accommodations permitted by the pre-reg convergence-failure clause. No loss/lambda/gamma/fall_weight change.",
                "lam_s": tvg.LAM_S, "lam_f": tvg.LAM_F, "lam_t": LAM_T, "w_wr": W_WR, "fall_weight": args.fall_weight,
                "lr": args.lr, "grad_clip": args.clip, "objective": "L_FWCE + lam_s*L_src + lam_f*L_fall + lam_t*L_tgt (G1, unchanged)",
                "v2_guard": {"min_clean_accuracy": V2_GUARD_ACC, "min_clean_macro_f1": V2_GUARD_F1},
                "train_epsilons": F["train_epsilons"], "train_pgd_steps": args.train_pgd_steps,
                "epochs_run": last_epoch, "split_sizes": F["split_sizes"], "test_set_used": False,
                "selected_epochs": {k: best[k][1] for k in ck}, "checkpoints": {k: str(v) for k, v in ck.items()},
                "go_no_go_ref": "results/safety_guided_defense/boundary_aware_selective_at/seed42/g1_baseline_val_frontier.json (LeNet G1 val PGD AUROC 0.876 / recall@FAR<=10% 0.477)",
                "preregistration": "results/safety_guided_defense/variantG_bilstm_representation_test/BILSTM_G1_REPRESENTATION_TEST_PREREGISTRATION.md",
                "claim_boundary": "window-level digital-domain white-box; seed42/BiLSTM only; not solved/certified/clinical/OTA",
                "device": str(device), "python_version": platform.python_version(), "torch_version": torch.__version__,
                "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(F["exp"])), "elapsed_seconds": elapsed}
        with (meta_dir / f"{run}_metadata.json").open("w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, default=str)
    print("-" * 80)
    print(f"{tag} done in {elapsed:.1f}s ({last_epoch} epochs)." + ("" if smoke else
          " selected epochs: " + ", ".join(f"{k}={best[k][1]}" for k in ck)))
    if not smoke:
        print("  NEXT: export val clean/fgsm/pgd (--model bilstm) for selected checkpoints; val PGD AUROC vs 0.876 bar; PGD-20 durability.")
    print("=" * 80)


def main():
    args = parse_args()
    if args.seed != 42:
        raise SystemExit(f"BiLSTM G1 fine-tune is seed-42 ONLY for now (got seed {args.seed}).")
    F = tvg.load_foundation(args)
    F = swap_to_bilstm_init(F, args)
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
