; D9 GUARD-DECISION?/EVIDENCE-STATUS?: 8 positive, 4 falsifying D1 outcomes.
(список
  (захист-рішення? (quote allow))
  (захист-рішення? (quote warn))
  (захист-рішення? (quote reject))
  (захист-рішення? (quote unknown))
  (хибне? (захист-рішення? (quote deny)))
  (хибне? (захист-рішення? (список (quote allow))))
  (захист-доказ-стан? (quote confirmed))
  (захист-доказ-стан? (quote partial))
  (захист-доказ-стан? (quote unresolved))
  (захист-доказ-стан? (quote broken))
  (хибне? (захист-доказ-стан? (quote absent)))
  (хибне? (захист-доказ-стан? (список (quote confirmed)))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити хибне? not?)
