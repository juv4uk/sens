; Шість ратифікованих D9-проєкцій епістемічних даних з lib/epistemic.lisp.
; SENS-виконання: 6 позитивних + 2 негативних закони, усі D1:YES.
; Коди: D9:101100110,101101010,101010011,101111111,101010100,101111000.
(list
  (equal?
    (твердження-твердження
      (як-є (claim (statement факт) (source джерело) (review reviewed))))
    (як-є факт))
  (equal?
    (твердження-перевірка
      (як-є (claim (statement факт) (source джерело) (review reviewed))))
    (як-є reviewed))
  (equal?
    (доказ-метод
      (як-є (evidence (claim-ref посилання) (method перевірка) (outcome supports) (source-ref джерело))))
    (як-є перевірка))
  (equal?
    (доказ-підсумок
      (як-є (evidence (claim-ref посилання) (method перевірка) (outcome supports) (source-ref джерело))))
    (як-є supports))
  (equal?
    (намір-ціль
      (як-є (intent (goal результат) (requires ()) (stop-on ()) (produces ()))))
    (як-є результат))
  (equal?
    (спостереження-твердження
      (як-є (observation (source прилад) (statement сигнал))))
    (як-є сигнал))
  (not?
    (equal?
      (твердження-перевірка
        (як-є (claim (statement факт) (source джерело) (review reviewed))))
      (як-є факт)))
  (not?
    (equal?
      (доказ-підсумок
        (як-є (evidence (claim-ref посилання) (method перевірка) (outcome supports) (source-ref джерело))))
      (як-є перевірка))))
