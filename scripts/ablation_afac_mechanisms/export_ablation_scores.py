"""
AFAC 2x2 ablation -- score export driver.

Delegates every export to the frozen `scripts/export_probability_predictions.py`, so the attack
pipeline (FGSM single-step; PGD L-inf steps=10, alpha=epsilon/6, no value clamp) is byte-identical
to every historical AFAC/G1/D10/D11/D13/D14 export in this repository. This driver adds NO attack
logic of its own; it only enumerates (variant, seed, checkpoint, epsilon, split) and shells out.

Exports, per trained model:
    checkpoints : last (epoch 70)  and  maxscore (validation-selected)
    epsilons    : 0.015 (primary)  and  0.030 (secondary)   -- kept strictly separate downstream
    splits      : val (used for ALL threshold selection)  and  test (confirmatory benchmark only)

The val exports are what every threshold is chosen from. Test exports exist only so a frozen,
validation-selected threshold can be applied once for the confirmatory read; no selection of any
kind is performed on test scores (enforced in analyze_ablation.py, not here).

Commands:
    python scripts/ablation_afac_mechanisms/export_ablation_scores.py --seeds 42
    python scripts/ablation_afac_mechanisms/export_ablation_scores.py --seeds 42 43 44 45 46
"""
from __future__ import annotations

from pathlib import Path
import argparse
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[2]
VARIANTS = ("V00", "V10", "V01", "V11")
CKPTS = ("last", "maxscore")
EPSILONS = (0.015, 0.03)
SPLITS = ("val", "test")


def eps_token(eps: float) -> str:
    sys.path.insert(0, str(REPO / "scripts"))
    sys.path.insert(0, str(REPO / "third_party" / "WiFi-CSI-Sensing-Benchmark"))
    import run_converged_attacks as rca
    return rca.epsilon_to_token(eps)


def ckpt_path(variant: str, seed: int, ckpt: str) -> Path:
    d = REPO / "checkpoints" / "ablation_afac_mechanisms" / variant / f"seed{seed}"
    return d / (f"{variant}_seed{seed}_last.pt" if ckpt == "last"
                else f"{variant}_seed{seed}_maxscore_best.pt")


def main():
    p = argparse.ArgumentParser(description="Export ablation fall scores (delegates to frozen exporter).")
    p.add_argument("--seeds", type=int, nargs="+", required=True)
    p.add_argument("--variants", nargs="+", default=list(VARIANTS))
    p.add_argument("--threads", type=int, default=2)
    p.add_argument("--skip-existing", action="store_true", default=True)
    p.add_argument("--force", action="store_true", help="re-export even if the CSV already exists")
    args = p.parse_args()

    tokens = {e: eps_token(e) for e in EPSILONS}
    py = str(REPO / ".venv" / "Scripts" / "python.exe")
    exporter = str(REPO / "scripts" / "export_probability_predictions.py")

    jobs, done, skipped, failed = [], 0, 0, []
    for variant in args.variants:
        for seed in args.seeds:
            for ckpt in CKPTS:
                cp = ckpt_path(variant, seed, ckpt)
                if not cp.exists():
                    print(f"[miss] checkpoint absent, skipping: {cp.relative_to(REPO)}")
                    continue
                for eps in EPSILONS:
                    for split in SPLITS:
                        run_name = f"{variant}_seed{seed}_{ckpt}_eps{tokens[eps]}"
                        out_dir = (REPO / "results" / "ablation_afac_mechanisms" / variant
                                   / f"seed{seed}" / "eval" / split)
                        marker = out_dir / f"{run_name}_pgd_probabilities_{split}_epsilon_{tokens[eps]}.csv"
                        jobs.append((variant, seed, ckpt, eps, split, run_name, out_dir, marker, cp))

    print(f"[plan] {len(jobs)} export jobs")
    t0 = time.time()
    for (variant, seed, ckpt, eps, split, run_name, out_dir, marker, cp) in jobs:
        if marker.exists() and not args.force:
            skipped += 1
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        cmd = [py, exporter, "--checkpoint", str(cp), "--model", "lenet",
               "--epsilon", str(eps), "--run-name", run_name,
               "--out-dir", str(out_dir), "--split", split]
        r = subprocess.run(cmd, capture_output=True, text=True,
                           env={**__import__("os").environ,
                                "OMP_NUM_THREADS": str(args.threads),
                                "MKL_NUM_THREADS": str(args.threads)})
        if r.returncode != 0:
            failed.append((run_name, split, r.stderr[-500:]))
            print(f"[FAIL] {run_name} {split}\n{r.stderr[-500:]}")
        else:
            done += 1
            print(f"[ok] {run_name} split={split} ({done}/{len(jobs)-skipped})", flush=True)

    print(f"[done] exported={done} skipped_existing={skipped} failed={len(failed)} "
          f"elapsed={time.time()-t0:.0f}s")
    if failed:
        for f in failed:
            print("  FAILED:", f[0], f[1])
        sys.exit(1)


if __name__ == "__main__":
    main()
