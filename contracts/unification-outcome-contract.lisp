; #219 — контракт результату уніфікації, визначений мовою Lisp.
; Чинна українська функція «спостерігати-уніфікацію» повертає
; окремі протокольні результати для успіху й невдачі.
; Порожню успішну підстановку не плутаємо з Каноном 0;
; причину невдачі не вигадуємо.

(unification-outcome-contract/1
  ((query . спостерігати-уніфікацію)
   (input . (left right substitution))
   (result-forms . ((unified substitution)
                    (unification-failure left right substitution)))
   (bare-canon-zero-result . forbidden-for-completed-query)
   (generic-truth-coercion . forbidden))

  ((law . empty-substitution-is-success-data)
   (raw-result . ())
   (observed-result . (unified ()))
   (not-equal . ())))

  ((law . established-unification-failure-is-not-canon-zero)
   (raw-result . fail)
   (observed-result-form . (unification-failure left right substitution))
   (cause . not-invented)
   (not-equal . ()))
)
