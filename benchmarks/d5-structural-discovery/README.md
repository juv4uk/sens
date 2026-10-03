# D5 post-ingest structural discovery (#2583)

This directory consumes the completed Early-Lisp historical ledger and builds a
conservative capability-factor hypergraph.

It deliberately distinguishes:
- historical observations;
- already-derived D1-D4 behavior;
- historical representation mechanisms;
- post-D4 factor candidates;
- proved independent roots (currently zero);
- D5 residents (no new residents).

Current first-pass post-D4 factor candidates:
- shared-location update;
- non-local exit;
- raw-form input;
- explicit caller environment;
- returned-form protocol;
- expansion timing;
- invocation packaging.

Current bounded corpus status:
- historical rows consumed: 19/19;
- post-D4 factor observations: 7;
- bounded-independent factor observations: 7;
- roots promoted by this structural model: 0;
- new D5 residents: 0;
- D5 map: 8 selector-generated + 24 UNKNOWN/free.

These are structural observations, not placements or automatically promoted roots.
RETURN's residue-root theorem is tracked separately by #2488/#2504; this model
does not derive or allocate its width/coordinate.
