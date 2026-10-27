# TypeScript Standards Reference

## Baseline

- **TypeScript 7.x** (the native, Go-based compiler, GA in July 2026). Check https://github.com/microsoft/TypeScript/releases for the current stable version.
- **Node.js: the current Active LTS.** Check https://nodejs.org/en/about/previous-releases. As of October 2026 that is Node 24; Node 26 enters LTS in late October 2026.
- ESM only: `"type": "module"` in `package.json`.

TS 6.0 deprecated old options and 7.0 removed them, so never emit `target: "es5"`, `moduleResolution: "node"`/`"node10"`, `baseUrl`-based path aliases, `outFile`, or AMD/UMD/System modules.

## Standards the skeleton must meet

| Standard | What it governs |
|---|---|
| `strict` tsconfig family | `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`. |
| `verbatimModuleSyntax` | Type-only imports must be written `import type { X }`. This also breaks most cycles at runtime. |
| `erasableSyntaxOnly` | No `enum`, `namespace`, or constructor parameter properties, so the code runs under Node's built-in type stripping. Use `as const` objects or string-literal unions instead of enums. |
| `module`/`moduleResolution: "nodenext"` | Relative imports carry the `.js` extension (`import { x } from "./canonical.js"`). |
| TSDoc | All doc comments are `/** ... */` using TSDoc tags (`@param`, `@returns`, `@throws`, `@packageDocumentation`). |
| Naming | `camelCase` functions and variables, `PascalCase` types and classes, `UPPER_SNAKE` constants, `kebab-case` file names. |
| Lint/format | ESLint flat config + typescript-eslint (strict-type-checked) and Prettier, **or** Biome. Use whichever the repo already has. Default: Biome (one tool). |

## Layout

```
<project>/
├── package.json
├── tsconfig.json
├── biome.json            # or eslint.config.js + .prettierrc
├── vitest.config.ts
├── README.md  BUILD_ORDER.md  TRACEABILITY.md  .gitignore
├── src/
│   ├── index.ts          # public API / entry point
│   └── <area>/<module>.ts
└── test/
    └── <area>/<module>.test.ts
```

## Docstring mapping

**File level**: a `/** ... @packageDocumentation */` comment at the very top of the file, before the imports, holding the same labelled blocks as `docstrings.md` §2 (summary, Problem:, Piece of the problem:, Why this comes now:, Build order:, Previous:, Next:, Build these in order:, Depends on:, Depended on by:, Spec coverage:).

**Function level**: TSDoc block tags absorb all the text that follows them, so put the labelled prose **before** the block tags:

```ts
/**
 * Return the canonical Indicator for a raw value of a kind.
 *
 * Problem piece: ...
 *
 * Why it matters: ...
 *
 * What: ...
 *
 * Spec: S8.1 | Ticket: — | Traces to: I3
 *
 * Build steps:
 * 1. Task: ...
 *    Think about: ...
 *    Expected outcome: ...
 *
 * @param kind - Indicator kind, optionally qualified with "@<namespace>".
 * @param value - Raw value exactly as extracted.
 * @returns The canonical Indicator.
 * @throws {@link ValidationFailure} "bad indicator" for refused input.
 */
export function canonicalize(kind: string, value: string): Indicator {
  throw new Error("Not implemented: S8.1 canonicalize");
}
```

## Stub idiom

- **Stateful components**: prefer factory functions that return an interface (`createRouteStore(): RouteStore`) over classes. A derived-class constructor cannot be a throw-only stub (it must call `super()`), and `erasableSyntaxOnly` rules out parameter properties. If the spec demands a class, declare its fields with initializers and leave the methods as stubs.

- Function bodies contain only `throw new Error("Not implemented: <spec id> <name>");`.
- Types, interfaces, and `as const` objects are complete: they are the contract.
- Classes declare all fields with types. Methods throw as above.

## Imports needed only by future bodies

TypeScript itself only complains about unused imports when `noUnusedLocals` is on. Turn it off for the skeleton, with a marker comment, and do the same for the linter:

```jsonc
// tsconfig.json
"noUnusedLocals": false,      // SKELETON: re-enable once all stubs are implemented
"noUnusedParameters": false,  // SKELETON
```

In Biome, set `linter.rules.correctness.noUnusedImports` and `noUnusedVariables` to `"off"` with the same comment. In ESLint, turn off `@typescript-eslint/no-unused-vars`.

Also turn off the auto-fix that converts imports to `import type` (Biome `style/useImportType`; ESLint `@typescript-eslint/consistent-type-imports`). In a stub, a value the future body needs may appear only in type positions, and the auto-fix would silently turn it into a type-only import. Do not run `--write`/`--fix` before turning it off.

## Cycles

ES modules tolerate some cycles, but initialization-order bugs follow. Fix the design first. A reference that is purely a type uses `import type`, which is erased and never forms a runtime cycle.

## Tooling (`package.json` excerpt)

```json
{
  "type": "module",
  "engines": { "node": ">=24" },
  "scripts": {
    "build": "tsc -p .",
    "typecheck": "tsc --noEmit",
    "lint": "biome check .",
    "test": "vitest run"
  },
  "devDependencies": {
    "typescript": "^7",
    "@types/node": "^24",
    "vitest": "latest",
    "@biomejs/biome": "latest"
  }
}
```

Write root-level tool configs as `.mjs` or `.json` (for example `vitest.config.mjs`, `biome.json`), so they stay out of the module graph. The checker also skips root `*.config.*` files.

Use two tsconfigs: `tsconfig.json` (build: `rootDir: "src"`) and `tsconfig.test.json` (extends it, `rootDir: "."`, includes `src` and `test`, `noEmit: true`). Chain both in `npm run typecheck`. `engines` follows the baseline, not the local machine.

Generate the Biome config with `npx @biomejs/biome init` (or match the installed version's schema) rather than copying keys, because Biome renames config keys between minor versions. Set `"types": ["node"]` in tsconfig so Node globals resolve.

`tsconfig.json`: `target: "es2024"`, `module: "nodenext"`, `moduleResolution: "nodenext"`, `rootDir: "src"`, `outDir: "dist"`, `declaration: true`, plus the strict flags above.

## Test stubs

```ts
/** Tests for src/canonical.ts (build step 4). Covers: S8.1, S8.2. */
import { describe, it } from "vitest";
import { canonicalize } from "../src/canonical.js";

describe("canonicalize", () => {
  /**
   * Account numbers under 8 digits are refused.
   * Spec: S8.1 | Traces to: D27
   * Expected outcome: canonicalize("account", "1234") throws ValidationFailure("bad indicator").
   */
  it.todo("rejects an account suffix");
});
```

## Validation commands

```bash
python3 <skill-dir>/scripts/check_skeleton.py <root> --lang typescript
npx tsc --noEmit -p <root>
npx biome check <root>       # or npx eslint <root>
npx vitest run --root <root> # all todo, none failing
```

If dependencies cannot be installed (no network), run whatever `tsc` is available for syntax only, and say in your report that full type checking still needs to be done.
