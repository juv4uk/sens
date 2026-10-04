# Direct function-number algebra (#3359)

This experiment starts from the project rule that function identities are
exact-width binary numbers.

No human operation name is needed to perform the mathematics.

Canonical width laws tested first:

```text
XOR/AND/OR : Wn × Wn -> Wn
append bit : Wn × W1 -> W(n+1)
full ADD   : Wn × Wn -> W(n+1)
full MUL   : Wn × Wn -> W(2n)
concat     : Wa × Wb -> W(a+b)
```

No modulo truncation and no minimal-width collapse are used.

Key first results:

```text
append: D3×bit -> W4   16/16
append: D4×bit -> W5   32/32

ADD: W3×W3 -> W4       15/16  (only 1111 unreachable)
ADD: W4×W4 -> W5       31/32  (only 11111 unreachable)

concat: W3×W3 -> W6    64/64  bijection
concat: W4×W4 -> W8    256/256 bijection

MUL: W3×W3 -> W6       26/64 distinct products
MUL: W4×W4 -> W8       90/256 distinct products
```

Most importantly, square now respects exact width:

```text
W3 × W3 -> W6
W4 × W4 -> W8
```

So `W3:100 * W3:100 = W6:010000`, not an arbitrarily re-widthed D5
number.

D6/D8 outputs are mathematical coordinates/research predictions only until
their semantic laws independently establish residency.
