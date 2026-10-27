#!/usr/bin/env python3
"""Validate a generated project skeleton against the spec-skeleton contract.

Checks (all languages):
  * BUILD_ORDER.md and TRACEABILITY.md exist.
  * Every source file has a file-level doc block with the required labels.
  * Every function/method has a doc block with What/Why/Spec/Build steps/
    Task/Expected outcome; every test has Spec + Expected outcome.
  * Function bodies are stubs only (no implementation logic).
  * Spec IDs cited in code and IDs listed in TRACEABILITY.md match both ways.
  * "Build order: Step N of M" is consistent and exactly one file declares
    itself the start of the project.
Python only:
  * No `from __future__` imports.
  * Every module under src/ imports cleanly in a fresh interpreter
    (catches circular imports and missing project symbols).

Usage:
  check_skeleton.py ROOT --lang {python,typescript,go,rust,generic}
                    [--python /path/to/python3.14] [--no-import-check]

Exit code 0 = no errors (warnings allowed), 1 = errors found.
"""

import argparse
import ast
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "dist", "build", "target",
    "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", "vendor",
}
FILE_LABELS = ["Problem:", "Piece of the problem:", "Why this comes now:",
               "Build order:", "Previous:", "Next:", "Build these in order:",
               "Depends on:", "Depended on by:", "Spec coverage:"]
FUNC_LABELS = ["Problem piece:", "Why it matters:", "What:", "Spec:",
               "Ticket:", "Traces to:", "Build steps", "Task:",
               "Expected outcome:"]
CLASS_LABELS = ["Problem piece:", "Why it matters:", "What:", "Spec:"]
MARKERS = {"__init__.py", "mod.rs", "lib.rs", "index.ts"}  # Go doc.go IS the package header
CAP_RE = re.compile(r"\bC\d+\b")
TEST_LABELS = ["Spec:", "Expected outcome:"]
START_RE = re.compile(r"start of the project", re.I)
STEP_RE = re.compile(r"Build order:\s*Step\s+(\d+)\s+of\s+(\d+)", re.I)
SPEC_LINE_RE = re.compile(r"Spec:\s*([^|\n]+)")
NO_ID = {"—", "-", "–", "none", "n/a", ""}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    cited_ids: set[str] = field(default_factory=set)
    steps: dict[str, tuple[int, int]] = field(default_factory=dict)
    nexts: dict[str, str] = field(default_factory=dict)
    caps_cited: dict[str, set[str]] = field(default_factory=dict)
    starts: list[str] = field(default_factory=list)
    n_files: int = 0
    n_funcs: int = 0

    def err(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


def iter_files(root: Path, exts: tuple[str, ...]) -> list[Path]:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS
                       and not d.startswith(".")]
        for f in filenames:
            if not f.endswith(exts) or f.endswith(".d.ts"):
                continue
            if Path(dirpath) == root and re.search(r"\.config\.\w+$", f):
                continue  # tool config (vitest/eslint/etc.), not part of the module graph
            out.append(Path(dirpath) / f)
    return sorted(out)


def missing(text: str, labels: list[str]) -> list[str]:
    return [lab for lab in labels if lab not in text]


def collect_ids(text: str, rep: Report) -> list[str]:
    ids = []
    for m in SPEC_LINE_RE.finditer(text):
        for raw in re.split(r"[,;]", m.group(1)):
            tok = raw.strip().strip("`").strip()
            if tok.lower() not in NO_ID:
                ids.append(tok)
    rep.cited_ids.update(ids)
    return ids


