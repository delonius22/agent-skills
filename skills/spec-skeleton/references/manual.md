# Manual Path: Writing Files by Hand (TypeScript, Go, Rust, others)

The renderer fully generates Python only. For other languages, `render_skeleton.py --docs-only` still writes `BUILD_ORDER.md` and `TRACEABILITY.md` from `skeleton.toml`, and still validates the plan (cycles, forward uses, uncited specs). You write the source files, test stubs, and tooling config yourself, in build order, following these rules and the language reference.

Use the manifest as your script: copy each module's prose (`summary`, `owns`, `why_now`, item fields, steps) into the doc comments instead of composing it again. Do not re-decide anything the manifest already says. If you need to change it, change the manifest and re-run `--docs-only` so the docs stay in sync.

## Source files

- **Every file has a file-level doc comment** with: the one-line `Problem:`; `Piece of the problem:` (capability ID, what the file owns, where it stops); `Why this comes now:`; `Build order: Step N of M` with `Previous:` and `Next:` pointers; `Build these in order:`; `Depends on:` (each project module and exactly what is used from it); `Depended on by:`; and `Spec coverage:`. Take step numbers and neighbours from `BUILD_ORDER.md`'s Sequence table.
- **Every import the finished file will need is present now**, including project modules. Apply the language reference's rule for imports only a future body will use. Import only what the specs name or what nearly every implementation would need; never import a library just to hint at an approach.
- **Every function, method, and type has a doc comment** in the `docstrings.md` §3 format and the depth tier from §6.
- **Signatures and data shapes are complete.** Only bodies are empty, using the language's stub idiom, which always names the spec ID.
- **Package markers and entry modules** follow `docstrings.md` §2.
- **Open questions** are their own numbered step (SKILL.md, step 7).

## Supporting files

- **Test stubs**: one test file per source module, mirroring its path. One test per non-open build step's expected outcome, with a short doc comment citing its spec ID, marked skipped or todo using the language's idiom. No assertions.
- **Tooling config**: the manifest, linter, formatter, type checker, and test-runner config from the language reference, plus `.gitignore` and a README (purpose from the PRD, install, run tests, link to BUILD_ORDER.md).
- The generated `TRACEABILITY.md` leaves the Test(s) column as `—`. List each module's tests in its test file's header instead. Re-running `--docs-only` rewrites `TRACEABILITY.md`, so don't hand-edit it.

Validate with `check_skeleton.py --lang <lang> --quiet` and the language's own tools. Fix failures with targeted edits; never rewrite a whole file to fix one doc comment.
