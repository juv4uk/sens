# Contract Authority Drift Inventory — #1774 slice A

**Agent:** Vyasa (Оксі) | **Date:** 2026-09-29 | **File:** `language-contract.lisp`

---

## Класифікація інваріантів (Contract 9.0)

| Invariant | Current Text | Classification | Rationale |
|-----------|--------------|----------------|-----------|
| `sid8-function-space` | 256 SIDs, no second ontology | **canonical-language** | Still valid: one function-identity space |
| `single-function-ontology` | No second named ontology | **canonical-language** | Still valid |
| `surface-non-authority` | Human surfaces non-authoritative | **canonical-language** | Still valid |
| `core-profile-law` | Core1-4 may have different laws per SID | **obsolete** | Contradicts #1703: ONE foundation law Core1–4 |
| `kernel-archipelago` | Kernels consume Sid8, no new identity | **canonical-language** | Still valid mechanism boundary |
| **`sid-00000111-control`** | **3-field COND, UnsatisfiedConditional on exhaustion** | **obsolete** | Contradicts #1663/#1713: 2-part COND, exhaustion → structural `()` |
| `reader-apostrophe` | Apostrophe → SID 00000001 | **canonical-language** | Still valid reader behavior |
| `reader-eight-bits` | 8 bare bits → Sid8 | **canonical-language** | Still valid reader behavior |
| `reader-decimal-separator` | Dot/comma decimal separators | **canonical-language** | Still valid reader behavior |
| **`error-classification`** | **UnsatisfiedConditional for COND exhaustion** | **obsolete** | Contradicts #1663/#1713: exhaustion → structural `()` |
| `migration-debt-00000000` | () structural, 00000000 not empty | **canonical-language** | Still valid (completed #1332) |

---

## Header Fields Classification

| Field | Current Value | Classification | Action |
|-------|---------------|----------------|--------|
| `major` | 9 | **relabel** | Historical Contract 9.0 |
| `minor` | 0 | **keep** | Version |
| `note` | "RATIFIED by owner 2026-09-24..." | **demote** | Historical Contract 9.0, superseded |
| `covers` | G1-8, S1-3 | **keep** | Coverage groups |
| `invariants` | 12 entries | **relabel** | Per-clause classification |

---

## Рекомендовані зміни

1. **Header:** `major` → 9 (historical), add `superseded-by` pointer
2. **Note:** "RATIFIED..." → "HISTORICAL Contract 9.0 — superseded by #1703/#1663"
3. **Relabel obsolete invariants:** `core-profile-law`, `sid-00000111-control`, `error-classification`
4. **Add supersession pointers:** #1703 (foundation), #1663 (2-part COND), #1713 (Predicate1), #1714 (runtime)
5. **Preserve canonical invariants** unchanged

---

## Запропонований оновлений `language-contract.lisp`

```lisp
; language-contract.lisp — HISTORICAL Contract 9.0 — superseded by #1703/#1663
; Історичний Contract 9.0 — замінено #1703/#1663.
; Contract 9.0 ratified by owner 2026-09-24.
; Breaking conceptual change: sens (СЕНС) has exactly one function-identity space.
; Every function identity is exactly eight bits: 00000000..11111111.
; No word, symbol, string, enum label, historical name, opcode, backend name or
; host mechanism is a second function identity.
;
; SUPERSEDED: #1703 (one foundation law Core1–4), #1663 (2-part COND),
; #1713 (Predicate1), #1714 (runtime COND migration).
; Current authoritative contract: see #1703, #1663, #1713, #1714.
;
; Contract 9.0 ratified by owner 2026-09-24.
; Breaking conceptual change: sens (СЕНС) has exactly one function-identity space.
; Every function identity is exactly eight bits: 00000000..11111111.
; No word, symbol, string, enum label, historical name, opcode, backend name or
; host mechanism is a second function identity.
;
; Core profiles may assign different laws/results/mechanisms to the same SID.
; They do not create new identities.
;
; Current executable reality after #1332: () is a structural empty value outside
; the complete 00000000..11111111 function space. Function 00000000 is not ().
; The remaining SID/Sid8 -> SENS vocabulary migration is tracked by #1384.

((major . 9) (minor . 0)
 (superseded-by . (#1703 #1663 #1713 #1714))
 (status . historical-superseded)
 (note . "HISTORICAL Contract 9.0 — superseded by #1703/#1663. RATIFIED by owner 2026-09-24. Contract 9.0 established sens (СЕНС) with one and only one function-identity space: exact eight-bit SIDs 00000000..11111111. Human surfaces and implementation labels are non-authoritative projections only. Core profiles select laws over the same SID. #1332 is complete in current executable reality: () is a structural value outside the function space and 00000000 is not the empty-list value. Vocabulary reconciliation to SENS-native terms continues under #1384. SUPERSEDED: #1703 (one foundation law), #1663 (2-part COND), #1713 (Predicate1), #1714 (runtime).")
 (covers . (G1 G2 G3 G4 G5 G6 G7 G8 S1 S2 S3))
 (invariants
   . ((sid8-function-space
       . "The complete function-identity space is exactly 00000000..11111111. All 256 slots are reserved exclusively for functions. A function identity is the eight bits themselves; it is not text, a string, a symbol, a literal, a decimal number, a human name, an enum label, an opcode, or a backend identifier.")
      (single-function-ontology
       . "There is no second named function ontology. Runtime, compiler IR, contracts, backends and tooling must not introduce named identities beside Sid8. Internal mechanism metadata may describe how an already-selected SID executes, but may never rename or redefine the function.")
      (surface-non-authority
       . "Human-language and symbolic surfaces are optional source/UI routing metadata only. A surface may resolve mechanically to Sid8; it never creates a function, owns meaning, or becomes an identity. No name->meaning->SID or SID->named-meaning layer is authoritative.")
      (core-profile-law
       . "OBSOLETE — Core1–4 now share ONE foundation law per #1703. Historical: Core1/Core2/Core3/Core4 were law profiles over the same Sid8 identities. Profile selection may change the admitted law/result/mechanism for a SID, but never its eight-bit identity and never the global function-ID space.")
      (kernel-archipelago
       . "Execution kernels may own native mechanisms and observations. They consume an already-selected Sid8 plus arguments/context and may return native observations. Kernel operator names, opcodes and native types never acquire sens function identity by themselves.")
      (sid-00000111-control
       . "OBSOLETE — superseded by #1663 (2-part COND) and #1713 (Predicate1). Historical: for the current Core4 law of SID 00000111, clauses had exactly three fields: (query expected-result expression), checked left-to-right, evaluated only the first matching expression, and failed with UnsatisfiedConditional on exhaustion. Older Core profiles may have retained their separately pinned law for the same SID.")
      (reader-apostrophe
       . "At expression start, apostrophe is reader sugar whose produced list head is SID 00000001 directly. It must not create an intermediate named function identity. Inside an identifier, apostrophe remains an ordinary Unicode character.")
      (reader-eight-bits
       . "Exactly eight bare 0/1 source characters are read directly into Sid8. The reader does not reinterpret them as decimal or binary numeric data and does not wrap them in String/Symbol.")
      (reader-decimal-separator
       . "Dot and comma are equivalent decimal separators only for otherwise valid finite decimal/base-10 scientific numeric input. Non-numeric tokens retain their ordinary data behavior; this rule never affects Sid8.")
      (error-classification
       . "OBSOLETE — superseded by #1663 (2-part COND exhaustion → structural `()`). Historical: ErrorKind remains observable semantics. UnsatisfiedConditional was the exhaustion failure for the current Core4 law of SID 00000111; existing named error categories remained observable until separately migrated.")
      (migration-debt-00000000
       . "Historical #1332 migration debt is complete in the current runtime: () is represented as a structural empty value outside the function space, and function 00000000 is not the empty-list value and receives no replacement ground-value identity."))))

