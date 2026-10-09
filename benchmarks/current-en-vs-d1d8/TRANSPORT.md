# Current English vs D1-D8 — representation/transport lane

This is the representation/accounting lane for #3088 / #3137.

It compares the current English surface and the current canonical D1-D8 source
only after both candidates lower to the same exact-domain trace and execute to
the same oracle.

The bounded CI fixture is deliberately small (D3 only). It proves the accounting
machinery; it is **not** a whole-language compression result.

## Metrics

Per paired workload the lane records:

- source bytes;
- lowered AST node count;
- semantic payload bits for the canonical binary lane;
- packed bytes;
- physical payload-container bits;
- final-byte unused tail bits;
- payload utilization.

The following stay `null` until their production owners exist:

- standalone framing bits — #2189;
- total standalone wire bits — #2189;
- canonical artifact/FASL bytes for the current envelope.

The English row does not pretend to own canonical payload metrics. Those fields
stay null there.

## Production APIs

Canonical accounting uses only:

- `parse_binary_source_words`;
- `pack_binary_source_tokens`;
- `packed_transport_accounting`.

No one-byte-per-word approximation is used.

## Pair invariant

Rows use the shared #3116 schema and validator.

Before any row is emitted:

1. English and canonical sources must parse;
2. both must lower to the same span-independent exact-domain trace;
3. legacy byte identity must not appear after lowering;
4. both must execute to the same value/output;
5. the independent fixture oracle must match.

## Current limitation

The headline corpus remains BLOCKED until the production source/envelope spine
is complete:

- #3134 BinaryNumber admission;
- #3135 numeric Local admission;
- #1696 remaining Symbol boundary cleanup;
- #2189 standalone framing.

No private Number/local/framing encoding is introduced by this benchmark.

Principle: **account every layer separately; never call byte-container slack or
unknown framing "semantic payload".**
