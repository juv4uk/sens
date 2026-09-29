; language-contract.lisp — current machine-readable Level 1/2 contract.
;
; Contract 10.0 target ratified by owner 2026-09-29 under #1694.
; Breaking conceptual change: canonical sens (СЕНС) has exactly three payload
; domains outside parenthesized structure: Function, Number, Text.
;
; Function is the complete exact 8-bit space 00000000..11111111.
; Number is the binary-first numeric domain, kept orthogonal to Function.
; Text is a sequence of exact UPC-7 codes and never a runtime dispatch key.
;
; Binary-only language law:
;   canonical SENS semantic identity/data/control is owned only by bits.
;   Human names, decimal spellings, Unicode/UTF-8, symbols and host labels
;   are projections/metadata outside the canonical language boundary.
;
; Active width constitution:
;   predicate answer = exact 1 bit: 0 NO, 1 YES
;   default lexical/control cell = exact 2 bits
;   text code = exact 7 bits (UPC-7)
;   function identity = exact 8 bits
;
; Default 2-bit cells:
;   00 = real canonical SPACE/separator
;   01 = close structure
;   10 = open structure
;   11 = typed-payload escape
;
; The canonical language does not target a whitespace-free continuous bitstream.
;
; Parentheses define structure/composition; they do not create a fourth payload
; domain. Symbol/name/container-layout/host-tag are not canonical language
; ontologies. Human names and decimal notation are frontend projections only.
;
; This file is a migration target on branch contract/1694-three-payload-v10.
; Merge requires the executable gates tracked by #1694; current main still
; contains Symbol/decimal-reader/runtime representation debt.

