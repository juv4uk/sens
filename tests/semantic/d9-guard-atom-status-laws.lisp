; D9 GUARD-DECISION?/EVIDENCE-STATUS?: 8 positive, 4 falsifying D1 outcomes.
(list
  (захист-рішення? (quote allow))
  (захист-рішення? (quote warn))
  (захист-рішення? (quote reject))
  (захист-рішення? (quote unknown))
  (not? (захист-рішення? (quote deny)))
  (not? (захист-рішення? (list (quote allow))))
  (захист-доказ-стан? (quote confirmed))
  (захист-доказ-стан? (quote partial))
  (захист-доказ-стан? (quote unresolved))
  (захист-доказ-стан? (quote broken))
  (not? (захист-доказ-стан? (quote absent)))
  (not? (захист-доказ-стан? (list (quote confirmed)))))
