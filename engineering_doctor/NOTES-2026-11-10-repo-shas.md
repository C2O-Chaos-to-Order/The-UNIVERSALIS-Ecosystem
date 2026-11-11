# Addendum 2026-11-10 — commit fingerprints on run records

This note records a gap found in Engineering Doctor `validate_record()` and
the fix that followed. It does not rewrite earlier run records.

## Before (verified in source)

`engineering_doctor/schema/run_record.v0.1.json` listed `repo_shas` as a
required field, typed only as an object. The Python function
`validate_record()` did not require the field and did not inspect its
contents. `build_record()` copied the supplied map into the record,
including an empty map. The parameter type was `dict[str, str | None]`,
so a null `default_sha` from an UNKNOWN inventory query could be stored.
The string `working-tree` would also have been accepted as a value.

Core unit tests constructed records with `repo_shas={}`. That is valid
only when `inventory` lists no named repositories. It did not prove that
inventoried repositories received complete fingerprints.

## Fix

`validate_record()` now requires `repo_shas` and calls
`validate_repo_shas()`:

- the field must be present and an object
- each value must be a 40-character or 64-character lowercase
  hexadecimal SHA
- null is rejected
- `working-tree` (and `working_tree`) is rejected; a working-tree digest,
  if recorded, must use a separate field such as `working_tree_digests`
- every inventory entry with a `name` must appear in `repo_shas`, or in
  the separate `unresolved_repo_shas` map with a non-empty reason
- an empty `repo_shas` map is rejected when inventory lists named
  repositories that have no unresolved reason

`execute()` no longer writes null into `repo_shas`. When a repository SHA
cannot be resolved, the name is recorded in `unresolved_repo_shas` and
the UNKNOWN inventory result is still retained on the record.

No SHA values were invented for this change.

## Local mutation check (not committed)

On 2026-11-10, the line `errors.extend(validate_repo_shas(record))` was
removed locally and `RepoShaValidationTests` was run on Python 3.14.10.
Result: 6 failed, 2 passed. The passing cases were the missing-field
test (still caught by the required-field list) and the valid-SHA test.
The guard was restored before any commit. Mutation exit status was 1.

## Known gaps that remain

- A well-formed SHA is not checked against a remote. The validator does
  not prove that the commit exists.
- `unresolved_repo_shas` reasons are not judged for truth.
- An empty `repo_shas` map is still accepted when inventory lists no
  named repositories (for example, a skipped or refused inventory).
