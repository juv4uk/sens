; Єдине джерело семантики перевірки LIFE-1: двійковий SENS.
; Rust/CI можуть тільки завантажити цей файл і спостерігати підсумковий D1-біт.
; Первинні функції: D3:001 010 011 100 101 110 111, D4:0010 0011 1110.
; Назви нижче — лише локальні зв'язування та цитовані дані, не нові коди.
; D1:1 = (010 (001 ())); D1:0 = (010 (111 (001 ()) (001 ()))).
;
; Якщо хоча б один SENS-свідок поверне D1:0, результат усього файла D1:0.

(0011 життя--ні?
  (0010 (біт)
    (110
      (біт (010 (111 (001 ()) (001 ()))))
      ((010 (001 ())) (010 (001 ()))))))

(0011 життя--всі?
  (0010 (біти)
    (110
      ((010 біти) (010 (001 ())))
      ((100 біти) (життя--всі? (011 біти)))
      ((010 (001 ())) (010 (111 (001 ()) (001 ())))))))

(0011 життя--свідок
  (0010 ()
    (життя--всі?
      (1110
        ; Атом / порожнє / вкладений список: тільки структурний D3-закон.
        (життя--рівні? (001 ()) (001 ()))
        (життя--рівні? (001 а) (001 а))
        (життя--ні? (життя--рівні? (001 а) (001 б)))
        (життя--ні? (життя--рівні? (001 а) (001 (а))))
        (життя--ні? (життя--рівні? (001 (а)) (001 а)))
        (життя--рівні? (001 (а (б в))) (001 (а (б в))))
        (життя--ні? (життя--рівні? (001 (а (б в))) (001 (а (б г)))))
        (життя--ні? (життя--рівні? (001 (а)) (001 (а б))))
        (життя--рівні? (001 (готово (джерело радіо)))
                        (001 (готово (джерело радіо))))
        (життя--ні?
          (життя--рівні?
            (001 (готово (джерело радіо)))
            (001 (готово (джерело інше)))))
        ; Порівняння планувальника залишається даними, не host EQUAL.
        (життя--рівні?
          (life-scheduler-field
            (001 (pending-invocation
                   (producer datalog)
                   (trigger (projection-ready prolog-to-datalog))
                   (provenance-ref observation-42)
                   (priority ordinary)
                   (semantic-id 00001100)))
            (001 trigger))
          (001 (projection-ready prolog-to-datalog)))
        (101
          (life-scheduler-projection-ready?
            (001 (pending-invocation
                   (producer datalog)
                   (trigger (projection-ready prolog-to-datalog))
                   (provenance-ref observation-42)
                   (priority ordinary)
                   (semantic-id 00001100)))
            (001 ((projection-ready prolog-to-datalog observation-42))))
          (001 present))
        (101
          (life-scheduler-projection-ready?
            (001 (pending-invocation
                   (producer datalog)
                   (trigger (projection-ready prolog-to-datalog))
                   (provenance-ref observation-42)
                   (priority ordinary)
                   (semantic-id 00001100)))
            (001 ((projection-ready prolog-to-datalog observation-99))))
          (001 absent))
        (101
          (life-scheduler-projection-ready?
            (001 (pending-invocation
                   (producer datalog)
                   (trigger (projection-ready prolog-to-datalog))
                   (provenance-ref observation-42)
                   (priority ordinary)
                   (semantic-id 00001100)))
            (001 ((projection-ready another-contract observation-42))))
          (001 absent))
        (життя--рівні?
          (life-scheduler-pending
            (1110
              (001 (pending-invocation
                     (producer datalog)
                     (trigger (projection-ready prolog-to-datalog))
                     (provenance-ref observation-42)
                     (priority ordinary)
                     (semantic-id 00001100)))
              (001 (pending-invocation
                     (producer datalog)
                     (trigger (projection-ready prolog-to-datalog))
                     (provenance-ref observation-42)
                     (priority ordinary)
                     (semantic-id 00001100)))))
          (001
            ((pending-invocation
              (producer datalog)
              (trigger (projection-ready prolog-to-datalog))
              (provenance-ref observation-42)
              (priority ordinary)
              (semantic-id 00001100)))))
        (життя--рівні?
          (life-scheduler-quiescence
            (001 ()) (001 ()) (001 no-transition-required))
          (001 (quiescence-state quiescent)))))))

(життя--свідок)
