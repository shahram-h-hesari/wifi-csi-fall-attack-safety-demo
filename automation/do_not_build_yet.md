# Do-not-build-yet — parking lot

SOURCE-OF-TRUTH. Each item lists **why not now** and the **revisit condition** that would change the
answer. Keeping this explicit prevents rejected ideas from resurfacing and re-consuming analysis time.

| Item | Why not now | Revisit when |
|---|---|---|
| Automated val hyperparameter / threshold search (Optuna-style) | 44 validation falls — unbounded automated selection **will** overfit validation and repeat the D10/D11 val→test transfer failure at scale | Only with an explicit multiplicity budget + the `validation_selection_log.csv` counter live and reviewed |
| Multi-seed fan-out launcher (seeds 43–46) | Premature by project rule; no seed-42 candidate has passed a frozen read at ε=0.030 yet | A seed-42 candidate survives a frozen test read |
| Overleaf / thesis `.tex` auto-editor or auto-sync | Thesis repo must stay human-gated; auto-edits destroy provenance | Never auto; at most generate `.tex` fragments into `tables/` for manual copy |
| Auto-commit / auto-push hooks | Provenance requires deliberate commits; `git-stage-check` is the human gate | Not planned |
| Parallel / concurrent experiment execution | Violates one-model-at-a-time; `experiment-queue` gives the benefit sequentially | Not planned |
| CI / GitHub-Actions training pipeline | GPU is local; cloud CI is infra cost with no scientific payoff now | If compute moves off local machine |
| Two-way Notion sync | Creates a second writable source-of-truth; a Notion-side edit flowing back is an evidence-free state change | Never (one-way push only) |
| PostToolUse hook that mutates the dashboard | Too chatty; state-mutating background magic muddies provenance | A Stop-event *reminder* (non-mutating) is acceptable at Stage 5+ |
| Static HTML dashboard (`dashboard/index.html`, Stage 8) | Depends on stable `status.json` (Stage 4) + `artifact_manifest.csv` (Stage 6); building now risks schema churn, false confidence, and CSS meta-work | Both dependencies exist AND the Markdown dashboard has run *generated* (not hand-maintained) for ≥ a few days |
