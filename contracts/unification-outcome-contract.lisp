; #219 — контракт результату уніфікації, визначений мовою Lisp.
; `unify` залишається історичним механізмом. `unify-observe`
; явно подає його встановлений результат: порожня підстановка
; не плутається з відсутністю відповіді Канону 0, а причина
; невдачі не вигадується.

(unification-outcome-contract/1
  ((query . unify-observe)
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
