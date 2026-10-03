# #2711 — neutral D6 theorem-input gate

This directory exists to help independent D6 work without contaminating the
independent falsifier.

It **does not** search coordinates and does **not** implement the attacks owned
by #2702.

The gate reuses the two merged theorem-first witnesses:

- #2704 — no unexplained D5 -> D6 one-delta child;
- #2708 — no new D4 + two-delta product family.

It also freezes the current historical placement candidate set:

```text
SETQ -> D6:001111 (OD-001 owner-ready only, nonadmitted)
```

Expected normal result:

```text
D6-INPUTS-STABLE
```

Any theorem/input drift yields:

```text
D6-ANALYSIS-REOPEN-REQUIRED
```

That means **rerun theorem analysis**.  It never means “fill a free D6 slot”.

`--self-test` mutates an in-memory copy of the snapshot to prove that a new
candidate or changed witness result flips the gate to REOPEN.

Principle: **freeze the evidence, not the answer.**
