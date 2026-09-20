(binary 8)

; Executable Lisp-owned witness for the canonical semantic registry.
; Registry occupancy and the full 8-bit Binary value domain are deliberately
; separate: 11111111 must round-trip as Binary even though it is not currently
; an admitted semantic-registry row.

(def semantic-registry-self-hosted-witness
  (lambda (source)
    (let* ((registry (semantic-registry-read-source source))
           (rows (semantic-registry-rows registry))
           (quote-row (semantic-registry-row-in registry 00000001))
           (quote-id (semantic-registry-id-in registry 'quote))
           (invoke-id (semantic-registry-id-in registry 'invoke))
           (leading-zero-row (semantic-registry-row-in registry 00000101))
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
        (semantic-registry-row-in registry 11111111)
        (write-to-string invoke-roundtrip)
        (equal? invoke-roundtrip (semantic-registry-row-id (semantic-registry-row-in registry 10101000)))))))

; Machine-readable handoff for downstream consumers.
; Git commit pinning is provenance and stays outside language semantics.
; The digest is content identity of the exact canonical source bytes. The full
; parsed canonical rows are handed off directly, so Binary SID values are
; preserved without building a second identity projection or recursive shadow table.
(def semantic-registry-handoff-witness
  (lambda (source)
    (let* ((registry (semantic-registry-read-source source))
           (rows (semantic-registry-rows registry)))
      (list
        (quote semantic-registry-handoff/1)
        (list (quote authority) semantic-registry-source-path)
        (list (quote revision-policy) (quote pin-git-commit-containing-authority))
        (list (quote source-digest) (sha256-hex source))
        (list (quote binary-width) 8)
        (list (quote row-count) (length rows))
        (cons (quote canonical-rows) rows)))))
