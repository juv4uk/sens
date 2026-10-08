# Direct machine access as data

This document fixes the architectural meaning of direct machine access in SENS.

SENS is direct about machine instructions as data. It is not opaque about the path from meaning to silicon.

## 1. The direct path

```text
SENS semantics
    ↓
machine effect
    ↓
target projection
    ↓
admission
    ↓
encoding
    ↓
machine
```

Each stage is inspectable and owned by SENS.

- Effect is data: a requirement such as bounded-u64 ADD is represented as inspectable SENS-owned machine-effect data.
- Form is data: opcode, operand structure, ModRM/REX information and operand holes are explicit target-projection data.
- Encoding is a function: the SENS machine layer transforms an admitted form into exact bytes.
- Bytes are derived: they are the final representation of a proved path, not an independent semantic authority.

This extends the target-neutral seam established by #4342.

## 2. Direct does not mean execution without a gate

Between a concrete target form and physical execution sits admission.

```text
execute-safe
decode-only-safety
platform-gated
unsupported-current-grammar
unknown
```

`unknown` must be zero in a completed census.

A form may be representable as data, projectable to a target, and encodable to exact bytes without being physically executable. That is intentional fail-closed behavior.

- execute-safe may cross the bounded host-execution boundary;
- decode-only-safety may be encoded/decoded and independently checked, but is not physically executed;
- platform-gated requires an explicit target feature gate;
- unsupported-current-grammar fails with a named status;
- unknown is an evidence gap, not permission.

This follows the execution-class boundary owned by #4086.

## 3. Three levels that must never be conflated

```text
EFFECT ≠ FORM ≠ BYTES
```

A canonical effect such as bounded add is not an x86 ADD form.
An x86 form such as ADD r8, r8 is not its byte encoding.
The bytes are a derived encoding of the admitted form.

Therefore:

```text
semantic meaning
    ≠
machine effect
    ≠
ISA form
    ≠
encoded bytes
```

Every transition between these levels is a proved SENS-owned law or projection.

## 4. External assemblers are controls, not authorities

```text
SENS form → SENS encoding
        ↘
       GAS/NASM
        ↓
     comparison
```

GAS, NASM and similar tools may answer whether an independent tool produced the same machine representation.
They do not answer what a SENS operation means.
External assembler output therefore never becomes semantic authority, machine-effect authority, or target-form authority.

## 5. Hidden machine state stays below the semantic/effect boundary

The canonical effect layer must not inherit hidden architectural state from a target ISA.

Target-local state such as x86 flags may be used by a projection as an implementation mechanism, but any downstream-observable information required by the canonical effect graph must be explicit above the projection boundary.

This is the consequence of #4381/#4392:

```text
if a later canonical effect can observe it,
it must be explicit before target projection.
```

## 6. The compact doctrine

> Direct access to instructions as data: yes, across the whole path.
>
> Direct access to unrestricted execution: no; execution crosses admission.
>
> Meaning comes from effects and semantic law, not from ISA mnemonics or bytes.
>
> Directness without gates would be C; SENS is direct because every gate remains transparent and named.

## Verification

Current-main review anchor: `9f20e0c0a29384f2ead1fa584ed215f2fa9e27f3`.

## Authority boundaries

- #4342 — canonical target-neutral machine-effect seam.
- #4086 — execution/admission classification and real-silicon safety boundary.
- #4392 — explicit-output law; no hidden target state in canonical effects.
- The SENS machine layer owns target projection and encoding.
- External assemblers remain differential controls only.

This document changes no semantic identity, domain coordinate, admission table, or runtime behavior.
