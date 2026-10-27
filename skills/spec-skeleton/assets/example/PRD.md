# PRD: Tally — split shared expenses

## Problem
Roommates log shared expenses in a spreadsheet. At the end of the month nobody can tell who owes whom, the math is error-prone, and settling up takes many small transfers.

## Goals
- G1: Given a month of expenses, tell each person exactly who to pay and how much.
- G2: Settle with as few transfers as practical.
- G3: Never lose or invent a cent.

## Users
Small households (2 to 10 people) who export expenses to CSV.

## Invariants
- I1: The sum of all balances is exactly zero.
- I2: Money is never represented as a floating-point number.

## Non-goals
- N1: Multiple currencies.
- N2: Storing history between runs.