def check_file_header(rel: str, doc: str | None, rep: Report,
                      is_test: bool) -> None:
    rep.n_files += 1
    if not doc or not doc.strip():
        rep.err(rel, "missing file-level docstring/doc comment")
        return
    if is_test:
        return
    miss = missing(doc, FILE_LABELS)
    if miss:
        rep.err(rel, f"file docstring missing labels {miss}")
    m = STEP_RE.search(doc)
    if m:
        rep.steps[rel] = (int(m.group(1)), int(m.group(2)))
    elif "Build order:" in doc:
        rep.warn(rel, "Build order line not in 'Step N of M' form")
    if START_RE.search(doc) and Path(rel).name not in MARKERS:
        rep.starts.append(rel)
    m2 = re.search(r"Next:(.*?)(?:\n\s*\n|$)", doc, re.S)
    if m2:
        rep.nexts[rel] = m2.group(1)
    for lab in ("Piece of the problem:",):
        if lab in doc:
            seg = doc.split(lab, 1)[1].split("\n\n", 1)[0]
            caps = set(CAP_RE.findall(seg))
            if not caps:
                rep.warn(rel, "'Piece of the problem' names no capability ID (C1, C2, ...)")
            rep.caps_cited.setdefault(rel, set()).update(caps)
    if "Spec coverage:" in doc:
        cov = doc.split("Spec coverage:", 1)[1].split("|", 1)[0]
        for raw in re.split(r"[,;\n]", cov):
            tok = raw.strip().strip("`")
            if tok and tok.lower() not in NO_ID:
                rep.cited_ids.add(tok)


def check_func_doc(where: str, doc: str | None, rep: Report, kind: str) -> None:
    rep.n_funcs += 1
    if not doc or not doc.strip():
        rep.err(where, f"{kind} has no docstring")
        return
    labels = {"func": FUNC_LABELS, "class": CLASS_LABELS,
              "test": TEST_LABELS}[kind]
    miss = missing(doc, labels)
    if miss:
        rep.err(where, f"{kind} docstring missing {miss}")
    collect_ids(doc, rep)
    if kind in ("func", "class") and "Problem piece:" in doc:
        seg = doc.split("Problem piece:", 1)[1].split("\n\n", 1)[0]
        caps = set(CAP_RE.findall(seg))
        if not caps:
            rep.warn(where, "'Problem piece' names no capability ID (C1, C2, ...)")
        rep.caps_cited.setdefault(where, set()).update(caps)
    if kind == "func":
        n_steps = len(re.findall(r"^\s*\d+\.\s+Task:", doc, re.M))
        # Depth tiers (docstrings.md §6): only full-depth functions (3+ steps)
        # need a long Why; helpers may be brief.
        if n_steps >= 3 and "Why it matters:" in doc:
            para = doc.split("Why it matters:", 1)[1].split("\n\n", 1)[0]
            if len(para.split()) < 15:
                rep.warn(where, f"'Why it matters:' is thin ({len(para.split())} "
                                f"words) for a full-depth function")
        n_task = doc.count("Task:")
        n_out = doc.count("Expected outcome:")
        if n_task != n_out:
            rep.warn(where, f"{n_task} Task: vs {n_out} Expected outcome: lines")
        steps = doc.split("Build steps", 1)[-1]
        task_text = " ".join(re.findall(r"(?:Task|Think about):(.*?)(?=Think about:|Expected outcome:|$)", steps, re.S))
        for out in re.findall(r"Expected outcome:(.*?)(?=\n\s*\d+\.|$)", steps, re.S):
            if len(out.split()) < 3:
                rep.warn(where, f"Expected outcome too vague to test: {out.strip()!r}")
        if re.search(r"\w+\.\w+\([^)]*\)", task_text):
            rep.warn(where, "build steps look like they contain code calls "
                            "(e.g. foo.bar(...)); describe outcomes instead")


# --------------------------------------------------------------------- Python

def py_is_test(path: Path) -> bool:
    return path.name.startswith("test_") or path.name == "conftest.py" \
        or "tests" in path.parts


def py_stub_ok(body: list[ast.stmt]) -> bool:
    rest = body[1:] if (body and isinstance(body[0], ast.Expr)
                        and isinstance(getattr(body[0], "value", None), ast.Constant)
                        and isinstance(body[0].value.value, str)) else body
    if not rest:
        return True
    if len(rest) != 1:
        return False
    s = rest[0]
    if isinstance(s, ast.Pass):
        return True
    if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) \
            and s.value.value is Ellipsis:
        return True
    if isinstance(s, ast.Raise) and s.exc is not None:
        exc = s.exc.func if isinstance(s.exc, ast.Call) else s.exc
        return isinstance(exc, ast.Name) and exc.id == "NotImplementedError"
    return False


