# status-report-v1

Parent: sens#3159 / #3111.

This fixture is a bounded civilian welfare/status report. It is not a tactical
or military status vocabulary.

Canonical tuple:

```text
(schema-version form-kind message-id timestamp welfare-code location note)
```

Golden datum:

```lisp
(1 2 "s-0001" "2026-10-04T00:00:00Z" 0 (0) (0))
```

Field law:

- [0] = schema version 1;
- [1] = form kind 2 = status report;
- [2] = opaque message id;
- [3] = UTC timestamp;
- [4] = welfare/status code; v1 code 0 = safe;
- [5] = location union; `(0)` = explicitly unknown;
- [6] = note union; `(0)` = explicitly absent.

The numeric values are schema data scoped by tuple position. They are not SENS
function/domain identities.

The canonical machine serialization is checked in as
`status-report-v1.wire` and runtime-verified by
`write-to-string -> read -> write-to-string`.

Exact payload accounting:

- 78 UTF-8 bytes;
- 624 bits;
- exact UTF-8 hex pinned by test.

`status-report-v1.surfaces.tsv` uses numeric projection coordinates only.
Human words are display projections and never canonical field keys.

This first slice deliberately does not pretend a general EMRG schema parser
already exists. It proves the datum, serialization and projection boundary.
Fail-closed schema parsing/validation belongs to the parser/renderer lane once
the form contracts are stable.
