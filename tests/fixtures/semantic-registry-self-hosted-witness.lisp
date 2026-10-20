; Executable Lisp-owned witness for the canonical semantic registry.
; Ukrainian projection only. Registry occupancy and full binary domain remain separate.

(визначити semantic-registry-self-hosted-witness
  (функція (source)
    (нехай ((registry (semantic-registry-read-source source))
           (rows (semantic-registry-rows registry))
           (quote-row (semantic-registry-row-in registry 1))
           (quote-id (semantic-registry-id-in registry (як-є quote)))
           (invoke-id (semantic-registry-id-in registry (як-є invoke)))
           (leading-zero-row (semantic-registry-row-in registry 5))
           (max-roundtrip (semantic-registry-round-trip 255))
           (invoke-roundtrip (semantic-registry-round-trip 168)))
      (список
        (довжина rows)
        (binary-print (semantic-registry-row-id quote-row))
        (semantic-registry-surface-name (як-є en) quote-row)
        (binary-print quote-id)
        (binary-print invoke-id)
        (binary-print (semantic-registry-row-id leading-zero-row))
        (binary-print max-roundtrip)
        (semantic-registry-row-in registry 255)
        (binary-print invoke-roundtrip)
        (однакові? invoke-roundtrip (semantic-registry-row-id (semantic-registry-row-in registry 168)))))))

(визначити semantic-registry-handoff-witness
  (функція (source)
    (нехай ((registry (semantic-registry-read-source source))
           (rows (semantic-registry-rows registry)))
      (список
        (як-є semantic-registry-handoff/1)
        (список (як-є authority) semantic-registry-source-path)
        (список (як-є revision-policy) (як-є pin-git-commit-containing-authority))
        (список (як-є source-digest) (source-digest source))
        (список (як-є binary-width) 8)
        (список (як-є row-count) (довжина rows))
        (сполучити (як-є canonical-rows) rows)))))
