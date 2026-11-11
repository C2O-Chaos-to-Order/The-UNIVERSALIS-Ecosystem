# Research and evidence scaffold

This directory is a corpus-agnostic package layout, validator, and empty programme template. It is for recording research assessments, simulation executions, requirements, and the limits of those records. It does not contain tablet text. It does not produce research findings, scientific validation, security certification, or production readiness by being present.

The private C2O corpus stays outside this repository. Clause references in a package are identifiers only. See [tools/CORPUS.md](tools/CORPUS.md). Source roles and sigla are governed by [SOURCE_PROVENANCE.md](SOURCE_PROVENANCE.md).

Evidence-record fields follow the governing Plan. The mapping is in [PLAN_SCHEMA_CONFORMANCE.md](PLAN_SCHEMA_CONFORMANCE.md). The package contract is in [SPECIFICATION.md](SPECIFICATION.md).

## Workflow from clause to report

1. Identify a clause by identifier only. If you index a private corpus, run `corpus_probe.py` on a directory outside this repository and do not commit clause text or uncleared titles.
2. Register sources in `sources/source_register.json` with a `review_scope`. When the source is a git object, declare `repository`, a repository-relative `path`, `commit`, and `blob_sha` together.
3. Copy `research/_TEMPLATE_research_card.md` to `research/<record_id>.md` and add one object to `research/research_records.json`. The assessment is the research activity. It is not the simulation.
4. Author the case in `simulations/scenarios.json`, including `input`, `expected`, `protocol_version`, and `configuration`, before you run it.
5. Run one case in its own subprocess:

   ```bash
   python simulations/run_one.py --case SIM-001 --output results/SIM-001.json
   ```

   `run_all.py` does that for every case and writes an execution log. The runner records `execution_outcome`
   as `executed` or `failed` and sets `evidence_status` to `documented`, because what it produced is a
   documented record of a run. It always sets `authorization_status` to `NOT_AUTHORIZED`. It never awards
   programme credit.
6. Update the ledgers and `metadata/programme_status.json` so the counts match the records. Leave acceptance, review, and authorization at their unset values unless a decision file cites them.
7. Add each new file to `metadata/classifications.json` as `PUBLICLY_CLEARED` only when it is public material. Then refresh hashes:

   ```bash
   python scaffold/tools/package_files.py --manifest path/to/programme
   ```

   That command refuses to invent a classification. It is not a clearance review.
8. Validate:

   ```bash
   python scaffold/tools/validate_programme.py path/to/programme
   ```
9. Write a report from `reports/_TEMPLATE_report.md`. The ten sections are task and scope, source of truth, method, evidence, findings, execution status, build status, risk and governance, repository disposition, and next action. A report file does not create programme credit.
10. `verified`, `independently_reproduced`, `validated` and `authorized` evidence states, and
    `authorization_status` of `AUTHORIZED`, require a JSON decision in `decisions/` that cites the owner or
    reviewer. Whether something is authorized is tracked in its own column, which no
    evidence state ever assigns; `evidence_status: authorized` does not imply `authorization_status: AUTHORIZED`.

Requirement ids are `ULC-<tablet>-<clause>`. One requirement belongs to one research card and must name a declared clause identifier. `ULC-00-01` in the requirement template is an example placeholder. It is not the separate collection-level register `UNI-001`…`UNI-015`.

## Validation profiles

The validator supports three distinct modes:

```bash
python scaffold/tools/validate_programme.py PATH/TO/PACKAGE
python scaffold/tools/validate_programme.py PATH/TO/PACKAGE --profile internal-candidate
python scaffold/tools/validate_programme.py PATH/TO/PACKAGE --profile public-release
```

- Default (no profile): historical `PUBLICLY_CLEARED`-only consistency gate; `release_ready` is always false.
- `internal-candidate`: admits `INTERNAL_CANDIDATE` and `PUBLICLY_CLEARED`; `release_ready` is always false. This profile is for uncleared work in a private repository or private workspace.
- `public-release`: requires every file and record to be `PUBLICLY_CLEARED`, a cited owner decision with `authority: owner`, `authorization_status: AUTHORIZED`, and the programme ID in `target_ids`, and that every source with Git locator fields has a complete D09 locator to this package's declared repository or a source-specific, authorized owner exception. A reviewer decision or a classification label alone cannot authorize release.

The validator checks that an owner authorization is cited; it cannot authenticate the owner or prove that the decision was genuinely made. No profile establishes scientific validation, programme acceptance, or production readiness.

## Create an empty package

```bash
python scaffold/tools/new_programme.py \
  --target ./example-programme \
  --programme-id EXAMPLE-PROGRAMME \
  --edition 0.0.0
python scaffold/tools/validate_programme.py ./example-programme
```

The new package has empty ledgers, zero counts, `evidence_status` `proposed`, `execution_outcome` `not_executed`, and `authorization_status` `NOT_AUTHORIZED`. The tool writes a placeholder manifest and then replaces it with SHA-256 locks. Creating the package is not validation of a finding, and a later passing validation is not acceptance.

## Run the tests

```bash
python -m unittest discover -s scaffold/tests -v
```

The tests use the Python standard library only. Negative fixtures must fail, and each failure names the check that caught it.

## Limits

- The scaffold measures whether a package keeps its records, hashes, counts, and claims consistent. It does not decide that a claim is true.
- A result file is evidence of a recorded run only to the extent its fields say so. The validator does not re-execute cases.
- `CANDIDATE_PENDING_OWNER_REVIEW` is not programme credit. `AWARDED` without a decision record fails validation.
- `evidence_status`, `execution_outcome` and `authorization_status` are three different fields. The default
  authorization value is `NOT_AUTHORIZED`. An execution outcome is never an evidence state, and tooling
  cannot infer authorization from the evidence ladder.
- Passing validation is not owner acceptance, independent review, scientific validation, security certification, production readiness, or release authorization.
- This repository is public. Do not place private corpus text, credentials, or internal-candidate packages here. The default and public-release profiles require `PUBLICLY_CLEARED`; the internal-candidate profile is only for private workspaces and is refused for packages located inside this public repository. The validator checks declared labels, not the words inside a file.
- No third-party packages are required. Do not add a dependency for this scaffold.
