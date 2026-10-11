; Executable Lisp-owned witness for the canonical semantic registry.
; Registry occupancy and the full 8-bit Binary value domain are deliberately
; separate: 11111111 must round-trip as Binary even though it is not currently
; an admitted semantic-registry row.

(0011 semantic-registry-self-hosted-witness
  (0010 (source)
    (001001 ((registry (semantic-registry-read-source source))
           (rows (semantic-registry-rows registry))
           (quote-row (semantic-registry-row-in registry 00000001))
           (quote-id (semantic-registry-id-in registry 'quote))
           (invoke-id (semantic-registry-id-in registry 'invoke))
           (leading-zero-row (semantic-registry-row-in registry 00000101))
           (max-roundtrip (semantic-registry-round-trip 11111111))
           (invoke-roundtrip (semantic-registry-round-trip 10101000)))
      (1110
        (000000 rows)
        (11110100 (semantic-registry-row-id quote-row))
        (semantic-registry-surface-name 'en quote-row)
        (11110100 quote-id)
        (11110100 invoke-id)
        (11110100 (semantic-registry-row-id leading-zero-row))
        (11110100 max-roundtrip)
        (semantic-registry-row-in registry 11111111)
        (11110100 invoke-roundtrip)
        (11110111 invoke-roundtrip (semantic-registry-row-id (semantic-registry-row-in registry 10101000)))))))

; Machine-readable handoff for downstream consumers.
; Git commit pinning is provenance and stays outside language semantics.
; The digest is content identity of the exact canonical source bytes. The full
; parsed canonical rows are handed off directly, so Binary SID values are
; preserved without building a second identity projection or recursive shadow table.
(0011 semantic-registry-handoff-witness
  (0010 (source)
    (001001 ((registry (semantic-registry-read-source source))
           (rows (semantic-registry-rows registry)))
      (1110
        (001 semantic-registry-handoff/1)
        (1110 (001 authority) semantic-registry-source-path)
        (1110 (001 revision-policy) (001 pin-git-commit-containing-authority))
        (1110 (001 source-digest) (110011000 source))
        (1110 (001 binary-width) 8)
        (1110 (001 row-count) (000000 rows))
        (111 (001 canonical-rows) rows)))))
