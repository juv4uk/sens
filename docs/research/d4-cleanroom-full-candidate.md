# D4 minimal historical bootstrap candidate — #3225

History may propose capabilities, but old coordinates have zero authority.

Filter: keep only capabilities required by the historical/self-host bootstrap or useful stable derived residents; remove historical mechanisms and derivable conveniences that do not need their own identity.

```text
0000 APPLY
0001 EVAL
0010 LAMBDA
0011 DEFINE
0100 NOT
0101 UNALLOCATED
0110 CDAR
0111 CDDR
1000 CAAR
1001 CADR
1010 LOOKUP
1011 BIND
1100 EVCON
1101 EVLIS
1110 LIST
1111 UNALLOCATED
```

Why these fibres under the ratified D3:
- EMPTY -> APPLY/EVAL: resolved execution vs contextual interpretation;
- QUOTE -> LAMBDA/DEFINE: executable abstraction vs persistent named binding;
- ATOM -> NOT + hole: predicate convenience; no second necessary capability;
- CDR/CAR -> selector composition theorem;
- EQ -> LOOKUP/BIND: identity-keyed environment read/write;
- COND -> EVCON/EVLIS: conditional/list evaluator helpers;
- CONS -> LIST + hole: repeated construction; no second necessary capability.

Only LAMBDA and DEFINE are treated as new irreducible bootstrap capabilities. The others are generated/derived residents. Holes are intentional.

Historical functions such as LABEL, FUNCTION/FUNARG, EVALQUOTE, PAIRLIS, ASSOC and APPEND do not receive D4 identities because the existing research classified them as derived or mechanism-only.
