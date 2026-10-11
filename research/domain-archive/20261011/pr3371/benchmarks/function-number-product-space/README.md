# Exact product-space algebra (#3369)

The function is the exact-width binary number.

This benchmark proves, exhaustively:

```text
W6 ≅ W3 × W3
W8 ≅ W4 × W4
```

using:

```text
pair_n(a,b) = (a << n) | b
split_n(x)  = (high_n(x), low_n(x))
```

The mapping is a bijection:

```text
W3×W3 -> W6   64/64
W4×W4 -> W8   256/256
```

## Product laws

The following factor componentwise exactly:

```text
XOR
AND
OR
NOT
```

and:

```text
popcount(pair(a,b)) = popcount(a)+popcount(b)
Hamming(pair(a,b),pair(c,d))
  = Hamming(a,c)+Hamming(b,d)
```

Numeric order is also exact lexicographic order on the pair:

```text
pair(a,b) < pair(c,d)
iff
a<c or (a=c and b<d)
```

## Addition: exact carry coupling

Addition is not falsely declared componentwise.

```text
low   = (b+d) mod 2^n
carry = floor((b+d)/2^n)
high  = a+c+carry
```

So:

```text
pair(a,b)+pair(c,d) = (high << n) | low
```

The naive componentwise-add law fails exactly when the low half emits a carry:

```text
W6  (n=3): 1,792 / 4,096 cases
W8  (n=4): 30,720 / 65,536 cases
```

## Multiplication

Multiplication is also exact over the pair factors:

```text
(a·2^n+b)(c·2^n+d)
=
ac·2^(2n) + (ad+bc)·2^n + bd
```

So W6/W8 are not merely enumerations. Their number algebra can be replayed
from lower-width factors plus a tiny set of exact laws.

This result concerns the mathematical function-number spaces. It does not
automatically ratify semantic D6/D8 resident meanings.
