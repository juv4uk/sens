; #749 — executable Lisp-owned witness for island compatibility.
; Ukrainian projection only.

(визначити island-compat-schema
  (функція () (перше island-compat-document)))

(визначити island-compat-entries
  (функція () (решта island-compat-document)))

(визначити island-compat-field
  (функція (entry field)
    (нехай ((found (знайти-за-ключем field entry)))
      (за-умовою
        ((атом? found) (як-є ()))
        (так (решта found))))))

(визначити island-compat-find
  (функція (identity entries)
    (за-умовою
      ((атом? entries) (як-є ()))
      ((однакові? (island-compat-field (перше entries) (як-є identity)) identity)
       (перше entries))
      (так (island-compat-find identity (решта entries))))))

(визначити island-compat-entry
  (функція (identity)
    (island-compat-find identity (island-compat-entries))))

(визначити island-compat-check
  (функція (identity field expected)
    (нехай ((entry (island-compat-entry identity)))
      (за-умовою
        ((атом? entry) (список (як-є missing-entry) identity))
        ((однакові? (island-compat-field entry field) expected) (як-є ()))
        (так (список (як-є mismatch) identity field expected
                 (island-compat-field entry field)))))))

(визначити island-compat-first-failure
  (функція (checks)
    (за-умовою
      ((атом? checks) (як-є ()))
      ((атом? (перше checks)) (island-compat-first-failure (решта checks)))
      (так (перше checks)))))

(визначити island-compat-witness
  (функція ()
    (нехай ((failure
            (island-compat-first-failure
              (список
                (island-compat-check
                  (як-є semantic-id) (як-є owner) (як-є sens))
                (island-compat-check
                  (як-є semantic-id) (як-є representation) (як-є opaque-u8))
                (island-compat-check
                  (як-є semantic-id) (як-є kernel-interpretation) (як-є forbidden))
                (island-compat-check
                  (як-є execution-witness) (як-є cardinality) (як-є zero-or-more))
                (island-compat-check
                  (як-є execution-witness) (як-є multiple-kernels-per-sid) (як-є allowed))
                (island-compat-check
                  (як-є island-call) (як-є producer-required) (як-є yes))
                (island-compat-check
                  (як-є island-call) (як-є provenance-preserved) (як-є yes))
                (island-compat-check
                  (як-є island-call) (як-є universal-result-coercion) (як-є forbidden))
                (island-compat-check
                  (як-є zero-results) (як-є result-count) 0)
                (island-compat-check
                  (як-є zero-results) (як-є literal-empty-list-alias) (як-є forbidden))
                (island-compat-check
                  (як-є one-result) (як-є result-count) 1)
                (island-compat-check
                  (як-є many-results) (як-є result-count) (як-є many))
                (island-compat-check
                  (як-є many-results) (як-є multiplicity-preserved) (як-є yes))
                (island-compat-check
                  (як-є bridge) (як-є missing-bridge) (як-є legal))
                (island-compat-check
                  (як-є bridge) (як-є semantic-equivalence-assumed) (як-є no))
                (island-compat-check
                  (як-є missing-kernel) (як-є legal) (як-є yes))
                (island-compat-check
                  (як-є missing-kernel) (як-є changes-sid-meaning) (як-є no))
                (island-compat-check
                  (як-є missing-kernel) (як-є changes-registry-numbering) (як-є no))))))
      (за-умовою
        ((тотожне? (island-compat-schema) (як-є island-compat-contract/1))
         (за-умовою
           ((атом? failure)
            (список (як-є island-compat-witness)
                  (список (як-є status) (як-є pass))
                  (список (як-є detail) (як-є semantic-owner-island-mechanism))))
           (так
            (список (як-є island-compat-witness)
                  (список (як-є status) (як-є fail))
                  (список (як-є detail) failure)))))
        (так
         (список (як-є island-compat-witness)
               (список (як-є status) (як-є fail))
               (список (як-є detail)
                     (список (як-є schema) (island-compat-schema)))))))))
