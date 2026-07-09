---
name: git-stage-check
description: Pre-commit staging verifier for the WiFi-CSI thesis repo. Checks staged files for seed isolation, checkpoint leakage, log files, and git HEAD before commit.
---

Use this skill before any git commit in this repository.

Goal:
Verify that the staged files are safe to commit and do not accidentally include checkpoints, raw logs, or wrong-seed experiment files.

When invoked:

1. Ask the user:
   "Which seed(s) and variant are expected in this commit? Example: seed44, AFAC, G1, D10, D11."

2. Run:
   git diff --cached --name-status

3. Run:
   git status --short

4. Run:
   git rev-parse --short HEAD

5. Analyze only the staged files from:
   git diff --cached --name-status

Rules:

A. Checkpoint protection
- If any staged file ends with .pt, .pth, or .ckpt, report:
  VIOLATION: checkpoint file staged.
- These files must not be committed.

B. Log-file protection
- If any staged file ends with .log, report:
  VIOLATION: raw log file staged.
- Raw logs should not be committed unless the user explicitly says this is intentional.

C. Seed isolation
- Valid seed labels are seed42, seed43, seed44, seed45, and seed46.
- Compare staged file paths against the expected seed labels provided by the user.
- If a staged file contains a seed label that is not expected, report:
  VIOLATION: wrong-seed file staged.

D. Unstaged warning
- From git status --short, warn about modified but unstaged files that may affect provenance.
- Do not treat unstaged files as commit blockers unless they are clearly wrong-seed result files.

Final output format:

=== STAGE CHECK REPORT ===
Expected seed/variant:
Staged file count:
Checkpoint violations:
Log-file violations:
Wrong-seed staged files:
Unstaged warnings:
git HEAD:
Final decision:
==========================

If there are no violations, print:
STAGE CHECK PASSED - safe to commit.

If there is any violation, print:
STAGE CHECK FAILED - do not commit until violations are resolved.

Never run git add.
Never run git commit.
Never run git push.
Never modify files.
