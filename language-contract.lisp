; language-contract.lisp — current machine-readable Level 1/2 contract.
;
; Contract 10.1 — domain-authority cutover under #2490/#2817/#2822.
;
; The observable PredicateBit / ATOM / EQ / COND law of Contract 10.0 is
; preserved. What changes here is identity authority:
;
;   semantic object = exact binary number + exact domain + proved/ratified law
;
; The earlier flat Function8/Sens8 ontology is historical compatibility
; provenance. Its exact Contract 10.0 authority text is frozen at:
;
;   contracts/history/language-contract-10.0-flat-function8.lisp
;
; Historical exact-8 transport/backend projections may remain during migration,
; but they cannot mint or redefine canonical domain identity.

((major . #d10) (minor . 1)
 (status . current-domain-qualified-authority)
 (note . "Contract 10.1 implements the #2490/#2817 domain-authority cutover while preserving the observable Contract 10 PredicateBit/ATOM/EQ/COND law. Canonical identity is an exact binary object in an exact domain under a proved or ratified law. Flat Function8/Sens8 is compatibility/history only and cannot override D1-D6 domain authority. Contract 10.0 is preserved verbatim under contracts/history/language-contract-10.0-flat-function8.lisp.")
 (history . "Contract 10.0 flat Function8 authority is NON-NORMATIVE provenance after #2822.")
 (covers . (G1 G2 G3 G4 G5 G6 G7 G8 S1 S2 S3))
 (invariants
   . ((binary-domain-identity
       . "Every canonical semantic object is identified by its exact binary number together with its exact domain and the proved or ratified law that interprets that object in that domain. Equal packed numeric payloads in different widths or domains are not thereby the same identity.")
      (domain-non-inference
       . "Bits or width alone never mint semantic membership, occupancy, callability, or meaning. Domain admission is an explicit typed/law-backed claim. A free coordinate remains unallocated until admitted by the owning domain.")
      (legacy-sens8-compatibility
       . "Historical Sens8/Sid8/Function8 values may remain only as explicitly named compatibility, transport, provenance, or backend mechanism projections during migration. They are not the universal semantic identity and cannot compare equal to a domain-qualified object merely by packed bits.")
      (no-width-coercion
       . "Zero-padding, truncation, low-nibble extraction, integer equality, or any other width-changing transform cannot create or recover canonical domain identity unless a separately proved role-aware projection law explicitly authorizes that compatibility conversion.")
      (surface-non-authority
       . "Human-language and symbolic surfaces are optional source/UI routing metadata only. A surface may resolve mechanically to an already-admitted domain-qualified identity or to an explicitly legacy compatibility projection; it never creates semantic identity, owns meaning, or becomes authority.")
      (predicate-one-bit
       . "D1 PredicateBit answers are exactly one contextual bit: 1 means YES and 0 means NO. PredicateBit is not Number, host Bool, T/NIL, Symbol, structural (), or any wider domain value. No third predicate answer and no graded-width truth value is active.")
      (structure-two-bit
       . "D2/racana2 is exact two-bit structural syntax under its ratified law: 00 separator, 01 close, 10 open, 11 dot. These words are structure-domain objects and are not numeric or callable identities merely because they are binary.")
      (d3-foundation
       . "D3/bija3 is the exact three-bit Core foundation: 000 structural empty (), 001 QUOTE, 010 ATOM, 011 COND, 100 CONS, 101 CAR, 110 CDR, 111 EQ. Human role names are documentation projections. Historical eight-bit forms, where still required, are explicit role-aware compatibility projections rather than canonical D3 identity.")
      (d4-bootstrap
       . "Core.D4 is the exact four-bit bootstrap domain ratified by #2169. Its residents execute only under D4 law; 0101 and 1001 remain unallocated. No historical Function8 identity may be reconstructed from a D4 word by zero extension, low-nibble matching, or visual resemblance.")
      (later-core-domain-residency
       . "Core.D5 and Core.D6 residency is owned by their ratified owner maps/laws. Residency, derivability, callability and runtime implementation are separate facts: a resident may be derived, and an implemented carrier does not by itself make every coordinate callable.")
      (atom-one-bit-core1-4
       . "D3 010 ATOM has one law across Core1/Core2/Core3/Core4: structural empty () and every admitted non-pair value answer PredicateBit 1; pair answers PredicateBit 0. Structural () is an ATOM-yes subject, not a truth value. Historical Function8 00000010 is compatibility projection only.")
      (eq-one-bit-core1-4
       . "D3 111 EQ has one law across Core1/Core2/Core3/Core4: the same admitted atom answers PredicateBit 1; distinct admitted atoms answer PredicateBit 0; pair/out-of-domain input raises the named domain/type failure. EQ is not deep structural equality. Historical Function8 00000011 is compatibility projection only.")
      (core-profile-law
       . "Core1/Core2/Core3/Core4 are law profiles over the same admitted domain identities. Profiles may differ outside the shared foundation, but they may not assign different observable laws/results to D3 010 ATOM, D3 111 EQ, or D3 011 COND.")
      (kernel-archipelago
       . "Execution kernels may own native mechanisms and observations. They consume an already-selected domain-qualified semantic object or an explicitly compatibility-tagged legacy projection plus arguments/context. Kernel operator names, opcodes, packed bytes and native types never acquire SENS semantic identity by themselves.")
      (d3-011-control
       . "D3 011 COND has one law across Core1/Core2/Core3/Core4. Every clause has exactly two fields: (test expression). Tests are evaluated left-to-right and must return exact PredicateBit. PredicateBit 1 selects and evaluates that clause expression; PredicateBit 0 skips it. If no clause selects, COND returns structural (). Structural () is not a predicate answer. Historical Function8 00000111 is compatibility projection only.")
      (reader-apostrophe
       . "At expression start, apostrophe is reader sugar for the already-admitted D3 001 QUOTE identity. It must not create an intermediate human or legacy eight-bit semantic identity. Inside an identifier, apostrophe remains an ordinary Unicode character.")
      (reader-exact-width
       . "Canonical binary reading must preserve exact word width and payload. A syntactically valid binary word is not automatically admitted to a semantic domain merely from width. Bare historical eight-bit forms may remain only in explicitly compatibility-owned reader paths while domain-qualified source admission migrates.")
      (reader-decimal-separator
       . "Dot and comma are equivalent decimal separators only for otherwise valid finite decimal/base-10 scientific numeric input. Non-numeric tokens retain their ordinary boundary behavior; this numeric projection rule never mints Core domain identity.")
      (error-classification
       . "Named error categories remain observable where separately admitted, but UnsatisfiedConditional is not the exhaustion law of D3 011 COND. Any remaining producer or witness for three-part COND exhaustion is transition debt and must not override the current shared foundation.")
      (legacy-eight-zero
       . "Historical exact-8 00000000 is not structural empty and is not an alias for D3 000. Canonical structural empty belongs to its admitted exact domain/law; equal packed numeric zero across different domains does not collapse identity."))))