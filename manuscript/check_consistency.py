"""Every numeric literal in the sources must correspond to a recorded quantity.

Run before submission. Any change to the text afterwards requires running it again.
"""
import re, csv, sys, pathlib, glob

TOL = 5e-4

def load_ledger(path="tables/manuscript_numbers.csv"):
    with open(path) as fh:
        return {r["quantity"]: float(r["value"]) for r in csv.DictReader(fh)}

SKIP = re.compile(r"\\includegraphics|\\label|\\ref|\\cite|\\begin|\\end|\\input")

def literals(src):
    """Numeric literals in prose. Layout directives and cross-references are skipped."""
    for i, line in enumerate(src.splitlines(), 1):
        if line.lstrip().startswith("%") or SKIP.search(line):
            continue
        for m in re.finditer(r"(?<![\w.\\])\d+\.\d+(?![\w])", line):
            yield i, float(m.group()), m.group(), line.strip()
        # integer percentages are quantities too, and were invisible to the pattern above
        for m in re.finditer(r"(?<![\w.])(\d+)\\%", line):
            yield i, float(m.group(1)), m.group(1), line.strip()

def match(x, values, text):
    """Compare at the precision the literal was written to, not at any precision.

    Matching a three-decimal literal against every ledger value rounded to one decimal
    lets almost anything through; with a few hundred entries that check passes trivially.
    """
    dp = len(text.split(".")[1]) if "." in text else 0
    for v in values:
        for w in (v, abs(v)):
            if abs(x - round(w, dp)) <= 10 ** (-dp) / 2 + 1e-12:
                return True
    return False

def check_numbers(paths, ledger):
    values = list(ledger.values()); bad = []
    for p in paths:
        for line_no, x, text, ctx in literals(pathlib.Path(p).read_text()):
            if not match(x, values, text):
                bad.append((p, line_no, x, ctx[:70]))
    return bad

def check_coincidence(paths, ledger, tol=5e-4):
    """A literal that matches only one ledger entry, and one from an unrelated part of the
    analysis, is probably a coincidence rather than a citation. Reported for review: the
    check cannot know which entry the author meant, only that there is exactly one and it
    may be the wrong one."""
    out = []
    for p in paths:
        for line_no, x, text, ctx in literals(pathlib.Path(p).read_text()):
            hits = [k for k, v in ledger.items()
                    if abs(x - v) <= tol or abs(x - round(v, 3)) <= tol]
            if len(hits) == 1:
                out.append((p, line_no, x, hits[0], ctx[:52]))
    return out

def check_duplicates(ledger, tol=1e-4):
    items = sorted(ledger.items(), key=lambda kv: kv[1]); out = []
    for (k1, v1), (k2, v2) in zip(items, items[1:]):
        if abs(v1 - v2) <= tol and k1 != k2:
            out.append((k1, v1, k2, v2))
    return out

def check_empty_cells(pattern="tables/*.tex"):
    out = []
    for p in glob.glob(pattern):
        for i, line in enumerate(pathlib.Path(p).read_text().splitlines(), 1):
            if not line.rstrip().endswith(r"\\"):
                continue
            # a dash is a deliberate "not applicable"; an empty field is not
            if re.search(r"&\s*&", line) or line.rstrip().endswith(r"& \\"):
                out.append((p, i, line.strip()[:70]))
    return out

def check_latex(pattern="tables/*.tex"):
    """Unescaped specials and column-count mismatches."""
    out = []
    for p in glob.glob(pattern):
        src = pathlib.Path(p).read_text()
        m = re.search(r"\\begin\{tabular\}\{([^}]*)\}", src)
        if m:
            ncol = len(re.sub(r"[^lcrp]", "", m.group(1)))
            for i, line in enumerate(src.splitlines(), 1):
                if line.rstrip().endswith(r"\\") and "&" in line:
                    if line.count("&") + 1 != ncol:
                        out.append((p, i, f"{line.count('&')+1} fields, {ncol} columns"))
        for i, line in enumerate(src.splitlines(), 1):
            if r"\detokenize{\detokenize" in line:
                out.append((p, i, "nested \\detokenize"))
            if line.lstrip().startswith(("\\label", "\\input", "\\caption")):
                continue
            body = re.sub(r"\\detokenize\{[^}]*\}", "", line)
            body = re.sub(r"\\ref\{[^}]*\}", "", body)      # labels carry underscores
            body = re.sub(r"\\[a-zA-Z]+", "", body)
            for ch in "_#":
                if re.search(r"(?<!\\)" + re.escape(ch), body):
                    out.append((p, i, f"unescaped {ch}")); break
    return out

