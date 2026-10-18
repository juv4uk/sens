; Шість ратифікованих D9-проєкцій епістемічних даних з lib/epistemic.lisp.
; SENS-виконання: 6 позитивних + 2 негативних закони, усі D1:YES.
; Коди: D9:101100110,101101010,101010011,101111111,101010100,101111000.
(список
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
  (хибне?
    (equal?
      (твердження-перевірка
        (як-є (claim (statement факт) (source джерело) (review reviewed))))
      (як-є факт)))
  (хибне?
    (equal?
      (доказ-підсумок
        (як-є (evidence (claim-ref посилання) (method перевірка) (outcome supports) (source-ref джерело))))
      (як-є перевірка))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити хибне? not?)
