# Rust Standards Reference

## Baseline

- **Stable Rust 1.98, edition 2024.** Check https://releases.rs/ for the current stable version.
- `Cargo.toml`: `edition = "2024"`, `rust-version = "<chosen stable>"`.

## Standards the skeleton must meet

| Standard | What it governs |
|---|---|
| Rust API Guidelines | Naming (`snake_case` items, `UpperCamelCase` types, `SCREAMING_SNAKE` consts), conversion method names (`as_`/`to_`/`into_`), error types that implement `std::error::Error`, `# Errors`/`# Panics` doc sections. |
| rustdoc conventions | `//!` module docs at the top of every file, `///` docs on every item, a summary sentence first. |
| rustfmt | Formatting (defaults). |
| clippy | `cargo clippy --all-targets -- -D warnings`, with the skeleton allowances below. |
| Edition 2024 | Use the 2024 rules for `unsafe extern`, RPIT lifetime capture, and `gen` as a reserved keyword. Avoid naming anything `gen`. |

## Layout

```
<project>/
├── Cargo.toml
├── README.md  BUILD_ORDER.md  TRACEABILITY.md  .gitignore
├── src/
│   ├── lib.rs            # crate docs, module declarations, skeleton lint allowances
│   ├── main.rs           # only if the PRD describes a binary; thin, calls into lib
│   └── <module>.rs or <module>/mod.rs
└── tests/                # integration tests only if the spec defines a public API
```

Use `<module>.rs` with a `<module>/` directory for its submodules (the modern style), not `mod.rs`, unless the repo already uses `mod.rs`.

## Docstring mapping

File level: `//!` lines at the top of each module file, holding the `docstrings.md` §2 labelled blocks.

Function level:

```rust
/// Return the canonical Indicator for a raw value of a kind.
///
/// Problem piece: ...
///
/// Why it matters: ...
///
/// What: ...
///
/// Spec: S8.1 | Ticket: — | Traces to: I3
///
/// # Errors
///
/// Returns [`Error::BadIndicator`] for any input the rules below refuse.
///
/// # Build steps
///
/// 1. Task: ...
///    Think about: ...
///    Expected outcome: ...
pub fn canonicalize(kind: &str, value: &str) -> Result<Indicator, Error> {
    todo!("S8.1: canonicalize")
}
```

## Stub idiom

- Function bodies contain only `todo!("<spec id>: <name>")`.
- Structs, enums, traits, and consts are complete. Derive `Debug`, `Clone`, `PartialEq`, and `Eq` where the spec implies value semantics.
- Error type: one `Error` enum per crate (or per major module), with one variant per failure category in the specs. Use `thiserror` for the `Display`/`Error` impls. It is the ecosystem default, so add it, note it under "Assumptions" in BUILD_ORDER.md, and list it in the "Third-party" line.

## Imports, parameters, and dead code in a skeleton

Unused imports, unused parameters, and never-called functions are warnings in Rust, not errors, but `-D warnings` turns them into errors. Put one marked allowance at the top of `lib.rs` (and `main.rs`):

```rust
// SKELETON: remove once every todo!() is implemented.
#![allow(unused_imports, unused_variables, dead_code)]
```

Inside a crate, module `use` cycles compile. The build order still follows the tier rules, so that each module can be implemented and tested using only earlier ones.

## Tests

Unit tests go in a `#[cfg(test)] mod tests` block at the bottom of each module file (idiomatic, and it can reach private items):

```rust
#[cfg(test)]
mod tests {
    use super::*;

    /// Account numbers under 8 digits are refused.
    ///
    /// Spec: S8.1 | Traces to: D27
    /// Expected outcome: `canonicalize("account", "1234")` returns `Err(Error::BadIndicator)`.
    #[test]
    #[ignore = "skeleton: S8.1 not implemented"]
    fn rejects_account_suffix() {
        todo!()
    }
}
```

## Validation commands

```bash
python3 <skill-dir>/scripts/check_skeleton.py <root> --lang rust
cd <root> && cargo fmt --check && cargo check --all-targets && cargo clippy --all-targets -- -D warnings && cargo test
```

`cargo check` needs network access the first time, to fetch crates. Without network access, report that the dependencies are still unresolved.
