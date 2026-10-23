; Єдине джерело семантики перевірки LIFE-1: SENS.
; Rust/CI можуть тільки завантажити цей файл і спостерігати підсумковий D1-біт.
; Українська проєкція точного Д1: істина — так, хиба — ні. () є лише структурою Д3.
;
; Якщо хоча б один SENS-свідок поверне D1:0, результат усього файла D1:0.
; Код додавання у полі semantic-id — ратифікована укр-проєкція Д5:01010,
; а не старий SID8:00001100 чи його десятковий запис 12.

(визначити життя--ні?
  (функція (біт)
    (за-умовою
      (біт ні)
      (так так))))

(визначити життя--всі?
  (функція (біти)
    (за-умовою
      ((атом? біти) так)
      ((перше біти) (життя--всі? (решта біти)))
      (так ні))))

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
                   (semantic-id додати)))
            (як-є trigger))
          (як-є (projection-ready prolog-to-datalog)))
        ; Негативні записи теж обчислює SENS, а не тестовий хост.
        (життя--рівні?
          (життя-поле-запису
            (як-є (pending-invocation (producer)))
            (як-є producer))
          (як-є absent))
        (життя--рівні?
          (життя-поле-запису
            (як-є (pending-invocation (producer datalog extra)))
            (як-є producer))
          (як-є absent))
        (життя--рівні?
          (життя-поле-запису
            (як-є (pending-invocation (producer datalog . extra)))
            (як-є producer))
          (як-є absent))
        (життя--рівні?
          (життя-поле-запису
            (як-є (pending-invocation (producer datalog)))
            (як-є producer))
          (як-є datalog))
        (тотожне? (життя-проєкція-готова?
            (як-є (pending-invocation
                   (producer datalog)
                   (trigger (projection-ready prolog-to-datalog))
                   (provenance-ref observation-42)
                   (priority ordinary)
                   (semantic-id додати)))
            (як-є ((projection-ready prolog-to-datalog observation-42))))
          (як-є present))
        (тотожне? (життя-проєкція-готова?
            (як-є (pending-invocation
                   (producer datalog)
                   (trigger (projection-ready prolog-to-datalog))
                   (provenance-ref observation-42)
                   (priority ordinary)
                   (semantic-id додати)))
            (як-є ((projection-ready prolog-to-datalog observation-99))))
          (як-є absent))
        (тотожне? (життя-проєкція-готова?
            (як-є (pending-invocation
                   (producer datalog)
                   (trigger (projection-ready prolog-to-datalog))
                   (provenance-ref observation-42)
                   (priority ordinary)
                   (semantic-id додати)))
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
                     (semantic-id додати)))
              (як-є (pending-invocation
                     (producer datalog)
                     (trigger (projection-ready prolog-to-datalog))
                     (provenance-ref observation-42)
                     (priority ordinary)
                     (semantic-id додати)))))
          (як-є
            ((pending-invocation
              (producer datalog)
              (trigger (projection-ready prolog-to-datalog))
              (provenance-ref observation-42)
              (priority ordinary)
              (semantic-id додати)))))
        (життя--рівні?
          (життя-спокій
            (як-є ()) (як-є ()) (як-є no-transition-required))
          (як-є (quiescence-state quiescent)))
        (життя--рівні?
          (життя-обрати-готове (як-є ()) (як-є ()))
          (як-є (scheduler-selection none)))
        (життя--рівні?
          (життя-обрати-готове
            (як-є ((pending-invocation (producer datalog) (trigger (projection-ready prolog-to-datalog)) (provenance-ref observation-42) (priority ordinary) (semantic-id додати))))
            (як-є ((projection-ready prolog-to-datalog observation-42))))
          (як-є (scheduler-selection ready (pending-invocation (producer datalog) (trigger (projection-ready prolog-to-datalog)) (provenance-ref observation-42) (priority ordinary) (semantic-id додати)) ())))
        (життя--рівні?
          (життя-обрати-готове
            (як-є ((pending-invocation (producer datalog) (trigger (projection-ready prolog-to-datalog)) (provenance-ref observation-99) (priority ordinary) (semantic-id додати)) (pending-invocation (producer datalog) (trigger (projection-ready prolog-to-datalog)) (provenance-ref observation-42) (priority ordinary) (semantic-id додати))))
            (як-є ((projection-ready prolog-to-datalog observation-42))))
          (як-є (scheduler-selection ready (pending-invocation (producer datalog) (trigger (projection-ready prolog-to-datalog)) (provenance-ref observation-42) (priority ordinary) (semantic-id додати)) ())))
      )))

(визначити життя--свідок
  (функція ()
    (життя--всі? (життя--свідок-біти))))

(життя--свідок)
