; #218 — контракт класифікації клауз знань, визначений мовою Lisp.
; Клауза відповідає своїм доменним видом, а не історичним t/().
; Структурну форму спостерігають на нижчому рівні; публічну
; відповідь домену знань читають споживачі знань.

(knowledge-clause-kind-contract/1
  ((query . is-fact?)
   (input . clause)
   (result-layer . knowledge-domain)
   (result-forms . ((clause-kind fact)
                    (clause-kind rule)))
   (generic-truth-coercion . forbidden))

  ((law . empty-body-is-fact)
   (clause-shape . (head))
   (result . (clause-kind fact)))

  ((law . nonempty-body-is-rule)
   (clause-shape . (head condition ...))
   (result . (clause-kind rule))))
