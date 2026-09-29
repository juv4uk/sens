; language-contract.lisp — current machine-readable Level 1/2 contract.
;
; Contract 10.0 candidate, 2026-09-29.
; Authority source: owner decisions #1706, #1694, #1703, #1663, #1699.
; This contract removes stale Contract 9.0 authority for three-part COND and
; Core-specific predicate/control laws. It does not claim unfinished runtime
; migrations are already mechanically complete.
;
; Canonical SENS is binary-only. Function identity is exact Function8
; (00000000..11111111). Predicate results are an orthogonal contextual one-bit
; domain. Human names, Unicode text, decimal notation and host labels are
; boundary/mechanism projections, not canonical semantic identity.

((major . 10) (minor . 0)
 (note . "Contract 10.0 candidate from owner decisions #1706/#1694/#1703/#1663/#1699. Canonical SENS is binary-only: Control2 structure, exact Function8 identities, binary exact Number, UPC-7 Text7, and contextual Predicate1. Core1/Core2/Core3/Core4 share one ATOM/EQ/COND foundation law. Three-part COND and UnsatisfiedConditional exhaustion authority from Contract 9.0 are superseded.")
 (covers . (G1 G2 G3 G4 G5 G6 G7 G8 S1 S2 S3))
 (invariants
   . ((binary-only-super-law
       . "Canonical SENS semantic identity is owned only by exact binary representations. Current fundamental domains are structural/control bits, exact Function8, exact binary Number, UPC-7 Text7, and contextual Predicate1. Human names, Unicode/UTF-8 spelling, decimal notation, host enum labels and backend names are boundary, debug, provenance or mechanism only.")
      (function8-space
       . "The complete function-identity space is exactly 00000000..11111111. All 256 exact eight-bit forms are reserved exclusively for functions. Function identity is the eight bits themselves; it is not text, a string, a symbol, a literal, a decimal number, a human name, an enum label, an opcode, or a backend identifier.")
      (single-function-ontology
       . "There is no second named function ontology. Runtime, compiler IR, contracts, backends and tooling must not introduce named identities beside Function8. Internal mechanism metadata may describe how an already-selected Function8 executes, but may never rename or redefine the function.")
      (surface-non-authority
       . "Human-language and symbolic surfaces are optional source/UI routing metadata only. A surface may resolve mechanically to Function8; it never creates a function, owns meaning, or becomes an identity. No name->meaning->Function8 or Function8->named-meaning layer is authoritative.")
      (domain-orthogonality
       . "Equal-looking bits in different domains are not interchangeable. Predicate1 1 is not Number 1; Control2 00 is not Number 0; Text7 0000000 is not Number 0; Function8 00000010 is not Number 2. Width plus semantic domain owns meaning; no implicit coercion follows from shared bit patterns.")
      (predicate1-law
       . "Predicate results are exactly one contextual bit: 1 means YES and 0 means NO. There is no third predicate value, no active graded 1^n/0^n truth law, and structural () is never a predicate answer. Predicate1 is not Number and has no numeric alias.")
      (shared-foundation-law
       . "Core1, Core2, Core3 and Core4 share one foundation law for Function8 00000010 (ATOM), 00000011 (EQ), and 00000111 (COND). Core profiles may differ elsewhere, but must not redefine these predicate/control identities.")
      (sid-00000010-atom
       . "Function8 00000010 asks whether its argument is atomic/non-pair. Pair returns Predicate1 0. Structural empty () and every admitted non-pair value return Predicate1 1.")
      (sid-00000011-eq
       . "Function8 00000011 is atom-domain identity. The same admitted atom returns Predicate1 1; distinct admitted atoms return Predicate1 0; pair or other out-of-domain input produces the named domain/type failure owned by the active contract.")
      (sid-00000111-control
       . "Function8 00000111 accepts only two-field clauses (test expression), checked left-to-right. Predicate1 1 selects and evaluates expression; Predicate1 0 skips the clause; any other test result is a named contract/type failure. Exhaustion returns structural () and does not create a predicate value.")
      (structural-empty-law
       . "Structural () is data/empty structure outside the Function8 space and outside Predicate1. It may be returned by COND exhaustion, but it is never FALSE, never a third truth value, and never aliases function 00000000.")
      (core-profile-law
       . "A core profile selects implementation/library behavior over the single Function8 space. It may not mint identities, change the shared ATOM/EQ/COND foundation, or promote host/mechanism labels to SENS semantics.")
      (kernel-archipelago
       . "Execution kernels may own native mechanisms and observations. They consume already-resolved SENS identities/data plus arguments/context. Kernel operator names, opcodes and native types never acquire SENS semantic identity by themselves.")
      (reader-apostrophe
       . "At the human source boundary, apostrophe at expression start is reader sugar whose produced list head is Function8 00000001 directly. It must not create an intermediate named function identity. Inside explicit human text, apostrophe remains ordinary boundary text before Text7 encoding.")
      (reader-eight-bits
       . "Exactly eight bare 0/1 source characters in function position are read directly as Function8. The reader must not reinterpret them as decimal or generic numeric data and must not wrap them in String/Symbol.")
      (human-number-boundary
       . "Decimal and rational notation may exist as human/source presentation, but canonical Number meaning is exact binary and must not depend on retaining the original decimal spelling.")
      (text7-boundary
       . "Canonical Text identity is UPC-7/Text7. Unicode/UTF-8 is permitted at human/UI/host boundaries only and must lower reversibly to Text7 where the layout admits the text.")
      (migration-status
       . "This contract states active language law. Open implementation migrations remain implementation debt and must converge to this law; their incomplete state does not re-authorize superseded Contract 9.0 semantics."))))
