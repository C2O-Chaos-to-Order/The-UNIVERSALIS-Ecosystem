# Private corpus probe

`corpus_probe.py` reads a local directory of tablet markdown files and emits an index. The corpus is private C2O source. It is expected to live outside this repository. This public repository stores clause identifiers only. It does not store clause text, and this tool does not embed any.

## What the probe is for

A programme package may cite a clause by identifier, for example an identifier you assign when you register the clause. The probe helps an operator, on a machine that already has the private corpus, list tablet number, clause number, clause title, character count, and SHA-256 for each clause, plus one corpus-level digest. That index is an inventory of the files it was shown. It is not a research finding, a requirement, or permission to copy the corpus into this repository.

Do not commit probe output to this repository unless the titles in it have been cleared for public release. Titles are read from the private files and are printed in the index. The digest is a SHA-256; it is not a copy of the clause text, and it is also not evidence that anyone reviewed the clauses.

## Expected layout

The probe reads `*.md` files in the directory you pass. It does not walk subdirectories and it does not follow symlinks.

Each file name is:

```text
tablet-<number>-technical.md
tablet-<number>-human.md
```

`<number>` is an integer. The file begins with a heading `# Tablet <number>` and the same integer. Each clause is a second-level heading in one of these shapes:

```text
## Clause 1: Title
## Clause 1 — Title
## 1. Title
```

The clause title is the heading text after the separator. The body is the text between that heading and the next clause heading. Character count is the number of Unicode characters in that body after newlines are normalized to `\n` and one leading or trailing newline is removed. SHA-256 is the digest of that UTF-8 body. The corpus digest is the SHA-256 of a canonical JSON line per clause, in tablet, side, and clause order. The line includes the title, so a title change changes the digest. The digest is not reversible.

This layout is a reading convention for the probe. It is not a copy of the private corpus and it does not define tablet content.

## How to run it

```bash
python scaffold/tools/corpus_probe.py /path/outside/this/repo/private-corpus
python scaffold/tools/corpus_probe.py /path/outside/this/repo/private-corpus --output /tmp/corpus-index.json
```

Stdout is the default destination. `--output` must be outside the corpus directory. The probe exits with a non-zero status and an explicit message when the directory is absent:

```text
CORPUS_ABSENT: corpus directory does not exist: ...
```

It exits non-zero, and writes nothing, when the output path is inside the corpus (`CORPUS_WRITE_REFUSED`). A format problem is `CORPUS_FORMAT`. An empty directory is `CORPUS_EMPTY`.

## What it will not do

- It will not create the corpus directory.
- It will not write, rename, or delete anything inside the corpus directory.
- It will not decide that a clause identifier in a programme package matches a private file. That comparison, if you need it, stays on the machine where the corpus is authorized to be read.
- It will not accept, review, or authorize anything. Evidence states for those steps live in `evidence_states.py` and require a cited decision record.
