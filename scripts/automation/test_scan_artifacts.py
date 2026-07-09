#!/usr/bin/env python
"""Stage 6 acceptance test for scan_artifacts.py. Read-only except for a scratchpad manifest.

Covers the seven required checks:
  1. dry-run does not write the manifest
  2. --write writes ONLY the manifest (+ .meta.json)
  3. idempotency (two writes -> identical manifest CSV)
  4. no frozen-test from filename heuristic
  5. a validation file named with "test" is still validation-only
  6. 15-artifact spot-check labels (+ path preflight; propose closest match if any missing)
  7. no writes to results/ figures/ tables/ notes/ thesis/ checkpoints/ .codex/

Run: python scripts/automation/test_scan_artifacts.py
"""
from __future__ import annotations

import csv
import glob
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scan_artifacts as sa  # noqa: E402

REPO = sa.REPO
PROTECTED = ["results", "figures", "tables", "notes", "thesis_artifacts", "checkpoints", ".codex"]

SPOT = [
 ("results/converged_baseline/converged_seed42_summary_metrics.csv", "test-descriptive"),
 ("results/converged_attacks/converged_seed42_pgd_safety_metrics_test_epsilon_0_03.csv", "test-descriptive"),
 ("results/defense_attempt_inventory/pgd_epsilon_frontier/frozen_test_read/AFAC_maxscore_eps0015_TESTREAD_pgd_probabilities_test_epsilon_0_015.csv", "frozen-test"),
 ("results/defense_attempt_inventory/pgd_epsilon_frontier/frozen_test_read/FROZEN_H15_TEST_RESULT.md", "frozen-test"),
 ("results/defense_attempt_inventory/defense_attempt_results_long.csv", "diagnostic-internal"),
 ("results/safety_guided_defense/variantG_bilstm_representation_test/seed42/g1_finetune_cleaninit/val_eval/BLF_v2safety_pgd_probabilities_val_epsilon_0_03.csv", "validation-only"),
 ("results/defense_attempt_inventory/pgd_epsilon_frontier/val_sweep/eps0015/AFAC_maxscore_eps0015_pgd_probabilities_val_epsilon_0_015.csv", "validation-only"),
 ("results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/test_eval/optionB_maxscore_pgd_probabilities_test_epsilon_0_03.csv", "test-post-hoc"),
 ("results/thesis_table_9_robustness_failure_thresholds.csv", "test-descriptive"),
 ("tables/chapter_cross_architecture_multiseed_table.tex", "test-descriptive"),
 ("figures/thesis_figure_2_fgsm_pgd_epsilon_sweep.png", "test-descriptive"),
 ("figures/converged_ch06_artifacts/ch06_figure_6_1_defense_effect_summary.png", "test-descriptive"),
 ("results/multiseed_robustness/multiseed_summary_stats.csv", "test-descriptive"),
 ("results/safety_guided_defense/final_defense_synthesis/REPRESENTATION_CEILING_CAPSTONE.md", "diagnostic-internal"),
 ("results/defense_attempt_inventory/H15_FROZEN_TEST_DECISION_MEMO.md", "diagnostic-internal"),
]


def preflight():
    ok = True
    for p, _ in SPOT:
        if not (REPO / p).exists():
            ok = False
            base = os.path.basename(p)
            cands = (glob.glob(f"results/**/{base}", recursive=True)
                     + glob.glob(f"figures/**/{base}", recursive=True)
                     + glob.glob(f"tables/**/{base}", recursive=True))
            print(f"[preflight] MISSING {p}")
            for c in cands[:3]:
                print(f"            PROPOSED replacement -> {c}")
    print(f"[preflight] {'all 15 paths present' if ok else 'MISSING paths — fix SPOT list, do not auto-substitute'}")
    return ok


def protected_snapshot():
    out = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO),
                         capture_output=True, text=True)
    return {ln for ln in out.stdout.splitlines()
            if any(ln[3:].strip().strip('"').startswith(g + "/") for g in PROTECTED)}


def main():
    results = []
    ok_all = True

    def check(name, cond):
        nonlocal ok_all
        ok_all &= cond
        results.append((name, cond))
        print(f"[{'PASS' if cond else 'FAIL'}] {name}")

    pf = preflight()
    check("6a. path preflight (15 present)", pf)

    tmp = Path(tempfile.mkdtemp(prefix="scan_acc_"))
    m1 = tmp / "m1.csv"
    m2 = tmp / "m2.csv"
    real = REPO / "automation" / "artifact_manifest.csv"
    real_before = real.exists()

    # 1. dry-run writes nothing
    before = protected_snapshot()
    r = subprocess.run([sys.executable, "scripts/automation/scan_artifacts.py"],
                       cwd=str(REPO), capture_output=True, text=True)
    check("1. dry-run: manifest not created", (real.exists() == real_before) and r.returncode == 0)

    # 7. dry-run touched no protected path
    check("7. dry-run: no protected path modified", protected_snapshot() == before)

    # 2/3. two writes to scratchpad
    subprocess.run([sys.executable, "scripts/automation/scan_artifacts.py",
                    "--write", "--manifest-out", str(m1)], cwd=str(REPO), capture_output=True)
    subprocess.run([sys.executable, "scripts/automation/scan_artifacts.py",
                    "--write", "--manifest-out", str(m2)], cwd=str(REPO), capture_output=True)
    check("2. --write did not write into real automation manifest", real.exists() == real_before)
    check("3. idempotency: two manifests byte-identical",
          m1.read_bytes() == m2.read_bytes())
    check("7b. --write to scratchpad: no protected path modified", protected_snapshot() == before)
    check("2b. sidecar meta.json produced", m1.with_suffix(".meta.json").exists())

    rows = {r["path"]: r for r in csv.DictReader(m1.open(encoding="utf-8"))}

    # 4. no frozen-test from filename heuristic (fabricated adversarial names, pure labeler)
    frozen = sa.build_frozen_allowlist()
    by_path, by_base = sa.load_ledger()
    fake_test = "results/NOWHERE/some_FROZEN_TEST_thing_test_epsilon_0_03.csv"
    lvl, _, _ = sa.evidence_level(fake_test, frozen, by_path, by_base)
    check("4. fabricated 'FROZEN_TEST' name is NOT frozen-test", lvl != "frozen-test")

    # 5. validation file named with 'test' still validation-only
    val_named_test = "results/x/val_eval/model_test_pgd_probabilities_val_epsilon_0_03.csv"
    lvl2, _, _ = sa.evidence_level(val_named_test, frozen, by_path, by_base)
    check("5. val file named with 'test' -> validation-only", lvl2 == "validation-only")

    # 6. spot-check labels
    spot_ok = True
    for p, exp in SPOT:
        got = rows.get(p, {}).get("evidence_level", "MISSING")
        if got != exp:
            spot_ok = False
            print(f"    spot MISMATCH {p}: want {exp} got {got}")
    check("6. 15 spot-check evidence labels", spot_ok)

    # extra invariant: every frozen-test row lives in the allowlist
    fr = [p for p, r in rows.items() if r["evidence_level"] == "frozen-test"]
    check("4b. every frozen-test row is in the protocol allowlist", all(p in frozen for p in fr))

    print("\nRESULT:", "ALL PASS" if ok_all else "FAILURES")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
