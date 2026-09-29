# Layout Demotion Inventory — #1774 slice D

**Agent:** Vyasa (Оксі) | **Date:** 2026-09-29 | **File:** `memory-layout-contract.lisp`

---

## Класифікація тегів (tag ordinals)

| Tag | Name | Current Status | Classification | Rationale |
|-----|------|----------------|----------------|-----------|
| 0 | fixnum | present | **host/mechanism** | Mechanism representation of exact integer; not language semantics |
| 1 | cons | present | **host/mechanism** | Mechanism pair representation; binary structure (Control2) is canonical |
| 2 | symbol | present | **obsolete** | Conflicts with binary-only: no Symbol in canonical ontology (#1696) |
| 3 | nil | present | **host/mechanism** | Mechanism empty list; structural Nil is Control2 `01` |
| 4 | true | present | **obsolete** | Conflicts with binary-only: predicate=1/0, no Bool (#1713/#1714) |
| 5 | primitive | present | **host/mechanism** | Mechanism primitive function entry point |
| 6 | string | present | **obsolete** | UTF-8 string as canonical conflicts with Text7 (#1700) |
| 7 | rational | present | **host/mechanism** | Mechanism representation (two 64-bit pointers) |
| 8 | closure | present | **host/mechanism** | Mechanism representation (env + code pointer) |
| 9 | tcp-conn | present | **host/resource** | Host OS handle, not language value |

---

## Header Fields Classification

| Field | Current Value | Classification | Action |
|-------|---------------|----------------|--------|
| `kind` | `memory-layout-design` | **keep** | Accurate |
| `version` | `(1 0)` | **keep** | Mechanism version |
| `authority` | `mechanism-private` | **keep** | Correct |
| `lifecycle` | `historical-transition` | **keep** | Correct |
| `format` | `nan-boxing-64` | **keep** | Mechanism format |
| `nan-marker` | ... | **keep** | Mechanism detail |
| `fpga-lisp-compatibility` | ... | **keep** | Mechanism evidence |
| `layout` | ... | **keep** | Mechanism layout |
| `tags` | 10 entries | **relabel** | Add classification per tag |
| `heap-representation` | ... | **keep** | Mechanism detail |
| `notes` | ... | **update** | Clarify classification |

---

## Recommended Changes

1. **Add per-tag classification** in `tags` section
2. **Clarify header** — already largely correct (`authority . mechanism-private`, `lifecycle . historical-transition`)
3. **Relabel obsolete tags** with explicit status
4. **Preserve mechanism-private tags** with clear boundary

---

## Proposed Updated `tags` Section

```lisp
(tags . ((fixnum . 0)        ; host/mechanism — exact integer representation
         (cons . 1)          ; host/mechanism — pair structure (Control2 is canonical)
         (symbol . 2)        ; OBSOLETE — conflicts with binary-only ontology (#1696)
         (nil . 3)           ; host/mechanism — empty list (Control2 `01` canonical)
         (true . 4)          ; OBSOLETE — conflicts with binary-only predicate=1/0 (#1713)
         (primitive . 5)     ; host/mechanism — primitive function entry
         (string . 6)        ; OBSOLETE — UTF-8 string conflicts with Text7 (#1700)
         (rational . 7)      ; host/mechanism — two 64-bit pointers
         (closure . 8)       ; host/mechanism — env + code pointer
         (tcp-conn . 9)))    ; host/resource — OS handle, not language value
```

---

## Coordination

- No overlap with #1714 (runtime), #1708 (Rust test retirement), #1709 (semantic witnesses)
- Aligns with WSM evidence: 3-bit bootstrap vs 4-bit nan-box = mechanism-private
- Supports #1709 semantic witness corpus: exact SID contracts are authority, not layout tags
