# #2711 — neutral D6 theorem-input gate

This directory exists to help independent D6 work without contaminating the
independent falsifier.

It **does not** search coordinates and does **not** implement the attacks owned
by #2702.

The gate reuses the two merged theorem-first witnesses:

- #2704 — no unexplained D5 -> D6 one-delta child;
- #2708 — no new D4 + two-delta product family.

It freezes the theorem inputs while allowing the one already-authorized owner transition:

```text
PRE  SETQ -> D6:001111 owner-ready / nonadmitted
POST SETQ -> D6:001111 owner-ratified resident
```

No other candidate/resident transition is accepted. A new coordinate, second manual resident,
or theorem-witness change still reopens D6 analysis.

Expected normal result:

```text
D6-INPUTS-STABLE
```

Any theorem/input drift yields:

```text
D6-ANALYSIS-REOPEN-REQUIRED
```

That means **rerun theorem analysis**.  It never means “fill a free D6 slot”.

The PRE→POST SETQ transition is not treated as theorem-input drift because OD-001 already
authorizes that exact change; the gate still rejects every neighboring or unrelated transition.

`--self-test` mutates an in-memory copy of the snapshot to prove that a new
candidate or changed witness result flips the gate to REOPEN.

Principle: **freeze the evidence, not the answer.**
