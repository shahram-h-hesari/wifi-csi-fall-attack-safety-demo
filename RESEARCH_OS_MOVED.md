# Research OS Moved

The embedded Research OS copy that previously lived in this experiment repository has been
retired. The canonical Research OS repository is now:

```text
C:\Users\Hesar\Documents\GitHub\research-os
```

Use `research-os/main` for dashboards, registries, receipts, acceptance contracts, roadmap
state, and Research OS automation.

Historical embedded Research OS files remain available in Git history and in the annotated
archival tag:

```text
archive/research-os-source-pre-decommission
```

This repository remains authoritative for experiment code, results, figures, checkpoints,
thesis artifacts, experiment-specific agents/skills, and safety controls that protect this
experiment workspace. In particular, the live test-split safeguards remain here:

```text
scripts/automation/test_split_guard.py
scripts/automation/test_split_guard_cases.py
.claude/settings.json
```

Do not recreate Research OS governance files in this repository. When Research OS state or
dashboard work is needed, switch to the canonical `research-os` repository and resolve this
repository as the external experiment/evidence source.
