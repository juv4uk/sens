; knowledge/sens-primary.lisp
; Статус: operational doctrine (не language-contract).
; Parent authority: language-contract.lisp Contract 11.0.
; Issue: #1590 / migration #2817 / doctrine repair #2893.
;
; Це не створює нову semantic authority і не змінює language-contract.lisp.
; Це machine-readable operational doctrine: SENS первинний, але його поточна
; identity вже не є flat Sens8. Канонічна семантична identity:
;
;   exact binary object + exact domain + proved / ratified law
;
; Historical Sens8/Sid8/Function8 survives only at explicit compatibility,
; transport, backend or provenance boundaries.

(sens-primary/2
  (status operational)
  (issue 1590)
  (migration 2817)
  (updated 2026-10-03)

  (vertical
    (identity domain-qualified-binary)
    (meaning language-law)
    (execution witness-only))

  (identity-law
    (canonical
      (exact-bits required)
      (exact-domain required)
      (proved-or-ratified-law required))
    (equal-packed-payload-across-domains not-identity)
    (width-alone not-semantic-membership)
    (zero-padding forbidden)
    (truncation forbidden)
    (low-bit-reconstruction forbidden))

  (core-domains
    (D1 exact-one-bit predicate)
    (D2 exact-two-bit structure)
    (D3 exact-three-bit foundation)
    (D4 exact-four-bit bootstrap)
    (D5 exact-five-bit typed-domain)
    (D6 exact-six-bit typed-domain)
    (residency callability derivability implementation distinct-facts))

  (axioms
    (1 (semantic-object exact-bits exact-domain admitted-law))
    (2 (domain is-interpretation-boundary not-inferred-from-payload-or-width))
    (3 (historical-sens8 compatibility-only transport backend provenance))
    (4 (historical-names car cdr cons eq atom cond plus
         are surface-only not-semantic-authority))
    (5 (semantic-core uses domain-qualified-identity not text-surrogate))
    (6 (backends rust c common-lisp prolog datalog clips fpga wasm
         are witnesses not meaning-sources))
    (7 (transport-preserves-identity but-does-not-create-it))
    (8 (no parallel canonical identity beside exact-domain-identity))
    (9 (conflict historical-flat-sens8-vs-current-domain-law
         -> current-domain-law-wins))
    (10 (identity not-callability))
    (11 (compatibility not-canonical-domain)))

  (design-question
    "Як би система виглядала, якби exact-domain SENS був первинним,
     а flat Sens8 та людські імена з'явилися лише пізніше як compatibility
     і surface projections?")

  (anti-pattern
    "Як відновити значення домену з восьми бітів, padding, low nibble,
     назви, host type або table position?")

  (forbidden
    (text-as-semantic-identity-in-core)
    (backend-defines-sens-meaning)
    (flat-sens8-as-universal-language-identity)
    (width-only-mints-semantic-membership)
    (implicit-cross-domain-coercion)
    (english-name-stronger-than-domain-law))

  (allowed-surfaces
    (uk ukr en sa sym historical-compatibility))

  (compatibility
    (sens8 explicit-only)
    (sid8 explicit-only)
    (function8 explicit-only)
    (reverse-byte-to-domain-inference forbidden))

  (transport
    (role preserve-not-define-identity)
    (legacy-exact8 explicit-compatibility-only)
    (domain-qualified exact-width-and-payload)
    (display bit-string-ok-as-projection-not-identity)))
