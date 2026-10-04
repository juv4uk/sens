# resource-request-v1

Parent: sens#3158 / #3111.

This fixture is a bounded civilian resource request. It is not a military
logistics vocabulary.

Canonical tuple:

```text
(schema-version form-kind message-id timestamp resource-code quantity unit-code location note)
```

Golden datum:

```lisp
(1 1 "r-0001" "2026-10-04T00:00:00Z" 0 4 0 (0) (0))
```

Field law:

- [0] = schema version 1;
- [1] = form kind 1 = resource request;
- [2] = opaque message id;
- [3] = UTC timestamp;
- [4] = resource category code; v1 code 0 = potable water;
- [5] = exact quantity; fixture value 4;
- [6] = unit code; v1 code 0 = litre;
- [7] = location union; `(0)` = explicitly unknown;
- [8] = note union; `(0)` = explicitly absent.

Codes are scoped by tuple position. The two zeros at [4] and [6] do not share
identity: one is a resource-category value and one is a unit value. They are
schema data, not SENS function/domain identities.

The canonical machine serialization is checked in as
`resource-request-v1.wire` and runtime-verified by
`write-to-string -> read -> write-to-string`.

Current exact payload accounting:

- 95 UTF-8 bytes;
- 760 bits;
- exact UTF-8 hex pinned by test.

`resource-request-v1.surfaces.tsv` uses numeric projection coordinates only.
Human words are display projections and never canonical field keys.
