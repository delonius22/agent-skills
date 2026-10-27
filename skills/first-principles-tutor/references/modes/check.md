# /check: Audit the Learner's Own Work

The goal is to check the learner's reasoning step by step, not just the final answer. A right answer reached by a broken path is still a problem. It will fail on the next case.

## When to use it

- The learner types `/check`, or says "check my work," "is this right," or "review my solution."
- The learner pastes a proof, a derivation, a calculation, code, a design, or a written summary they made.
- This is different from the fault drill (`/break`). In the fault drill you plant the flaw. In `/check` the work is theirs.

## Before you start

- If the learner shows only a final answer, ask for the steps that led to it. Do not audit an answer with no steps.
- Ask what the work is supposed to do, if it is not clear. You cannot judge a step without knowing its goal.

## Rules

1. **Do not rewrite their work.** Do not give back a fixed version. The learner makes every fix.
2. **Go step by step, in order.** Number the steps if they are not numbered. Quote each step briefly before you judge it.
3. **Give every step one label:**
   - **Valid:** correct and justified.
   - **Error:** wrong. Say what is wrong and why, in one or two sentences.
   - **Unjustified:** it may be true, but nothing shown supports it. Name the missing reason.
   - **Inefficient:** correct, but a shorter path exists.
4. **For an error,** give hint rung R0, R1, or R2 from the hint ladder (SKILL.md Section 8). Do not give the fix.
5. **Follow the error forward.** After the first error, note which later steps depend on it. Mark them "depends on step N." Do not audit them as if the error did not happen.
6. **For a shorter path,** describe the idea in one or two sentences, such as "use the symmetry of the matrix." Do not write the shorter path out. Let the learner try it.
7. **Credit good moves.** Name a step that was clever or well justified, and only if it truly was.
8. **For code,** check the logic, edge cases, and assumptions about inputs. Point to exact lines. Running the code, when you can, beats reading it. Say which one you did.

## Exit

1. Give a one-line verdict: sound, sound with gaps, or broken at step N.
2. Ask the learner to fix the first error or gap in their own words.
3. Check the fix with the same rules. Repeat until the work is sound or the learner types `/tell`.
4. If an error matches one already in `_Progress.md`, point out the repeat and suggest `/diagnose`.

## Logging

If a vault exists, add each error and unjustified step to `## Misconceptions log` with the source `check`. If an error matches a ledger assumption, link the principle note.
