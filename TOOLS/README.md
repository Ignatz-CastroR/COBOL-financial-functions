# TOOLS/

Project automation, not project deliverable. Nothing here is a financial
function; everything here exists to keep the actual functions honest.

## compile-check.py

Walks `SRC/`, parses each file's `FUNCTION-ID` declarations and its
`REPOSITORY` paragraph, builds the resulting call graph, topologically
sorts it, and compiles every file with GnuCOBOL in dependency order:
leaves first, so that a failure is reported once, at its true source,
rather than as a wall of downstream errors from every function that
happens to depend on the broken one.

```
python3 TOOLS/compile_check.py
```

Exits 0 if everything compiles, 1 otherwise. This is exactly what the
continuous integration workflow in `.github/workflows/build.yml` runs
on every push.

## generate-callgraph.py

Uses the same parsing approach to emit the project's call graph as
Graphviz DOT files under `DOCS/DIAGRAMS/`: one master graph, and one
focused subgraph per `SRC/` domain folder. If Graphviz's `dot` command
is installed, it also renders each `.dot` file to `.svg`, which is what
the root and domain READMEs embed.

```
python3 TOOLS/generate_callgraph.py
```

Because these diagrams are generated directly from the same
`REPOSITORY` declarations the compiler itself enforces, they cannot
drift out of sync with the actual code the way a hand-drawn diagram
eventually does.

## A note on the deliberate duplication between these two scripts

Both scripts parse COBOL source the same way, and that logic is
currently written twice rather than shared. That is a conscious,
temporary choice: with exactly two consumers, the parsing logic's fan-in
is two, and this project's own convention, stated in the root README,
is that a function [or in this case, a small chunk of parsing logic]
gets promoted to a shared module only once a second caller actually
exists. That threshold has technically been reached with these two
scripts; extracting a `TOOLS/cobol_parser.py` module both scripts import
from is the natural next refactor, left undone here so both files stay
independently readable for now.
