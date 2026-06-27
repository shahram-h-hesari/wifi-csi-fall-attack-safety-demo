"""
Variant G seed-42 pilot evaluation driver (analysis/eval only; no training).

For each pre-registered setting (G1/G2/G3) and its selection-v2 candidate checkpoints, invokes the
committed eval tools to produce the same test_eval artifact family used for Variant F:
  * export_probability_predictions.py  (clean / FGSM@0.030 / PGD-10@0.030 probabilities+logits)
  * export_probability_predictions.py  (PGD-20@0.030 probabilities, run-name suffix _pgd20)
  * run_converged_attacks.py --epsilon-sweep   (18-eps FGSM+PGD sweep; v2safety only, to bound compute)

Seed 42 ONLY. Reads the frozen G checkpoints under
checkpoints/safety_guided_defense/variantG_targeted_hardneg/seed42/. Writes under
results/safety_guided_defense/variantG_targeted_hardneg/seed42/test_eval/. Does NOT train, does NOT
touch seed44/45/46, does NOT use the test set for any selection. Idempotent (re-running overwrites
only its own test_eval CSVs).

Command:  python scripts/run_variantG_eval.py            # all settings
          python scripts/run_variantG_eval.py --setting G1
"""
from __future__ import annotations
from pathlib import Path
import argparse, subprocess, sys

EXP = Path(__file__).resolve().parents[1]
PY = sys.executable
CK = EXP / "checkpoints" / "safety_guided_defense" / "variantG_targeted_hardneg" / "seed42"
TE = EXP / "results" / "safety_guided_defense" / "variantG_targeted_hardneg" / "seed42" / "test_eval"
# v2safety = primary report candidate; v2maxrec/v2lowFA reported as secondary context.
CANDIDATES = ["v2safety", "v2maxrec", "v2lowFA"]
SWEEP_CANDIDATES = ["v2safety"]   # 18-eps sweep only for the primary candidate (compute budget)


def run(cmd):
    print(">>", " ".join(str(c) for c in cmd), flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=str(EXP))
    if r.returncode != 0:
        raise SystemExit(f"eval subcommand failed ({r.returncode}): {' '.join(map(str, cmd))}")


def eval_candidate(setting, cand):
    ckpt = CK / f"seed42_variantG_{setting}_{cand}_best.pt"
    if not ckpt.exists():
        print(f"[skip] {setting} {cand}: checkpoint not found ({ckpt.name})"); return False
    rn = f"G_{setting}_{cand}"
    # probabilities: clean / FGSM / PGD-10
    run([PY, "scripts/export_probability_predictions.py", "--checkpoint", ckpt, "--model", "lenet",
         "--run-name", rn, "--out-dir", TE, "--split", "test", "--epsilon", "0.03", "--pgd-steps", "10"])
    # probabilities: PGD-20 (pgd condition is the PGD-20 one)
    run([PY, "scripts/export_probability_predictions.py", "--checkpoint", ckpt, "--model", "lenet",
         "--run-name", f"{rn}_pgd20", "--out-dir", TE, "--split", "test", "--epsilon", "0.03", "--pgd-steps", "20"])
    # 18-eps FGSM+PGD sweep (primary candidate only)
    if cand in SWEEP_CANDIDATES:
        run([PY, "scripts/run_converged_attacks.py", "--checkpoint", ckpt, "--model", "lenet",
             "--run-name", rn, "--results-dir", TE, "--epsilon-sweep", "--attacks", "both"])
    return True


def main():
    ap = argparse.ArgumentParser(description="Variant G seed-42 eval driver (no training).")
    ap.add_argument("--setting", choices=["G1", "G2", "G3"], default=None, help="default: all three")
    args = ap.parse_args()
    TE.mkdir(parents=True, exist_ok=True)
    settings = [args.setting] if args.setting else ["G1", "G2", "G3"]
    done = []
    for s in settings:
        for c in CANDIDATES:
            if eval_candidate(s, c):
                done.append(f"{s}/{c}")
    print(f"[done] evaluated: {', '.join(done) if done else '(none)'}")


if __name__ == "__main__":
    main()
