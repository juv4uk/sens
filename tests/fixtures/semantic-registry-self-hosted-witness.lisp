; Executable Lisp-owned witness for the canonical semantic registry.
; Registry occupancy and the full 8-bit Binary value domain are deliberately
; separate: 11111111 must round-trip as Binary even though it is not currently
; an admitted semantic-registry row.

(00001001 semantic-registry-self-hosted-witness
  (00001000 (source)
    (10011101 ((registry (semantic-registry-read-source source))
           (rows (semantic-registry-rows registry))
           (quote-row (semantic-registry-row-in registry 00000001))
           (quote-id (semantic-registry-id-in registry 'quote))
           (invoke-id (semantic-registry-id-in registry 'invoke))
           (leading-zero-row (semantic-registry-row-in registry 00000101))
           (max-roundtrip (semantic-registry-round-trip 11111111))
           (invoke-roundtrip (semantic-registry-round-trip 10101000)))
      (00100111
        (00101000 rows)
        (01001100 (semantic-registry-row-id quote-row))
        (semantic-registry-surface-name 'en quote-row)
        (01001100 quote-id)
        (01001100 invoke-id)
        (01001100 (semantic-registry-row-id leading-zero-row))
        (01001100 max-roundtrip)
        (semantic-registry-row-in registry 11111111)
        (01001100 invoke-roundtrip)
        (00100010 invoke-roundtrip (semantic-registry-row-id (semantic-registry-row-in registry 10101000)))))))

; Machine-readable handoff for downstream consumers.
; Git commit pinning is provenance and stays outside language semantics.
; The digest is content identity of the exact canonical source bytes. The full
; parsed canonical rows are handed off directly, so Binary SID values are
; preserved without building a second identity projection or recursive shadow table.
(00001001 semantic-registry-handoff-witness
  (00001000 (source)
    (10011101 ((registry (semantic-registry-read-source source))
           (rows (semantic-registry-rows registry)))
      (00100111
        (00000001 semantic-registry-handoff/1)
        (00100111 (00000001 authority) semantic-registry-source-path)
        (00100111 (00000001 revision-policy) (00000001 pin-git-commit-containing-authority))
        (00100111 (00000001 source-digest) (10100001 source))
        (00100111 (00000001 binary-width) 8)
        (00100111 (00000001 row-count) (00101000 rows))
        (00000100 (00000001 canonical-rows) rows)))))
