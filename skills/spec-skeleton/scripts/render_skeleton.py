#!/usr/bin/env python3
"""Render a project skeleton from a skeleton.toml manifest.

The model writes only the judgment (problem, capabilities, module plan, and the
prose of each docstring) into skeleton.toml. This script derives everything
mechanical from it: Previous/Next pointers, step numbers, Depends on /
Depended on by, import lines, stub bodies, package markers, test stubs,
BUILD_ORDER.md, TRACEABILITY.md, and tooling config.

Modes:
  render_skeleton.py skeleton.toml --plan        BUILD_ORDER.md only (checkpoint)
  render_skeleton.py skeleton.toml --docs-only   BUILD_ORDER.md + TRACEABILITY.md
  render_skeleton.py skeleton.toml               full render (Python only)
Options:
  --out DIR     project root (default: the manifest's directory)
  --dry-run     report what would change, write nothing
  --force       overwrite files even if they contain implemented code
  --no-format   skip running `ruff format` on generated Python

Safety: a source or test file whose bodies are no longer stubs is never
overwritten without --force. Config files (pyproject.toml, .gitignore,
README.md) are created if missing and otherwise left alone unless --force.

Exit code 0 = rendered, 1 = manifest errors (nothing written).
Requires Python 3.11+ (tomllib). Standard library only.
"""

import argparse
import ast
import hashlib
import json
import re
import shutil
import subprocess
import sys
import textwrap
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

WIDTH = 88
DASH = "—"


# ------------------------------------------------------------------ helpers

def cap1(s: str) -> str:
    s = " ".join(s.split())
    return s[:1].upper() + s[1:]


def natural(xs: list[str]) -> list[str]:
    def key(x: str) -> list[object]:
        return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", x)]
    return sorted(xs, key=key)


def period(s: str) -> str:
    s = " ".join(s.split())
    return s if not s or s[-1] in ".!?" else s + "."


def wrap(text: str, indent: int, first: str = "", hang: int = 0) -> list[str]:
    """Wrap one or more paragraphs; `first` is a label put before line one."""
    out: list[str] = []
    paras = [p for p in re.split(r"\n\s*\n", text.strip())] or [""]
    pad = " " * indent
    for i, p in enumerate(paras):
        p = " ".join(p.split())
        lead = first if i == 0 else ""
        lines = textwrap.wrap(
            lead + p, width=WIDTH - indent, subsequent_indent=" " * hang,
            break_long_words=False, break_on_hyphens=False) or [lead.rstrip()]
        if i:
            out.append("")
        out.extend(pad + ln if ln else "" for ln in lines)
    return out


def ids(xs: list[str] | str | None) -> str:
    if not xs:
        return DASH
    if isinstance(xs, str):
        return xs
    return ", ".join(xs)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


