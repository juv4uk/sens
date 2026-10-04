# D4 clean-room full candidate — #3225

Full 16/16 research candidate derived from ratified D1-D3 plus local D4 fibre laws.

**Not ratified.** Historical D4/SID8/Sens8 names are forbidden as premises.

```text
0000  GROUND?
0001  COALESCE
0010  ABSTRACT
0011  ENTER
0100  COMPOSITE?
0101  EXECUTABLE?
0110  CDAR
0111  CDDR
1000  CAAR
1001  CADR
1010  ASSOC-READ
1011  ASSOC-WRITE
1100  DISPATCH
1101  REENTER
1110  COLLECT
1111  MAP-BUILD
```

Local fibre laws:
- EMPTY -> ground observation / fallback recovery;
- QUOTE -> construct delayed executable / enter represented executable;
- ATOM -> close current kind partition / observe new executable carrier;
- CDR/CAR -> selector composition;
- EQ -> identity-keyed association read/write;
- COND -> finite dispatch / unbounded re-entry;
- CONS -> finite collection / recursive transform-and-build.

Status discipline:
- selectors are already generated;
- REENTER has a clean-room lower-bound witness (#3230/#3233);
- ABSTRACT is under independent clean-room attack (#3229);
- all other rows remain candidates until their fibre witness passes;
- no posterior historical match changes semantic authority.
