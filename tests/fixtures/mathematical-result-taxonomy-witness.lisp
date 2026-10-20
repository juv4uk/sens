; #225 — Lisp-owned verifier for the mathematical-result taxonomy.
; Ukrainian projection only.
; The host transports contracts/mathematical-result-taxonomy.lisp into
; mathematical-result-taxonomy-document; every semantic expectation is here.

(визначити mrt-field
  (функція (entry field)
    (нехай ((found (знайти-за-ключем field entry)))
      (за-умовою
        ((атом? found) (як-є ()))
        (так (решта found))))))

(визначити mrt-find
  (функція (identity entries)
    (за-умовою
      ((атом? entries) (як-є ()))
      ((однакові? (mrt-field (перше entries) (як-є identity)) identity)
       (перше entries))
      (так (mrt-find identity (решта entries))))))

(визначити mrt-entry
  (функція (identity)
    (mrt-find identity (решта mathematical-result-taxonomy-document))))

(визначити mrt-expect
  (функція (identity field expected)
    (нехай ((entry (mrt-entry identity)))
      (за-умовою
        ((атом? entry) (список (як-є missing-entry) identity))
        ((однакові? (mrt-field entry field) expected) (як-є ()))
        (так
         (список
           (як-є mismatch)
           identity
           field
           expected
           (mrt-field entry field)))))))

(визначити mrt-first-failure
  (функція (checks)
    (за-умовою
      ((атом? checks) (як-є ()))
      ((атом? (перше checks)) (mrt-first-failure (решта checks)))
      (так (перше checks)))))

(визначити mathematical-result-taxonomy-witness
  (функція ()
    (нехай ((failure
            (mrt-first-failure
              (список
                (mrt-expect (як-є laws)
                            (як-є domain-owner)
                            (як-є mathematical-result))
                (mrt-expect (як-є laws)
                            (як-є object-approximation-identity)
                            (як-є distinct))
                (mrt-expect (як-є laws)
                            (як-є generic-truth-coercion)
                            (як-є forbidden))
                (mrt-expect (як-є laws)
                            (як-є many-valued-collapse)
                            (як-є forbidden))
                (mrt-expect (як-є pi-example)
                            (як-є number-system)
                            (як-є real))
                (mrt-expect (як-є pi-example)
                            (як-є rationality)
                            (як-є transcendental))
                (mrt-expect (як-є pi-example)
                            (як-є algebraic-status)
                            (як-є transcendental))
                (mrt-expect (як-є pi-example)
                            (як-є result-role)
                            (як-є exact-object))
                (mrt-expect (як-є sqrt2-example)
                            (як-є number-system)
                            (як-є real))
                (mrt-expect (як-є sqrt2-example)
                            (як-є rationality)
                            (як-є irrational))
                (mrt-expect (як-є sqrt2-example)
                            (як-є algebraic-status)
                            (як-є algebraic))
                (mrt-expect (як-є sqrt2-example)
                            (як-є result-role)
                            (як-є exact-object))
                (mrt-expect (як-є approximation-role)
                            (як-є required-metadata)
                            (як-є (target approximant precision-or-error-guarantee)))
                (mrt-expect (як-є approximation-role)
                            (як-є approximant-remains-own-mathematical-object)
                            (як-є так))
                (mrt-expect (як-є interval-enclosure-role)
                            (як-є required-metadata)
                            (як-є (target lower-bound upper-bound enclosure-guarantee)))
                (mrt-expect (як-є symbolic-expression-role)
                            (як-є many-valued-status)
                            (як-є forbidden))))))
      (за-умовою
        ((хибне? (тотожне? (перше mathematical-result-taxonomy-document)
                  (як-є mathematical-result-taxonomy/1)))
         (список (як-є mathematical-result-taxonomy-witness)
               (список (як-є status) (як-є fail))
               (список (як-є detail) (як-є schema))))
        ((атом? failure)
         (список (як-є mathematical-result-taxonomy-witness)
               (список (як-є status) (як-є pass))
               (список (як-є detail) (як-є standard-math-classification))))
        (так
         (список (як-є mathematical-result-taxonomy-witness)
               (список (як-є status) (як-є fail))
               (список (як-є detail) failure)))))))
