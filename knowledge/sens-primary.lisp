; knowledge/sens-primary.lisp
; Статус: operational doctrine (не language-contract).
; Issue: #1590
; Рамка: SENS первинний; англійські/інші імена — лише surface.
;
; Це не створює нову semantic authority і не змінює language-contract.lisp.
; Це machine-readable нагадування: як проєктувати, ніби SENS був первинним
; з самого початку, а не «прикрученим» до історичного Lisp.

(sens-primary/1
  (status operational)
  (issue 1590)
  (updated 2026-09-28)

  (vertical
    (identity sens8)
    (meaning language-law)
    (execution witness-only))

  (axioms
    (1 (function-space exact-256 00000000 11111111))
    (2 (each-sens exactly-eight-bits))
    (3 (sens-is-not text string quoted-literal decimal-number english-name))
    (4 (historical-names car cdr cons eq atom cond plus
         are surface-only not-semantic-authority))
    (5 (semantic-core uses sens-identity not text-surrogate))
    (6 (backends rust c common-lisp prolog datalog clips fpga wasm
         are witnesses not meaning-sources))
    (7 (prefer one-byte transport over temporary text encoding of sens))
    (8 (no parallel canonical identity beside sens))
    (9 (conflict historical-lisp-vs-sens-clarity -> sens-wins
         compatibility-built-on-top)))

  (design-question
    "Як би система виглядала, якби SENS був первинним з 1958,
     а англійські імена з'явилися лише пізніше як surface?")

  (anti-pattern
    "Як прикрутити SENS до звичного Lisp?")

  (forbidden
    (text-as-sens-identity-in-core)
    (backend-defines-sens-meaning)
    (second-canonical-function-id-layer)
    (english-name-stronger-than-sens))

  (allowed-surfaces
    (uk ukr en sa sym historical-compatibility))

  (transport
    (preferred packed-byte-one-way)
    (source-reader exact-eight-0-1-digits-ok)
    (display eight-bit-string-ok-as-projection-not-identity)))
