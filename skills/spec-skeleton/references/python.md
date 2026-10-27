# Python Standards Reference

## Baseline

- **Target: the latest stable CPython that the toolchain supports.** Pinned baseline: **Python 3.14** (stable since 2025-10-07). Python 3.15.0 shipped on 2026-10-09. Target 3.15 only when ruff and mypy both accept `py315`/`3.15` without a preview or "under development" warning (ruff 0.16.x still warns); otherwise stay on 3.14 and record why in `toolchain_note`. Check https://devguide.python.org/versions/ for "bugfix" status. Make sure any interpreter you install for validation is a final release (`python -V` shows no `a`, `b`, or `rc`). Never target a prerelease unless the user asks.
- Set `requires-python = ">=3.14"` (or the chosen version) in `pyproject.toml`.

## Standards the skeleton must meet

| Standard | What it governs in the skeleton |
|---|---|
| PEP 8 | Naming (`snake_case` functions/modules, `PascalCase` classes, `UPPER_CASE` constants), 4-space indent, import grouping, line length (use ruff's 88 default unless the repo says otherwise). |
| PEP 257 | Docstring placement, a summary line, and a blank line after it. The section layout comes from `docstrings.md`; parameter sections use **Google style**. |
| PEP 484 / 526 | Full type hints on every parameter, return value, and module-level constant. |
| PEP 585 / 604 | Built-in generics (`list[str]`, `dict[str, int]`) and `X \| None`. Never `typing.List` or `Optional`. |
| PEP 695 / 696 | `class Repo[T]:`, `def first[T](xs: list[T]) -> T:`, and `type Alias = ...`. Never `TypeVar` boilerplate. |
| PEP 649 / 749 | Annotations are evaluated lazily (3.14+). Forward references and type-only imports work **without** `from __future__ import annotations`. |
| PEP 621 / 517 / 518 | All project metadata and tool config live in `pyproject.toml`. No `setup.py` or `setup.cfg`. |
| PEP 735 | Dev tools (ruff, mypy, pytest) go in `[dependency-groups]`, not in runtime dependencies. |
| PEP 561 | Add an empty `py.typed` marker to the package. |

## Hard rules

- **Never write `from __future__ import ...`**, of any kind. On 3.14+ it is unnecessary: lazy annotations already cover the only reason a skeleton would use it.
- **Absolute imports only** (`from fraudgraph.models import Indicator`), grouped and ordered stdlib → third-party → first-party, one blank line between groups (ruff `I` rules enforce this). No wildcard imports.
- **Import specific names** that the file uses (`from pkg.errors import ValidationFailure`). Prefer this to `import pkg.errors` so the "Depends on" list in the docstring matches the import lines exactly.

## Layout (src layout)

```
<project>/
├── pyproject.toml
├── README.md
├── BUILD_ORDER.md
├── TRACEABILITY.md
├── .gitignore
├── src/
│   └── <package>/
│       ├── __init__.py        # package docstring; re-exports only if the spec defines a public API
│       ├── __main__.py        # entry point if the PRD describes a CLI/app
│       ├── py.typed
│       └── <subpackage>/...
└── tests/
    ├── conftest.py            # only if shared fixtures are named in specs
    └── <subpackage path>/test_<module>.py   # src/pkg/ingest/parser.py -> tests/ingest/test_parser.py
```

The src layout prevents tests from importing the working tree by accident, so the package must be installed (`pip install -e .` or `uv sync`) before the tests run.

## Stub idiom

```python
def canonicalize(kind: str, value: str) -> Indicator:
    """...full docstring..."""
    raise NotImplementedError("S8.1: canonicalize")
```

- Function and method bodies contain the docstring plus a single `raise NotImplementedError("<spec id>: <name>")`. Nothing else.
- **Data classes** are complete: declare every field with its type and default (`@dataclass(frozen=True, slots=True)` when the spec implies immutability). The fields are the contract.
- **Enums** are complete when the spec lists the members.
- **Protocols** (`typing.Protocol`) for any interface the spec describes with more than one implementation. Write the body as `...`, which is idiomatic for protocol members.
- **Constants** get their real value when the spec gives one. Otherwise raise an open question and leave a clearly marked placeholder: `MAX_VALUE_CHARS: Final[int] = 0  # OQ-3: spec silent on limit`.

## Imports needed only by future bodies

The skeleton includes every import the finished file will need. Imports used in signatures or data classes are "used" already. Imports that only a future function body needs (for example `ipaddress` in `canonical.py`) are flagged by ruff as F401 (unused import). Do **not** delete them, and do **not** scatter `# noqa`. Instead, add one commented, temporary ignore to `pyproject.toml`:

```toml
[tool.ruff.lint.per-file-ignores]
# SKELETON: imports are pre-declared for bodies not yet written.
# Remove this entry once every NotImplementedError is gone.
"src/**/*.py" = ["F401"]
"tests/**/*.py" = ["F401"]
```

## Circular imports

A runtime import cycle crashes the skeleton the moment anything imports it, so the checker imports every module to catch this.

1. **First fix the design.** A cycle means a shared concept lives in the wrong module. Move it down (usually into `models` or a new `types` module) and update the build order.
2. **Only if the reference is type-only** (module A needs B's class purely for annotations, and B imports A at runtime), guard it:

   ```python
   from typing import TYPE_CHECKING

   if TYPE_CHECKING:
       from fraudgraph.graph.merge import MergePlan
   ```

   On 3.14+, annotations that use `MergePlan` work without `__future__`, because they are not evaluated at definition time. Mention the guard in the file docstring's "Depends on" line ("type-only").

## Tooling config (`pyproject.toml`)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "<project>"
version = "0.1.0"
description = "<one line from PRD>"
readme = "README.md"
requires-python = ">=3.14"
dependencies = [
    # runtime deps named or clearly implied by SPECS.md, unpinned upper bound
]

[project.scripts]
# "<cli-name>" = "<package>.__main__:main"   # if the PRD describes a CLI

[dependency-groups]
dev = ["ruff", "mypy", "pytest"]

[tool.ruff]
line-length = 88
target-version = "py314"
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
python_version = "3.14"
strict = true
mypy_path = "src"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
```

Only add third-party dependencies that the specs name or clearly require (for example an HTTP client when S6 describes calling a REST API). Each one must also appear in the "Third-party" line of every file docstring that imports it.

## Test stubs

```python
"""Tests for fraudgraph.canonical (build step 4).

Covers: S8.1, S8.2. Each test guards one expected outcome from the build
steps in src/fraudgraph/canonical.py.
"""

import pytest

from fraudgraph.canonical import canonicalize
from fraudgraph.errors import ValidationFailure


@pytest.mark.skip(reason="skeleton: S8.1 not implemented")
def test_canonicalize_rejects_account_suffix() -> None:
    """...see docstrings.md §8..."""
```

## Validation commands

```bash
python3 <skill-dir>/scripts/check_skeleton.py <root> --lang python
ruff check <root> && ruff format --check <root>
mypy <root>/src           # stubs type-check because NotImplementedError is NoReturn
pytest <root> -q          # all tests collected and skipped, none erroring
```

**Run every tool under the target interpreter**, not only the checker. A mypy or pytest installed for an older Python cannot parse PEP 695 syntax. The simplest way:

```bash
uv run --no-project --python 3.14 --with mypy -- mypy <root>/src
uv run --no-project --python 3.14 --with pytest -- pytest <root> -q   # pyproject sets pythonpath
```

`__main__.py` keeps its one-line guard (`if __name__ == "__main__": raise SystemExit(main())`). It is glue, not a function body.

If the local interpreter is older than the target (for example, 3.11 when targeting 3.14), PEP 695 syntax will not parse and the checker's import test cannot run. Install the target interpreter (`uv python install 3.14`) and pass `--python <path>` to the checker. Do not downgrade the code to suit the old interpreter.
