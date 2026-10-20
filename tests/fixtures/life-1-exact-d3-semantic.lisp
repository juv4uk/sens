; Єдине джерело семантики перевірки LIFE-1: SENS.
; Rust/CI можуть тільки завантажити цей файл і спостерігати підсумковий D1-біт.
; Українська проєкція. D1:1 = (атом? (як-є ())); D1:0 = (атом? (сполучити (як-є ()) (як-є ()))).
;
; Якщо хоча б один SENS-свідок поверне D1:0, результат усього файла D1:0.

(визначити життя--ні?
  (функція (біт)
    (за-умовою
      (біт (атом? (сполучити (як-є ()) (як-є ()))))
      ((атом? (як-є ())) (атом? (як-є ()))))))

(визначити життя--всі?
  (функція (біти)
    (за-умовою
      ((атом? біти) (атом? (як-є ())))
      ((перше біти) (життя--всі? (решта біти)))
      ((атом? (як-є ())) (атом? (сполучити (як-є ()) (як-є ())))))))

(визначити життя--свідок-біти
  (функція ()
    (список
        (життя--рівні? (як-є ()) (як-є ()))
        (життя--рівні? (як-є а) (як-є а))
        (життя--ні? (життя--рівні? (як-є а) (як-є б)))
        (життя--ні? (життя--рівні? (як-є а) (як-є (а))))
        (життя--ні? (життя--рівні? (як-є (а)) (як-є а)))
        (життя--рівні? (як-є (а (б в))) (як-є (а (б в))))
        (життя--ні? (життя--рівні? (як-є (а (б в))) (як-є (а (б г)))))
        (життя--ні? (життя--рівні? (як-є (а)) (як-є (а б))))
        (життя--рівні? (як-є (готово (джерело радіо)))
                        (як-є (готово (джерело радіо))))
        (життя--ні?
          (життя--рівні?
            (як-є (готово (джерело радіо)))
            (як-є (готово (джерело інше)))))
        (життя--рівні?
          (життя-поле-запису
            (як-є (pending-invocation
                   (producer datalog)
                   (trigger (projection-ready prolog-to-datalog))
                   (provenance-ref observation-42)
                   (priority ordinary)
                   (semantic-id 12)))
            (як-є trigger))
          (як-є (projection-ready prolog-to-datalog)))
        (тотожне? (життя-проєкція-готова?
            (як-є (pending-invocation
                   (producer datalog)
                   (trigger (projection-ready prolog-to-datalog))
                   (provenance-ref observation-42)
                   (priority ordinary)
                   (semantic-id 12)))
            (як-є ((projection-ready prolog-to-datalog observation-42))))
          (як-є present))
        (тотожне? (життя-проєкція-готова?
            (як-є (pending-invocation
                   (producer datalog)
                   (trigger (projection-ready prolog-to-datalog))
                   (provenance-ref observation-42)
                   (priority ordinary)
                   (semantic-id 12)))
            (як-є ((projection-ready prolog-to-datalog observation-99))))
          (як-є absent))
        (тотожне? (життя-проєкція-готова?
            (як-є (pending-invocation
                   (producer datalog)
                   (trigger (projection-ready prolog-to-datalog))
                   (provenance-ref observation-42)
                   (priority ordinary)
                   (semantic-id 12)))
            (як-є ((projection-ready another-contract observation-42))))
          (як-є absent))
        (життя--рівні?
          (життя-очікування
            (список
              (як-є (pending-invocation
                     (producer datalog)
                     (trigger (projection-ready prolog-to-datalog))
                     (provenance-ref observation-42)
                     (priority ordinary)
                     (semantic-id 12)))
              (як-є (pending-invocation
                     (producer datalog)
                     (trigger (projection-ready prolog-to-datalog))
                     (provenance-ref observation-42)
                     (priority ordinary)
                     (semantic-id 12)))))
          (як-є
            ((pending-invocation
              (producer datalog)
              (trigger (projection-ready prolog-to-datalog))
              (provenance-ref observation-42)
              (priority ordinary)
              (semantic-id 12)))))
        (життя--рівні?
          (життя-спокій
            (як-є ()) (як-є ()) (як-є no-transition-required))
          (як-є (quiescence-state quiescent)))
        (життя--рівні?
          (життя-обрати-готове (як-є ()) (як-є ()))
          (як-є (scheduler-selection none)))
        (життя--рівні?
          (життя-обрати-готове
            (як-є ((pending-invocation (producer datalog) (trigger (projection-ready prolog-to-datalog)) (provenance-ref observation-42) (priority ordinary) (semantic-id 12))))
            (як-є ((projection-ready prolog-to-datalog observation-42))))
          (як-є (scheduler-selection ready (pending-invocation (producer datalog) (trigger (projection-ready prolog-to-datalog)) (provenance-ref observation-42) (priority ordinary) (semantic-id 12)) ())))
        (життя--рівні?
          (життя-обрати-готове
            (як-є ((pending-invocation (producer datalog) (trigger (projection-ready prolog-to-datalog)) (provenance-ref observation-99) (priority ordinary) (semantic-id 12)) (pending-invocation (producer datalog) (trigger (projection-ready prolog-to-datalog)) (provenance-ref observation-42) (priority ordinary) (semantic-id 12))))
            (як-є ((projection-ready prolog-to-datalog observation-42))))
          (як-є (scheduler-selection ready (pending-invocation (producer datalog) (trigger (projection-ready prolog-to-datalog)) (provenance-ref observation-42) (priority ordinary) (semantic-id 12)) ())))
      )))

(визначити життя--свідок
  (функція ()
    (життя--всі? (життя--свідок-біти))))

(життя--свідок)
