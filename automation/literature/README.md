# Literature Registry — Policy (Research OS layer, D4a-1)

`paper_registry.yaml` is the SOURCE-OF-TRUTH for academic papers already cited or discussed in
the thesis, the experiment documentation, and the Research OS. It exists so that later layers —
the experiment-candidate registry, the Next Experiment Brainstorm Checker, literature-backed gap
analysis, and future dashboard literature summaries — can resolve "which real publication backs
this direction?" against one validated file instead of re-auditing the thesis every time. None of
those later layers is implemented yet; this registry makes no experiment recommendation.

## Purpose and scope (D4a-1: LOCAL CITED SOURCES ONLY)

- Every record was backfilled **read-only** from local, already-committed sources: the thesis
  repository's `references.bib`, its chapter citations, and the D1–D12 literature-framing section
  of `appendices/internal_defense_experiment_ledger.md`.
- **No external lookup was performed** — no web search, Crossref, Semantic Scholar, Google
  Scholar, or downloads. `registry_scope.external_metadata_verification: pending` records this.
- A later step (D4a-2, separate approval) may verify and enrich bibliographic metadata
  externally. Until then, every paper's `verification_status` is `local_bib_only` and no DOI or
  field may be presented as externally verified.

## Canonical paper identity

- `paper_id` pattern: `paper_<first-author-token>_<year>_<short-title-token>`, built only from
  locally recorded metadata — never from guessed metadata.
- `paper_id` values are unique and stable; downstream layers reference papers by `paper_id`, not
  by citation key.
- Internal experiment/ledger labels (`AFAC`, `BASAT`, `H15`, `D1`–`D14`, `G1`, `A1`, …) are NOT
  papers and must never be used as a paper title or `paper_id`. A paper record for an internal
  method exists only when a real cited publication underlies it (e.g., `pan2024sat` underlies the
  D11/SAT line; nothing underlies the internal label "BASAT" itself).

## Citation-key aliasing and duplicate handling

- A paper may own multiple `citation_keys` (e.g., the bib header documents the key replacement
  `narasimhan2013pauc` → `narasimhan2013partialauc`; both keys live on that ONE record).
- A citation key belongs to exactly one canonical paper — the validator refuses shared ownership.
- Duplicate detection uses: exact `paper_id`, exact citation keys, locally recorded DOI equality,
  and normalized-title equality (lowercased, punctuation-stripped — normalization is used ONLY
  for detection; the authoritative display title is preserved verbatim from the bibliography).
- DOI is a strong duplicate signal only when a DOI is locally recorded; DOIs are never inferred.
- Similarly named but distinct publications are NOT merged (e.g., `wicam2022` "WiCAM" and
  `xu2024wicam` "WiCAM2.0" are different papers and were deliberately not conflated).

## Metadata and verification states

- `metadata_status`: `complete_local` (title/authors/year/venue all present locally),
  `partial_local` (some fields missing locally — `notes` must say what is missing),
  `conflicting_local` (two local sources disagree — `metadata_conflicts` must describe the
  conflict; it is recorded, never silently resolved).
- `verification_status`: `local_bib_only` (all of D4a-1) or `externally_verified` (reserved for
  D4a-2; forbidden while `registry_scope.external_metadata_verification` is `pending`).
- Known label quirks are recorded in `notes` (e.g., citation-key labels `yang2022sensefi` /
  `song2018mat` whose bib year fields say 2023 / 2017); the bibliography's year FIELD is treated
  as the local assertion.

## Paper claims vs. our interpretation (hard separation)

- `paper_contribution_summary` paraphrases what the LOCAL framing/citation context says the paper
  reports. It never contains our results.
- `relevance_to_current_results` is OUR Research-OS interpretation, prefixed "OUR
  INTERPRETATION:", with `interpretation_status: local_interpretation`. It is never presented as
  a claim the paper makes.
- `paper_limitations_summary` stays `null` unless a limitation is locally documented — it is
  never invented.
- `claim_boundaries` list what must NOT be inferred from each paper (e.g., image-domain defenses
  do not automatically transfer to CSI; a paper's benchmark result is not our experiment result;
  no paper establishes clinical fall-risk prediction for our system).

## Candidate-direction mappings

- `candidate_direction_tags` entries carry an explicit relationship strength:
  `direct` / `indirect` / `background` / `not_established`. A paper is never marked as supporting
  a direction merely because the direction sounds related.

## Literature gaps

- `literature_gaps` records directions that currently lack a locally cited supporting paper (or
  whose anchors are in the wrong modality). A gap is first-class information; it is closed by
  finding and citing a real publication, never by fabricating a record.

## No clinical overclaiming

- `registry_scope.clinical_claims_allowed: false`. No record may assert clinical validation,
  clinical efficacy, or deployment readiness — for a cited paper or for our system. The validator
  rejects assertive clinical/deployment claims.

## No full text, no long quotations

- PDFs and copyrighted full text are never copied into the repository: the registry is a
  bibliographic and provenance index, not a document store, and redistributing full text would
  exceed both fair use and the registry's purpose. `full_text_status: not_stored_locally`.
- Long verbatim quotations are not stored: summaries must be short paraphrases so the registry
  never becomes an unlicensed extract collection (the validator enforces a length ceiling).
- No PDF is required to exist locally for a record to validate.

## Source provenance

- Every paper has at least one `source_records` entry naming the repository alias
  (`research_os` or `thesis_overleaf`), a repository-relative path (never an absolute local
  filesystem path), the source type, and the citation key seen there.

## Future integration boundaries (NOT implemented in D4a-1)

- **D4a-2 external verification:** may add externally verified metadata and flip
  `verification_status` — a separate, approval-gated step.
- **Experiment-candidate integration:** a future experiment-candidate registry may cite
  `paper_id`s as literature support; that layer must consume this registry read-only and must
  respect each mapping's relationship strength and claim boundaries. Nothing in this registry
  recommends or schedules an experiment.

## Validation

- Validator: `scripts/automation/validate_paper_registry.py` (read-only, no network, no PDF
  requirement). Tests: `scripts/automation/test_paper_registry.py`.
- Acceptance contract: `automation/acceptance/paper-registry.yaml`. Task: `REG-PAPERS`
  (approval-gated).
