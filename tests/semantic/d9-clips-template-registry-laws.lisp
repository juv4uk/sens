; Вісім нативних D1-законів D9 CLIPS з lib/clips-import.lisp.
; Два D9 resident-слова, без прямого допуску їх як машинних opcode.
(список
  (equal? (clips-deftemplate-ім'я (як-є (deftemplate читання (slot датчик))))
          (як-є читання))
  (equal? (clips-шаблони-з-форми (як-є ())) (як-є ()))
  (equal? (clips-шаблони-з-форми (як-є ((deffacts набір (факт)))))
          (як-є ()))
  (equal?
    (clips-шаблони-з-форми
      (як-є ((deftemplate читання (slot датчик) (slot значення)))))
    (як-є ((читання датчик значення))))
  (equal?
    (clips-шаблони-з-форми
      (як-є ((deffacts шум (сигнал))
              (deftemplate перший (slot а))
              (deftemplate другий (slot б)))))
    (як-є ((перший а) (другий б))))
  (equal?
    (clips-шаблон-слот-порядок
      (як-є другий)
      (clips-шаблони-з-форми
        (як-є ((deftemplate перший (slot а))
                (deftemplate другий (slot б))))))
    (як-є (б)))
  (equal?
    (clips-шаблон-слот-порядок
      (як-є відсутній)
      (clips-шаблони-з-форми
        (як-є ((deftemplate перший (slot а))))))
    (як-є ()))
  (equal?
    (clips-шаблони-з-форми
      (як-є (((deftemplate) помилкове)
              (deftemplate робоче (slot дані)))))
    (як-є ((робоче дані)))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
