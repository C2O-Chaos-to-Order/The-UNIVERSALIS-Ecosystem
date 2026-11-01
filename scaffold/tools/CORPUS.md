# Private corpus probe

`corpus_probe.py` reads a local paired tablet collection and emits an index. The corpus is
private C2O source. It is expected to live outside this repository. This public repository
stores clause identifiers only. It does not store clause text, and this tool does not embed
any.

## What the probe is for

A programme package may cite a clause by identifier, for example an identifier you assign
when you register the clause. The probe helps an operator, on a machine that already has the
private corpus, list tablet number, side, clause number, clause title, character count, and
SHA-256 for each clause, plus one corpus-level digest and a pair-by-pair reconciliation. That
index is an inventory of the files it was shown. It is not a research finding, a
requirement, or permission to copy the corpus into this repository.

The index carries no clause bodies. Clauses are indexed by number, title, length and digest,
so an index file can be reviewed without opening the text.

Do not commit probe output to this repository unless the titles in it have been cleared for
public release. Titles are read from the private files and are printed in the index. The
digest is a SHA-256; it is not a copy of the clause text, and it is also not evidence that
anyone reviewed the clauses.

## Reading convention for this corpus family

This is a reading convention for the paired tablet collection as it is currently written.
It describes the shape of the files, not their content, and it is not a definition of what
a tablet is.

The two sides live in separate directories under a corpus root:

```text
<corpus-root>/
  C2O Tablets/tablets/       technical side
  Human Tablets/tablets/     human side
```

Run it against the root. The tool looks for these in order and does not walk the tree
recursively, so an unrelated directory cannot be picked up by accident.

Each side has its own file-name pattern:

```text
<NN>_<GEMSTONE>_TABLET.md    technical
<NN>_<GEMSTONE>_HUMAN.md     human
```

`<NN>` is a zero-padded tablet number. `<GEMSTONE>` is an upper-case token that may itself
contain underscores, for example a two-word gemstone name. The number in the name is the
tablet number.

Each file starts with a level-1 heading:

```text
# 00 — The <Gemstone> Tablet                    technical
# 00 — The <Gemstone> Tablet — Human Version    human
```

The em dash is U+2014. The human heading may omit the leading number; when it is present it
must agree with the file name. The technical heading must carry it. The human heading must
end with `Human Version`.

The two sides mark clauses differently. All of these are accepted:

```text
### I — <clause title>        technical side, and the human side where it uses level-3
**I — <clause title>.**      human side, bold style
```

A clause heading is a Roman numeral, an em dash, then the title. The title is free-form: it
may or may not begin with `Of`. Requiring a particular opening word is wrong, because not
every clause title uses one. A level-3 heading whose first token is not a Roman numeral is
front matter, not a clause, and is skipped.

Clause bodies run from the line after a clause heading to the line before the next clause
heading. Character count is the number of Unicode characters in that body after newlines
are normalized to `\n` and one leading or trailing newline is removed. SHA-256 is the digest
of that UTF-8 body.

The corpus digest is the SHA-256 of a canonical JSON line per clause, in tablet, side, and
clause order. The line includes the title, so a title change changes the digest. The digest
is not reversible.

## Pair reconciliation

The probe reconciles the two sides tablet by tablet and reports, per pair, whether both
sides are present and how many clauses each has. It reports a non-zero exit and a problem
line for:

- `UNPAIRED`, when a tablet number has only one side.
- `GEMSTONE_MISMATCH`, when the two sides name different gemstones for one number.
- `CLAUSE_MISMATCH`, when the two sides do not have the same clause numbers, listing the
  numbers that differ.
- `DUPLICATE_CLAUSE`, when a side repeats a clause number.

A clean run reports zero problems. Zero problems means the two sides agree on structure. It
does not mean the two sides agree in meaning, and it is not a research finding.

## How to run it

```bash
python scaffold/tools/corpus_probe.py /path/outside/this/repo/private-corpus
python scaffold/tools/corpus_probe.py /path/outside/this/repo/private-corpus --output /tmp/corpus-index.json
python scaffold/tools/corpus_probe.py --technical /path/to/technical --human /path/to/human
```

Stdout is the default destination. `--output` must be outside the corpus directory. The
probe exits with a non-zero status and an explicit message when the directory is absent:

```text
CORPUS_ABSENT: corpus directory does not exist: ...
```

It exits non-zero, and writes nothing, when the output path is inside the corpus
(`CORPUS_WRITE_REFUSED`). A layout problem is `CORPUS_FORMAT`. An empty collection is
`CORPUS_EMPTY`. A symlinked file or directory is refused (`CORPUS_SYMLINK_REFUSED`).

## What it will not do

- It will not create the corpus directory.
- It will not write, rename, or delete anything inside the corpus directory.
- It will not walk subdirectories.
- It will not decide that a clause identifier in a programme package matches a private
  file. That comparison, if you need it, stays on the machine where the corpus is
  authorized to be read.
- It will not accept, review, or authorize anything. Evidence states for those steps live in
  `evidence_states.py` and require a cited decision record.

## Leak check

`clause_leak_check.py` measures how much character-level text a public file shares with the
private corpus. Run it on a machine that already has the corpus, before publishing a change
that touched prose:

```bash
python scaffold/tools/clause_leak_check.py /path/outside/this/repo/private-corpus scaffold/
python scaffold/tools/clause_leak_check.py /path/outside/this/repo/private-corpus scaffold/ --threshold 30
```

It normalises whitespace on both sides and compares every public file against two disjoint
sets of targets:

- **clause bodies**, parsed with the same reader the probe uses, so the two tools cannot
  disagree about where a clause begins;
- **outside-clause-body text**, meaning each file's preamble, clause heading lines, and
  anything between or after clauses.

The two sets are complements of each other, so one copied passage is reported exactly once.
Reporting it once against the clause body and again against the whole file would inflate a
single overlap into two findings at the same length, which is why the split is by
complement rather than by comparing whole files as well as clauses. Text that sits outside
every clause body is still caught, on the outside-clause-body axis.

It reports the longest shared character run and exits non-zero when any pair exceeds the
threshold (default 40 characters). `--threshold` changes the limit and `--list` prints every
pair over it. Each finding names which axis it came from.

A shared run is a signal to look, not a verdict. A short shared run is normal in any
language and the default threshold sits well above that noise floor. The tool does not
classify a match as a quotation, a paraphrase, or a coincidence; it reports the extent and
the pair so a person can decide.

The tool refuses a corpus path inside this repository (`CORPUS_INSIDE_REPOSITORY`), exits
`2` for it and for an absent corpus (`CORPUS_ABSENT`), and never writes into the corpus.

Its tests use synthetic placeholder bodies in a temporary directory. No real clause text is
stored in this repository, including in the tests.

## The opt-in test against a real corpus

`tests/test_corpus_probe.py` includes one integration test that parses a real corpus and
asserts thirteen clauses per file across all pairs. It names no directory: it reads the
environment variable `C2O_CORPUS_ROOT` and skips with a message when that is unset or does
not contain both tablet sets. So the suite passes on a machine with no corpus, passes on a
machine that has one, and never depends on a path that happens to exist on one workstation.

```
C2O_CORPUS_ROOT=/path/to/research-checkout python3 -m unittest discover -s tests
```

Nothing in this repository records where that checkout lives. Keep the path in your shell,
not in a file that would be published.