def check_python(root: Path, rep: Report) -> list[Path]:
    files = iter_files(root, (".py",))
    for path in files:
        rel = str(path.relative_to(root))
        src = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src, filename=rel)
        except SyntaxError as e:
            rep.err(rel, f"does not parse under Python "
                         f"{sys.version_info.major}.{sys.version_info.minor}: {e.msg} "
                         f"(line {e.lineno}). If the code targets a newer Python, "
                         f"re-run with --python <newer interpreter>.")
            continue
        is_test = py_is_test(path)
        check_file_header(rel, ast.get_docstring(tree), rep, is_test)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                rep.err(f"{rel}:{node.lineno}", "`from __future__` import is forbidden")
        _walk_py(tree.body, rel, rep, is_test)
    return files


def _walk_py(body: list[ast.stmt], rel: str, rep: Report, is_test: bool,
             in_class: bool = False) -> None:
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            where = f"{rel}:{node.lineno} {node.name}()"
            test_fn = is_test and (node.name.startswith("test")
                                   or not in_class)
            kind = "test" if test_fn else "func"
            if is_test and not node.name.startswith("test"):
                # fixtures/helpers in tests: only need a docstring
                if not ast.get_docstring(node):
                    rep.err(where, "test helper has no docstring")
                continue
            check_func_doc(where, ast.get_docstring(node), rep, kind)
            if kind == "func" and not py_stub_ok(node.body):
                rep.err(where, "body contains implementation; skeleton bodies "
                               "must be docstring + raise NotImplementedError")
            if kind == "func":
                for s in node.body:
                    if isinstance(s, ast.Raise) and isinstance(s.exc, ast.Call) \
                            and not s.exc.args:
                        rep.warn(where, "NotImplementedError has no spec-ID message")
        elif isinstance(node, ast.ClassDef):
            where = f"{rel}:{node.lineno} class {node.name}"
            if is_test:
                if not ast.get_docstring(node):
                    rep.err(where, "test class has no docstring")
            else:
                check_func_doc(where, ast.get_docstring(node), rep, "class")
            _walk_py(node.body, rel, rep, is_test, in_class=True)


