# Overleaf project

Upload with **New Project -> Upload Project**, then compile `main.tex`.

- `main.tex` — manuscript, ACS `achemso` class with `journal=jcisd8` (J. Chem. Inf. Model.)
- `supporting.tex` — Supporting Information, compiled separately
- `references.bib` — 61 entries, all cited, all resolving
- `figures/` — 14 figure PDFs: 6 in the manuscript, 7 in the Supporting Information, and the
  table-of-contents graphic
- `tables/` — 38 LaTeX fragments, 7 used by the manuscript and 31 by the Supporting
  Information, plus `manuscript_numbers.csv`, the record of every quantity quoted in the text
- `check_consistency.py` — pre-submission checks

The figures and tables are generated from the stored results rather than edited by hand.
The renderer that writes the LaTeX fragments is not part of the released pipeline; the
pipeline produces the results the fragments are built from.

## Before submitting

Run `python3 check_consistency.py`. It reports:

- numeric literals in the prose with no matching entry in `tables/manuscript_numbers.csv`
- ledger keys within 1e-4 of each other, for review
- empty table cells
- unescaped LaTeX specials, column-count mismatches and nested `\detokenize`
- commands in the preamble that `achemso` does not define
- placeholders still to be filled
- references in one document to a label the other document defines
- tables and figures that are typeset but never referred to in their own text

The preamble check matters more than it looks. A stray undefined command there aborts the
title block, and the resulting PDF has no title, authors or abstract while every numeric check
still passes. After the script, compile and look at page one.

The last two checks exist because both failures were present in the sources and no other check
could see them. `main.tex` and `supporting.tex` compile separately, so a `\ref` across them
prints `??` in the released PDF while every numeric check passes; the labels usually arrive
through a shared fragment in `tables/`, not from the body text, so the fragments a document
inputs are searched with it.
