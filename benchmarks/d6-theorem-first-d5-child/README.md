# #2701 — D5 → D6 one-delta theorem-first witness

This benchmark deliberately searches **parents/laws**, not free D6 bit strings.

Current admitted D5 population:

```text
8 selector-generated semantic residents
24 UNKNOWN/free non-residents
0 manual non-selector residents
```

For every admitted D5 selector, appending either admitted selector law produces
the exact 16 generated D6 selectors.  Therefore the current D5 population has
no unexplained same-base + one-delta child.

The witness also consumes the post-D4 D5 eligibility closeout and requires
zero `d5_eligible=YES` factors.

Expected result:

```text
RESULT=NO-NEW-D5-ONE-DELTA-CHILD
```

This is a **reopen-on-change** guard: if a future theorem admits a new
non-selector D5 semantic resident or a new D5-eligible factor, this witness
must fail and #2701-style analysis must be rerun.  Failure does not allocate a
D6 coordinate.
