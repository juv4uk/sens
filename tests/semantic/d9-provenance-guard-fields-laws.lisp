; D9 provenance and Guard reference fields, ratified exact 9-bit residents.
; Eight positive/negative D1 witnesses with canonical quoted data, no
; immediate numeric LAMBDA-head and no D7 substitute for resident identities.
(список
  (equal? (походження-ціль (як-є (statement мета (source факт) (rule правило) (derived-from (дитина))))) (як-є мета))
  (equal? (походження-правило (як-є (statement мета (source факт) (rule правило) (derived-from (дитина))))) (як-є правило))
  (equal? (походження-джерело (як-є (statement мета (source факт) (rule правило) (derived-from (дитина))))) (як-є факт))
  (equal? (походження-похідний-з (як-є (statement мета (source факт) (rule правило) (derived-from (дитина))))) (як-є (дитина)))
  (equal? (захист-еталон-поле (як-є decision) (як-є (guard-finding (decision allow) (evidence-status confirmed)))) (як-є allow))
  (equal? (захист-еталон-поле (як-є evidence-status) (як-є (guard-finding (decision allow) (evidence-status confirmed)))) (як-є confirmed))
  (порожнє? (захист-еталон-поле (як-є відсутнє) (як-є (guard-finding (decision allow) (evidence-status confirmed)))))
  (хибне? (equal? (походження-правило (як-є (statement мета (source факт) (rule правило) (derived-from (дитина))))) (як-є помилка))))
