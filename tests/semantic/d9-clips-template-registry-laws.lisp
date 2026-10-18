; Вісім нативних D1-законів D9 CLIPS з lib/clips-import.lisp.
; Два D9 resident-слова, без прямого допуску їх як машинних opcode.
(список
  (equal? (clips-deftemplate-ім'я (quote (deftemplate читання (slot датчик))))
          (quote читання))
  (equal? (clips-шаблони-з-форми (quote ())) (quote ()))
  (equal? (clips-шаблони-з-форми (quote ((deffacts набір (факт)))))
          (quote ()))
  (equal?
    (clips-шаблони-з-форми
      (quote ((deftemplate читання (slot датчик) (slot значення)))))
    (quote ((читання датчик значення))))
  (equal?
    (clips-шаблони-з-форми
      (quote ((deffacts шум (сигнал))
              (deftemplate перший (slot а))
              (deftemplate другий (slot б)))))
    (quote ((перший а) (другий б))))
  (equal?
    (clips-шаблон-слот-порядок
      (quote другий)
      (clips-шаблони-з-форми
        (quote ((deftemplate перший (slot а))
                (deftemplate другий (slot б))))))
    (quote (б)))
  (equal?
    (clips-шаблон-слот-порядок
      (quote відсутній)
      (clips-шаблони-з-форми
        (quote ((deftemplate перший (slot а))))))
    (quote ()))
  (equal?
    (clips-шаблони-з-форми
      (quote (((deftemplate) помилкове)
              (deftemplate робоче (slot дані)))))
    (quote ((робоче дані)))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
