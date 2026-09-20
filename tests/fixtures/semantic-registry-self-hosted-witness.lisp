(binary 8)

; Executable Lisp-owned witness for the canonical semantic registry.
; Registry occupancy and the full 8-bit Binary value domain are deliberately
; separate: 11111111 must round-trip as Binary even though it is not currently
; an admitted semantic-registry row.

(def semantic-registry-self-hosted-witness
  (lambda (source)
    (let* ((registry (semantic-registry-read-source source))
           (rows (semantic-registry-rows registry))
           (quote-row (semantic-registry-row 00000001))
           (quote-id (semantic-registry-id 'quote))
           (invoke-id (semantic-registry-id 'invoke))
           (leading-zero-row (semantic-registry-row 00000101))
           (max-roundtrip (semantic-registry-round-trip 11111111))
           (invoke-roundtrip (semantic-registry-round-trip 10101000)))
      (list
        (semantic-registry-format registry)
        (length rows)
        (write-to-string (semantic-registry-row-id quote-row))
        (semantic-registry-surface-name 'en quote-row)
        (write-to-string quote-id)
        (write-to-string invoke-id)
        (write-to-string (semantic-registry-row-id leading-zero-row))
        (write-to-string max-roundtrip)
        (semantic-registry-row 11111111)
        (write-to-string invoke-roundtrip)
        (equal? invoke-roundtrip (semantic-registry-row-id (semantic-registry-row 10101000)))))))
