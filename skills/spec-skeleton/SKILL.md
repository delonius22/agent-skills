---
name: spec-skeleton
description: Generate a standards-compliant project skeleton (folders, stub source files, tests, tooling config, build order, traceability matrix) from a PRD.md and SPECS.md, with docstrings written as a thinking aid that replaces code autocomplete. They state the problem being solved, chain every file to the next in human build order, explain from first principles why each function and class matters, and give conceptual build steps with no code. Use this whenever a developer supplies or points at a PRD, product requirements doc, spec, SPECS.md, design doc, or technical spec and wants a scaffold, skeleton, stubs, boilerplate, starter repo, project structure, or "set up the project" — in Python, TypeScript, Go, Rust, or another language — even if they never say the word "skeleton".
compatibility: Needs Python 3.11+ to run the bundled scripts (standard library only). ruff, mypy, and pytest (or the target language's tools) are optional but used for validation when present.
metadata:
  version: "2.0.0"
---

# Spec Skeleton

Turn a PRD.md and SPECS.md into a project skeleton that a developer can build from start to finish **without turning on code autocomplete**. The skeleton is a map, not an implementation: every file and function exists, every import is in place, and no function body contains logic.

The docstrings do the teaching. A developer who reads them in build order should always be able to answer four questions:

0. **What problem are we solving?** The problem is stated once in `BUILD_ORDER.md`, broken into the capabilities that must exist, and restated in every file.
1. **Where do I start, and what is next?** One file is the start of the project. Every file names its `Previous` and `Next`, and lists its own functions in the order to build them.
2. **Why does this piece matter?** Every function and class says which piece of the problem it answers and argues, from first principles, what would break without it.
3. **How do I build it?** Conceptual steps that state the goal, the facts needed, and the one decision worth thinking about, without the code.

What people usually lack is not syntax. It is knowing what to build next, why, and how to break it down, and that gap is what sends them to autocomplete. Close that gap and leave the typing to them. The steps should make the developer think, but never leave them stuck.

## How the work is split

**You write the judgment. A script writes everything mechanical.** All your decisions go into one manifest, `skeleton.toml`, at the project root: the problem, the capabilities, the spec index, the module plan, and the prose of each docstring. `scripts/render_skeleton.py` derives the rest: step numbers, `Previous`/`Next`, `Depends on`/`Depended on by`, import lines, stub bodies, package markers, test stubs, `BUILD_ORDER.md`, `TRACEABILITY.md`, and tooling config. Never type anything the renderer derives. That would only waste output and drift out of sync.

- **Python**: full render.
- **Other languages**: `--docs-only` renders `BUILD_ORDER.md` and `TRACEABILITY.md` and validates the plan. You write the source files by hand (`references/manual.md`).

## Inputs

- `PRD.md`: the product view (goals, users, requirements, invariants, non-goals).
- `SPECS.md`: the technical view (components, data formats, rules, interfaces).
- Optional: ticket IDs, an existing repo, a target language or version the user names.

Read both documents in full before designing anything. Do not skim; the build steps you write later must cite clauses you actually read.

If either file is missing, ask for it. If the language is not stated in either file or the request, ask; when nobody is there to answer, pick the language the specs most strongly imply, and record that choice under `assumptions`.

## Workflow

### 1. Resolve the standards baseline

Read the reference file for the target language. It lists the standards the skeleton must meet and a pinned baseline version:

| Language | Reference |
|---|---|
| Python | `references/python.md` |
| TypeScript / JavaScript | `references/typescript.md` |
| Go | `references/go.md` |
| Rust | `references/rust.md` |
| Anything else | `references/generic.md` |

"Latest standard" means the current stable toolchain and the official style guides for it, not every proposal ever filed. If you have web access, confirm the current stable version (the reference says where to check) and use it when it is newer than the pinned baseline and already released, not merely scheduled. If you cannot check, use the pinned baseline and say so in the report. Record the version and why in `toolchain_note`. If the user or specs name a version, that wins.

### 2. Index the specs; state the problem

Read `references/manifest.md` now; it defines every field you will write. Build the index before designing modules, so nothing gets lost and every ID you cite is real.

- **Spec IDs** (`[[specs]]`, in document order) come from SPECS.md. Use the document's own IDs verbatim (`S8.1`, `§4.2`, `REQ-12`). If its clauses carry bare numbers (`1.1`), prefix them with `S` (`S1.1`) so they cannot be confused with versions or PRD IDs. If it has none, derive stable IDs from heading numbers (`S3.2` for the second subsection of section 3), and if headings are unnumbered, number them in document order. Give each separately stated rule its own ID: a bullet, numbered item, or sentence that sets a requirement gets the next index under its heading. That way two runs over the same spec produce the same IDs. Record the rule in `spec_id_scheme`.
- **Traces** point at PRD requirement, goal, invariant, or decision IDs (`I3`, `G2`, `D27`), using the same derivation rule if the PRD has none (`P2.1`).
- **Tickets** come only from the user. Otherwise leave them out (they render as `—`). Never invent ticket numbers.

Then **state the problem and break it into capabilities** (`references/docstrings.md` §1): `problem`, `problem_short`, and 3 to 7 `[[capabilities]]`. A capability is a need, not a technology. Every module must serve at least one, and the renderer refuses a capability no module serves.

Note every gap, contradiction, or unstated decision as a `[[questions]]` entry. Do not resolve them silently by inventing behaviour.

### 3. Design the module graph and build order

Decide the modules, then order them the way an experienced engineer would actually build the system. This is often **not** the order the spec is written in. The test: could a developer implement this module right now, using only modules earlier in the order, and check that it works? The renderer enforces the mechanical half of this test: it refuses any `uses` of a later module (unless `type_only`) and any cycle.

Default tiers, from first to last:

1. **Foundations**: errors/exceptions, constants, configuration shape. These depend on nothing in the project. The first one is "the start of the project".
2. **Data contracts**: domain types, models, schemas, enums. You must know what the data is before you can validate, parse, or store it.
3. **Pure core logic**: validation, normalization, calculation, and rules that work only on the data contracts, with no I/O.
4. **Boundary adapters**: parsers, loaders, serializers, storage, external API clients. These come *after* the contracts and validation they produce or consume.
5. **Orchestration**: services and pipelines that combine core logic with adapters.
6. **Interfaces**: CLI, HTTP handlers, jobs, and the entry point.

Within a tier, put first whatever unlocks the earliest end-to-end check (a thin vertical slice beats a finished layer nobody can run). Within a file, order items the same way: helpers before the functions that call them.

Other foundation modules that import nothing from the project get a `root_reason`. Record "satisfies <interface> in <module>" relationships in `unlocks_note`. Where the language defines interfaces next to their consumer (Go), the implementer can come first. If two modules need each other, the design is wrong: move the shared piece into a lower module.

Write the `[[modules]]` entries (path, capability, summary, owns, why_now, imports, uses), with no items yet.

### 4. Checkpoint: get the plan approved

```bash
python3 <skill-dir>/scripts/render_skeleton.py skeleton.toml --plan
```

This validates the plan and writes `BUILD_ORDER.md`. Show the user its Sequence table and open questions, and **wait for approval** before writing any items. A wrong module graph is the most expensive mistake this skill can make, because every file built on it must be redone; approving one table is cheap. When nobody is there to answer, continue and note in the report that the plan was not reviewed.

### 5. Write the items, module by module, in build order

Add `[[modules.items]]` for every function, class, and constant, following `references/docstrings.md`. Read it before the first item: §3 to §5 say what each prose field must contain, and §6 says how deep to go.

- **Depth follows thought, not a template** (§6). Public functions and anything that owns a rule get the full treatment. Small helpers get a one- or two-sentence Why, a one-sentence What, and one or two steps. Every tier keeps every label.
- **`Why it matters` is first principles** (§4): the goal, the constraint that makes this piece necessary, what breaks without it, and why it lives here.
- **Build steps are conceptual and calibrated** (§5). `task` holds the goal plus every fact the developer cannot work out alone (limits, formats, spec grammars, error messages, named algorithms). `think` is at most one question, never answered. `outcome` is something a test can check. Never give the technique: no library calls, expressions, pseudo-code, loop shapes, or unrequired data structures. Each non-open step becomes a skipped test, so give it a short `test` slug.
- **Signatures and data shapes are complete.** Parameter types, return types, and field types are contracts; write them in full. If you give `args`, they must match the signature exactly (the renderer checks).
- **Imports**: list every import the finished file will need (`stdlib`, `third_party`, `uses`). Import only what the specs name or what nearly every implementation would need. Never import a library just to hint at an approach.
- **Never invent requirements.** A rule the specs do not give becomes an open question (step 7).

### 6. Render

```bash
python3 <skill-dir>/scripts/render_skeleton.py skeleton.toml          # Python
python3 <skill-dir>/scripts/render_skeleton.py skeleton.toml --docs-only   # other languages
```

The renderer validates the whole manifest first and writes nothing if it finds an error. Each error is one line naming the module and item; fix the manifest and re-run. For other languages, now write the source files by hand from the manifest (`references/manual.md`).

Re-rendering is cheap and safe. It writes only changed files, and it never overwrites a file someone edited by hand (tracked in `.skeleton.lock`), a file with implemented bodies, or an existing config file, unless `--force` is passed. Deliver `skeleton.toml` and `.skeleton.lock` with the project, so the skeleton can be re-rendered when the specs change.

### 7. Open questions

Where the specs are silent or contradict each other, add a step with `open = "OQ-<n>"` and a `task` naming what is undecided. It renders as:

```
N. Task: Open question (spec silent): <what is undecided>.
   Expected outcome: Resolve with the spec owner before implementing; logged as OQ-<n> in BUILD_ORDER.md.
```

An open question is always its own step; never fold it into a step that also has a real outcome. Define it in `[[questions]]` with `cites` listing both clauses if they contradict each other.

### 8. Validate before you report

```bash
python3 <skill-dir>/scripts/check_skeleton.py <project-root> --lang <python|typescript|go|rust|generic> --quiet
```

The checker confirms that every file and function has the required doc sections, that bodies are stubs only, that cited spec IDs match `TRACEABILITY.md`, that no Python file uses `from __future__`, and (for Python) that every module imports cleanly. `--quiet` prints errors only, grouped by file. Then run the language's own checks from its reference (`ruff check`, `ruff format --check`, `mypy`, `pytest`, `tsc --noEmit`, `go vet ./...`, `cargo check`) if they are installed.

**Fix in the manifest, then re-render. Never hand-edit generated files and never regenerate a file by hand to fix one docstring.** For hand-written languages, fix with targeted edits. Do not hand over a skeleton that fails its own checks.

**When the local toolchain is older than the target, or there is no network access**, keep the target version in the manifests anyway. The manifests are the deliverable, and the user's machine is the real target. Validate as far as you can without changing the deliverable: run the tools under the target interpreter if you can install it (for example `uv python install`, or `GOTOOLCHAIN=go1.27`), or validate a scratch copy whose version line is lowered. Then list in your report exactly which checks still need to run. Never lower the version in the delivered files just to make a local check pass.

### 9. Report

Tell the user, briefly: where the skeleton is, the toolchain baseline you chose, the number of modules and spec IDs covered, whether the plan was approved at the checkpoint, and the open questions they need to resolve. Mention that editing `skeleton.toml` and re-rendering updates the skeleton safely. Do not paste the files into the chat.
