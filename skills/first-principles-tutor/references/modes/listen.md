# /listen: Compare the Learner's Explanation to a Source

The goal is to find where the learner's version of an idea differs from an authoritative source. The learner explains from memory, and you compare the two claim by claim.

## When to use it

- The learner types `/listen`, or says "compare my explanation to this" or "did I get this right?" and gives a source.
- The learner gives two things: a source (a textbook section, a paper, documentation, or a vault principle note) and their own explanation.
- Their explanation can be written, a voice transcript, or a description of a diagram they drew. Two or three of these together work best.

## Before you start

- **Make sure it came from memory.** Ask once: "Did you write this without looking at the source?" An explanation copied from the source tests nothing. If they looked, ask them to try again without looking, or note that the result only checks their reading.
- If there is no source, use the principle note from the vault. If there is no vault, ask for a source. Do not use your own recall as the authority unless the learner agrees, and label it `[T3: model recall, unverified]`.

## Rules

1. **Break the source into its key claims.** Mark the claims that carry the most weight (the ★ ones, if a spec exists).
2. **Label each source claim:**
   - **Matched:** the learner said it correctly, in any words.
   - **Missing:** the learner left it out.
   - **Distorted:** the learner said something close to it, but wrong in a way that matters.
3. **Label each extra claim** the learner made that the source does not contain:
   - **Added, correct:** true, and supported by a T1 or T2 source. Say so.
   - **Added, wrong:** false. Say why.
   - **Added, unverified:** label it `[T3 ⚠ unverified]`.
4. **If the source looks wrong,** do not quietly side with it. Flag the conflict, give the better-supported view with its tier, and let the learner decide.
5. **Compare the modes with each other.** If the written version and the diagram disagree, point it out. A mismatch between modes usually shows exactly where the understanding is shaky.
6. **Sort issues by cost:** distorted claims first, then missing ★ claims, then missing details. Do not list every small detail.
7. **Do not rewrite their explanation.** Point to the gap and ask them to fix it.

## Exit

1. Give a short score: matched, missing, distorted, and added, in counts.
2. List the top three issues, worst first.
3. Ask the learner to re-explain only the worst one, in their own words and without looking.
4. Check the new version. When it passes, save it as their explanation in the principle note (`> [!quote] My explanation`).

## Logging

If a vault exists, add each distorted claim to `## Misconceptions log` with the source `listen`.
