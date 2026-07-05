"""
D14 training -- partial-AUC / low-FAR ranking-loss fine-tuning (FINAL F20 ATTEMPT).

Fine-tunes the AFAC-score checkpoint (D8b `optionB_maxscore`) with a PGD adversarial-training
cross-entropy term plus a low-FAR ranking term that penalizes adversarial fall scores ranked below
the high-risk non-fall tail. Validation-only; the held-out TEST split is NEVER touched by this
script.

Pre-registration: 20260704_d14_partial_auc_low_far_preregistration.md (thesis commit
7ee228369052461682741a372a1ac2c3209fecb1). Preflight: commit 67efeda578db53ae4eab0ca82dccb0d5c9373f23.

Ranking loss (per PGD-attacked minibatch), s(x) = softmax(logits)[:, 1] (fall class index 1):
    H = top-k non-fall by s(x), k = max(1, ceil(0.20 * N_nonfall_batch)); margin m = 0.10
    L_rank = mean_{i in fall, j in H} max(0, m - (s_i - s_j))
    (0 if the batch has no fall or no non-fall samples)
    L_D14 = lambda_ce * L_PGD_CE + lambda_rank * L_rank

Configs (differ ONLY in lambda_rank): A = (1.00, 0.50), B = (1.00, 1.00). Seeds: 42, 43, 44 only.

Commands (safe): --help, --dry-run (builds nothing that touches data).
Running WITHOUT --dry-run performs training and per-epoch VALIDATION diagnostics only.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import argparse
import csv
import json
import platform
import subprocess
import sys
import time

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

sys.path.insert(0, str(Path(__file__).resolve().parent))
import d14_common as C  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="D14 low-FAR ranking-loss fine-tuning (validation-only; final F20 attempt).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--config", choices=sorted(C.CONFIGS), required=True,
                   help="Pre-registered config (A or B). Configs differ ONLY in lambda_rank.")
    p.add_argument("--seed", type=int, required=True,
                   help="Pre-registered seed (42, 43, or 44 only).")
    p.add_argument("--epochs", type=int, default=C.DEFAULT_EPOCHS,
                   help="Fine-tune epochs (identical across configs/seeds).")
    p.add_argument("--lr", type=float, default=C.DEFAULT_LR,
                   help="Adam learning rate (identical across configs/seeds).")
    p.add_argument("--batch-size", type=int, default=C.DEFAULT_BATCH_SIZE,
                   help="Training batch size (identical across configs/seeds).")
    p.add_argument("--use-d10-fallback", action="store_true",
                   help="Start from the D10 fallback checkpoint instead of AFAC-score. "
                        "Only permitted if the AFAC-score checkpoint is unusable; must be "
                        "declared before training, never selected after seeing outcomes.")
    p.add_argument("--dry-run", action="store_true",
                   help="Print the resolved config and exit WITHOUT loading data or training.")
    return p.parse_args()


def resolve_start_checkpoint(args):
    if args.use_d10_fallback:
        ckpt = C.D10_FALLBACK_CHECKPOINT
        which = "D10_fallback (GR1_v2macroF1)"
    else:
        ckpt = C.AFAC_SCORE_CHECKPOINT
        which = "AFAC_score_primary (optionB_maxscore)"
    C.refuse_if_test_path(ckpt)
    return ckpt, which


def fall_scores(model, adv_batch):
    """s(x) = softmax(logits)[:, FALL_CLASS_INDEX], grad-carrying."""
    logits = model(adv_batch).float()
    probs = torch.softmax(logits, dim=1)
    return probs[:, C.FALL_CLASS_INDEX], logits


def ranking_loss(s, labels):
    """Low-FAR hinge ranking loss on one adversarial minibatch.

    Fall/non-fall identity from TRUE labels. High-risk tail H selected by DETACHED score
    value; hinge penalty computed on the grad-carrying scores. Returns (loss, active_bool).
    """
    fall_mask = labels == C.FALL_CLASS_INDEX
    nonfall_mask = ~fall_mask
    n_fall = int(fall_mask.sum().item())
    n_nonfall = int(nonfall_mask.sum().item())
    if n_fall == 0 or n_nonfall == 0:
        return s.new_zeros(()), False

    s_fall = s[fall_mask]                       # (F,)
    s_nonfall = s[nonfall_mask]                 # (Nn,)
    k = C.tail_k(n_nonfall)
    # select the top-k non-fall tail by DETACHED value, then gather grad-carrying scores
    tail_idx = torch.topk(s_nonfall.detach(), k=min(k, n_nonfall), largest=True).indices
    s_H = s_nonfall[tail_idx]                    # (K,)
    diff = s_fall.unsqueeze(1) - s_H.unsqueeze(0)          # (F, K)
    hinge = torch.clamp(C.RANK_MARGIN - diff, min=0.0)      # max(0, m - (s_i - s_j))
    return hinge.mean(), True


def train_one_epoch(model, train_loader, rca, atk_criterion, ce_criterion,
                    optimizer, device, lambda_ce, lambda_rank):
    """Full-batch PGD-AT epoch: attack whole minibatch, then L_ce + lambda_rank * L_rank."""
    model.train()
    tot_ce = tot_rank = tot_total = 0.0
    n_batches = 0
    n_rank_active = 0
    for inputs, labels in train_loader:
        inputs = inputs.to(device).float()
        labels = labels.type(torch.LongTensor).to(device)

        # PGD attack on the whole minibatch (byte-identical eval-convention attack).
        model.eval()
        adv = rca.generate_attacked_batch(
            model, inputs, labels, atk_criterion, "pgd",
            C.PGD_EPSILON, C.PGD_ALPHA, C.PGD_STEPS)
        model.train()

        optimizer.zero_grad()
        s, logits = fall_scores(model, adv)
        l_ce = ce_criterion(logits, labels)
        l_rank, active = ranking_loss(s, labels)
        loss = lambda_ce * l_ce + lambda_rank * l_rank
        loss.backward()
        optimizer.step()

        tot_ce += float(l_ce.item())
        tot_rank += float(l_rank.item())
        tot_total += float(loss.item())
        n_batches += 1
        n_rank_active += int(active)

    return {
        "train_pgd_ce_loss": tot_ce / max(n_batches, 1),
        "train_rank_loss": tot_rank / max(n_batches, 1),
        "train_total_loss": tot_total / max(n_batches, 1),
        "n_batches": n_batches,
        "n_rank_active_batches": n_rank_active,
        "rank_active_fraction": n_rank_active / max(n_batches, 1),
    }


def eval_pgd_fall_scores(model, val_loader, rca, atk_criterion, device):
    """Validation PGD fall scores s(x) and binary fall labels (for cap-0.17 selection)."""
    model.eval()
    y, s = [], []
    for inputs, labels in val_loader:
        inputs = inputs.to(device).float()
        labels = labels.type(torch.LongTensor).to(device)
        adv = rca.generate_attacked_batch(
            model, inputs, labels, atk_criterion, "pgd",
            C.PGD_EPSILON, C.PGD_ALPHA, C.PGD_STEPS)
        with torch.no_grad():
            probs = torch.softmax(model(adv).float(), dim=1)
        s.extend(probs[:, C.FALL_CLASS_INDEX].cpu().tolist())
        y.extend([1 if int(t) == C.FALL_CLASS_INDEX else 0 for t in labels.cpu().tolist()])
    return y, s


def main():
    args = parse_args()
    config = C.validate_config(args.config)
    seed = C.validate_seed(args.seed)
    lam = C.CONFIGS[config]
    lambda_ce, lambda_rank = lam["lambda_ce"], lam["lambda_rank"]
    start_ckpt, which_start = resolve_start_checkpoint(args)

    out_dir = C.D14_RESULTS_ROOT / f"config_{config}" / f"seed{seed}"
    print("=" * 78)
    print(f"D14 training  config={config} (lambda_ce={lambda_ce}, lambda_rank={lambda_rank})  "
          f"seed={seed}")
    print(f"start checkpoint: {which_start}")
    print(f"  {start_ckpt}")
    print(f"PGD: eps={C.PGD_EPSILON}, steps={C.PGD_STEPS}, alpha={C.PGD_ALPHA:.6f}, "
          f"random_start={C.PGD_RANDOM_START}")
    print(f"ranking loss: margin m={C.RANK_MARGIN}, tail_frac={C.RANK_TAIL_FRACTION}, "
          f"adv_fraction={C.ADV_FRACTION} (full-batch PGD-AT)")
    print(f"epochs={args.epochs}, lr={args.lr}, batch_size={args.batch_size}")
    print(f"output dir: {out_dir}")
    print(f"clean guard: {C.CLEAN_GUARD}")
    print(f"TEST SPLIT: never accessed by this script.")
    print("=" * 78)

    if args.dry_run:
        print("[dry-run] resolved config only; no data loaded, no training run. Exiting.")
        return

    if not start_ckpt.exists():
        raise SystemExit(f"start checkpoint not found: {start_ckpt}")

    s1, rca, build_model = C.import_pipeline()
    s1.set_seed(seed)
    data = s1.load_raw_ut_har(C.BENCH_DIR)
    train_loader, val_loader, _test_loader_unused, split_sizes = s1.build_loaders(
        data, args.batch_size)
    # _test_loader_unused is deliberately never referenced past this point.
    assert split_sizes["val"] == 496, f"expected 496 val windows, got {split_sizes['val']}"

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model("lenet").to(device)
    state = torch.load(start_ckpt, map_location=device, weights_only=False)
    sd = state["model_state_dict"] if isinstance(state, dict) and "model_state_dict" in state else state
    model.load_state_dict(sd, strict=True)

    ce_criterion = nn.CrossEntropyLoss()
    atk_criterion = nn.CrossEntropyLoss()   # unweighted attack loss (untargeted)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    out_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = out_dir / "training_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"d14_config_{config}_seed{seed}_training_log.csv"

    best = None  # highest val PGD recall at cap-0.17 among clean-guard-passing epochs
    log_rows = []
    t0 = time.time()
    for epoch in range(1, args.epochs + 1):
        tr = train_one_epoch(model, train_loader, rca, atk_criterion, ce_criterion,
                             optimizer, device, lambda_ce, lambda_rank)

        # per-epoch validation diagnostics (clean guard) + PGD cap-0.17 selection metric
        _, c_true, c_pred, _ = s1.run_inference(model, val_loader, ce_criterion, device)
        clean_acc = s1.accuracy_of(c_true, c_pred)
        clean_mf1 = s1.macro_f1_of(c_true, c_pred)
        clean_fb = s1.compute_fall_binary_metrics(c_true, c_pred)
        clean_fall_recall = clean_fb["fall_recall"]

        y_val, s_val = eval_pgd_fall_scores(model, val_loader, rca, atk_criterion, device)
        sel = C.select_threshold(y_val, s_val, C.PRIMARY_FAR_CAP)
        val_pgd_recall_017 = sel["recall"] if sel else float("nan")
        val_pgd_far_017 = sel["FAR"] if sel else float("nan")
        val_pgd_tp_017 = sel["TP"] if sel else 0

        guard_ok = (clean_acc >= C.CLEAN_GUARD["min_clean_accuracy"]
                    and clean_mf1 >= C.CLEAN_GUARD["min_clean_macro_f1"]
                    and clean_fall_recall >= C.CLEAN_GUARD["min_clean_fall_recall"])

        row = {
            "epoch": epoch,
            "train_pgd_ce_loss": f"{tr['train_pgd_ce_loss']:.6f}",
            "train_rank_loss": f"{tr['train_rank_loss']:.6f}",
            "train_total_loss": f"{tr['train_total_loss']:.6f}",
            "n_batches": tr["n_batches"],
            "n_rank_active_batches": tr["n_rank_active_batches"],
            "rank_active_fraction": f"{tr['rank_active_fraction']:.4f}",
            "val_clean_accuracy": f"{clean_acc:.6f}",
            "val_clean_macro_f1": f"{clean_mf1:.6f}",
            "val_clean_fall_recall": f"{clean_fall_recall:.6f}",
            "val_pgd_recall_at_cap017": f"{val_pgd_recall_017:.6f}",
            "val_pgd_far_at_cap017": f"{val_pgd_far_017:.6f}",
            "val_pgd_tp_at_cap017": val_pgd_tp_017,
            "clean_guard_pass": guard_ok,
        }
        log_rows.append(row)
        print(f"[epoch {epoch:02d}] ce={tr['train_pgd_ce_loss']:.4f} rank={tr['train_rank_loss']:.4f} "
              f"rank_active={tr['rank_active_fraction']:.2f} | clean acc={clean_acc:.3f} "
              f"mF1={clean_mf1:.3f} fR={clean_fall_recall:.3f} guard={'ok' if guard_ok else 'FAIL'} | "
              f"valPGD R@0.17={val_pgd_recall_017:.3f} (TP={val_pgd_tp_017}, FAR={val_pgd_far_017:.3f})")

        # in-run checkpoint selection: best val PGD recall@cap-0.17 among guard-passing epochs;
        # tie-break lower FAR, then earlier epoch (documented; identical for all configs/seeds).
        if guard_ok and sel is not None:
            key = (val_pgd_recall_017, -val_pgd_far_017, -epoch)
            if best is None or key > best["key"]:
                best = {"key": key, "epoch": epoch,
                        "val_pgd_recall_017": val_pgd_recall_017,
                        "val_pgd_far_017": val_pgd_far_017,
                        "val_pgd_tp_017": val_pgd_tp_017,
                        "state_dict": {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}}

    # write training log
    with log_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(log_rows[0].keys()))
        w.writeheader()
        w.writerows(log_rows)
    print(f"[write] {log_path.relative_to(C.REPO)}")

    # save best + last checkpoints
    last_ckpt_path = out_dir / f"d14_config_{config}_seed{seed}_last.pt"
    torch.save({"epoch": args.epochs, "model_state_dict": model.state_dict(),
                "config": config, "seed": seed}, last_ckpt_path)
    best_ckpt_path = out_dir / f"d14_config_{config}_seed{seed}_best.pt"
    if best is not None:
        torch.save({"epoch": best["epoch"], "model_state_dict": best["state_dict"],
                    "config": config, "seed": seed,
                    "selection": "best val PGD recall@cap-0.17 within clean guard"},
                   best_ckpt_path)
        print(f"[write] {best_ckpt_path.relative_to(C.REPO)} (epoch {best['epoch']})")
    else:
        print("[warn] NO epoch passed the clean guard; no best checkpoint saved. "
              "Validation gate will treat this config/seed as guard-failing.")

    # export canonical VALIDATION scores for the best checkpoint via the byte-identical
    # export tool (clean/FGSM/PGD, eps=0.030, PGD-10). --split val ONLY (never test).
    val_eval_dir = out_dir / "val_eval"
    if best is not None:
        run_name = f"d14_config_{config}_seed{seed}"
        cmd = [sys.executable,
               str(C.REPO / "scripts" / "export_probability_predictions.py"),
               "--checkpoint", str(best_ckpt_path),
               "--model", "lenet", "--epsilon", str(C.PGD_EPSILON),
               "--pgd-steps", str(C.PGD_STEPS),
               "--run-name", run_name,
               "--out-dir", str(val_eval_dir), "--split", "val"]
        print("[export] canonical validation scores via export_probability_predictions.py --split val")
        subprocess.run(cmd, check=True)

    # metadata
    meta = {
        "stage": "d14_low_far_ranking_finetune",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "thesis_prereg_commit": C.D14_PREREG_COMMIT,
        "thesis_clarification_commit": C.D14_CLARIFICATION_COMMIT,
        "preflight_commit": C.PREFLIGHT_COMMIT,
        "config": config, "seed": seed,
        "lambda_ce": lambda_ce, "lambda_rank": lambda_rank,
        "start_checkpoint": str(start_ckpt),
        "start_checkpoint_rule": "AFAC-score primary; D10 fallback only if AFAC unusable",
        "used_d10_fallback": bool(args.use_d10_fallback),
        "score_convention": "s(x) = softmax(logits)[:, 1] (fall class index 1); higher = more fall-like",
        "pgd": {"epsilon": C.PGD_EPSILON, "steps": C.PGD_STEPS, "alpha": C.PGD_ALPHA,
                "random_start": C.PGD_RANDOM_START, "projection": "L-infinity, no [0,1] clamp",
                "loss": "untargeted cross-entropy on true label"},
        "ranking_loss": {"margin_m": C.RANK_MARGIN, "tail_fraction": C.RANK_TAIL_FRACTION,
                         "definition": "H=top-k nonfall by s(x), k=max(1,ceil(0.20*N_nonfall_batch)); "
                                       "L_rank=mean_{i in fall, j in H} max(0, m-(s_i-s_j)); "
                                       "0 if batch lacks fall or non-fall"},
        "adv_fraction": C.ADV_FRACTION,
        "full_batch_pgd_statement": ("D14 uses full-batch PGD adversarial fine-tuning; "
                                     "no 50/50 clean/PGD mixture was used. Both L_PGD_CE and "
                                     "L_rank are computed on the PGD-attacked minibatch. Clean "
                                     "behavior is protected by the clean validation guard."),
        "clean_guard": C.CLEAN_GUARD,
        "epochs": args.epochs, "lr": args.lr, "batch_size": args.batch_size,
        "best_epoch": (best["epoch"] if best else None),
        "test_set_used": False,
        "no_test_read_statement": "This training script performed NO held-out test read. "
                                  "Only the training and validation splits were accessed.",
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "elapsed_seconds": time.time() - t0,
    }
    meta_path = out_dir / f"d14_config_{config}_seed{seed}_metadata.json"
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"[write] {meta_path.relative_to(C.REPO)}")
    print("[done] D14 training complete for this config/seed. NO test read performed.")


if __name__ == "__main__":
    main()
