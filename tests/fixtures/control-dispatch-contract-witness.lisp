; #217 — Lisp-owned verifier for the canonical control-dispatch contract.
; The host transports contracts/control-dispatch-contract.lisp into
; `control-dispatch-document`; semantic expectations live here.

(def cd-field
  (функція (entry field)
    (let ((found (assoc field entry)))
      (за-умовою
        ((атом? found) (як-є ()))
        (t (решта found))))))

(def cd-find
  (функція (identity entries)
    (за-умовою
      ((атом? entries) (як-є ()))
      ((equal? (cd-field (перше entries) (як-є identity)) identity)
       (перше entries))
      (t (cd-find identity (решта entries))))))

(def cd-entry
  (функція (identity)
    (cd-find identity (решта control-dispatch-document))))

(def cd-expect
  (функція (identity field expected)
    (let ((entry (cd-entry identity)))
      (за-умовою
        ((атом? entry) (список (як-є missing-entry) identity))
        ((equal? (cd-field entry field) expected) (як-є ()))
        (t
         (список
           (як-є mismatch)
           identity
           field
           expected
           (cd-field entry field)))))))

(def cd-first-failure
  (функція (checks)
    (за-умовою
      ((атом? checks) (як-є ()))
      ((атом? (перше checks)) (cd-first-failure (решта checks)))
      (t (перше checks)))))

(def control-dispatch-contract-witness
  (функція ()
    (let ((failure
            (cd-first-failure
              (список
                (cd-expect (як-є canonical-cond)
                           (як-є semantic-id)
                           "0007")
                (cd-expect (як-є canonical-cond)
                           (як-є role)
                           (як-є ordered-dispatch))
                (cd-expect (як-є canonical-cond)
                           (як-є generic-value-coercion)
                           (як-є forbidden))
                (cd-expect (як-є canonical-cond)
                           (як-є nil-as-false)
                           (як-є forbidden))
                (cd-expect (як-є canonical-cond)
                           (як-є host-bool-authority)
                           (як-є forbidden))

                (cd-expect (як-є exact-q-control)
                           (як-є accepted-domain)
                           (як-є exact-q-decision))
                (cd-expect (як-є exact-q-control)
                           (як-є yes-action)
                           (як-є select))
                (cd-expect (як-є exact-q-control)
                           (як-є no-action)
                           (як-є continue))

                (cd-expect (як-є structural-control)
                           (як-є implicit-consumption)
                           (як-є forbidden))
                (cd-expect (як-є structural-control)
                           (як-є dispatch)
                           (як-є explicit-match-required))

                (cd-expect (як-є mathematical-result-control)
                           (як-є implicit-consumption)
                           (як-є forbidden))

                (cd-expect (як-є reasoning-control)
                           (як-є implicit-consumption)
                           (як-є forbidden))
                (cd-expect (як-є reasoning-control)
                           (як-є dispatch)
                           (як-є explicit-match-required))

                (cd-expect (як-є no-answer-control)
                           (як-є false-meaning)
                           (як-є forbidden))
                (cd-expect (як-є no-answer-control)
                           (як-є implicit-consumption)
                           (як-є forbidden))

                ; Syntax is deliberately not invented before the semantic
                ; protocol is stable. #217 may later ratify a matching surface.
                (cd-expect (як-є structural-control)
                           (як-є clause-syntax)
                           (як-є not-yet-ratified))))))
      (за-умовою
        ((хибне? (тотожне? (перше control-dispatch-document)
                  (як-є control-dispatch-contract/1)))
         (список (як-є control-dispatch-contract-witness)
               (список (як-є status) (як-є fail))
               (список (як-є detail) (як-є schema))))
        ((атом? failure)
         (список (як-є control-dispatch-contract-witness)
               (список (як-є status) (як-є pass))
               (список (як-є detail) (як-є explicit-domain-control))))
        (t
         (список (як-є control-dispatch-contract-witness)
               (список (як-є status) (як-є fail))
               (список (як-є detail) failure)))))))
