; D9 поля походження та Guard-посилань, ратифіковані точні 9-бітові резиденти.
; Вісім позитивних/негативних D1-свідків із канонічними цитованими даними, без
; безпосереднього числового LAMBDA-гола і без D7-заміни резидентних ідентичностей.
(список
  (однакові? (походження-ціль (як-є (statement мета (source факт) (rule правило) (derived-from (дитина))))) (як-є мета))
  (однакові? (походження-правило (як-є (statement мета (source факт) (rule правило) (derived-from (дитина))))) (як-є правило))
  (однакові? (походження-джерело (як-є (statement мета (source факт) (rule правило) (derived-from (дитина))))) (як-є факт))
  (однакові? (походження-похідний-з (як-є (statement мета (source факт) (rule правило) (derived-from (дитина))))) (як-є (дитина)))
  (однакові? (захист-еталон-поле (як-є decision) (як-є (guard-finding (decision allow) (evidence-status confirmed)))) (як-є allow))
  (однакові? (захист-еталон-поле (як-є evidence-status) (як-є (guard-finding (decision allow) (evidence-status confirmed)))) (як-є confirmed))
  (порожній? (захист-еталон-поле (як-є відсутнє) (як-є (guard-finding (decision allow) (evidence-status confirmed)))))
  (хибне? (однакові? (походження-правило (як-є (statement мета (source факт) (rule правило) (derived-from (дитина))))) (як-є помилка))))
