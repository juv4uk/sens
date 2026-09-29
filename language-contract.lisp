; language-contract.lisp — current machine-readable Level 1/2 contract.
;
; Contract 10.0 target ratified by owner 2026-09-29 under #1694.
; Breaking conceptual change: canonical sens (СЕНС) has exactly three payload
; domains outside parenthesized structure: Function, Number, Text.
;
; Function is the complete exact 8-bit space 00000000..11111111.
; Number is the binary-first numeric domain, kept orthogonal to Function.
; Text is UTF-8 data and never a runtime dispatch key.
;
; Parentheses define structure/composition; they do not create a fourth payload
; domain. Symbol/name/container-layout/host-tag are not canonical language
; ontologies. Human names and decimal notation are frontend projections only.
;
; This file is a migration target on branch contract/1694-three-payload-v10.
; Merge requires the executable gates tracked by #1694; current main still
; contains Symbol/decimal-reader/runtime representation debt.

((major . #d10) (minor . 0)
 (note . "RATIFIED TARGET by owner 2026-09-29 under #1694. Canonical sens (СЕНС) has parenthesized structure plus exactly three payload domains: Function, Number, Text. Function is exact eight-bit 00000000..11111111; Number is binary-first and orthogonal to Function; Text is UTF-8 data. Symbol/name/container-layout/host-tag are not fourth language ontologies. Human names and decimal notation are projections that must lower before canonical execution. Merge of Contract 10.0 requires executable conformance for #1694.")
 (covers . (G1 G2 G3 G4 G5 G6 G7 G8 S1 S2 S3))
 (invariants
   . ((three-payload-ontology
       . "Outside parenthesized structure, canonical sens has exactly three payload domains: Function, Number, and Text. No Symbol, identifier, predicate-answer wrapper, container layout, host tag, enum label, opcode, or backend-native object may become a fourth fundamental language payload domain.")
      (parentheses-are-structure
       . "Opening and closing parentheses express structure/composition only. List, pair, vector, map, record, buffer, or other container shapes may be structural or mechanism representations, but their representation does not mint a new atomic language ontology. The empty () remains structural emptiness outside the 256 function slots.")
      (text-utf8-data
       . "Text is UTF-8 data. Text bytes and human spellings never select runtime semantics after lowering. KOI8, Char8, host strings, and other encodings may exist only as boundary/mechanism representations with explicit projection to Text.")
      (no-canonical-symbol
       . "Canonical sens has no Symbol payload category. Human function names resolve to Function before canonical execution; human local names resolve to lexical slots; textual data is Text; unknown bare words fail closed in canonical mode instead of becoming symbols.")
      (locals-are-slots-not-names
       . "Local variable spellings are human/debug metadata only. After resolution, canonical execution addresses locals by structural numeric slot/index/depth information and does not depend on the UTF-8 spelling of a local name.")
      (binary-number-domain
       . "Number is a language-owned numeric domain distinct from Function even when physical bits coincide. Canonical numeric source/serialization is binary-owned; decimal exact-rational notation is a human or explicitly transitional projection and may not become a second canonical numeric semantics.")
      (derived-layout-non-ontology
       . "Numeric buffers, vectors, maps, records, island observations, machine bytes, and optimized layouts are either structures composed from the three payload domains or mechanism representations with parity witnesses. Optimization never creates a fourth semantic value domain.")
      (predicate-answer-projection
       . "Predicate YES/NO laws may remain language semantics, but their representation must project into Number or structure built from Function/Number/Text. A standalone PredicateAnswer or truth wrapper is not a fourth fundamental payload domain.")
      (sid8-function-space
       . "The complete function-identity space is exactly 00000000..11111111. All 256 slots are reserved exclusively for functions. A function identity is the eight bits themselves; it is not text, a string, a symbol, a literal, a decimal number, a human name, an enum label, an opcode, or a backend identifier.")
      (single-function-ontology
       . "There is no second named function ontology. Runtime, compiler IR, contracts, backends and tooling must not introduce named identities beside Sid8. Internal mechanism metadata may describe how an already-selected SID executes, but may never rename or redefine the function.")
      (surface-non-authority
       . "Human-language and symbolic surfaces are optional source/UI routing metadata only. A surface may resolve mechanically to Sid8; it never creates a function, owns meaning, or becomes an identity. No name->meaning->SID or SID->named-meaning layer is authoritative.")
      (core-profile-law
       . "Core1/Core2/Core3/Core4 are law profiles over the same Sid8 identities. Profile selection may change the admitted law/result/mechanism for a SID, but never its eight-bit identity and never the global function-ID space.")
      (kernel-archipelago
       . "Execution kernels may own native mechanisms and observations. They consume an already-selected Sid8 plus arguments/context and may return native observations. Kernel operator names, opcodes and native types never acquire sens function identity by themselves.")
      (sid-00000111-control
       . "For the current Core4 law of SID 00000111, clauses have exactly three fields: (query expected-result expression), are checked left-to-right, evaluate only the first matching expression, and fail with UnsatisfiedConditional on exhaustion. Older Core profiles may retain their separately pinned law for the same SID.")
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
