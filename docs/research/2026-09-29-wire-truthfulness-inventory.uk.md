# Wire Truthfulness Inventory — #1774 slice E

**Agent:** Vyasa (Оксі) | **Date:** 2026-09-29 | **File:** `crates/sens/src/value.rs` (method `render_canonical_wire`)

---

## Current Implementation Audit

### `render_canonical_wire` (lines ~840-870)

```rust
fn render_canonical_wire(value: &Value) -> String {
    match value {
        // CANONICAL BINARY DOMAINS
        Value::Number(number, Exactness::Exact) if number.is_finite() && number.fract() == 0.0 => {
            Rational::integer(*number as i64).to_binary_wire_token()
        }
        Value::Rational(number) => number.to_binary_wire_token(),
        Value::Pair(_, _) => render_pair_canonical_wire(value),
        Value::Vector(values) => { ... },
        
        // SILENT FALLBACK — HUMAN TEXTUAL RENDERER
        _ => render(value, true),
    }
}
```

### `render` (lines ~750-830) — Human Textual Renderer (`quote_strings: true`)

Used as **silent fallback** for all non-binary-domain variants.

---

## Value Variant Classification

| Value Variant | `render_canonical_wire` Path | Classification | Binary Canonical? |
|---------------|------------------------------|----------------|-------------------|
| `Number` (Exact, finite, integer) | Binary wire token | **canonical-binary** | ✅ |
| `Rational` | Binary wire token | **canonical-binary** | ✅ |
| `Pair` | Recursive canonical wire | **canonical-binary** | ✅ |
| `Vector` | Recursive canonical wire | **canonical-binary** | ✅ |
| `Number` (Inexact / non-finite) | Fallback → `render` | **transition-debt** | ❌ |
| `Nil` | Fallback → `render` → `"()"` | **canonical-binary?** | ⚠️ (structural, not SID) |
| `Bool` | Fallback → `render` → `"t"`/`"()"` | **obsolete** | ❌ (Bool retired) |
| `Number` (Inexact) | Fallback → `render` | **transition-debt** | ❌ |
| `Rational` | **Binary** | ✅ |
| `Sid` | Fallback → `render` → binary SID string | **canonical-binary?** | ⚠️ (SID is canonical but uses `render`) |
| `String` | Fallback → `render` → quoted string | **human/boundary-projection** | ❌ |
| `Symbol` | Fallback → `render` → symbol name | **obsolete/transition-debt** | ❌ (Symbol retired) |
| `Pair` | **Binary** | ✅ |
| `Closure` | Fallback → `<lambda>` | **host/mechanism** | ❌ |
| `Macro` | Fallback → `<macro>` | **host/mechanism** | ❌ |
| `TcpConnection` | Fallback → `<tcp-connection>` | **host/resource** | ❌ |
| `TcpListener` | Fallback → `<tcp-listener>` | **host/resource** | ❌ |
| `Builtin` | Fallback → `#<builtin name>` | **host/mechanism** | ❌ |
| `HostHandle` | Fallback → `#<host-handle kind>` | **host/mechanism** | ❌ |
| `Vector` | **Binary** (recursive) | ✅ |
| `NumericBuffer` | Fallback → `#i32(...)` / `#f32(...)` | **host/mechanism** | ❌ |

---

## Classification Summary

| Classification | Variants | Count | Action |
|----------------|----------|-------|--------|
| **canonical-binary** | Number (exact int), Rational, Pair, Vector | 4 | Keep — extend if needed |
| **canonical-binary?** | Nil, Sid | 2 | Clarify / add explicit binary path |
| **transition-debt** | Number (inexact), Bool | 2 | Resolve per #1713/#1714 |
| **obsolete** | Bool, Symbol | 2 | Remove / demote |
| **human/boundary-projection** | String, Symbol | 2 | Explicit boundary, not canonical |
| **host/mechanism** | Closure, Macro, Builtin, HostHandle, NumericBuffer, Builtin | 6 | Explicit mechanism, not canonical |
| **host/resource** | TcpConnection, TcpListener | 2 | Explicit resource, not canonical |

---

## Foundation Leak Identified

**The claim "canonical wire" is stronger than reality:**

```rust
// Current claim: "Deterministic machine wire representation"
// Actual: only 4 of ~20 variants have binary canonical paths
// 16 variants fall back to human textual renderer
```

**Silent fallback** `_ => render(value, true)` makes the claim false for ~80% of variants.

---

## Recommended Actions

| Variant | Recommended Strategy |
|---------|---------------------|
| `Nil` | Add explicit binary path: `()` is structural, not SID |
| `Sid` | Add explicit binary path: emit binary SID token (already binary) |
| `Number` (inexact) | Resolve via #1713/#1714 (Predicate1 binary) |
| `Bool` | Remove / demote (retired by #1713) |
| `Symbol` | Remove / demote (retired by #1696) |
| `String` | Explicit boundary projection (Text7/UPC-7) |
| `Closure`/`Macro`/`Builtin`/`HostHandle` | Explicit host/mechanism — not canonical |
| `TcpConnection`/`TcpListener` | Explicit host/resource — not canonical |
| `NumericBuffer` | Explicit host/mechanism — not canonical |

---

## Recommended API Change

**Option A (Extend binary domains):** Add explicit binary paths for all variants that have canonical binary identity (Nil, Sid, exact integers, etc.)

**Option B (Demote claim):** Rename `to_canonical_wire_string` → `to_presentation_wire_string` with explicit `canonical_wire` subset method for true binary domains only.

**Recommendation:** **Option A** for true canonical domains (Nil, Sid, exact int, Rational, Pair, Vector); **Option B** for the rest — explicit boundary methods.

---

## Coordination

- Aligns with #1709 semantic witnesses: canonical identities are SID-based
- Aligns with #1696 (Symbol retired), #1713 (Bool retired), #1700 (Text7)
- Coordinate with #1708 (Rust semantic test retirement) and #1709 (semantic witnesses)
