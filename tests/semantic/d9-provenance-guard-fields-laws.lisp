; D9 provenance and Guard reference fields, ratified exact 9-bit residents.
; Eight positive/negative D1 witnesses with canonical quoted data, no
; immediate numeric LAMBDA-head and no D7 substitute for resident identities.
(список
  (equal? (походження-ціль (001 (statement мета (source факт) (rule правило) (derived-from (дитина))))) (001 мета))
  (equal? (походження-правило (001 (statement мета (source факт) (rule правило) (derived-from (дитина))))) (001 правило))
  (equal? (походження-джерело (001 (statement мета (source факт) (rule правило) (derived-from (дитина))))) (001 факт))
  (equal? (походження-похідний-з (001 (statement мета (source факт) (rule правило) (derived-from (дитина))))) (001 (дитина)))
  (equal? (захист-еталон-поле (001 decision) (001 (guard-finding (decision allow) (evidence-status confirmed)))) (001 allow))
  (equal? (захист-еталон-поле (001 evidence-status) (001 (guard-finding (decision allow) (evidence-status confirmed)))) (001 confirmed))
  (порожнє? (захист-еталон-поле (001 відсутнє) (001 (guard-finding (decision allow) (evidence-status confirmed)))))
  (хибне? (equal? (походження-правило (001 (statement мета (source факт) (rule правило) (derived-from (дитина))))) (001 помилка))))
