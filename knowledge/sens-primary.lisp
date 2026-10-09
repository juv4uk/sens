; knowledge/sens-primary.lisp
; Status: operational doctrine (not language-contract authority).
; Issues: #1590 #3020 #4248 #4247 #4250
; Rule: SENS-primary exact-width binary authority; human names are projections.
;
; This file does not create semantic authority. It records how agents and
; mechanisms must consume the ratified contract without recreating a textual,
; byte-width, opcode, or backend-owned surrogate.

(sens-primary/2
  (status operational)
  (issues 1590 3020 4248 4247 4250)
  (updated 2026-10-08)

  (vertical
    (ідентичність exact-domain-bits)
    (law language-owned)
    (source-structure d2-binary)
    (storage mechanism-only)
    (transport mechanism-only)
    (execution witness-only)
    (human-projection derived-only))

  (identity-law
    (canonical-object exact-domain exact-bits domain-law)
    (width part-of-identity)
    (cross-domain-equal-payload not-equal-identity)
    (examples
      (D1 1)
      (D2 01)
      (D3 001)
      (D4 0001))
    (universal-eight-bit-space false))

  (current-foundation
    (contract 11 8)
    (ratified-domains D1 D2 D3 D4 D5 D6 D7 D8 D9)
    (D10 research-unratified))

  (axioms
    (1 (sens-is-not text string quoted-literal decimal-semantic-id
                    english-name ukrainian-name sanskrit-name host-opcode))
    (2 (sens-is-not compiled-executable object-file fasl bytecode-artifact))
    (3 (semantic-width not-equal host-container-width))
    (4 (carrier may-widen-storage without-changing-identity))
    (5 (human-names are projections generated-from-binary-authority))
    (6 (backends rust c common-lisp prolog datalog clips fpga wasm
         are witnesses not meaning-sources))
    (7 (legacy sens8 sid8 function8 u8
         compatibility-provenance-only not-universal-identity))
    (8 (packed-transport preserves exact-width-sequence
         without byte-padding-as-semantics))
    (9 (no parallel canonical ідентичність beside exact-domain-bits))
    (10 (conflict historical-lisp-vs-sens-clarity -> sens-wins
          compatibility-built-on-top)))

  (source
    (canonical visible-binary)
    (structure-domain D2
      (separator 00)
      (close 01)
      (open 10)
      (dot 11))
    (semantic-words exact-width)
    (word-boundaries presentation-visible)
    (human-reader explicit-projection-or-compatibility only)
    (no-silent-name-fallback))

  (transport
    (packed-bitstream preferred-when-transporting)
    (byte-container allowed-as-mechanism)
    (one-byte-per-value not-canonical)
    (container-size not-semantic-width)
    (framing not-identity))

  (projection
    (surfaces uk ukr sa en LISP sym historical-compatibility)
    (direction binary-authority -> human-projection)
    (reverse-direction not-authority)
    (rename-preserves-identity true))

  (design-question
    "Як би система виглядала, якби exact-width binary SENS був первинним з 1958,
     а людські назви, storage containers і backends з'явилися пізніше?")

  (classification-question
    "На якому шарі ця властивість: identity, law, D2 source structure,
     storage container, transport/framing, execution mechanism чи projection?")

  (anti-patterns
    (treat-u8-as-language-width)
    (treat-binary-as-compiled-executable)
    (recover-meaning-from-human-name)
    (recover-meaning-from-opcode)
    (zero-pad-or-truncate-between-domains)
    (byte-align-each-semantic-word)
    (backend-defines-sens-meaning)
    (text-as-sens-identity-in-core)
    (second-canonical-function-id-layer)))
