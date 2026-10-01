# H-NIL corpus scan (#2019)

**Agent:** grok-xai  
**Scope:** textual patterns under `lib/` + `knowledge/` (134 `.lisp` files)  
**Not:** runtime eval of NIL opcode; not production change; **premise lock** held

## Method

```sh
python3 scripts/research-2019-h-nil-corpus-scan.py
```

Counts:

| pattern | meaning |
|---------|--------|
| `(nil …)` | human **callable** NIL head |
| `(00000001 nil)` / `(quote nil)` | NIL as **data** symbol |
| `()` | empty list **data** |
| `00000000` | Function8 slot-zero mentions (table identity, not proof of operator NIL) |

## Results (measured)

```text
files                 134
nil_call_head           0
quoted_nil_as_data      2
empty_list_token     5745
sid_zero_mentions       ~table/registry rows only
verdict              supports_H_NIL_conjecture
```

Quoted-nil hits are **EQ/data** branches in Core1 eval (compare expression to symbol nil), not `(nil args…)` operator calls.

## Interpretation (bounded)

- Current tree **does not require** callable operator NIL in surface forms.  
- Empty is carried as **`()` data** at high frequency.  
- Slot `00000000` in function-table is **mechanism/identity row**, not evidence of corpus forms that *invoke* NIL as a function.

This **strengthens** H-NIL as conjecture; it does **not** upgrade #2018 off premise and does **not** reassign codes.

## Falsifier still open

A required form whose only honest model is “invoke operator NIL” (eval head SID / host null-as-op) would weaken H-NIL.

## Related foundation numbers (already on main)

| source | number |
|--------|--------|
| Layer-0 checker | pass (D1/racanā2/boundaries) |
| CAR exclusive support depth4 (#2035) | 30 |
| Hamming density seeds (#2008) | 0.4286 |
| Generator economy CAR/CDR ratio | 3.0 |
| one-off ATOM→NULL economy | ≤1 (weak) |
