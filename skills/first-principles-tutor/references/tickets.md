# Tickets

Adapted from the `planning-and-task-breakdown` skill in Addy Osmani's agent-skills (MIT license): https://github.com/addyosmani/agent-skills/tree/main/skills/planning-and-task-breakdown

If that skill is installed in this environment, use it for BUILD-mode planning (it writes `tasks/plan.md` and `tasks/todo.md`) and mirror each task into the vault as a ticket note. If it is not installed, use the formats below. They keep its core rules.

## Rules kept from the source skill

- **Small and verifiable.** Every ticket has explicit acceptance criteria and a way to check them.
- **Three-criteria limit.** If you cannot state acceptance in three or fewer bullets, split the ticket.
- **"And" in the title means two tickets.**
- **Vertical slices.** Deliver one complete thin path at a time, not one whole layer at a time.
- **Dependency order.** Foundations first. High-risk items early so failure shows up fast.
- **Checkpoints** every two or three tickets.
- **Sizes:** XS (one step), S, M, L. **XL means split it.**

## Vertical slicing for learning

Horizontal (bad): all definitions → all formulas → all code → finally how it fits.
Vertical (good): trace one request, one data point, or one example through the *whole* system at shallow depth first. Then deepen each principle along that path. The learner sees how the pieces connect from the first ticket.

## ID scheme

`T{principle}.{n}`. Example: `T03.2` is the second ticket for principle P03.

## BUILD-mode ticket

```markdown
---
type: ticket
mode: build
principle: "[[P03 - <name>]]"
status: todo        # todo | doing | done | skipped
size: S             # XS | S | M | L
depends_on: ["[[T03.1 - <name>]]"]
tags: [learning/<topic>, ticket]
---
# T03.2 - <Short title>

**Description:** One paragraph on what this ticket accomplishes.

**Connection to the whole:** How this piece serves the full project, and what breaks without it.

**Acceptance criteria:**
- [ ] <Specific, testable condition>
- [ ] <Specific, testable condition>

**Verification:**
- [ ] Tests pass: <command>
- [ ] Build succeeds: <command>
- [ ] Manual check: <what to look at>

**Learning check:** <One question the learner must answer after finishing, such as "Why does this fail if the input is unsorted?">

**Files likely touched:** `path/to/file`

> [!info] Depth limit
> <Only if applicable: what could not be covered and why>
```

## UNDERSTAND-mode ticket

```markdown
---
type: ticket
mode: understand
principle: "[[P03 - <name>]]"
status: todo
size: S
depends_on: []
tags: [learning/<topic>, ticket]
---
# T03.2 - <Short title>

**Objective:** The learner can <observable verb: explain | derive | compute | predict | diagnose | compare | apply> <what>.

**Connection to the whole:** How this piece of understanding serves the full subject.

**Acceptance criteria (evidence the learner produces):**
- [ ] <e.g., "Explains in own words why X causes Y">
- [ ] <e.g., "Correctly predicts the output when Z doubles">

**Verification (how the teacher checks):** translation test | worked problem | fault found | prediction test

**Prompt to start:** <The first question the teacher asks. The learner attempts before any explanation.>

> [!info] Depth limit
> <Only if applicable>
```

Avoid vague objective verbs such as "understand", "know", or "learn about". They cannot be checked.

## Checkpoint note

After every two or three tickets:

```markdown
## Checkpoint after T03.1 to T03.3
- [ ] Retrieval quiz: 3 questions, at least one from an earlier principle
- [ ] Learner links this principle to one other principle in their own words
- [ ] Misconceptions logged in [[_Progress]]
```
