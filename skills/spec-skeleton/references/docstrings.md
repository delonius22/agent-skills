# Docstring Formats

The docstrings are a thinking aid, not a spec index. A developer reading them in build order should be able to answer four questions without opening a code-completion tool:

0. **What problem are we solving?** (the project's problem, restated in every file)
1. **Where do I start, and what comes next?** (the file chain and the function order inside each file)
2. **Why does this piece matter?** (first principles: which part of the problem it answers, and what breaks without it)
3. **How do I build it?** (conceptual steps that make the developer think, without giving them the code)

The examples are in Python. Each language reference shows how the same labels map onto its doc-comment syntax. Keep the labels and their order the same in every language, because the checker and human readers depend on them.

## Contents
1. The problem and its capabilities (BUILD_ORDER.md)
2. File-level docstring
3. Function-level docstring
4. Writing "Why it matters" from first principles
5. Writing build steps: calibrating difficulty
6. Depth tiers: full and helper
7. Classes, data types, and methods
8. Test stubs
9. Full worked example (start of project)

**With the renderer (Python):** you write only the prose fields in `skeleton.toml` (references/manifest.md). The labels, step numbers, pointers, dependency lists, spec coverage, and test stubs shown below are generated. Read this file for what the prose must say, not for layout you need to type.

---

## 1. The problem and its capabilities

Every docstring points back to one problem statement, so write that first, at the top of `BUILD_ORDER.md`:

```markdown
## The problem
Fraud analysts get records from a dozen sources and cannot see that two records describe
the same person, because the same email, phone, or account number arrives spelled many
different ways. They link records by hand, miss rings, and sometimes merge strangers.

### What must be true for it to be solved
- **C1 Shared vocabulary of failure**: every part of the system reports bad input the same way. (step 1)
- **C2 Sameness**: a single rule decides when two raw values are the same real-world value. (steps 3-4)
- **C3 Intake**: records from every source become the same internal shape. (steps 5-6)
- **C4 Linking**: records that share a canonical value are joined, and nothing else is. (step 7)
- **C5 Answering**: an analyst can ask "who is connected to X?" and get the linked set. (steps 8-11)
```

How to derive the capabilities: ask what has to exist, at minimum, for the PRD's goals to be met. Drop "how" words such as database, API, or class, and keep only the needs. Usually there are 3 to 7. Every module should serve at least one capability. A module that serves none is either missing a capability or does not belong. A capability that no module serves is a gap.

---

## 2. File-level docstring

```python
"""Canonicalize raw indicator values into one spelling per value.

Problem: Analysts cannot see that records describe the same person because
identical values arrive spelled differently. (Full statement: BUILD_ORDER.md,
"The problem".)

Piece of the problem: C2 Sameness. Before anything can be linked, the system
needs one rule for when two raw values are "the same value". This file owns
that rule for every indicator kind, and nothing else: it does not read files,
touch storage, or decide what to link.

Why this comes now: The data shapes from step 3 exist, so the output type is
known. The importers (step 6) and the linker (step 7) cannot be written or
tested until this rule exists, because their correctness is defined in terms
of it.

Build order: Step 4 of 11.
Previous: fraudgraph/models.py (step 3), which defines Indicator, the type this
    file returns.
Next: fraudgraph/ingest/schema.py (step 5), which describes the source formats
    whose values this file will canonicalize.

Build these in order:
    1. digits_only: the smallest rule; accounts, cards, and phones reuse it.
    2. passes_luhn: a self-contained check; only cards need it.
    3. canonicalize: the public rule; combines 1 and 2 with the per-kind rules.

Depends on:
    fraudgraph.errors: ValidationFailure. Raised for every rejected value.
    fraudgraph.models: Indicator, MAX_VALUE_CHARS. The return type and the
        length limit.
    Standard library: ipaddress, re.
    Third-party: none.

Depended on by:
    fraudgraph.ingest.parser: canonicalizes every extracted field.
    fraudgraph.graph.merge: relies on canonical values as merge keys.

Spec coverage: S8.1, S8.2 | Traces to: I3, D27
"""
```

What each label is for:

- **Summary line**: one sentence that ends in a period.
- **Problem**: the project's problem in one or two sentences, identical in every file, ending with the pointer to BUILD_ORDER.md. It repeats on purpose: whatever file a developer opens, the goal is in front of them.
- **Piece of the problem**: the capability ID (`C2`) and its name, what this file owns, and where its responsibility stops. Saying what the file does *not* do stops scope creep as well as confusion.
- **Why this comes now**: what earlier steps made this file possible, and what later steps are waiting on it. This is what makes the order feel natural rather than arbitrary.
- **Build order / Previous / Next**: `Step N of M`. `Previous` names the step N-1 file and `Next` names the step N+1 file, each with a short clause on how it relates to this one. Follow `Next` from step 1 and you walk the whole project. The first file writes `Previous: none. This is the start of the project.` The last file writes `Next: none. This is the final step; the project is complete when its tests pass.`
- **Build these in order**: every function and class in the file, in the order to build them, each with half a line on why it comes at that point. Smallest, most-reused pieces come first.
- **Depends on**: each project module, followed by the *specific* symbols used and what they are used for. Then the standard library and third-party packages, writing `none` when there are none.
- **Depended on by**: each consumer and what it uses this file for. The entry point writes `nothing in this project; this is the entry point.`
- **Spec coverage**: every spec ID any function here answers, plus the PRD traces.

**The start of the project** writes:

```
Depends on:
    Nothing in this project. This module is the start of the project.
    Build it first.
    Standard library: none.
    Third-party: none.
```

**Foundation roots** are other modules that also import nothing from the project but are not first. They write:

```
Depends on:
    Nothing in this project (foundation root). Placed at step N because <reason>.
```

**Package marker files** (`__init__.py`, `mod.rs`, `index.ts`, Go `doc.go`) get the same docstring at package scope. They share the step number of the package's first module (`Build order: Step 3 of 11 (package marker; shares step with tally.core.money)`). Their `Previous`/`Next` match that module's.

**Entry modules whose behaviour is module-level glue** (a top-level `await main()` call, or an `if __name__ == "__main__":` guard) add a `Build steps:` block after `Spec coverage:`.

---

## 3. Function-level docstring

```python
def canonicalize(kind: str, value: str) -> Indicator:
    """Return the canonical Indicator for a raw value of a kind.

    Problem piece: C2 Sameness, for a single value. This is the one place the
    system decides that "Foo@X.com" and "foo@x.com" are the same email, and
    that the account suffix "4421" is not the same as account "99014421".

    Why it matters: The goal is to link records that describe the same real
    thing. Linking works by comparing values for exact equality, so equality
    has to mean "same real-world thing". Raw data breaks that in two
    directions. One value can be spelled many ways, which hides real links.
    Partial values look like full ones, which creates false links. Both
    failures are invisible downstream, because the linker just sees equal or
    unequal strings. So every link the system ever makes is only as correct as
    this function. That is why it refuses doubtful values outright (D27): a
    missed link can be recovered later, but a false merge corrupts every
    answer built on it.

    What: Takes a kind label (optionally qualified, e.g. "account@bank_a")
    and a raw value exactly as a source supplied it. Returns the one Indicator
    that stands for that value everywhere in the system. Refuses input that
    is malformed, or that cannot be a genuine instance of its kind.

    Spec: S8.1 | Ticket: — | Traces to: I3

    Args:
        kind: Indicator kind, optionally qualified with "@<namespace>".
        value: Raw value exactly as extracted from the source.

    Returns:
        The canonical Indicator for this value.

    Raises:
        ValidationFailure: With message "bad indicator" for any refused input.

    Build steps:
    1. Task: Decide whether the input deserves processing at all. The value,
       after trimming surrounding whitespace, must be non-empty and no longer
       than MAX_VALUE_CHARS. The kind must fully match the spec's grammar
       `[a-z_]{1,40}(@[a-z0-9_.-]{1,40})?`.
       Think about: Why check size and shape before normalizing? What would a
       multi-megabyte "email" cost you if you transformed it first?
       Expected outcome: Malformed input raises ValidationFailure("bad
       indicator") before any normalization runs.
    2. Task: Work out which normalization rules apply. The rules depend only
       on the base kind, the part before any "@"; the namespace is kept but
       never changes the rule.
       Think about: Why would "account@bank_a" and "account@bank_b" need the
       same rule but stay different kinds?
       Expected outcome: Qualified and unqualified kinds of the same base
       follow identical rules.
    3. Task: Reduce the value to one canonical spelling for its base kind. IP:
       its shortest standard form, with an IPv4 address embedded in IPv6
       collapsed to plain IPv4. Email: lowercase. Domain: lowercase, no
       trailing dot, in its ASCII (IDNA) form. Account and card: digits only.
       Phone: digits only, keeping a leading "+". Anything else: unchanged.
       Think about: For each kind, which differences are cosmetic and which
       carry meaning? Why does a phone keep its "+" when an account loses its
       dashes?
       Expected outcome: Every cosmetic variant of a value produces exactly the
       same canonical string.
    4. Task: Refuse canonical values that cannot be genuine (D27): an email
       that is not a whole valid address; a domain the IDNA conversion
       rejects; an account under 8 digits; a card outside 12-19 digits or
       failing the Luhn check; a phone under 7 digits; anything empty.
       Think about: Why must these checks run on the canonical value rather
       than the raw one?
       Expected outcome: Each listed case raises ValidationFailure("bad
       indicator"); a valid value of every kind passes.
    5. Task: Return the Indicator built from the original kind and the
       canonical value.
       Expected outcome: Two accounts that share a suffix never compare equal,
       because the key is the full number (HANDOFF §4).
    """
    raise NotImplementedError("S8.1: canonicalize")
```

Order and labels (fixed):

1. Summary line: what it returns or does, in one sentence.
2. `Problem piece:` the capability ID and the exact sliver of it this function answers, made concrete with a domain example where one helps.
3. `Why it matters:` first-principles reasoning (see §4). Several sentences.
4. `What:` the contract: inputs, output, and what it refuses. Someone reading only this paragraph knows how to call it.
5. `Spec: <ids> | Ticket: <id or —> | Traces to: <PRD ids or —>`
6. The language's standard parameter, return, and error sections (Google style in Python).
7. `Build steps:` numbered. Each step has `Task:`, an optional `Think about:`, and `Expected outcome:`.

---

## 4. Writing "Why it matters" from first principles

"Because the spec says so" is not a reason. Reason up from the need:

1. **Start from the goal** of the capability this function serves, in plain terms.
2. **Name the constraint** that makes this function necessary: the fact about the world, the data, or the rest of the system that the goal runs into.
3. **Say what goes wrong without it**, or if it is done badly. Be specific about who sees the failure and how.
4. **Explain why it lives here**, rather than earlier, later, or inline in its caller.

The `canonicalize` example walks those four moves: linking is the goal; equality is the constraint; hidden and false links are the failures; and "every link is only as correct as this function" is the reason it lives at the start.

Test your paragraph by deleting the function in your head. If the Why paragraph does not already describe what would break, rewrite it.

---

## 5. Writing build steps: calibrating difficulty

The steps should leave the developer thinking, but never stuck. A developer who is stuck turns autocomplete on. A developer handed the code does not learn anything. Aim between the two.

**The same step, three ways:**

| Level | Example | Problem |
|---|---|---|
| Too vague | Task: Validate the input. Expected outcome: Input is valid. | No rules and no checkable outcome. The developer has nothing to reason from, so they go and look for code. |
| Too much | Task: `v = value.strip()`; if `len(v) == 0 or len(v) > MAX_VALUE_CHARS: raise ValidationFailure(...)` | This is the code written in English. Nothing is left to think about. |
| Just right | Task: Decide whether the input deserves processing at all: trimmed value non-empty and at most MAX_VALUE_CHARS; kind fully matches the spec grammar. Think about: why check before normalizing? Expected outcome: malformed input raises ValidationFailure("bad indicator") before any normalization runs. | The goal, the rules, the one decision that matters, and a way to know you are done. |

**Rules for each part:**

- **Task**: one goal in domain language, plus every *fact* the developer cannot work out alone: limits, formats, grammars the spec states, error messages, external protocol rules, and named algorithms the spec requires (Luhn, HMAC-SHA256, RFC 3339). Facts are not code, so give them all. Never give the technique: no library calls, expressions, variable names, pseudo-code, loop shapes, or data structures the spec does not require.
- **Think about** (optional, at most one per step): a *question* that points at the decision that matters, such as an ordering choice, an edge case, an invariant, or a failure mode. Never answer it, and never name an API or data structure in it. Leave it out when the step is obvious; a question on every trivial step is noise.
- **Expected outcome**: something a test can check. "Works correctly" does not count; "returns `[]` for an empty file" does. The skipped test stubs are written from these.

**Size**: each step should be one sitting of focused thought, roughly 5 to 20 lines of code once written. Split any step with two separate outcomes, and merge trivial ones. Most functions need 2 to 6 steps.

**Order**: write the steps in the order a careful developer would do them, which is not always the order the spec lists rules. A common pattern: reject bad input, then work out the cases, then transform, then check the result, then return.

**Open questions**: where the spec is silent, the step becomes the open question (see SKILL.md step 6). Never fill the gap with a guess dressed up as a fact.

**Character set**: avoid unusual Unicode punctuation (en dashes, curly quotes), which several linters flag. Write "12-19" or "12 to 19". The em dash in `Ticket: —` is the only exception.

---

## 6. Depth tiers: full and helper

Not every function deserves the same docstring. Depth should follow how much the developer has to think, not a fixed template.

| Tier | Use it for | Why it matters | What | Args/Returns/Raises | Build steps |
|---|---|---|---|---|---|
| **Full** | Public functions, anything that owns a capability rule, anything with a real design decision | The four moves of §4, several sentences | The full contract | Yes | Usually 3 to 6 |
| **Helper** | Small internal pieces with one obvious job (a name check, a formatter) | One or two sentences: what breaks without it | One sentence | Only when it raises something callers must handle | 1 or 2 |

Every tier keeps every label (`Problem piece`, `Why it matters`, `What`, the `Spec` line, `Build steps`, `Task`, `Expected outcome`), because the checker and human readers rely on them. The checker only asks for a long Why on functions with 3 or more steps.

If a helper turns out to need a third step or a `Think about:`, it was not a helper. Promote it to full.

---

## 7. Classes, data types, and methods

- **Classes and data types**: a summary line, `Problem piece:`, `Why it matters:`, `What:`, the `Spec:` line, then `Attributes:`. A pure data class with fully declared fields has no build steps, because its declaration is the contract. Its Why paragraph still explains why this shape, and why these fields, are the right representation of the problem.
- **Classes with behaviour**: the same, plus build steps for any invariant the constructor must establish.
- **Methods**: the full function format.
- **Protocols / interfaces / traits**: Problem piece, Why it matters, and What describe the role. Each abstract method gets the full function format, with build steps written as obligations on implementers.
- **Constants**: the real value when the spec gives one, with a comment citing the spec ID. Otherwise use an open question.

---

## 8. Test stubs

Each test function's docstring has a summary line stating the behaviour, a `Spec:` line, and one `Expected outcome:` copied from (or sharpened from) the matching build step. Tests do not need Problem piece, Why it matters, or build steps.

```python
@pytest.mark.skip(reason="skeleton: S8.1 not implemented")
def test_canonicalize_rejects_account_suffix() -> None:
    """Account numbers under 8 digits are refused.

    Spec: S8.1 | Traces to: D27
    Expected outcome: canonicalize("account", "1234") raises
    ValidationFailure("bad indicator").
    """
```

---

## 9. Full worked example (start of project)

```python
"""Define the error types every other module raises.

Problem: Analysts cannot see that records describe the same person because
identical values arrive spelled differently. (Full statement: BUILD_ORDER.md,
"The problem".)

Piece of the problem: C1 Shared vocabulary of failure. Every later piece
either rejects bad data or reports a broken source, and the CLI must turn
each kind of failure into the right exit code and message (S11.2). This file
owns those failure categories and nothing else; it contains no logic.

Why this comes now: Nothing needs to exist before a failure can be named, and
almost everything after this raises or catches one of these errors. Writing
them first means no later module has to import another module's internals
just to catch its errors.

Build order: Step 1 of 11.
Previous: none. This is the start of the project.
Next: fraudgraph/config.py (step 2), which reports a bad config with the
    ConfigError defined here.

Build these in order:
    1. FraudgraphError: the base every other error inherits from.
    2. ValidationFailure, PayloadError, StorageError: one per failure
       category in the specs.

Depends on:
    Nothing in this project. This module is the start of the project.
    Build it first.
    Standard library: none.
    Third-party: none.

Depended on by:
    fraudgraph.models, fraudgraph.canonical, fraudgraph.ingest.parser,
    fraudgraph.store, fraudgraph.cli: raise or catch these errors.

Spec coverage: S2.4, S11.2 | Traces to: G4
"""
```
