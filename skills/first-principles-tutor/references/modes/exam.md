# /exam: Find the Learner's Ceiling

The goal is to find the exact level where the learner's understanding stops working, and to name why. A score alone is not useful; the point where it breaks is.

## When to use it

- The learner types `/exam`, or says "test me," "how good am I at this," or "find my level."
- After a principle or subject is marked mastered, to check that the mastery is real.
- Do not use it to teach. If the learner has not studied the topic yet, say so and offer Phase 0 instead.

## The difficulty ladder

Pick the topic scope first: one principle, a group of principles, or the whole subject. Then climb these levels. Fit each level to the topic.

| Level | What the question demands |
|---|---|
| 1 | Recall a fact or definition |
| 2 | Explain a fact in plain words |
| 3 | Apply it to a simple, typical case |
| 4 | Apply it to a case with a twist (one changed condition) |
| 5 | Predict what happens when an assumption from the ledger fails |
| 6 | Compare two approaches and name the trade-off |
| 7 | Find the fault in a flawed example |
| 8 | Handle an edge case or a mix of two principles |
| 9 | Design or change something to meet a new requirement |
| 10 | Transfer the principle to a different field and defend where it stops applying |

Start one level below the learner's last known level. For a new learner, start at Level 2.

## Rules

1. **One question per turn.** State its level, like "Level 4." Then stop and wait.
2. **Ask for confidence** (0 to 100%) before levels 5 and up. A wrong answer given with high confidence matters most.
3. **Correct answer:** Confirm in one line. Move up one level.
4. **Wrong or partly wrong answer:** Name the exact part that is wrong. Do not give the right answer yet. Ask one new question at the same level. Use a different case, not the same question in new words.
5. **Two misses at the same level** set the ceiling. The ceiling is the highest level passed.
6. **No hints during the exam.** The hint ladder is turned off. If the learner types `/hint` or `/tell`, end the exam and log the level where it ended.
7. **Do not grade generously.** "Close" is a miss when the missing part is the reasoning. Saying the right word for the wrong reason is a miss.
8. Stop at Level 10 if the learner passes it. Say that the ladder could not find a ceiling, and suggest `/transfer` drills on a harder field.

## Exit report

When the ceiling is found, give a short report:

- **Ceiling:** Level N passed, Level N+1 failed twice.
- **What broke:** the exact misconception or missing link, in one or two sentences. Point to the principle note it belongs to.
- **Both failed answers,** quoted briefly, with the reason each one failed.
- **Next step:** usually re-teaching that principle with a new example (SKILL.md Phase 4, step 2). If the same flaw has shown up before, suggest `/diagnose`.

Now give the correct answers to the two failed questions, then ask one check question that uses them.

## Logging

If a vault exists for this topic, add a row to `## Exam log` in `_Progress.md`. Add each miss to `## Misconceptions log` with the source `exam`. If no vault exists, include the report in the session summary and offer to start one.
