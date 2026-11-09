# Source provenance

This document is the provenance contract for sources cited by a programme package. It is
corpus-agnostic. It contains no clause text, no transcription, and no distinctive wording
from any private manuscript corpus. Clause references elsewhere in this repository are
identifiers only. See [tools/CORPUS.md](tools/CORPUS.md).

A source register entry in `sources/source_register.json` follows
[`schemas/source_register_entry.schema.json`](schemas/source_register_entry.schema.json).
Two of its fields exist only to keep provenance honest: `source_role` and
`independence_from`.

## Three source roles are kept strictly separate

A manuscript is normally encountered through more than one kind of source. These are
distinct and are never cited as though they were each other:

1. **Catalogue transcription** (`catalogue_transcription`). The holding institution's or a
   digital library's catalogue record and its description. It is a description *of* the
   object written by someone else. It is not the object, not a reading of the object, and
   not an edition. Its dates, folio ranges, titles, and attributions are that catalogue's
   claims and are recorded as such.
2. **Manuscript-image transcription** (`manuscript_image_transcription`). Our own reading
   made directly from images of the object. This is primary work on the witness. It is
   independent of any catalogue and of any printed edition only to the extent that the
   reader did not consult them while transcribing; when a reader did consult an edition,
   that dependence is recorded in `independence_from`.
3. **Critical edition** (`critical_edition`). A third party's edited text with its own
   apparatus, its own witness selection, and its own editorial decisions. It is a scholarly
   product, not a facsimile. Agreeing with it is not independent confirmation, and a
   difference from it is not automatically an error in either direction.

Two further roles are available where they apply: `edition_page_image` for images of a
printed edition's own pages, `secondary_study` for scholarship about a witness or edition,
`dataset` and `software` for machine-readable inputs and code, and `other` where none of
these fits.

Keeping the roles apart matters because they fail differently. A catalogue can carry a
wrong folio range. Our own transcription can misread a ligature. An edition can normalise
orthography or adopt a reading its base witness does not carry. Collapsing the three into
one "the manuscript says" statement destroys the ability to tell which of those happened.

## Witness sigla

A witness siglum is an identifier a critical edition assigns to a manuscript it collates,
so that its apparatus can refer to that manuscript in shorthand.

- A siglum is recorded here **only** when the cited edition itself assigns it **and** the
  entry records a locator into that edition for the assignment
  (`witness_siglum_locator`).
- **No siglum is assigned by this repository.** Do not invent one. Do not infer one from a
  manuscript's presence in an edition's list of witnesses, from the order of witnesses, or
  from a secondary description. Being used by an editor is not the same as being given a
  siglum by that editor.
- `witness_siglum` is accepted only on a source whose `source_role` is `critical_edition`,
  because only the edition can assign it. The validator refuses a siglum without a locator,
  a locator without a siglum, and a siglum on any other role.
- A manuscript identified by shelfmark and repository needs no siglum to be cited. The
  shelfmark is the durable identifier.

## Public-release source repository

On `--profile public-release` only, a git-pinned source (one that declares `commit` or
`blob_sha`) must belong to this package's own public repository. The package declares that
repository in `metadata/programme_status.json` as `repository`. The source declares its
repository on the source-register entry. The two names must match.

A source pinned to a different repository is refused unless an owner exception record in
`decisions/` names that source: `authority: owner`, a cited `decided_by` and `citation`,
and the source id in `target_ids`. The validator checks that such a record is cited; it
cannot authenticate the owner or confirm the exception was granted.

This rule is corpus-agnostic. It compares repository names and does not hard-code any
corpus, remote, or repository. The default profile and `--profile internal-candidate` do
not apply it. A package that cites another repository remains representable as an
`INTERNAL_CANDIDATE`; it cannot be reported `release_ready` until the citation is replaced,
the owner excepts that source, or the source is no longer git-pinned.

## Corpus boundary

- No clause text, no transcription, and no distinctive wording from a private corpus
  appears in this file or anywhere in this repository.
- The actual text stays in its separately controlled evidence location, outside this
  repository.
- Traceability uses clause identifiers and non-sensitive metadata: repository, shelfmark,
  folio range, image sequence number, catalogue record URL, edition page range.
- `tools/clause_leak_check.py` reports the longest shared character run between any public
  file and any clause body in a private corpus you point it at, after whitespace
  normalisation. It exits non-zero above a configurable threshold. It never writes into the
  corpus and refuses a corpus path inside this repository.

## Instantiation under examination

Everything below is descriptive metadata about one object. It quotes no clause and
paraphrases none.

- **Object.** British Library, Oriental Manuscripts, **Add MS 7527**.
- **Digitisation.** Digitised by the **Qatar Digital Library** (QDL).
- **Complete-codex PDF.** `QDL_Add_MS_7527_Complete_Codex.pdf`.

### Image counts, with their scopes, kept apart

Two counts describe this material and they have **different scopes**. They are not
interchangeable and must never be merged into a single number:

| Count | What it counts | Source of the count |
| --- | --- | --- |
| **384 images** | The **full bound volume** titled "Three treatises on natural philosophy and medicine", as described by its IIIF manifest. | IIIF manifest of the bound volume |
| **320 items, ff. 2v–170r** | The **Add MS 7527 item-level record only**, which is nested inside that larger volume. | QDL item-level catalogue record |

Reading the 384 as the item's length, or the 320 as the volume's length, is an error of
scope. A statement about the volume and a statement about the item are different
statements.

### The three sources for this object, registered separately

| Role | What it is | Independence |
| --- | --- | --- |
| `catalogue_transcription` | The QDL catalogue description of Add MS 7527. | Independent of our own reading. It is not a transcription of the text. |
| `manuscript_image_transcription` | Our own transcription made from the digitised manuscript images. | Independent of the catalogue and of the edition **only** insofar as the transcriber did not consult them. Record any consultation in `independence_from`. |
| `critical_edition` | Weisser's 1979 critical edition. | A third-party edited text. Our transcription is not independent confirmation of it, and it is not independent confirmation of our transcription. |

No `witness_siglum` is recorded for Add MS 7527 in this repository. Whether Weisser's 1979
edition assigns one, and on which page, has not been established here from the edition
itself. That is an open obligation, not an assumption to be filled in later without
documentary evidence.

## Limits

- This document does not transcribe, translate, or characterise the content of any
  manuscript. It records how sources are labelled and kept apart.
- Recording a source, a shelfmark, or an image count is not a research finding, not a
  collation, and not evidence that any reading is correct.
- The presence of a role and a locator does not mean anyone checked the underlying object.
  It means the citation names which kind of source it is, so a later reader can check it.
