(binary 8)

; Executable Lisp-owned witness for the canonical semantic registry.
; The host test only checks the returned observation; all registry reading,
; Binary lookup, surface lookup and Binary read/print/read round-trip happen
; inside Lisp.

(def semantic-registry-self-hosted-witness
  (lambda ()
    (let* ((registry (semantic-registry-read))
           (rows (semantic-registry-rows registry))
           (quote-row (semantic-registry-row 00000001))
           (invoke-row (semantic-registry-row 10101000))
           (leading-zero-row (semantic-registry-row 00000101))
           (max-row (semantic-registry-row 11111111))
           (quote-id (semantic-registry-id 'quote))
           (uk-quote-id (semantic-registry-id 'як-є))
           (ukr-quote-id (semantic-registry-id 'як-є))
           (invoke-id (semantic-registry-id 'invoke))
           (roundtrip (semantic-registry-round-trip 10101000)))
      (list
        (semantic-registry-format registry)
        (length rows)
        (equal?
          (semantic-registry-row-namespaces-from-row quote-row)
          (semantic-registry-namespaces))
        (write-to-string (semantic-registry-row-id quote-row))
        (semantic-registry-surface-name 'en quote-row)
        (semantic-registry-surface-name 'uk quote-row)
        (semantic-registry-surface-name 'ukr quote-row)
        (semantic-registry-surface-name 'sa quote-row)
        (semantic-registry-surface-name 'sym quote-row)
        (write-to-string quote-id)
        (write-to-string uk-quote-id)
        (write-to-string ukr-quote-id)
        (write-to-string invoke-id)
        (write-to-string (semantic-registry-row-id invoke-row))
        (write-to-string (semantic-registry-row-id leading-zero-row))
        (write-to-string (semantic-registry-row-id max-row))
        (write-to-string roundtrip)
        (equal? roundtrip (semantic-registry-row-id invoke-row)))))))
