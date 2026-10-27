# The Manifest: `skeleton.toml`

A complete, validated example (a 7-module Python CLI) is in `assets/example/`: `PRD.md`, `SPECS.md`, and the `skeleton.toml` built from them. Read it only if a field's use is unclear.

You write the judgment; `scripts/render_skeleton.py` writes everything else. The manifest lives at the project root and stays there as the source of truth: to change the skeleton, edit the manifest and re-render.

**Write only what needs thought.** Never write anything the renderer derives: step numbers, `Previous:`/`Next:`, `Depended on by:`, `Spec coverage:`, import lines for project modules, stub bodies, package markers (`__init__.py`), test stubs, `TRACEABILITY.md`, or tooling config. Writing them by hand wastes output and can only drift out of sync.

Use TOML multi-line strings (`"""..."""`) for prose. Line breaks inside prose do not matter; the renderer re-wraps everything to 88 columns. A blank line inside a string starts a new paragraph.

## `[project]`

| Key | Required | Meaning |
|---|---|---|
| `name` | yes | Distribution name. |
| `package` | Python | Import name (`src/<package>/`). |
| `language` | yes | `python` for a full render; anything else gets `--plan` / `--docs-only` only. |
| `python` | no | Target version, default `"3.14"`. |
| `description` | yes | One line from the PRD, for `pyproject.toml` and README. |
| `problem` | yes | 2 to 4 sentences for `BUILD_ORDER.md` (docstrings.md §1). |
| `problem_short` | yes | 1 to 2 sentences repeated in every file's `Problem:` line. |
| `toolchain_note` | yes | The baseline you chose, and why. |
| `spec_id_scheme` | yes | `verbatim`, or the derivation rule. |
| `cli` | no | Console-script name; requires a `<package>/__main__.py` module with `main()`. |
| `dependencies` | no | Third-party runtime packages the specs name. |
| `assumptions` | no | List of strings. |

## `[[capabilities]]`, `[[specs]]`, `[[questions]]`

```toml
[[capabilities]]
id = "C2"
name = "Sameness"
need = "a single rule decides when two raw values are the same real-world value"

[[specs]]
id = "S8.1"                       # every traceable clause, in document order
summary = "Canonicalize each indicator kind; refuse doubtful values."
traces = ["I3", "D27"]            # PRD IDs
# out_of_scope = "PRD non-goal N2"  # instead of citing it from code

[[questions]]
id = "OQ-1"
text = "Spec is silent on the maximum value length"
cites = ["S8.1"]                  # conflicting or silent clauses
```

## `[[modules]]` (array order = build order)

In `uses`, `symbols` is a comma-separated string (`"InternalError, InvalidInputError"`). Name a module by its dotted import name (Python: `fraudgraph.errors`) or by its `path`, with or without the extension (other languages: `src/errors.ts` or `src/errors`).

Step 1 must import nothing from the project. A module may only `use` modules that come earlier, except with `type_only = true`. The renderer refuses cycles and forward uses, so the build-order test is enforced for you.

```toml
[[modules]]
path = "fraudgraph/canonical.py"  # relative to src/
capability = ["C2"]
summary = "Canonicalize raw indicator values into one spelling per value."
owns = """What this file owns and where its responsibility stops."""
why_now = """What earlier steps made it possible; what later steps wait on it."""
root_reason = "..."               # only for foundation roots other than step 1
stdlib = ["import ipaddress", "import re"]   # verbatim import lines
third_party = []                  # verbatim import lines
uses = [
  { module = "fraudgraph.errors", symbols = "ValidationFailure", why = "raised for every rejected value" },
  { module = "fraudgraph.graph.merge", symbols = "MergePlan", why = "annotation only", type_only = true },
]
spec = []                         # module-level spec IDs, rarely needed
main_guard = false                # true for __main__.py: adds the __name__ guard
unlocks_note = ""                 # e.g. "satisfies Store in fraudgraph.service"
# [[modules.steps]] ...           # file-level Build steps, only for main_guard modules;
                                  # these document glue and produce no tests
```

For `--plan`, modules need no items. Add items after the user approves the plan.

## `[[modules.items]]` (array order = "Build these in order")

**Functions** (`def`/`async def`), using the docstrings.md field contents:

```toml
[[modules.items]]
name = "canonicalize"
signature = "def canonicalize(kind: str, value: str) -> Indicator"
order_note = "the public rule; combines 1 and 2"   # half a line for "Build these in order"
summary = "Return the canonical Indicator for a raw value of a kind."
piece = "C2 Sameness, for a single value. ..."     # must name a capability ID
why = """First-principles paragraph (docstrings.md §4)."""
what = """The contract."""
spec = ["S8.1"]
ticket = "—"                       # optional; never invent one
traces = ["I3"]                    # optional; PRD IDs for this item's Spec line (the file header collects them)
args = { kind = "...", value = "..." }   # optional; must match the signature exactly (omit self/cls)
returns = "..."                    # optional
raises = { ValidationFailure = "..." }   # optional

[[modules.items.steps]]
task = "Goal plus every fact the developer cannot work out alone"
think = "One question; optional"
outcome = "Something a test can check"
test = "rejects_oversize"          # optional test-name slug; default step<N>

[[modules.items.steps]]
open = "OQ-1"                      # an open-question step; no outcome, no test
task = "what is undecided"
```

Each non-open step becomes one skipped test, `test_<function>_<slug>`, in `tests/<subpath>/test_<module>.py`.

**Classes**: `signature = "class Indicator"` (with bases if any), optional `decorators`, `attributes = { field = "meaning" }`, and `body` (verbatim lines: dataclass fields or enum members). Methods go in `[[modules.items.methods]]` with the full function shape. In a class whose signature names `Protocol`, method bodies render as `...`.

**Constants and type aliases**: `kind = "const"`, `name`, `line` (the full statement: `MAX: Final[int] = 254` or `type Cents = int`), `comment` (the spec ID, or `OQ-n: spec silent`), and an optional `order_note`.

## Running it

```bash
python3 <skill-dir>/scripts/render_skeleton.py skeleton.toml --plan   # BUILD_ORDER.md only
python3 <skill-dir>/scripts/render_skeleton.py skeleton.toml          # everything (Python)
python3 <skill-dir>/scripts/render_skeleton.py skeleton.toml --docs-only  # other languages
```

The renderer validates the manifest first and writes nothing if it finds errors. It prints one line per problem. It writes only changed files and never overwrites a file edited by hand (tracked in `.skeleton.lock`), a file with implemented bodies, or an existing config file, unless you pass `--force`. It runs `ruff check --select I --fix` and `ruff format` on generated Python when ruff is installed. Use `--dry-run` to preview.
