; #218 — Lisp-owned verifier for remaining structural-observation rows.
; The host transports the contract document into `structural-observation-document`.
;
; Case tables are verified one case at a time. This avoids asking the historical
; macro expander to reconstruct a nested dotted-alist literal merely to compare
; two pieces of semantic data. The contract remains authoritative; this witness
; only reads its fields and checks the required domain facts.

(визначити so-field
  (функція (entry field)
    (нехай ((found (знайти-за-ключем field entry)))
      (за-умовою
        ((атом? found) (як-є ()))
        (так (решта found))))))

(визначити so-find
  (функція (identity entries)
    (за-умовою
      ((атом? entries) (як-є ()))
      ((однакові? (so-field (перше entries) (як-є identity)) identity)
       (перше entries))
      (так (so-find identity (решта entries))))))

(визначити so-entry
  (функція (identity)
    (so-find identity (решта structural-observation-document))))

(визначити so-case-find
  (функція (case-name cases)
    (за-умовою
      ((атом? cases) (як-є ()))
      ((однакові? (so-field (перше cases) (як-є when)) case-name)
       (перше cases))
      (так (so-case-find case-name (решта cases))))))

(визначити so-expect
  (функція (identity field expected)
    (нехай ((entry (so-entry identity)))
      (за-умовою
        ((атом? entry) (список (як-є missing-entry) identity))
        ((однакові? (so-field entry field) expected) (як-є ()))
        (так (список (як-є mismatch) identity field expected
                 (so-field entry field)))))))

(визначити so-expect-case
  (функція (identity case-name expected-result)
    (нехай ((entry (so-entry identity)))
      (за-умовою
        ((атом? entry) (список (як-є missing-entry) identity))
        (так
         (нехай ((case-entry
                 (so-case-find case-name (so-field entry (як-є cases)))))
           (за-умовою
             ((атом? case-entry) (список (як-є missing-case) identity case-name))
             ((однакові? (so-field case-entry (як-є result)) expected-result)
              (як-є ()))
             (так
              (список
                (як-є case-mismatch)
                identity
                case-name
                expected-result
                (so-field case-entry (як-є result)))))))))))

(визначити so-first-failure
  (функція (checks)
    (за-умовою
      ((атом? checks) (як-є ()))
      ((атом? (перше checks)) (so-first-failure (решта checks)))
      (так (перше checks)))))

(визначити structural-observation-contract-witness
  (функція ()
    (нехай ((failure
            (so-first-failure
              (список
                (so-expect "1024" (як-є result-form) (як-є class-membership))
                (so-expect "1024" (як-є target-class) (як-є string))
                (so-expect-case
                  "1024"
                  (як-є string)
                  (як-є (class-membership string member)))
                (so-expect-case
                  "1024"
                  (як-є non-string)
                  (як-є (class-membership string nonmember)))
                (so-expect "1024" (як-є generic-truth-coercion) (як-є forbidden))
                (so-expect "1024" (як-є control-dispatch) (як-є explicit-result-equality))

                (so-expect "1025" (як-є input-domain) (як-є (string string)))
                (so-expect "1025" (як-є result-form) (як-є text-order))
                (so-expect-case
                  "1025"
                  (як-є left-before-right)
                  (як-є (text-order before)))
                (so-expect-case
                  "1025"
                  (як-є same-text)
                  (як-є (text-order same)))
                (so-expect-case
                  "1025"
                  (як-є left-after-right)
                  (як-є (text-order after)))
                (so-expect "1025" (як-є outside-domain) (як-є type-error))
                (so-expect "1025" (як-є generic-truth-coercion) (як-є forbidden))
                (so-expect "1025" (як-є control-dispatch) (як-є explicit-result-equality))

                (so-expect "1026" (як-є result-form) (як-є class-membership))
                (so-expect "1026" (як-є target-class) (як-є numeric-buffer))
                (so-expect-case
                  "1026"
                  (як-є numeric-buffer)
                  (як-є (class-membership numeric-buffer member)))
                (so-expect-case
                  "1026"
                  (як-є non-numeric-buffer)
                  (як-є (class-membership numeric-buffer nonmember)))
                (so-expect "1026" (як-є generic-truth-coercion) (як-є forbidden))
                (so-expect "1026" (як-є control-dispatch) (як-є explicit-result-equality))))))
      (за-умовою
        ((хибне? (тотожне? (перше structural-observation-document)
                  (як-є structural-observation-contract/1)))
         (список (як-є structural-observation-contract-witness)
               (список (як-є status) (як-є fail))
               (список (як-є detail) (як-є schema))))
        ((атом? failure)
         (список (як-є structural-observation-contract-witness)
               (список (як-є status) (як-є pass))
               (список (як-є detail) (як-є explicit-domain-results))))
        (так
         (список (як-є structural-observation-contract-witness)
               (список (як-є status) (як-є fail))
               (список (як-є detail) failure)))))))