def py_import_check(root: Path, files: list[Path], python: str,
                    rep: Report) -> None:
    src = root / "src" if (root / "src").is_dir() else root
    project_tops = {p.name for p in src.iterdir()
                    if (p.is_dir() and (p / "__init__.py").exists())
                    or (p.suffix == ".py")}
    project_tops = {t.removesuffix(".py") for t in project_tops}
    for path in files:
        try:
            rel_to_src = path.relative_to(src)
        except ValueError:
            continue
        if "tests" in rel_to_src.parts or rel_to_src.parts[0] == "tests":
            continue
        parts = list(rel_to_src.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if not parts or parts[-1] == "__main__":
            continue
        mod = ".".join(parts)
        code = ("import importlib, sys; sys.path.insert(0, sys.argv[1]); "
                "importlib.import_module(sys.argv[2])")
        r = subprocess.run([python, "-c", code, str(src), mod],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            last = (r.stderr.strip().splitlines() or ["?"])[-1]
            m = re.search(r"No module named '([^'.]+)", last)
            if m and m.group(1) not in project_tops:
                rep.warn(mod, f"third-party dependency not installed: {last}")
            else:
                rep.err(mod, f"import failed (circular or missing project "
                             f"symbol?): {last}")


# ------------------------------------------------------- brace languages

LANG_CFG = {
    "typescript": dict(
        exts=(".ts", ".tsx", ".mts"),
        func=re.compile(
            r"^[ \t]*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*(\w+)"
            r"|^[ \t]*(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*(?::[^=]+)?=>"
            r"|^[ \t]+(?:public\s+|private\s+|protected\s+|static\s+|async\s+|override\s+)*"
            r"(?!if\b|for\b|while\b|switch\b|catch\b|return\b|constructor\b)(\w+)\s*\([^;{]*\)\s*(?::\s*[^{;]+)?\{",
            re.M),
        cls=re.compile(r"^[ \t]*(?:export\s+)?(?:abstract\s+)?(?:class|interface)\s+(\w+)", re.M),
        stub=re.compile(r"^\s*throw\s+new\s+\w*Error\s*\(", re.S),
        test_file=lambda p: bool(re.search(r"\.(test|spec)\.tsx?$", p.name)),
    ),
    "go": dict(
        exts=(".go",),
        func=re.compile(r"^func\s+(?:\([^)]*\)\s*)?(\w+)", re.M),
        cls=re.compile(r"^type\s+(\w+)\s+(?:struct|interface)", re.M),
        stub=re.compile(r"^\s*panic\s*\(", re.S),
        test_file=lambda p: p.name.endswith("_test.go"),
    ),
    "rust": dict(
        exts=(".rs",),
        func=re.compile(
            r"^[ \t]*(?:pub(?:\([^)]*\))?\s+)?(?:const\s+)?(?:async\s+)?(?:unsafe\s+)?"
            r"(?:extern\s+\"[^\"]*\"\s+)?fn\s+(\w+)", re.M),
        cls=re.compile(r"^[ \t]*(?:pub(?:\([^)]*\))?\s+)?(?:struct|enum|trait)\s+(\w+)", re.M),
        stub=re.compile(r"^\s*(?:todo|unimplemented)!\s*\(", re.S),
        test_file=lambda p: "tests" in p.parts,
    ),
    "generic": dict(
        exts=(".java", ".kt", ".cs", ".swift", ".rb", ".cpp", ".hpp", ".h", ".c",
              ".scala", ".php", ".dart"),
        func=None, cls=None, stub=None, test_file=lambda p: "test" in p.name.lower(),
    ),
}


def leading_comment(lines: list[str], idx: int) -> str:
    """Collect the comment block directly above line idx (skipping attrs)."""
    out: list[str] = []
    i = idx - 1
    while i >= 0 and re.match(r"^\s*(#\[|@\w)", lines[i]):
        i -= 1
    if i >= 0 and lines[i].strip().endswith("*/"):
        while i >= 0:
            out.append(lines[i])
            if lines[i].lstrip().startswith("/*"):
                break
            i -= 1
        return "\n".join(reversed(out))
    while i >= 0 and re.match(r"^\s*//", lines[i]):
        out.append(lines[i])
        i -= 1
    return "\n".join(reversed(out))


def strip_comment_markers(text: str) -> str:
    return re.sub(r"^\s*(/\*\*|\*/|\*|//[/!]?)\s?", "", text, flags=re.M)


def file_header(lang: str, path: Path, text: str) -> str:
    lines = text.splitlines()
    if lang == "rust":
        return "\n".join(l for l in lines if l.lstrip().startswith("//!"))
    if lang == "go":
        m = re.search(r"^package\s+\w+", text, re.M)
        if not m:
            return ""
        idx = text[: m.start()].count("\n")
        return leading_comment(lines, idx)
    # typescript / generic: first comment block in file
    m = re.match(r"\s*(/\*\*.*?\*/)", text, re.S)
    if m:
        return m.group(1)
    return "\n".join(l for l in lines[:80] if l.lstrip().startswith(("//", "#")))


def body_of(text: str, start: int) -> str | None:
    brace = text.find("{", start)
    semi = text.find(";", start)
    if brace == -1 or (semi != -1 and semi < brace and "\n" not in text[start:semi]):
        return None
    depth, i = 0, brace
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[brace + 1 : i]
        i += 1
    return None


def check_brace_lang(root: Path, lang: str, rep: Report) -> None:
    cfg = LANG_CFG[lang]
    files = iter_files(root, cfg["exts"])
    go_pkgs_with_doc: dict[Path, bool] = {}
    for path in files:
        rel = str(path.relative_to(root))
        text = path.read_text(encoding="utf-8", errors="replace")
        is_test = cfg["test_file"](path)
        header = strip_comment_markers(file_header(lang, path, text))
        if is_test and not header.strip() and text.lstrip().startswith(("//", "/*")):
            header = text.lstrip()[:400]
        if lang == "go" and not is_test:
            go_pkgs_with_doc.setdefault(path.parent, False)
            if path.name == "doc.go" or path.parent.name == "main" or \
                    (path.name == "main.go"):
                if all(l in header for l in FILE_LABELS):
                    go_pkgs_with_doc[path.parent] = True
                check_file_header(rel, header, rep, False)
            else:
                rep.n_files += 1
                if not header.strip() and not leading_comment(text.splitlines(), 0):
                    first = text.lstrip().startswith("//")
                    if not first:
                        rep.err(rel, "missing header comment")
                if all(l in header for l in FILE_LABELS):
                    go_pkgs_with_doc[path.parent] = True
                    check_file_header(rel, header, rep, False)
                    rep.n_files -= 1
        else:
            check_file_header(rel, header, rep, is_test)
        if cfg["func"] is None:
            for lab in FUNC_LABELS:
                if lab not in text:
                    rep.warn(rel, f"no '{lab}' found anywhere; check function docs")
            collect_ids(text, rep)
            continue
        lines = text.splitlines()
        in_rust_tests = False
        for m in cfg["func"].finditer(text):
            name = next(g for g in m.groups() if g)
            line_idx = text[: m.start()].count("\n")
            where = f"{rel}:{line_idx + 1} {name}()"
            if lang == "rust" and "mod tests" in text[: m.start()]:
                in_rust_tests = True
            doc = strip_comment_markers(leading_comment(lines, line_idx))
            prev = "\n".join(lines[max(0, line_idx - 4): line_idx])
            test_fn = is_test or (lang == "go" and name.startswith("Test")) or \
                (lang == "rust" and ("#[test]" in prev or in_rust_tests))
            if lang == "go" and name == "main":
                test_fn = False
            kind = "test" if test_fn else "func"
            check_func_doc(where, doc, rep, kind)
            if kind == "func":
                body = body_of(text, m.end())
                if body is not None:
                    cleaned = re.sub(r"//[^\n]*|/\*.*?\*/", "", body, flags=re.S).strip()
                    if cleaned and not cfg["stub"].match(cleaned):
                        rep.err(where, "body contains implementation; use the stub idiom")
                    elif cleaned and not re.search(r"[A-Z]+[-.]?\d|§", cleaned):
                        rep.warn(where, "stub message does not name a spec ID")
        for m in cfg["cls"].finditer(text):
            line_idx = text[: m.start()].count("\n")
            where = f"{rel}:{line_idx + 1} type {m.group(1)}"
            doc = strip_comment_markers(leading_comment(lines, line_idx))
            if is_test:
                continue
            check_func_doc(where, doc, rep, "class")
        if lang == "typescript" and is_test:
            for m in re.finditer(r"^\s*(?:it|test)\.(?:todo|skip)\s*\(", text, re.M):
                line_idx = text[: m.start()].count("\n")
                doc = strip_comment_markers(leading_comment(lines, line_idx))
                check_func_doc(f"{rel}:{line_idx + 1} test", doc, rep, "test")
    if lang == "go":
        for pkg, ok in go_pkgs_with_doc.items():
            if not ok:
                rep.err(str(pkg.relative_to(root)) or ".",
                        "package has no doc.go/package comment with the full "
                        "file-level labels")


# ------------------------------------------------------------- shared

def check_project_docs(root: Path, rep: Report) -> None:
    for name in ("BUILD_ORDER.md", "TRACEABILITY.md"):
        if not (root / name).exists():
            rep.err(name, "missing")
    trace = root / "TRACEABILITY.md"
    if trace.exists():
        matrix_ids: set[str] = set()
        in_spec_table = False
        for line in trace.read_text(encoding="utf-8").splitlines():
            if not line.strip().startswith("|"):
                in_spec_table = False
                continue
            cells = [c.strip().strip("`*") for c in line.strip().strip("|").split("|")]
            if not cells or set(cells[0]) <= set("-: "):
                continue
            if cells[0].lower() in {"spec id", "spec", "id", "spec ids"}:
                in_spec_table = True
                continue
            if in_spec_table and cells[0]:
                matrix_ids.add(cells[0])
        cited = {c for c in rep.cited_ids if c}
        orphan = sorted(matrix_ids - cited)
        unknown = sorted(cited - matrix_ids)
        out_of_scope = set()
        txt = trace.read_text(encoding="utf-8").lower()
        for oid in orphan:
            row = next((l for l in txt.splitlines() if l.strip("| ").startswith(oid.lower())), "")
            if "out of scope" in row or "non-goal" in row:
                out_of_scope.add(oid)
        orphan = [o for o in orphan if o not in out_of_scope]
        if orphan:
            rep.err("TRACEABILITY.md", f"spec IDs with no citing code: {orphan}")
        if unknown:
            rep.err("TRACEABILITY.md", f"IDs cited in code but not in matrix: {unknown}")
    bo = root / "BUILD_ORDER.md"
    if bo.exists():
        bot = bo.read_text(encoding="utf-8")
        if not re.search(r"^##\s+The problem", bot, re.M | re.I):
            rep.err("BUILD_ORDER.md", "missing '## The problem' section")
        defined = set(re.findall(r"\*\*(C\d+)\b", bot)) or set(CAP_RE.findall(bot))
        if not defined:
            rep.err("BUILD_ORDER.md", "no capabilities (C1, C2, ...) defined under The problem")
        cited = set().union(*rep.caps_cited.values()) if rep.caps_cited else set()
        undefined = sorted(cited - defined)
        if undefined:
            rep.err("capabilities", f"cited but not defined in BUILD_ORDER.md: {undefined}")
        unused = sorted(defined - cited)
        if unused and rep.caps_cited:
            rep.warn("capabilities", f"defined but no file/function claims them: {unused}")
    for rel, (n, m) in rep.steps.items():
        nxt = rep.nexts.get(rel)
        if nxt is None:
            continue
        if n == m:
            if not re.search(r"\bnone\b", nxt, re.I):
                rep.warn(rel, f"last step ({n} of {m}) but Next: is not 'none'")
        elif not re.search(rf"step\s+{n + 1}\b", nxt, re.I) and \
                not re.search(rf"step\s+{n}\b", nxt, re.I):
            rep.err(rel, f"Next: should point at step {n + 1}; got {nxt.strip()[:80]!r}")
    totals = {m for _, m in rep.steps.values()}
    if len(totals) > 1:
        rep.err("build order", f"inconsistent 'of M' totals across files: {sorted(totals)}")
    if rep.steps and len(rep.starts) == 0:
        rep.err("build order", "no file declares itself 'the start of the project'")
    elif len(rep.starts) > 1:
        rep.err("build order", f"several files claim to be 'the start of the project' "
                               f"(use the foundation-root wording for the others): {rep.starts}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--lang", required=True,
                    choices=["python", "typescript", "go", "rust", "generic"])
    ap.add_argument("--python", help="interpreter matching the project's target version")
    ap.add_argument("--no-import-check", action="store_true")
    ap.add_argument("--quiet", action="store_true",
                    help="print errors only (plus the totals line)")
    a = ap.parse_args()

    if a.python and os.path.realpath(a.python) != os.path.realpath(sys.executable) \
            and not os.environ.get("_SKEL_REEXEC"):
        env = dict(os.environ, _SKEL_REEXEC="1")
        return subprocess.call([a.python, __file__, *sys.argv[1:]], env=env)

    root = a.root.resolve()
    rep = Report()
    if a.lang == "python":
        files = check_python(root, rep)
        if not a.no_import_check:
            py_import_check(root, files, a.python or sys.executable, rep)
    else:
        check_brace_lang(root, a.lang, rep)
    check_project_docs(root, rep)

    # Grouped by file, one line per problem, so fixes can be targeted edits.
    groups: dict[str, list[str]] = {}
    items = [("ERROR", e) for e in rep.errors]
    if not a.quiet:
        items += [("WARN", w) for w in rep.warnings]
    for level, msg in items:
        where, _, text = msg.partition(": ")
        fname, _, loc = where.partition(":")
        groups.setdefault(fname, []).append(
            f"  {level:<5} {loc + ' ' if loc else ''}{text}".rstrip())
    for fname in sorted(groups):
        print(fname)
        print("\n".join(sorted(groups[fname], key=lambda x: not x.startswith("  ERROR"))))
    print(f"\nChecked {rep.n_files} files, {rep.n_funcs} functions/types; "
          f"{len(rep.errors)} errors, {len(rep.warnings)} warnings; "
          f"{len(rep.cited_ids)} spec IDs cited.")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
