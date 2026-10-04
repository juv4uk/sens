# D5 v2 shadow — #3284

Research-only rebase of full Core.D5 after owner-ratified D4 #3272.

## Phase A

Preserve all 32 D5 residents, all 16 existing two-resident blocks, and all OD-D5-LAW-001 relation classes. Move only the eight blocks needed to restore the selector generator under the new D4 selector prefixes.

```text
0110 CDAR -> 01100 CDAAR / 01101 CDADR
0111 CDDR -> 01110 CDDAR / 01111 CDDDR
1000 CAAR -> 10000 CAAAR / 10001 CAADR
1001 CADR -> 10010 CADAR / 10011 CADDR
```

Inverse displacement:

```text
1010 -> APPEND / REVERSE
1011 -> TIMES / QUOTIENT
1100 -> GO / RETURN
1101 -> LESSP / GREATERP
```

Expected mechanical result:

- 32/32 occupancy;
- 16 moved, 16 unchanged;
- all 16 D5 pair memberships preserved;
- selector generation restored 8/8;
- local-law class counts unchanged;
- no universal D4-parent theorem;
- no universal fifth-bit meaning.

## Phase B

D4 #3272 now contains `APPEND` at four bits. The old D5 resident `APPEND` is therefore explicitly flagged for semantic de-duplication. Phase A does not silently replace it.

The D5 resident set changes only after a separate owner decision.
