# EMRG consumer fixtures v1

This directory is the first bounded producer slice for sens#3111.

It does **not** define radio framing, modulation, frequency, authentication or a
military command vocabulary. It defines one civilian-safe semantic datum and
its SENS canonical serialization so downstream consumers can prove that
transport and UI language do not mutate meaning.

## station-checkin-v1

Canonical semantic tuple:

```text
(schema-version form-kind message-id timestamp location note)
```

The wire contains values only; the names above are documentation.

Numeric codes in v1:

- tuple[0] = `1`: schema version 1;
- tuple[1] = `0`: form kind 0 = station check-in;
- tuple[2] = opaque message id string;
- tuple[3] = UTC timestamp string;
- tuple[4] = location union; `(0)` = explicitly unknown;
- tuple[5] = note union; `(0)` = explicitly absent, `(1 "...")` is reserved
  for a non-authoritative free-text note in a later fixture.

The fixed tuple arity makes omission different from an explicit state:
location `(0)` means **known to be unknown**; removing tuple[4] is malformed.
Likewise note `(0)` means **explicitly absent**; it is not an empty string.

Fixture source:

```lisp
(1 0 "m-0001" "2026-10-04T00:00:00Z" (0) (0))
```

Its canonical SENS machine serialization is checked in as
`station-checkin-v1.wire` and verified by the sens runtime's
`write-to-string -> read -> write-to-string` round-trip.

Current exact accounting:

- canonical wire bytes: **69**;
- canonical wire bits: **552**;
- field count: **6**;
- UTF-8 hex is asserted in the integration test.

## Surface boundary

`station-checkin-v1.surfaces.tsv` contains Ukrainian, Polish and English
operator labels for the same positional fields/states. These strings are
projection metadata only. They do not occur as semantic keys in the canonical
wire and changing them must never change `station-checkin-v1.wire`.

Parser/renderer mechanics belong to sens#3110. This fixture intentionally gives
that lane one stable object to target without pre-deciding the remaining EMRG
forms.
