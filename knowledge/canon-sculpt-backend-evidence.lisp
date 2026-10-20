; #419 Журнал свідчень виконавців. Лише свідчення й навігація.

(canon-sculpt-backend-evidence
  (schema-version 1)
  (law
    (name lowering-is-not-derivation)
    (statement "Зниження до рідного виконавця, CML чи x86 підтверджує шлях реалізації, а не вивідність семантичного поняття з простіших понять Lisp."))
  (law
    (name shared-truth-not-copied-truth)
    (statement "Виконавці можуть користуватися одним еталонним корпусом Lisp; маніфести виконавців не повинні ставати другим семантичним оракулом."))

  (path
    (name native)
    (role execution-consumer)
    (evidence-source tests/fixtures/conformance.lisp)
    (status inspect-current-main))
  (path
    (name meta)
    (role independent-lisp-evaluator-consumer)
    (evidence-source tests/fixtures/conformance.lisp)
    (status inspect-current-main))
  (path
    (name cml)
    (role sibling-compiler-consumer)
    (evidence-source knowledge/lisp-backend-adapters.lisp)
    (status transport-contract-exists))
  (path
    (name x86-machine)
    (role mechanism-lowering)
    (evidence-source lib/machine)
    (status partial-admitted-subset))

  (candidate
    (identity PRIM_COND)
    (backend-note "Є свідчення обмеженого рідного зниження, але вони не визначають, чи cond є основним синтаксисом, чи макросом із простішої керувальної форми"))
  (candidate
    (identity PRIM_CONS)
    (backend-note "Машинне зниження побудови й доступу може підтверджувати швидкодію та переносимість, але не семантичну незвідність"))
  (candidate
    (identity PRIM_ATOM)
    (backend-note "Структурну класифікацію не можна обґрунтовувати міткою подання середовища виконання"))
  (candidate
    (identity PRIM_EQ)
    (backend-note "Семантика тотожності не зводиться до рівності вказівників лише тому, що виконавець так реалізує один випадок")))