((major . #d10) (minor . 0)
 (note . "RATIFIED TARGET by owner 2026-09-29 under #1694/#1702. Canonical sens (СЕНС) has exactly three payload domains: Function, Number, Text, plus two-bit lexical/structural control. Default cells are 00 SPACE, 01 close, 10 open, 11 typed-payload escape. Predicate answers are exactly one bit: 0 NO, 1 YES. Function is exact eight-bit 00000000..11111111; Text is exact seven-bit UPC-7; Number is binary-first and explicitly framed. The language keeps real canonical separators and does not target a whitespace-free continuous bitstream.")
 (covers . (G1 G2 G3 G4 G5 G6 G7 G8 S1 S2 S3))
 (invariants
   . ((binary-only-language
       . "Canonical sens is binary-only. Every canonical semantic identity, value, predicate result and lexical/control form is owned by an exact bit representation. Human names, decimal/hex spellings, Unicode/UTF-8 code points, symbols, host enum labels, booleans and textual opcodes may exist only before lowering or as debug/provenance/mechanism metadata; none may be required to recover canonical meaning.")
      (binary-domain-orthogonality
       . "Binary-only does not collapse domains. Width plus semantic context owns interpretation: one-bit predicate result, two-bit lexical/control cell, seven-bit UPC-7 Text code, eight-bit Function identity, and N-bit Number remain orthogonal even when their physical bit patterns overlap. No implicit coercion is permitted by bit-pattern coincidence.")
      (human-boundary-one-way
       . "Human/UI spellings resolve or encode exactly once into canonical bits. Canonical evaluator/compiler/FASL/wire/islands must not perform bits-to-name-to-bits, decimal-string-to-number, Unicode-to-Text identity recovery, or any equivalent semantic round trip.")
      (bit-width-constitution
       . "Active widths are role-specific: predicate result is exactly one bit (0 NO, 1 YES); the default lexical/control layer is exactly two bits; Text uses exact seven-bit UPC-7 codes; Function uses exact eight-bit identities. Number is binary and explicitly framed. The former 1..7-bit predicate gradation is inactive.")
      (default-two-bit-language
       . "The canonical reader defaults to two-bit cells: 00 is a real SPACE/separator, 01 closes structure, 10 opens structure, and 11 escapes to a typed payload. Separators are part of the canonical representation where grammar requires them and are not optional padding.")
      (no-continuous-stream-goal
       . "Canonical sens does not optimize away all separators to form a whitespace-free continuous bitstream. Number/Text framing exists only to delimit their own payloads safely; it does not remove the real 00 SPACE cells from canonical syntax.")
      (predicate-one-bit
       . "Predicate results are exactly one bit: 1 means YES and 0 means NO. No 00/11/etc. strength or width gradation is active. The one-bit result is consumed in predicate-result context and is not a free-standing default two-bit lexical token.")
      (three-payload-ontology
       . "Outside parenthesized structure, canonical sens has exactly three payload domains: Function, Number, and Text. No Symbol, identifier, predicate-answer wrapper, container layout, host tag, enum label, opcode, or backend-native object may become a fourth fundamental language payload domain.")
      (parentheses-are-structure
       . "Opening and closing parentheses express structure/composition only. List, pair, vector, map, record, buffer, or other container shapes may be structural or mechanism representations, but their representation does not mint a new atomic language ontology. The empty () remains structural emptiness outside the 256 function slots.")
      (text-upc7-data
       . "Text is a sequence of exact seven-bit UPC-7 identities 0000000..1111111 derived from the shiva-sutras UPC prototype. Human layouts/profiles map spellings to and from the same UPC-7 code stream without changing code identity. Unicode/UTF-8 may exist only at host/UI boundaries and is never a canonical Text identity.")
      (no-canonical-symbol
       . "Canonical sens has no Symbol payload category. Human function names resolve to Function before canonical execution; human local names resolve to lexical slots; textual data is Text; unknown bare words fail closed in canonical mode instead of becoming symbols.")
      (locals-are-slots-not-names
       . "Local variable spellings are human/debug metadata only. After resolution, canonical execution addresses locals by structural numeric slot/index/depth information and does not depend on the selected UPC-7 human layout spelling of a local name.")
      (binary-number-domain
       . "Number is a language-owned numeric domain distinct from Function even when physical bits coincide. Canonical numeric source/serialization is binary-owned; decimal exact-rational notation is a human or explicitly transitional projection and may not become a second canonical numeric semantics.")
      (derived-layout-non-ontology
       . "Numeric buffers, vectors, maps, records, island observations, machine bytes, and optimized layouts are either structures composed from the three payload domains or mechanism representations with parity witnesses. Optimization never creates a fourth semantic value domain.")
      (predicate-answer-projection
       . "Predicate semantics are strictly binary in the active language: exact one-bit 1 YES or 0 NO. A standalone multi-width PredicateAnswer domain and the historical 1..7-bit gradation are inactive and must not affect reader, evaluator, FASL, wire, or COND.")
      (atom-one-bit-core1-4
       . "Function 00000010 is the same atomic/non-pair predicate across Core1, Core2, Core3 and Core4: structural empty () -> 1, any admitted non-pair atomic value -> 1, pair -> 0. It does not return structural-kind. The empty structure is an ATOM-yes subject but is not itself a truth value.")
      (eq-one-bit-core1-4
       . "Function 00000011 is the same admitted-atom identity predicate across Core1, Core2, Core3 and Core4: same atom -> 1, distinct atoms -> 0, pair/outside-domain -> named type/domain failure. It does not return identity-relation and is not deep structural equality.")
      (sid8-function-space
       . "The complete function-identity space is exactly 00000000..11111111. All 256 slots are reserved exclusively for functions. A function identity is the eight bits themselves; it is not text, a string, a symbol, a literal, a decimal number, a human name, an enum label, an opcode, or a backend identifier.")
      (single-function-ontology
       . "There is no second named function ontology. Runtime, compiler IR, contracts, backends and tooling must not introduce named identities beside Sid8. Internal mechanism metadata may describe how an already-selected SID executes, but may never rename or redefine the function.")
      (surface-non-authority
       . "Human-language and symbolic surfaces are optional source/UI routing metadata only. A surface may resolve mechanically to Sid8; it never creates a function, owns meaning, or becomes an identity. No name->meaning->SID or SID->named-meaning layer is authoritative.")
      (core-profile-law
       . "Core1/Core2/Core3/Core4 are law profiles over the same Sid8 identities. Profiles may differ outside the shared foundation, but Function 00000010 ATOM, 00000011 EQ, and 00000111 COND have one shared predicate/control law across all four cores.")
      (kernel-archipelago
       . "Execution kernels may own native mechanisms and observations. They consume an already-selected Sid8 plus arguments/context and may return native observations. Kernel operator names, opcodes and native types never acquire sens function identity by themselves.")
      (sid-00000111-control
       . "Target law for SID 00000111 is the canonical two-part COND clause (test expression) across Core1-Core4. A test activates its expression only on exact one-bit YES=1; NO=0 skips the clause. Historical three-part expected-result clauses and graded predicate answers are migration debt, not target semantics.")
      (reader-apostrophe
       . "At expression start, apostrophe may exist as human/compatibility reader sugar whose produced list head is Function 00000001 directly. It must disappear before canonical execution and may not create an intermediate Symbol or named function identity.")
      (reader-eight-bits
       . "Exactly eight bare 0/1 source characters are read directly into Sid8. The reader does not reinterpret them as decimal or binary numeric data and does not wrap them in String/Symbol.")
      (reader-binary-number-default
       . "Canonical numeric reading is binary-first and must preserve exact numeric meaning without coercing exact eight-bit Function tokens. Decimal/scientific/rational human notation may be accepted only by a human/transition projection that lowers to Number before canonical execution; malformed canonical tokens fail closed rather than becoming Symbol.")
      (error-classification
       . "ErrorKind remains observable semantics. UnsatisfiedConditional is the exhaustion failure for the current Core4 law of SID 00000111; existing named error categories remain observable until separately migrated.")
      (migration-debt-00000000
       . "Historical #1332 migration debt is complete in the current runtime: () is represented as a structural empty value outside the function space, and function 00000000 is not the empty-list value and receives no replacement ground-value identity."))))
