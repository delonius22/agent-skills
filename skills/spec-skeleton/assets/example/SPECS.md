# SPECS: Tally

## 1. Input format
1.1 Input is a UTF-8 CSV file with header `date,payer,amount,participants`.
1.2 `amount` is a decimal string with at most two fractional digits, greater than zero, at most 100000.00.
1.3 `participants` is a `;`-separated list of names; the payer may or may not be in it.
1.4 Names are case-sensitive, 1 to 40 characters, no `;` or `,`.

## 2. Money
2.1 All money is stored as integer cents.
2.2 When an amount does not split evenly, the leftover cents go one each to participants in alphabetical order.

## 3. Balances
3.1 A person's balance is what they paid minus their share of every expense they participate in.
3.2 The sum of balances must be zero; otherwise the run fails with "internal: balances do not sum to zero".

## 4. Settlement
4.1 Repeatedly match the largest debtor with the largest creditor and transfer the smaller of the two amounts, until all balances are zero.
4.2 Ties are broken by name, alphabetically.

## 5. CLI
5.1 `tally settle FILE` prints one line per transfer: `<from> pays <to> <amount>` with amount formatted as `12.34`.
5.2 Exit code 0 on success, 2 on invalid input (with the message `error: line <n>: <reason>` on stderr), 1 on internal errors.
5.3 Currency conversion is not supported.
