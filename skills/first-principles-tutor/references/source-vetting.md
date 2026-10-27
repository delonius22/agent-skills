# Source Vetting

Read this at the start of Phase 1 and whenever you cite a claim.

## Tiers

| Tier | What counts | How to use it |
|---|---|---|
| **T1: Primary or authoritative** | Standards (IETF RFCs, ISO, W3C, IEEE, NIST); official documentation and source code; peer-reviewed papers; academic-press textbooks; government and statistical agencies; the original author or designer. | Default basis for every key claim. |
| **T2: Reputable secondary** | University course notes and lectures; established technical publishers; practitioner books or blogs by people with a verifiable track record in the field; review articles; Wikipedia *as a map to its cited T1 sources*, not as the final word. | Fine for explanation and context. For a pivotal claim, try to trace it to T1. |
| **T3: Unverified** | Reddit, forums, Stack Overflow answers, Medium or personal blogs by unknown authors, YouTube, social media, AI-generated content, and **your own recall**. | Allowed, but always labeled `[T3 ⚠ unverified]`. Never the only support for a pivotal claim without a warning callout. |

A high-vote, accepted Stack Overflow answer is still T3. It can be very good. Say it is useful and unverified, and name what would verify it (docs, a test you can run).

## Search order

1. Official docs, specs, or standards for the named thing.
2. Original paper or author.
3. University course material and textbooks.
4. Reputable secondary sources.
5. Community sources, only to find practical gotchas, and labeled T3.

## Rules

- **Cross-check pivotal claims** (anything marked ★) against two independent sources. Say when you could only find one.
- **Check dates.** Note each source's date. In fast-moving fields (software versions, ML, security, law), flag sources older than about three years and search for newer ones.
- **Show conflicts.** When sources disagree, present both positions, say which is better supported, and why.
- **No fake citations.** If you cannot produce a real, reachable URL or full reference, do not cite it. Say "I recall this but could not verify it" and label T3.
- **Separate fact from interpretation.** A source reporting a benchmark result is T1 for the number. Its explanation of *why* may be weaker.
- **No web tool?** Tell the learner at once. Everything from your recall is T3 until they or you verify it.

## Source brief (what the learner sees)

Keep it short. Format:

> **Sources found:** 4 T1, 2 T2, 1 T3.
> **Core claims:** (3 to 5 lines, each with its tier tag)
> **Conflicts:** (if any)
> **Gaps:** (what no good source covered, and whether that will limit depth)

## `01 - Sources.md` table

| # | Source (title, author, link) | Tier | Date | Supports which claims or principles | Notes |
|---|---|---|---|---|---|