@dataclass
class Problems:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def err(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


# ------------------------------------------------------------------ model

@dataclass
class Module:
    raw: dict
    path: str                 # relative to src/, e.g. tally/core/money.py
    dotted: str
    step: int = 0
    marker: bool = False      # generated package marker
    marker_for: "Module | None" = None

    @property
    def items(self) -> list[dict]:
        return self.raw.get("items", [])

    @property
    def caps(self) -> list[str]:
        c = self.raw.get("capability", [])
        return [c] if isinstance(c, str) else list(c)

    @property
    def uses(self) -> list[dict]:
        return self.raw.get("uses", [])


def dotted_of(path: str) -> str:
    p = path[:-3] if path.endswith(".py") else path
    parts = p.split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


class Manifest:
    def __init__(self, data: dict, probs: Problems) -> None:
        self.d = data
        self.p = probs
        self.proj = data.get("project", {})
        self.caps = {c["id"]: c for c in data.get("capabilities", [])}
        self.specs = {s["id"]: s for s in data.get("specs", [])}
        self.questions = {q["id"]: q for q in data.get("questions", [])}
        self.modules = [Module(m, m.get("path", "?"), dotted_of(m.get("path", "?")))
                        for m in data.get("modules", [])]
        for i, m in enumerate(self.modules, 1):
            m.step = i
        # A module can be named by its dotted name (Python), its path, or its
        # path without the extension (other languages).
        self.by_dotted: dict[str, Module] = {}
        for m in self.modules:
            for key in (m.dotted, m.path, re.sub(r"\.[A-Za-z0-9]+$", "", m.path)):
                self.by_dotted.setdefault(key, m)
        self.total = len(self.modules)
        self.lang = self.proj.get("language", "python").lower()

    # -------------------------------------------------------------- checks
    def validate(self, need_items: bool) -> None:
        p = self.p
        for k in ("name", "problem", "problem_short", "language"):
            if not self.proj.get(k):
                p.err("[project]", f"missing '{k}'")
        if self.lang == "python" and not self.proj.get("package"):
            p.err("[project]", "missing 'package' (import name)")
        if not 3 <= len(self.caps) <= 7:
            p.warn("[[capabilities]]", f"{len(self.caps)} capabilities; aim for 3 to 7")
        if not self.modules:
            p.err("[[modules]]", "no modules")
        seen_paths: set[str] = set()
        served: set[str] = set()
        cited: set[str] = set()
        for m in self.modules:
            w = f"module {m.path} (step {m.step})"
            if m.path in seen_paths:
                p.err(w, "duplicate path")
            seen_paths.add(m.path)
            for k in ("summary", "owns", "why_now"):
                if not m.raw.get(k):
                    p.err(w, f"missing '{k}'")
            if not m.caps:
                p.err(w, "serves no capability; add one or drop the module")
            for c in m.caps:
                if c not in self.caps:
                    p.err(w, f"capability {c} is not defined")
                served.add(c)
            for u in m.uses:
                dep = self.by_dotted.get(u.get("module", ""))
                if dep is None:
                    p.err(w, f"uses unknown module {u.get('module')!r}")
                    continue
                if not u.get("symbols") or not u.get("why"):
                    p.err(w, f"uses {dep.dotted}: needs 'symbols' and 'why'")
                if dep.step >= m.step and not u.get("type_only"):
                    p.err(w, f"uses {dep.dotted} (step {dep.step}), which comes "
                             f"later; reorder, or move the shared piece down")
            cited.update(m.raw.get("spec", []))
            if need_items and not m.items:
                p.err(w, "has no items")
            names: set[str] = set()
            for it in m.items:
                self._check_item(w, it, names, cited, top=True)
        for c in self.caps:
            if c not in served:
                p.err(f"capability {c}", "no module serves it (gap)")
        self._check_cycles()
        if need_items:
            for sid, s in self.specs.items():
                if sid not in cited and not s.get("out_of_scope"):
                    p.err(f"spec {sid}", "cited by no item and not marked out_of_scope")
            for sid in sorted(cited - set(self.specs)):
                p.err(f"spec {sid}", "cited but not defined in [[specs]]")
        if self.modules and self.modules[0].uses:
            p.err(f"module {self.modules[0].path}",
                  "step 1 must import nothing from the project")

    def _check_item(self, w: str, it: dict, names: set[str], cited: set[str],
                    top: bool) -> None:
        p = self.p
        kind = it.get("kind", "def")
        name = it.get("name") or ""
        iw = f"{w} {name or '?'}"
        if not name:
            p.err(w, "item missing 'name'")
        if name in names:
            p.err(iw, "duplicate name in module")
        names.add(name)
        if kind == "const":
            if not it.get("line"):
                p.err(iw, "const needs 'line'")
            return
        if not it.get("signature"):
            p.err(iw, "missing 'signature'")
        else:
            self._check_signature(iw, it)
        for k in ("summary", "piece", "why", "what"):
            if not it.get(k):
                p.err(iw, f"missing '{k}'")
        if not re.search(r"\bC\d+\b", it.get("piece", "")):
            p.err(iw, "'piece' must name a capability ID (C1, C2, ...)")
        spec = it.get("spec", [])
        if not spec:
            p.err(iw, "missing 'spec' IDs")
        cited.update(spec)
        is_class = it.get("signature", "").lstrip().startswith("class ")
        steps = it.get("steps", [])
        if not is_class and not steps:
            p.err(iw, "a function needs at least one step")
        for i, st in enumerate(steps, 1):
            if not st.get("task"):
                p.err(iw, f"step {i} missing 'task'")
            if st.get("open"):
                if st["open"] not in self.questions:
                    p.err(iw, f"step {i} cites undefined question {st['open']}")
            elif not st.get("outcome"):
                p.err(iw, f"step {i} missing 'outcome'")
        if len(steps) >= 3 and len(it.get("why", "").split()) < 15:
            p.warn(iw, "'why' is thin for a full-depth function (3+ steps)")
        mnames: set[str] = set()
        for meth in it.get("methods", []):
            self._check_item(iw, meth, mnames, cited, top=False)

    def _check_signature(self, iw: str, it: dict) -> None:
        sig = it["signature"].strip().rstrip(":")
        try:
            tree = ast.parse(sig + ":\n    pass\n")
        except SyntaxError as e:
            self.p.warn(iw, f"signature does not parse under Python "
                            f"{sys.version_info.major}.{sys.version_info.minor} "
                            f"({e.msg}); fine only if it uses newer syntax")
            return
        node = tree.body[0]
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        a = node.args
        params = [x.arg for x in a.posonlyargs + a.args + a.kwonlyargs]
        params += [x.arg for x in (a.vararg, a.kwarg) if x]
        params = [x for x in params if x not in ("self", "cls")]
        if node.name != it.get("name"):
            self.p.err(iw, f"signature names '{node.name}', item names '{it.get('name')}'")
        doc_args = it.get("args")
        if isinstance(doc_args, dict) and set(doc_args) != set(params):
            self.p.err(iw, f"'args' {sorted(doc_args)} do not match parameters "
                           f"{sorted(params)}")

    def _check_cycles(self) -> None:
        graph = {m.dotted: [self.by_dotted[u["module"]].dotted for u in m.uses
                            if not u.get("type_only") and u.get("module") in self.by_dotted]
                 for m in self.modules}
        state: dict[str, int] = {}

        def visit(n: str, trail: list[str]) -> None:
            state[n] = 1
            for d in graph.get(n, []):
                if state.get(d) == 1:
                    cyc = trail[trail.index(d):] + [d] if d in trail else [n, d]
                    self.p.err("import cycle", " -> ".join(cyc))
                elif d not in state:
                    visit(d, trail + [d])
            state[n] = 2

        for n in graph:
            if n not in state:
                visit(n, [n])

    # -------------------------------------------------------------- derived
    def consumers(self, m: Module) -> list[tuple[Module, dict]]:
        out = []
        for other in self.modules:
            for u in other.uses:
                if self.by_dotted.get(u.get("module", "")) is m:
                    out.append((other, u))
        return out

    def cap_label(self, cid: str) -> str:
        c = self.caps.get(cid, {})
        return f"{cid} {c.get('name', '')}".strip()

    def cap_steps(self) -> dict[str, list[int]]:
        out: dict[str, list[int]] = {c: [] for c in self.caps}
        for m in self.modules:
            for c in m.caps:
                out.setdefault(c, []).append(m.step)
        return out

    def module_specs(self, m: Module) -> list[str]:
        seen: list[str] = []

        def add(xs: list[str]) -> None:
            for x in xs:
                if x not in seen:
                    seen.append(x)
        add(m.raw.get("spec", []))
        for it in m.items:
            add(it.get("spec", []))
            for meth in it.get("methods", []):
                add(meth.get("spec", []))
        order = {sid: i for i, sid in enumerate(self.specs)}
        return sorted(seen, key=lambda x: order.get(x, len(order)))

    def module_traces(self, m: Module) -> list[str]:
        seen: list[str] = []
        for sid in self.module_specs(m):
            for t in self.specs.get(sid, {}).get("traces", []):
                if t not in seen:
                    seen.append(t)
        for it in m.items:
            for t in it.get("traces", []):
                if t not in seen:
                    seen.append(t)
        return natural(seen)


# ------------------------------------------------------------------ docs

def short_path(mf: Manifest, m: Module) -> str:
    return m.path


def render_build_order(mf: Manifest) -> str:
    pj = mf.proj
    L = [f"# Build Order — {pj.get('name', '')}", "", "## The problem",
         " ".join(pj.get("problem", "").split()), "",
         "### What must be true for it to be solved"]
    cs = mf.cap_steps()
    for cid, c in mf.caps.items():
        st = cs.get(cid, [])
        rng = (f"step {st[0]}" if len(st) == 1 else
               f"steps {', '.join(map(str, st))}") if st else "no step yet"
        L.append(f"- **{cid} {c.get('name', '')}**: {period(c.get('need', ''))} ({rng})")
    L += ["", "## How to use this skeleton",
          "Start at step 1. In each file: read the file docstring, then build the "
          "functions in its \"Build these in order\" list. For each function, read "
          "Problem piece / Why it matters / What, work through the build steps, then "
          "un-skip its tests and make them pass. When the file's tests pass, follow "
          "its `Next:` pointer. Once a function is implemented and tested, delete its "
          "Build steps block; keep Problem piece, Why it matters, and What as "
          "permanent docs.", "",
          f"Toolchain baseline: {' '.join(str(pj.get('toolchain_note', pj.get('python', '')) or DASH).split())}",
          f"Spec ID scheme: {' '.join(str(pj.get('spec_id_scheme', DASH)).split())}",
          "", "Generated from `skeleton.toml` by `render_skeleton.py`. Edit the "
          "manifest and re-render; do not hand-edit generated sections.",
          "", "## Sequence",
          "| Step | Module | Capability | Builds | Depends on | Unlocks |",
          "|---|---|---|---|---|---|"]
    for m in mf.modules:
        deps = sorted({mf.by_dotted[u["module"]].step for u in m.uses
                       if u.get("module") in mf.by_dotted})
        dep_s = ", ".join(map(str, deps)) if deps else (
            f"{DASH} (start of project)" if m.step == 1 else f"{DASH} (foundation root)")
        unl = sorted({o.step for o, _ in mf.consumers(m)})
        unl_s = ", ".join(map(str, unl)) if unl else DASH
        if m.raw.get("unlocks_note"):
            unl_s += f"; {m.raw['unlocks_note']}"
        builds = m.raw.get("summary", "").rstrip(".")
        specs = mf.module_specs(m)
        if specs:
            builds += f" ({', '.join(specs)})"
        L.append(f"| {m.step} | {m.path} | {', '.join(m.caps)} | {builds} | "
                 f"{dep_s} | {unl_s} |")
    L += ["", "## Dependency graph", "```mermaid", "flowchart TD"]
    for m in mf.modules:
        L.append(f'  s{m.step}["{m.step}. {m.path}"]')
    for m in mf.modules:
        for u in m.uses:
            d = mf.by_dotted.get(u.get("module", ""))
            if d:
                arrow = "-.->" if u.get("type_only") else "-->"
                L.append(f"  s{d.step} {arrow} s{m.step}")
    L += ["```", "", "## Assumptions"]
    for a in pj.get("assumptions", []) or ["None."]:
        L.append(f"- {period(a)}")
    L += ["", "## Open questions"]
    if not mf.questions:
        L.append("- None.")
    for qid, q in mf.questions.items():
        cites = f" (conflicting or silent clauses: {ids(q.get('cites'))})" if q.get("cites") else ""
        L.append(f"- **{qid}**: {period(q.get('text', ''))}{cites}")
    return "\n".join(L) + "\n"


def test_names_for(mf: Manifest, m: Module) -> dict[str, list[str]]:
    """Map spec ID -> test function names derived from step outcomes."""
    out: dict[str, list[str]] = {}
    for fn_name, it, owner in iter_funcs(m):
        for i, st in enumerate(it.get("steps", []), 1):
            if st.get("open") or not st.get("outcome"):
                continue
            tname = test_name(fn_name, owner, st, i)
            for sid in it.get("spec", []):
                out.setdefault(sid, []).append(tname)
    return out


def iter_funcs(m: Module):
    for it in m.items:
        sig = it.get("signature", "").lstrip()
        if it.get("kind") == "const":
            continue
        if sig.startswith("class "):
            if it.get("steps"):
                yield it["name"], it, None
            for meth in it.get("methods", []):
                yield meth["name"], meth, it["name"]
        else:
            yield it["name"], it, None


def test_name(fn: str, owner: str | None, st: dict, i: int) -> str:
    base = f"{slug(owner)}_{fn.strip('_')}" if owner else fn.strip("_")
    tail = slug(st["test"]) if st.get("test") else f"step{i}"
    return f"test_{slug(base)}_{tail}"


def test_path(mf: Manifest, m: Module) -> str:
    parts = m.path.split("/")
    sub = parts[1:-1]
    stem = parts[-1][:-3].strip("_") or "init"
    return "/".join(["tests", *sub, f"test_{stem}.py"])


def render_traceability(mf: Manifest, with_tests: bool) -> str:
    L = ["# Traceability", "",
         f"Spec ID scheme: {' '.join(str(mf.proj.get('spec_id_scheme', DASH)).split())}", "",
         "| Spec ID | Clause summary | PRD trace | File | Function(s) | Test(s) |",
         "|---|---|---|---|---|---|"]
    for sid, s in mf.specs.items():
        files, funcs, tests = [], [], []
        for m in mf.modules:
            hit = sid in m.raw.get("spec", [])
            for it in m.items:
                if sid in it.get("spec", []):
                    hit = True
                    funcs.append(it["name"])
                for meth in it.get("methods", []):
                    if sid in meth.get("spec", []):
                        hit = True
                        funcs.append(f"{it['name']}.{meth['name']}")
            if hit:
                files.append(f"src/{m.path}" if mf.lang == "python" else m.path)
                if with_tests:
                    tests += test_names_for(mf, m).get(sid, [])
        summ = " ".join(s.get("summary", "").split())
        if s.get("out_of_scope") and not files:
            L.append(f"| {sid} | {summ} | {ids(s.get('traces'))} | out of scope: "
                     f"{s['out_of_scope']} | {DASH} | {DASH} |")
            continue
        L.append(f"| {sid} | {summ} | {ids(s.get('traces'))} | "
                 f"{', '.join(files) or DASH} | {', '.join(funcs) or DASH} | "
                 f"{', '.join(tests) or DASH} |")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ python

def py_file_header(mf: Manifest, m: Module) -> list[str]:
    pj = mf.proj
    src = m.marker_for or m
    first = mf.modules[0]
    L: list[str] = [period(m.raw.get("summary", "")), ""]
    L += wrap(f"{' '.join(pj['problem_short'].split())} (Full statement: "
              f"BUILD_ORDER.md, \"The problem\".)", 0, "Problem: ")
    L.append("")
    caps = " / ".join(mf.cap_label(c) for c in m.caps)
    L += wrap(f"{caps}. {m.raw.get('owns', '')}", 0, "Piece of the problem: ")
    L.append("")
    L += wrap(m.raw.get("why_now", ""), 0, "Why this comes now: ")
    L.append("")
    if m.marker:
        L.append(f"Build order: Step {src.step} of {mf.total} (package marker; "
                 f"shares step with {src.dotted}).")
    else:
        L.append(f"Build order: Step {m.step} of {mf.total}.")
    i = src.step - 1
    prev = mf.modules[i - 1] if i > 0 else None
    nxt = mf.modules[i + 1] if i + 1 < len(mf.modules) else None
    if prev is None:
        L.append("Previous: none. This is the start of the project.")
    else:
        L += wrap(f"{prev.path} (step {prev.step}), {relation(mf, src, prev, True)}",
                  0, "Previous: ", hang=4)
    if nxt is None:
        L.append("Next: none. This is the final step; the project is complete when")
        L.append("    its tests pass.")
    else:
        L += wrap(f"{nxt.path} (step {nxt.step}), {relation(mf, src, nxt, False)}",
                  0, "Next: ", hang=4)
    L += ["", "Build these in order:"]
    if not m.items:
        L.append("    Nothing; this file holds no definitions.")
    for n, it in enumerate(m.items, 1):
        note = it.get("order_note") or it.get("summary") or (
            f"constant ({it['comment']})" if it.get("comment") else "constant")
        L += wrap(f"{it['name']}: {period(note)}", 4, f"{n}. ", hang=3)
    L += ["", "Depends on:"]
    proj_uses = m.uses
    if m.marker:
        L.append("    Nothing in this project (package marker).")
    elif not proj_uses and m.step == 1:
        L += ["    Nothing in this project. This module is the start of the project.",
              "    Build it first."]
    elif not proj_uses:
        reason = m.raw.get("root_reason") or "its place is set by the build order"
        L += wrap(f"Nothing in this project (foundation root). Placed at step "
                  f"{m.step} because {reason.rstrip('.')}.", 4, hang=4)
    for u in proj_uses:
        tag = " (type-only)" if u.get("type_only") else ""
        L += wrap(f"{u['module']}: {u['symbols']}{tag}. {period(cap1(u['why']))}",
                  4, hang=4)
    std = [imp_mod(x) for x in m.raw.get("stdlib", [])]
    tp = [imp_mod(x) for x in m.raw.get("third_party", [])]
    L.append(f"    Standard library: {', '.join(dict.fromkeys(std)) or 'none'}.")
    L.append(f"    Third-party: {', '.join(dict.fromkeys(tp)) or 'none'}.")
    L += ["", "Depended on by:"]
    if m.marker:
        L += wrap(f"Every module in {m.dotted} (package marker).", 4, hang=4)
    else:
        cons = mf.consumers(m)
        if not cons:
            L.append("    Nothing in this project; this is the entry point."
                     if m.raw.get("main_guard") or nxt is None else
                     "    Nothing in this project yet.")
        for o, u in cons:
            L += wrap(f"{o.dotted}: {u['symbols']}. {period(cap1(u['why']))}",
                      4, hang=4)
    specs = mf.module_specs(m) if not m.marker else []
    traces = mf.module_traces(m) if not m.marker else []
    L += ["", f"Spec coverage: {ids(specs)} | Traces to: {ids(traces)}"]
    if m.raw.get("steps"):
        L += ["", "Build steps:"]
        L += render_steps(m.raw["steps"], 0, mf)
    return L


def relation(mf: Manifest, me: Module, other: Module, is_prev: bool) -> str:
    """A short clause saying how a neighbouring step relates to this one."""
    for u in me.uses:
        if mf.by_dotted.get(u.get("module", "")) is other:
            return f"which defines {u['symbols']}, used here."
    for u in other.uses:
        if mf.by_dotted.get(u.get("module", "")) is me:
            return f"which uses {u['symbols']} from this file."
    summ = other.raw.get("summary", "").strip().rstrip(".")
    lead = "which comes just before" if is_prev else "which comes next"
    return f"{lead}: {summ[:1].lower() + summ[1:]}."


def imp_mod(line: str) -> str:
    mt = re.match(r"\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", line)
    return (mt.group(1) or mt.group(2)) if mt else line


def render_steps(steps: list[dict], ind: int, mf: Manifest) -> list[str]:
    L: list[str] = []
    for i, st in enumerate(steps, 1):
        lab = f"{i}. "
        h = len(lab)
        if st.get("open"):
            L += wrap(f"Open question (spec silent): {period(st['task'])}", ind,
                      f"{lab}Task: ", hang=h)
            L += wrap(f"Resolve with the spec owner before implementing; logged as "
                      f"{st['open']} in BUILD_ORDER.md.", ind + h, "Expected outcome: ")
            continue
        L += wrap(period(st["task"]), ind, f"{lab}Task: ", hang=h)
        if st.get("think"):
            L += wrap(st["think"], ind + h, "Think about: ")
        L += wrap(period(st["outcome"]), ind + h, "Expected outcome: ")
    return L


def render_doc(it: dict, ind: int, mf: Manifest, is_class: bool) -> list[str]:
    pad = " " * ind
    L = [pad + '"""' + period(it["summary"]), ""]
    L += wrap(it["piece"], ind, "Problem piece: ")
    L.append("")
    L += wrap(it["why"], ind, "Why it matters: ")
    L.append("")
    L += wrap(it["what"], ind, "What: ")
    L.append("")
    L.append(f"{pad}Spec: {ids(it.get('spec'))} | Ticket: {it.get('ticket', DASH)} | "
             f"Traces to: {ids(it.get('traces'))}")
    for sec, key in (("Attributes", "attributes"), ("Args", "args"),
                     ("Returns", "returns"), ("Yields", "yields"), ("Raises", "raises")):
        val = it.get(key)
        if not val:
            continue
        L += ["", f"{pad}{sec}:"]
        if isinstance(val, dict):
            for k, v in val.items():
                L += wrap(period(v), ind + 4, f"{k}: ", hang=4)
        else:
            L += wrap(period(val), ind + 4, hang=4)
    if it.get("steps"):
        L += ["", f"{pad}Build steps:"]
        L += render_steps(it["steps"], ind, mf)
    L.append(pad + '"""')
    return L


def render_item(it: dict, ind: int, mf: Manifest, protocol: bool) -> list[str]:
    pad = " " * ind
    if it.get("kind") == "const":
        c = f"  # {it['comment']}" if it.get("comment") else ""
        return [pad + it["line"] + c]
    sig = it["signature"].strip().rstrip(":")
    is_class = sig.startswith("class ")
    L = [pad + d for d in it.get("decorators", [])]
    L.append(f"{pad}{sig}:")
    L += render_doc(it, ind + 4, mf, is_class)
    body_pad = " " * (ind + 4)
    if is_class:
        body = it.get("body", [])
        if body:
            L.append("")
            L += [body_pad + b for b in body]
        is_proto = protocol or bool(re.search(r"\bProtocol\b", sig))
        for meth in it.get("methods", []):
            L.append("")
            L += render_item(meth, ind + 4, mf, is_proto)
    else:
        if protocol:
            L.append(body_pad + "...")
        else:
            spec = (it.get("spec") or ["?"])[0]
            L.append(f'{body_pad}raise NotImplementedError("{spec}: {it["name"]}")')
    return L


def render_imports(m: Module, pkg_prefix: str) -> list[str]:
    std = list(dict.fromkeys(m.raw.get("stdlib", [])))
    tp = list(dict.fromkeys(m.raw.get("third_party", [])))
    runtime = [u for u in m.uses if not u.get("type_only")]
    typeonly = [u for u in m.uses if u.get("type_only")]
    if typeonly and not any("TYPE_CHECKING" in s for s in std):
        std.append("from typing import TYPE_CHECKING")
    first = [f"from {u['module']} import {u['symbols']}" for u in runtime]
    def key(line: str) -> tuple[int, str]:
        return (0 if line.startswith("import ") else 1, imp_mod(line).lower())
    groups = [sorted(std, key=key), sorted(tp, key=key), sorted(first, key=key)]
    L: list[str] = []
    for g in groups:
        if g:
            if L:
                L.append("")
            L += g
    if typeonly:
        L += ["", "if TYPE_CHECKING:"]
        L += [f"    from {u['module']} import {u['symbols']}" for u in typeonly]
    return L


def render_py_module(mf: Manifest, m: Module) -> str:
    head = py_file_header(mf, m)
    L = ['"""' + head[0], *head[1:], '"""']
    imps = render_imports(m, mf.proj["package"])
    if imps:
        L += [""] + imps
    for it in m.items:
        L += ["", ""] if it.get("kind") != "const" else [""]
        L += render_item(it, 0, mf, protocol=False)
    if m.raw.get("main_guard"):
        L += ["", "", 'if __name__ == "__main__":', "    raise SystemExit(main())"]
    return "\n".join(L) + "\n"


def render_py_tests(mf: Manifest, m: Module) -> str | None:
    funcs = list(iter_funcs(m))
    tests = []
    imported: list[str] = []
    for fn, it, owner in funcs:
        for i, st in enumerate(it.get("steps", []), 1):
            if st.get("open") or not st.get("outcome"):
                continue
            top = owner or fn
            if top not in imported:
                imported.append(top)
            spec = it.get("spec") or ["?"]
            tname = test_name(fn, owner, st, i)
            target = f"{owner}.{fn}" if owner else fn
            what = (f"Check that {target} {st['test'].replace('_', ' ')}." if st.get("test")
                    else f"Step {i} of {target}: its expected outcome holds.")
            doc = [f'    """{what}', ""]
            doc.append(f"    Spec: {ids(spec)} | Traces to: {ids(it.get('traces'))}")
            doc += wrap(period(st["outcome"]), 4, "Expected outcome: ", hang=4)
            doc.append('    """')
            tests.append([f'@pytest.mark.skip(reason="skeleton: {spec[0]} not implemented")',
                          f"def {tname}() -> None:", *doc])
    if not tests:
        return None
    covers = ids(mf.module_specs(m))
    L = [f'"""Tests for {m.dotted} (build step {m.step}).', ""]
    L += wrap(f"Covers: {covers}. Each test guards one expected outcome from the build "
              f"steps in src/{m.path}.", 0)
    L += ['"""', "", "import pytest", ""]
    L.append(f"from {m.dotted} import {', '.join(sorted(imported, key=str.lower))}")
    for t in tests:
        L += ["", ""] + t
    return "\n".join(L) + "\n"


def make_markers(mf: Manifest) -> list[Module]:
    """One __init__.py per package directory, sharing its first module's step."""
    first_in: dict[str, Module] = {}
    for m in mf.modules:
        parts = m.path.split("/")[:-1]
        for k in range(1, len(parts) + 1):
            pkg = "/".join(parts[:k])
            first_in.setdefault(pkg, m)
    explicit = {m.path for m in mf.modules}
    out = []
    for pkg, first in first_in.items():
        path = f"{pkg}/__init__.py"
        if path in explicit:
            continue
        members = [x for x in mf.modules if x.path.startswith(pkg + "/")]
        caps = list(dict.fromkeys(c for x in members for c in x.caps))
        raw = {"summary": f"Package marker for {pkg.replace('/', '.')}.",
               "capability": caps,
               "owns": "This file only marks the package and holds no logic.",
               "why_now": f"It shares step {first.step} with "
                          f"{first.dotted}, the first module built in this package."}
        mk = Module(raw, path, pkg.replace("/", "."), first.step, True, first)
        out.append(mk)
    return out


PYPROJECT = """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{name}"
version = "0.1.0"
description = "{desc}"
readme = "README.md"
requires-python = ">={py}"
dependencies = [{deps}]
{scripts}
[dependency-groups]
dev = ["ruff", "mypy", "pytest"]

[tool.hatch.build.targets.wheel]
packages = ["src/{pkg}"]

[tool.ruff]
line-length = 88
target-version = "py{pyn}"
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "D", "ANN", "RUF"]
ignore = ["D203", "D213"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.per-file-ignores]
# SKELETON: imports are pre-declared for bodies not yet written.
# Remove this entry once every NotImplementedError is gone.
"src/**/*.py" = ["F401"]
"tests/**/*.py" = ["F401"]

[tool.mypy]
python_version = "{py}"
strict = true
mypy_path = "src"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --import-mode=importlib"
pythonpath = ["src"]
"""

GITIGNORE = """__pycache__/
*.py[cod]
.venv/
.mypy_cache/
.ruff_cache/
.pytest_cache/
dist/
build/
*.egg-info/
"""


def render_readme(mf: Manifest) -> str:
    pj = mf.proj
    return (f"# {pj['name']}\n\n{period(pj.get('description', ''))}\n\n"
            f"## The problem\n\n{' '.join(pj['problem'].split())}\n\n"
            "## Install\n\n```bash\nuv sync            # or: pip install -e . "
            "&& pip install ruff mypy pytest\n```\n\n"
            "## Run the tests\n\n```bash\nuv run pytest -q   # every test is "
            "skipped until you implement it\n```\n\n"
            "## How to build it\n\nFollow [BUILD_ORDER.md](BUILD_ORDER.md) from step 1. "
            "Spec coverage is in [TRACEABILITY.md](TRACEABILITY.md).\n")


def render_pyproject(mf: Manifest) -> str:
    pj = mf.proj
    py = str(pj.get("python", "3.14"))
    deps = ", ".join(f'"{d}"' for d in pj.get("dependencies", []))
    scripts = ""
    if pj.get("cli"):
        scripts = f'\n[project.scripts]\n{pj["cli"]} = "{pj["package"]}.__main__:main"\n'
    return PYPROJECT.format(name=pj["name"], desc=" ".join(pj.get("description", "").split()),
                            py=py, pyn=py.replace(".", ""), deps=deps, scripts=scripts,
                            pkg=pj["package"])


# ------------------------------------------------------------------ writing

def py_is_stub_only(src: str, is_test: bool = False) -> bool:
    """True if every function body is docstring + stub, and tests are untouched."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if is_test and node.name.startswith("test") and not any(
                    "skip" in ast.unparse(d) for d in node.decorator_list):
                return False
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(
                    getattr(body[0], "value", None), ast.Constant):
                body = body[1:]
            if not body:
                continue
            if len(body) > 1:
                return False
            s = body[0]
            if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) \
                    and s.value.value is Ellipsis:
                continue
            if isinstance(s, ast.Pass):
                continue
            if isinstance(s, ast.Raise) and isinstance(s.exc, ast.Call) and \
                    isinstance(s.exc.func, ast.Name) and s.exc.func.id == "NotImplementedError":
                continue
            return False
    return True


@dataclass
class Plan:
    write: dict[Path, str] = field(default_factory=dict)
    kinds: dict[Path, str] = field(default_factory=dict)   # doc | code | config


LOCK = ".skeleton.lock"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def apply(plan: Plan, root: Path, dry: bool, force: bool) -> dict[str, list[str]]:
    """Write changed files; never clobber hand edits or implemented code.

    `.skeleton.lock` remembers the hash of every file as last rendered. A file
    whose current hash differs from its lock entry was edited by hand and is
    kept unless --force. Without a lock entry, implemented code is detected by
    parsing (any non-stub body, or an un-skipped test).
    """
    lock_path = root / LOCK
    try:
        lock: dict[str, str] = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        lock = {}
    res: dict[str, list[str]] = {"created": [], "updated": [], "unchanged": [],
                                 "kept (edited by hand; merge, or use --force)": [],
                                 "kept (implemented code; merge by hand)": [],
                                 "kept (config exists; use --force)": []}
    for path, text in plan.write.items():
        rel = path.relative_to(root).as_posix()
        kind = plan.kinds[path]
        if path.exists():
            old = path.read_text(encoding="utf-8")
            if old == text:
                res["unchanged"].append(rel)
                lock[rel] = sha(text)
                continue
            if not force and kind == "config":
                res["kept (config exists; use --force)"].append(rel)
                continue
            if not force and kind == "code" and rel in lock and sha(old) != lock[rel]:
                res["kept (edited by hand; merge, or use --force)"].append(rel)
                continue
            if not force and kind == "code" and not py_is_stub_only(
                    old, is_test=rel.startswith("tests/")):
                res["kept (implemented code; merge by hand)"].append(rel)
                continue
            res["updated"].append(rel)
        else:
            res["created"].append(rel)
        lock[rel] = sha(text)
        if not dry:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    if not dry:
        lock_path.write_text(json.dumps(dict(sorted(lock.items())), indent=1) + "\n",
                             encoding="utf-8")
    return res


def ruff_format(paths: list[Path], root: Path) -> str:
    ruff = shutil.which("ruff")
    if not ruff:
        return "ruff not found: generated Python was not formatted; run `ruff format`."
    py = [str(p) for p in paths if p.suffix == ".py" and p.exists()]
    if not py:
        return ""
    subprocess.run([ruff, "check", "--select", "I", "--fix", "--exit-zero", "--quiet",
                    *py], cwd=root, capture_output=True, text=True)
    r = subprocess.run([ruff, "format", "--quiet", *py], cwd=root,
                       capture_output=True, text=True)
    if r.returncode:
        return "ruff format failed: " + (r.stderr or r.stdout).strip()[:300]
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--out", type=Path)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--plan", action="store_true")
    g.add_argument("--docs-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-format", action="store_true")
    a = ap.parse_args()

    try:
        data = tomllib.loads(a.manifest.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as e:
        print(f"ERROR manifest: {e}")
        return 1
    probs = Problems()
    mf = Manifest(data, probs)
    full = not (a.plan or a.docs_only)
    if full and mf.lang != "python":
        print(f"ERROR language '{mf.lang}': full render supports python only. Use "
              f"--docs-only and write source files by hand (references/manual.md).")
        return 1
    mf.validate(need_items=not a.plan)
    for w in probs.warnings:
        print(f"WARN  {w}")
    for e in probs.errors:
        print(f"ERROR {e}")
    if probs.errors:
        print(f"\n{len(probs.errors)} manifest errors; nothing written. "
              f"Fix skeleton.toml and re-run.")
        return 1

    root = (a.out or a.manifest.parent).resolve()
    plan = Plan()

    def put(rel: str, text: str, kind: str) -> None:
        p = root / rel
        plan.write[p] = text
        plan.kinds[p] = kind

    put("BUILD_ORDER.md", render_build_order(mf), "doc")
    if not a.plan:
        put("TRACEABILITY.md", render_traceability(mf, with_tests=full), "doc")
    if full:
        for m in mf.modules + make_markers(mf):
            put(f"src/{m.path}", render_py_module(mf, m), "code")
            if not m.marker:
                t = render_py_tests(mf, m)
                if t:
                    put(test_path(mf, m), t, "code")
        put(f"src/{mf.proj['package']}/py.typed", "", "config")
        put("pyproject.toml", render_pyproject(mf), "config")
        put(".gitignore", GITIGNORE, "config")
        put("README.md", render_readme(mf), "config")
        # Format in a scratch pass so "unchanged" compares formatted text.
        if not a.no_format and shutil.which("ruff"):
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                tmp_root = Path(td)
                tmp_paths = []
                for p, txt in plan.write.items():
                    if p.suffix == ".py":
                        tp = tmp_root / p.relative_to(root)
                        tp.parent.mkdir(parents=True, exist_ok=True)
                        tp.write_text(txt, encoding="utf-8")
                        tmp_paths.append((p, tp))
                (tmp_root / "pyproject.toml").write_text(render_pyproject(mf), encoding="utf-8")
                msg = ruff_format([tp for _, tp in tmp_paths], tmp_root)
                if msg:
                    print(f"WARN  {msg}")
                for p, tp in tmp_paths:
                    plan.write[p] = tp.read_text(encoding="utf-8")
        elif not a.no_format:
            print("WARN  ruff not found: generated Python was not formatted.")

    res = apply(plan, root, a.dry_run, a.force)
    verb = "would be" if a.dry_run else "were"
    for k, v in res.items():
        if v and k != "unchanged":
            print(f"{k} ({len(v)}): {', '.join(v)}")
    stale = []
    if full:
        known = {p.relative_to(root).as_posix() for p in plan.write}
        for sub in ("src", "tests"):
            for f in (root / sub).rglob("*.py") if (root / sub).is_dir() else []:
                if f.relative_to(root).as_posix() not in known and "__pycache__" not in f.parts:
                    stale.append(f.relative_to(root).as_posix())
    if stale:
        print(f"not in manifest ({len(stale)}; delete or add to skeleton.toml): "
              f"{', '.join(sorted(stale))}")
    print(f"\n{sum(len(v) for v in res.values())} files: {len(res['created'])} created, "
          f"{len(res['updated'])} updated, {len(res['unchanged'])} unchanged "
          f"({verb} written to {root}). Modules: {mf.total}; specs: {len(mf.specs)}; "
          f"open questions: {len(mf.questions)}.")
    if a.plan:
        print("Checkpoint: show the user BUILD_ORDER.md's Sequence table and wait for "
              "approval before writing items.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
