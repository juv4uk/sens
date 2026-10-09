# medical-assistance-request-v1

Parent: sens#3160 / #3111.

This fixture is a generic civilian request for medical assistance. It is a
communication form only. It does **not** diagnose, recommend treatment, infer
triage priority, classify casualties, or encode command/military semantics.

Canonical tuple:

```text
(schema-version form-kind message-id timestamp assistance-code person-count location note)
```

Golden datum:

```lisp
(1 3 "a-0001" "2026-10-04T00:00:00Z" 0 1 (0) (0))
```

Field law:

- [0] = schema version 1;
- [1] = form kind 3 = medical assistance request;
- [2] = opaque message id;
- [3] = UTC timestamp;
- [4] = assistance category code; v1 code 0 = generic medical assistance;
- [5] = exact affected-person count; fixture value 1;
- [6] = location union; `(0)` = explicitly unknown;
- [7] = note union; `(0)` = explicitly absent.

The numeric values are schema data scoped by tuple position. They are not SENS
function/domain identities.

The canonical machine serialization is checked in as
`medical-assistance-request-v1.wire` and runtime-verified by
`write-to-string -> read -> write-to-string`.

Exact payload accounting:

- 86 UTF-8 bytes;
- 688 bits;
- exact UTF-8 hex pinned by test.

`medical-assistance-request-v1.surfaces.tsv` uses numeric projection
coordinates only. Human words are display projections and never canonical
field keys.

No general medical parser or decision system is introduced here. Future
validation may reject malformed structure, but must not infer diagnosis,
treatment, triage or priority from this form.
