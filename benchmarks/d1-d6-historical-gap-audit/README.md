# D1-D6 historical gap audit — #2718

This benchmark joins the existing historical ledger, merged semantic placement,
ratified D5 baseline, and D6 unknown-frontier evidence.

It answers one question:

> Which historically attested capabilities are already explained by earlier
> ratified domains, and which surviving deltas still need a law before any
> residency can be ratified?

It is deliberately **not** a placement search.

Current expected result:

- 12 historical rows already explained by D1-D4;
- 4 rows need an exact domain/placement theorem: SET, RETURN, FEXPR, FSUBR;
- TRANSFORMER remains NEEDS-LAW until #2567 closes the Hart whole-form + expansion-stage relation;
- PROG is a composite, not a resident conclusion;
- SETQ/D6:001111 is the only owner-ready/nonadmitted residency decision;
- D5 stays 8 generated + 24 protected UNKNOWN + 0 manual residents;
- D6 stays 16 generated + 48 canonical UNKNOWN; 44 PURE-UNKNOWN are not a search space;
- arithmetic remains historical/Core-Math bridge work until a typed bridge is independently proved.

Run:

```bash
python3 benchmarks/d1-d6-historical-gap-audit/run.py --out /tmp/d1-d6-gap
```