# Commands the ACS class does not define. A stray one aborts the title block and
# silently produces a document with no title, authors or abstract, which the numeric
# checks below cannot see.
UNDEFINED = ["orcid", "orcidlink", "authornote", "correspondingauthor"]

def check_preamble(path="main.tex"):
    src = pathlib.Path(path).read_text()
    pre = src.split(r"\begin{document}")[0]
    out = []
    for cmd in UNDEFINED:
        for i, line in enumerate(pre.splitlines(), 1):
            if re.search(r"\\" + cmd + r"\b", line) and not line.lstrip().startswith("%"):
                out.append((path, i, f"\\{cmd} is not defined by achemso"))
    for required in [r"\title", r"\author", r"\affiliation", r"\email"]:
        if required not in pre:
            out.append((path, 0, f"{required} missing from the preamble"))
    return out

COUNTING = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|only|every|all|none|neither|both)\b"
    r"[^.]{0,60}\b(of the|of these|architectures?|regimes?|models?|rankings?)\b")

def check_counting(paths):
    """Verbal quantifiers carry claims that no numeric check can see. BLOCKER-1 of the
    third review round lived here: a sentence said two of three where the table said one."""
    out = []
    for p in paths:
        for i, line in enumerate(pathlib.Path(p).read_text().splitlines(), 1):
            if line.lstrip().startswith("%"):
                continue
            m = COUNTING.search(line)
            if m:
                out.append((p, i, m.group()[:56]))
    return out

def check_unreported(paths, ledger, prefixes=("auroc", "spec", "patt", "untrboth", "trenc",
                                              "resem", "icc", "n_eff", "tiefrac", "base500")):
    """Quantities computed and recorded but never quoted anywhere.

    The mirror of check_numbers. That check asks whether every number in the prose has a
    source; this one asks whether every recorded source reached the reader. An analysis can
    be run, come out favourably, and sit in the ledger unreported while every other check
    passes.

    Scope differs from check_numbers deliberately: table cells count as reporting, so the
    generated fragments are searched too. Signs live outside the literal in LaTeX, so
    magnitudes are compared."""
    body = " ".join(pathlib.Path(p).read_text() for p in paths)
    lits = {m.group() for m in re.finditer(r"\d+\.\d+", body)}
    out = []
    for k, v in ledger.items():
        if not any(k.startswith(p) for p in prefixes):
            continue
        hit = any(abs(float(t) - round(abs(v), len(t.split(".")[1]))) <= 5e-4 for t in lits)
        if not hit:
            out.append((k, v))
    return out

def check_placeholders(paths):
    out = []
    for p in paths:
        for i, line in enumerate(pathlib.Path(p).read_text().splitlines(), 1):
            for m in re.finditer(r"\[(?:repository URL|Zenodo DOI|corresponding author e-mail|ORCID)\]", line):
                out.append((p, i, m.group()))
    return out

# ---------------------------------------------------------------------------
# Three guards added after a review found each failure already present in the
# sources. Each one is cheap and catches a class the checks above cannot see.
# ---------------------------------------------------------------------------

def _inputs(doc):
    """Table fragments a document pulls in, with the label each one defines."""
    src = pathlib.Path(doc).read_text()
    out = {}
    for name in re.findall(r"\\input\{tables/([^}]*)\}", src):
        frag = pathlib.Path(f"tables/{name}.tex")
        if not frag.exists():
            continue
        m = re.search(r"\\label\{(tab:[^}]*)\}", frag.read_text())
        if m:
            out[name] = m.group(1)
    return out


