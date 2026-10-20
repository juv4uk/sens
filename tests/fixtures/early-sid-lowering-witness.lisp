; #1115 executable witness.
; The canonical registry API performs the semantic lookup.
; Ukrainian projection only. Backend boundary: exact identity, arguments, portable contract.

(визначити early-sid-lowering-backend-request?
  (функція (request)
    (за-умовою
      ((атом? request) (як-є no))
      (так
       (нехай ((first-field (перше request)))
         (за-умовою
           ((атом? first-field) (як-є no))
           (так
            (за-умовою
              ((тотожне? (перше first-field) (як-є sid))
               (як-є yes))
              (так (як-є no))))))))))

(визначити early-sid-lower
  (функція (registry surface arguments contract)
    (нехай ((sid (semantic-registry-id-in registry surface)))
      (за-умовою
        ((атом? sid) (як-є rejected))
        (так
         (список
           (сполучити (як-є sid) sid)
           (сполучити (як-є arguments) arguments)
           (сполучити (як-є contract) contract)))))))

(визначити early-sid-lowering-peer-check
  (функція (registry surface-a surface-b surface-c surface-d)
    (нехай ((a (semantic-registry-id-in registry surface-a))
          (b (semantic-registry-id-in registry surface-b))
          (c (semantic-registry-id-in registry surface-c))
          (d (semantic-registry-id-in registry surface-d)))
      (за-умовою
        ((тотожне? a b)
         (за-умовою
           ((тотожне? b c)
            (за-умовою
              ((тотожне? c d)
               (список (як-є same) a))
              (так (як-є distinct))))
           (так (як-є distinct))))
        (так (як-є distinct))))))

(визначити early-sid-lowering-witness
  (функція (registry-source)
    (нехай ((registry (semantic-registry-read-source registry-source)))
      (нехай ((atom-en (semantic-registry-id-in registry (як-є atom?)))
            (atom-uk (semantic-registry-id-in registry (як-є атом?)))
            (atom-ukr (semantic-registry-id-in registry (як-є атом?)))
            (atom-sa (semantic-registry-id-in registry (як-є aṇu)))
            (atom-sym (semantic-registry-id-in registry (як-є .?))))
        (список
          (early-sid-lowering-peer-check
            registry
            (як-є atom?) (як-є атом?) (як-є aṇu) (як-є .?))
          (early-sid-lowering-backend-request?
            (early-sid-lower
              registry
              (як-є atom?)
              (як-є (x))
              (як-є (portable-result-domain structural-relation))))
          (early-sid-lowering-backend-request?
            (як-є (surface atom?)))
          (тотожне? atom-en atom-uk)
          (тотожне? atom-en atom-ukr)
          (тотожне? atom-en atom-sa)
          (тотожне? atom-en atom-sym)
          (semantic-registry-id-in registry (як-є not-admitted-by-language)))))))
