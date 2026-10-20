; Executable Lisp-owned witness for LIFE-1 contract.
; Ukrainian projection only.

(визначити life-1-schema
  (функція () (перше life-1-document)))

(визначити life-1-entries
  (функція () (решта life-1-document)))

(визначити life-1-field
  (функція (entry field)
    (нехай ((found (знайти-за-ключем field entry)))
      (за-умовою
        ((атом? found) (як-є ()))
        (так (решта found))))))

(визначити life-1-find
  (функція (identity entries)
    (за-умовою
      ((атом? entries) (як-є ()))
      (так
       (за-умовою
         ((тотожне? (life-1-field (перше entries) (як-є identity)) identity)
          (перше entries))
         (так (life-1-find identity (решта entries))))))))

(визначити life-1-entry
  (функція (identity)
    (life-1-find identity (life-1-entries))))

(визначити life-1-check
  (функція (identity field expected)
    (нехай ((entry (life-1-entry identity)))
      (за-умовою
        ((атом? entry)
         (список (як-є missing-entry) identity))
        (так
         (за-умовою
           ((тотожне? (life-1-field entry field) expected)
            (як-є ()))
           (так
            (список (як-є mismatch) identity field expected
                  (life-1-field entry field)))))))))

(визначити life-1-first-failure
  (функція (checks)
    (за-умовою
      ((атом? checks) (як-є ()))
      (так
       (за-умовою
         ((атом? (перше checks))
          (life-1-first-failure (решта checks)))
         (так (перше checks)))))))

(визначити life-1-contract-witness
  (функція ()
    (нехай ((failure
            (life-1-first-failure
              (список
                (life-1-check (як-є life-trace) (як-є owner) (як-є sens))
                (life-1-check (як-є life-trace) (як-є truth-value) (як-є forbidden))
                (life-1-check (як-є source-observation) (як-є native-domain-preserved) (як-є yes))
                (life-1-check (як-є source-observation) (як-є universal-result-normalization) (як-є forbidden))
                (life-1-check (як-є projection) (як-є explicit) (як-є yes))
                (life-1-check (як-є projection) (як-є partial) (як-є yes))
                (life-1-check (як-є projection) (як-є semantic-equivalence-assumed) (як-є no))
                (life-1-check (як-є target-invocation) (як-є kernel-reinterpretation) (як-є forbidden))
                (life-1-check (як-є missing-source-kernel) (як-є changes-semantic-id-meaning) (як-є no))
                (life-1-check (як-є first-vertical-slice) (як-є source) (як-є prolog))
                (life-1-check (як-є first-vertical-slice) (як-є target) (як-є datalog))
                (life-1-check (як-є first-vertical-slice) (як-є shared-result-type) (як-є forbidden))
                (life-1-check (як-є liveness) (як-є fresh-checkout) (як-є required))))))
      (за-умовою
        ((тотожне? (life-1-schema) (як-є life-1-contract/1))
         (за-умовою
           ((атом? failure)
            (список (як-є life-1-contract-witness)
                  (список (як-є status) (як-є pass))
                  (список (як-є detail) (як-є provenance-not-truth))))
           (так
            (список (як-є life-1-contract-witness)
                  (список (як-є status) (як-є fail))
                  (список (як-є detail) failure)))))
        (так
         (список (як-є life-1-contract-witness)
               (список (як-є status) (як-є fail))
               (список (як-є detail)
                     (список (як-є schema) (life-1-schema)))))))))
