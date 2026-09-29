; binary-only-language-contract.lisp — binary-only canonical SENS law.
;
; Owner decision: 2026-09-29, #1706.
;
; This contract describes canonical language representation, not human display.
; Human/UI/host layers may use names, decimal numerals, Unicode, parentheses,
; and implementation-native objects, but must lower/project them before
; canonical execution.

(binary-only-language-contract/1
  (owner sens)
  (status ratified-target)
  (governing-issue 1706)

  (canonical-alphabet (0 1))
  (nonbinary-semantic-authority forbidden)

  (widths
    (predicate-result 1)
    (default-lexical-control 2)
    (text-code 7)
    (function-identity 8)
    (number variable-binary))

  (control2
    (00 space)
    (01 close-structure)
    (10 open-structure)
    (11 typed-payload-escape))

  (human-structure-projection
    (left-parenthesis -> 10)
    (right-parenthesis -> 01)
    (space -> 00)
    (projection-role human-reader-only))

  (canonical-domains
    (predicate-result exact-one-bit)
    (control exact-two-bit)
    (text upc7-sequence)
    (function exact-eight-bit)
    (number exact-binary-variable-width))

  (domain-orthogonality
    (same-bits-do-not-imply-same-domain yes)
    (implicit-function-number-coercion forbidden)
    (implicit-text-number-coercion forbidden)
    (implicit-predicate-number-coercion forbidden)
    (implicit-control-number-coercion forbidden)
    (implicit-any-domain-coercion-by-host-cast forbidden))

  (human-boundary
    (function-name canonical-identity forbidden)
    (decimal-number canonical-identity forbidden)
    (hex-number canonical-identity forbidden)
    (unicode-code-point text-identity forbidden)
    (utf8-byte-sequence text-identity forbidden)
    (symbol canonical-payload forbidden)
    (local-name execution-identity forbidden)
    (host-bool predicate-identity forbidden)
    (host-enum semantic-identity forbidden))

  (allowed-noncanonical-roles
    human-input
    human-output
    debug-metadata
    source-map
    provenance
    transition-debt
    mechanism-private)

  (one-way-lowering
    (human-function-spelling -> function8)
    (human-number-spelling -> binary-number)
    (human-text-spelling -> upc7-text)
    (human-parenthesis -> control2)
    (human-local-name -> binary-lexical-coordinate))

  (forbidden-round-trips
    bits-name-bits
    function-host-integer-function
    unicode-canonical-text-unicode
    decimal-string-canonical-number-decimal-string
    host-bool-language-truth)

  (canonical-layers
    source
    ast
    ir
    fasl
    wire
    evaluator
    compiler
    island-boundary)

  (failure-law
    (unknown-nonbinary-canonical-token fail-closed)
    (malformed-width fail-closed)
    (cross-domain-bit-collision fail-closed))

  (principle
    "Canonical SENS meaning is owned by bits from the start; human notation is projection only."))