def check_cross_document_refs(main="main.tex", si="supporting.tex"):
    """A \\ref in the Supporting Information to a label the manuscript defines.

    The two documents compile separately, so such a reference prints `??` in
    the released PDF while every numeric check passes. The labels usually
    arrive through a shared table fragment rather than from the body text, so
    the fragments a document inputs are searched with it."""
    def labels(doc):
        src = pathlib.Path(doc).read_text()
        for name in re.findall(r"\\input\{tables/([^}]*)\}", src):
            frag = pathlib.Path(f"tables/{name}.tex")
            if frag.exists():
                src += frag.read_text()
        return src

    main_src, si_src = labels(main), labels(si)
    defined_main = set(re.findall(r"\\label\{([^}]*)\}", main_src))
    defined_si = set(re.findall(r"\\label\{([^}]*)\}", si_src))
    out = []
    for doc, src, own, other in ((si, si_src, defined_si, defined_main),
                                 (main, main_src, defined_main, defined_si)):
        for lbl in set(re.findall(r"\\ref\{([^}]*)\}", src)):
            if lbl not in own:
                where = "defined only in the other document" if lbl in other else "undefined"
                out.append((doc, lbl, where))
    return out


def check_orphan_floats(docs=("main.tex", "supporting.tex")):
    """A table or figure that is typeset but never referred to in its own text."""
    out = []
    for doc in docs:
        src = pathlib.Path(doc).read_text()
        refs = set(re.findall(r"\\ref\{([^}]*)\}", src))
        for name, lbl in _inputs(doc).items():
            if lbl not in refs:
                out.append((doc, f"tables/{name}.tex", lbl))
        for lbl in re.findall(r"\\label\{(fig:[^}]*)\}", src):
            if lbl not in refs:
                out.append((doc, doc, lbl))
    return out

if __name__ == "__main__":
    ledger = load_ledger()
    paths = ["main.tex", "supporting.tex"]   # table cells come from the pipeline
    problems = 0
    bad = check_numbers(paths, ledger)
    print(f"[numbers]  {len(bad)} literal(s) without a recorded quantity")
    for p, i, x, ctx in bad: print(f"    {p}:{i}  {x}   {ctx}")
    problems += len(bad)
    dup = check_duplicates(ledger)
    print(f"[ledger]   {len(dup)} key pair(s) within 1e-3 — review, not necessarily an error")
    for a, va, b, vb in dup: print(f"    {a}={va:.4f}  ~  {b}={vb:.4f}")
    empty = check_empty_cells()
    print(f"[cells]    {len(empty)} empty cell(s)")
    for p, i, l in empty: print(f"    {p}:{i}  {l}")
    problems += len(empty)
    tex = check_latex()
    print(f"[latex]    {len(tex)} formatting problem(s)")
    for p, i, msg in tex: print(f"    {p}:{i}  {msg}")
    problems += len(tex)
    pre = check_preamble()
    print(f"[preamble] {len(pre)} problem(s) in the title block")
    for p, i, msg in pre: print(f"    {p}:{i}  {msg}")
    problems += len(pre)
    unrep = check_unreported(paths + sorted(glob.glob("tables/*.tex")), ledger)
    print(f"[unreported] {len(unrep)} recorded quantity(ies) never quoted — check each is "
          f"deliberate")
    for k, v in unrep[:25]: print(f"    {k} = {v:.4f}")
    cnt = check_counting(paths)
    print(f"[counting] {len(cnt)} verbal quantifier(s) — verify each against its table by hand")
    for p, i, txt in cnt: print(f"    {p}:{i}  {txt}")
    coin = check_coincidence(paths, ledger)
    print(f"[single]   {len(coin)} literal(s) matching exactly one ledger entry — check the "
          f"entry is the right one")
    for p, i, x, k, ctx in coin[:20]: print(f"    {p}:{i}  {x} -> {k}   {ctx}")
    ph = check_placeholders(paths)
    print(f"[fill-in]  {len(ph)} placeholder(s) still to complete")
    for p, i, msg in ph: print(f"    {p}:{i}  {msg}")
    xref = check_cross_document_refs()
    print(f"[xref]     {len(xref)} cross-document or undefined reference(s)")
    for doc, lbl, why in xref: print(f"    {doc}  \\ref{{{lbl}}}  {why}")
    problems += len(xref)
    orph = check_orphan_floats()
    print(f"[orphan]   {len(orph)} float(s) typeset but never referred to")
    for doc, where, lbl in orph: print(f"    {doc}  {where}  {lbl}")
    problems += len(orph)
    print(f"\n{'PASS' if problems == 0 else str(problems) + ' problem(s)'}")
    sys.exit(1 if problems else 0)
