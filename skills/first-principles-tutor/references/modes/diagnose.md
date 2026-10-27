# /diagnose: Find the Root Cause of Repeated Mistakes

The goal is to find the one flawed belief or habit of reasoning behind many separate mistakes. Fixing one root cause is faster than fixing ten symptoms one at a time.

## When to use it

- The learner types `/diagnose`, or says "why do I keep getting this wrong" or "what is my weak spot."
- `/exam` or `/check` finds a mistake that matches an earlier one.
- At the end of a long course, before the final review.

## Gather the evidence

1. **Read the logs.** Use the `## Misconceptions log` in `_Progress.md` for this topic. If the learner agrees, also read the logs from other topics in `Learning/`. The same root cause often shows up across subjects.
2. If there is no vault, ask the learner to paste their mistakes, failed questions, or past session notes.
3. **You need at least five mistakes.** With fewer, say plainly that there is not enough evidence for a root cause. Suggest an `/exam` to collect more, and stop.

## Find the root cause

1. **List the mistakes** in short form: what they said, and what was right.
2. **Group them by the reasoning step that failed, not by topic.** "Mixed up rate and amount" is a reasoning step. "Got the cache question wrong" is only a topic.
   Common reasoning failures to check:
   - Treating a design choice as a fundamental truth
   - Ignoring an assumption, or not checking when it holds
   - Confusing correlation, sequence, or cause
   - Mixing up a rate and an amount, or a part and the whole
   - Overgeneralizing from one example
   - Following a remembered procedure without knowing why it works
   - Losing track of units, scale, or edge cases
3. **Propose two or three candidate root causes.** Write each one as a belief the learner seems to hold, such as "You treat X as if it always means Y."
4. **Test each candidate against the evidence.** How many mistakes does it explain? Which ones does it not explain? Prefer the candidate that explains the most with the fewest extra assumptions.

## Confirm it with the learner

A root cause is only a hypothesis until it is tested. Label it "hypothesis" until then.

1. Write one or two probe questions. Each must be a new question where the suspected belief predicts a *specific* wrong answer.
2. Ask them one at a time, with a confidence rating (0 to 100%).
3. **If the learner gives the predicted wrong answer,** the root cause is confirmed.
   **If they answer correctly,** drop that candidate and test the next one.
   **If they give a different wrong answer,** add it to the evidence and go back to grouping.

## Exit report

- **Root cause:** the belief, in one sentence.
- **Evidence:** which logged mistakes it explains, and the probe result.
- **Why it is tempting:** what makes this belief feel right. A learner who knows why they were fooled is less likely to be fooled again.
- **Fix plan:** two or three targeted drills that use existing commands. For example: a `/break` drill built on the bad belief, a `/transfer` drill where the belief would fail, and a recheck in three days.

Do not make claims about the learner's personality, motivation, or ability. Diagnose the reasoning, not the person.

## Logging

Add a row to `## Root causes` in `_Progress.md`. Mark the related misconceptions with the root cause ID. Schedule the recheck on the normal review schedule.
