# Math Protocol

Use this for every equation that matters to the subject. Place the explanation directly beside the principle or code it belongs to, never in a detached appendix.

## The nine steps

1. **The question.** One sentence: what question does this equation answer?
2. **Standard form.** Write it exactly as the authoritative sources write it, in LaTeX (`$$ ... $$`). Do not rename symbols in the equation itself. The learner must be able to read the literature.
3. **Symbol table.** One row for *every* symbol: Greek letters, Latin letters, subscripts, and any operator a newcomer might not know (Σ, ∂, ∇, ∫, log bases).

   | Symbol | Nickname | What it does in this formula | Units | Typical sign or range |
   |---|---|---|---|---|

   The **nickname** is a short plain name that describes the symbol's *job here*: λ "decay rate", σ "spread", Δ "change in", Σ "add them all up", μ "average". The nickname goes beside the symbol, never in place of it.
4. **Read it aloud.** Restate the equation as a sentence using the nicknames.
5. **Worked example.** Real numbers. Show each substitution and carry units through every step. The example must attach to the same variables in the same places as the formula.
6. **Behavior.** What happens as each key input grows, shrinks, reaches zero, or goes negative? Where is the formula undefined or meaningless?
7. **Origin.** A short derivation or intuition for why the formula has this shape. If that exceeds reliable depth, use a Depth Limit callout and point to where the derivation lives.
8. **Assumptions.** What must be true for this formula to hold (linearity, independence, constant rate, and so on)? Add each one to the spec's assumption ledger.
9. **Learner task.** Change one input and ask the learner to predict the direction and rough size of the result before you compute it.

Also run a **units check**: both sides of the equation must have the same units. When they do not, something is wrong, and that check is itself a skill worth teaching.

## Example 1: a line

**Question:** Given an input, what output does a straight-line relationship produce?

$$ y = mx + b $$

| Symbol | Nickname | What it does | Units (taxi example) | Sign or range |
|---|---|---|---|---|
| $y$ | output (dependent variable) | The vertical coordinate of any point on the line. It depends on $x$. | dollars | any |
| $x$ | input (independent variable) | The horizontal coordinate of any point on the line. You choose it. | kilometers | any; here ≥ 0 |
| $m$ | slope, or rate of change | How steep the line is and which way it goes. Positive $m$ rises; negative $m$ falls. It is how much $y$ changes when $x$ goes up by one. | dollars per kilometer | any |
| $b$ | starting value (y-intercept) | Where the line crosses the y-axis, which is the value of $y$ when $x = 0$, the point $(0, b)$. | dollars | any |

**Read aloud:** output equals rate of change times input, plus starting value.

**Mapped example (taxi fare):**

| Taxi piece | Formula piece |
|---|---|
| Total fare | $y$ |
| Distance driven | $x$ |
| Price per kilometer | $m$ |
| Flag-drop fee charged the moment you get in | $b$ |

Where it breaks: real fares add waiting-time charges and surge pricing, so the true relationship is not a single straight line.

**Worked:** $m = 2$ dollars/km, $b = 3$ dollars, $x = 10$ km → $y = 2 \times 10 + 3 = 23$ dollars. Units check: (dollars/km × km) + dollars = dollars. ✓

**Learner task:** "If the trip doubles to 20 km, does the fare double? Predict before computing." (It does not, because $b$ does not double. That gap is a common misconception worth catching.)

## Example 2: exponential decay (Greek letter)

**Question:** How much of something remains after time passes, when it shrinks by a fixed fraction per unit of time?

$$ N(t) = N_0 \, e^{-\lambda t} $$

| Symbol | Nickname | What it does | Units | Sign or range |
|---|---|---|---|---|
| $N(t)$ | amount left | Quantity remaining at time $t$ | same as $N_0$ | ≥ 0 |
| $N_0$ | starting amount | Quantity at $t = 0$ (the subscript 0 means "at time zero") | e.g., grams, atoms | > 0 |
| $e$ | natural growth base | A fixed constant, about 2.718, that makes continuous rates work cleanly | none | constant |
| $\lambda$ | decay rate | Fraction lost per unit time (continuously). Bigger λ means faster shrinking. | 1 / time | > 0 |
| $t$ | elapsed time | How long it has been | time | ≥ 0 |

**Read aloud:** amount left equals starting amount times e raised to minus decay rate times elapsed time.

**Behavior:** at $t = 0$, $N = N_0$. As $t$ grows, $N$ approaches zero but never reaches it. Doubling λ makes it shrink twice as fast. The half-life is $\ln 2 / \lambda$.

**Assumption:** λ is constant over time. If the rate itself changes, this formula is wrong.
