# Go Standards Reference

## Baseline

- **Go 1.27** (released August 2026). Check https://go.dev/doc/devel/release for the current version.
- `go.mod`: `go 1.27`. Add a `toolchain` line only if the repo already uses one.

## Standards the skeleton must meet

| Standard | What it governs |
|---|---|
| Effective Go + Go Code Review Comments | Naming (`MixedCaps`, short package names, no `Get` prefix, initialisms like `ID`/`URL`), error handling, interface placement (define interfaces where they are consumed). |
| Go Doc Comments (go.dev/doc/comment) | Every package has a package comment beginning "Package <name>". Every exported identifier has a doc comment beginning with its own name. Lists are indented. |
| gofmt / goimports | Formatting and import grouping (stdlib, a blank line, then everything else). |
| go vet + staticcheck | Static checks. `golangci-lint` v2 if the repo already uses it. |
| Module layout | `cmd/<app>/main.go` for binaries and `internal/<pkg>/` for private packages. Use `pkg/` only if the PRD requires a public library API. |

## The unit of build order is the package

All files in a Go package share one scope, so the build order and the "Depends on" lists are kept **per package**. Each package has a `doc.go` that carries the file-level docstring content. The other files in that package get a short header comment, a summary plus "See doc.go for build order and dependencies", followed by their own `Spec coverage:` line.

Placement details:
- A single-file package (typically `cmd/<app>/main.go`) puts the full header on that file; there is no `doc.go`.
- In the other non-doc files, separate the short header from the `package` clause with a blank line. Otherwise it becomes a second package doc comment.
- Test files put their header comment directly above `package`.

The Go compiler rejects import cycles between packages, so the design must be acyclic from the start.

## Docstring mapping

```go
// Package canonical canonicalizes raw indicator values into one spelling per value.
//
// Problem: ... (Full statement: BUILD_ORDER.md, "The problem".)
//
// Piece of the problem: C2 Sameness. ...
//
// Why this comes now: ...
//
// Build order: Step 4 of 11.
// Previous: internal/models (step 3), which defines Indicator.
// Next: internal/ingest/schema (step 5), which describes the source formats.
//
// Build these in order:
//  1. digitsOnly: the smallest rule; reused by account, card, and phone.
//  2. Canonicalize: the public rule; combines the per-kind rules.
//
// Depends on:
//   - internal/errs: ErrBadIndicator. Returned for every rejected value.
//   - internal/models: Indicator, MaxValueChars.
//   - Standard library: net/netip, regexp, strings, unicode.
//   - Third-party: golang.org/x/net/idna.
//
// Depended on by:
//   - internal/ingest: canonicalizes every extracted field.
//
// Spec coverage: S8.1, S8.2 | Traces to: I3, D27
package canonical
```

Functions (the comment starts with the identifier's name, per Go convention):

```go
// Canonicalize returns the canonical Indicator for a raw value of a kind.
//
// Problem piece: ...
//
// Why it matters: ...
//
// What: ...
//
// Spec: S8.1 | Ticket: — | Traces to: I3
//
// Errors: returns ErrBadIndicator for any input the rules below refuse.
//
// Build steps:
//  1. Task: ...
//     Think about: ...
//     Expected outcome: ...
//  2. Task: ...
//     Expected outcome: ...
func Canonicalize(kind, value string) (models.Indicator, error) {
	panic("not implemented: S8.1 Canonicalize")
}
```

Unexported functions get the same comment, starting with their lowercase name.

## Stub idiom

- Function bodies contain only `panic("not implemented: <spec id> <Name>")`. That is a terminating statement, so it compiles whatever the return types are.
- Structs, interfaces, constants, and sentinel errors (`var ErrBadIndicator = errors.New("bad indicator")`) are complete.

## Imports needed only by future bodies

Go **refuses to compile** a file with unused imports, and there is no flag to turn that off. To keep every needed import present, anchor each import that only the future body will use with a blank-identifier reference at the end of the file:

```go
// SKELETON import anchors: delete each line once a function body uses that package.
var (
	_ = netip.ParseAddr
	_ = strings.ToLower
	_ = idna.Lookup
)
```

Use a real exported identifier from each package (one the implementation will plausibly call). Packages already used in signatures or struct fields do not need an anchor.

## Unused-code linters

staticcheck's U1000 (unused code) fires on stub helpers and fields until their callers are written. Disable it for the skeleton phase with a marked entry in `staticcheck.conf` (`checks = ["all", "-U1000"]  # SKELETON: re-enable when stubs are implemented`).

## Tests

`<file>_test.go` in the same package (white-box) unless the spec defines a public API worth black-box testing (`package canonical_test`).

```go
// TestCanonicalizeRejectsAccountSuffix checks that account numbers under 8 digits are refused.
//
// Spec: S8.1 | Traces to: D27
// Expected outcome: Canonicalize("account", "1234") returns ErrBadIndicator.
func TestCanonicalizeRejectsAccountSuffix(t *testing.T) {
	t.Skip("skeleton: S8.1 not implemented")
}
```

## Validation commands

```bash
python3 <skill-dir>/scripts/check_skeleton.py <root> --lang go
cd <root> && gofmt -l . && go vet ./... && go build ./... && go test ./...
```

Third-party modules need `go mod tidy` and network access. Keep `go 1.27` in `go.mod` even if the local Go is older: try `GOTOOLCHAIN=go1.27 go build ./...` first. If that cannot download, validate a scratch copy (with the directive lowered and any unreachable module swapped for a compile-only stub through a scratch `go.work`), and report which checks remain. Without network access, say which modules are still unresolved.
