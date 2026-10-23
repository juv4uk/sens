; #801 — свідок планувальника LIFE-1, семантика належить СЕНС.
; Виконувані назви взято з lib/life-1-scheduler.lisp.
; Позначки повідомлень Прологу й Даталогу залишаються даними протоколу.
; Значення semantic-id у прикладах — повна укр-проєкція D5:01010 (додати),
; не десятковий історичний SID8-слот 12.

(визначити свідок-планувальника-життя-1
  (функція ()
    (нехай ((перший-виклик
             (як-є
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-42)
                 (priority ordinary)
                 (semantic-id додати))))
           (дубль-першого-виклику
             (як-є
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-42)
                 (priority ordinary)
                 (semantic-id додати))))
           (виклик-з-іншим-джерелом
             (як-є
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-99)
                 (priority ordinary)
                 (semantic-id додати))))
           (очікування
             (життя-очікування
               (список перший-виклик дубль-першого-виклику виклик-з-іншим-джерелом)))
           (готові-проєкції
             (як-є
               ((projection-ready
                  prolog-substitutions-to-datalog-facts
                  observation-42)
                (projection-ready
                  prolog-substitutions-to-datalog-facts
                  observation-99))))
           (обраний-виклик
             (життя-обрати-готове очікування готові-проєкції))
           (помилкове-походження
             (життя-проєкція-готова?
               перший-виклик
               (як-є
                 ((projection-ready
                    prolog-substitutions-to-datalog-facts
                    observation-99)))))
           (помилковий-міст
             (життя-проєкція-готова?
               перший-виклик
               (як-є
                 ((projection-ready
                    different-bridge-contract
                    observation-42))))))
      (за-умовою
        ((атом? обраний-виклик)
         (список
           (як-є life-1-scheduler-witness)
           (список (як-є status) (як-є fail))
           (список (як-є detail) (як-є missing-selection))))
        (так
         (нехай ((готове (перше (решта обраний-виклик)))
                (залишок (перше (решта (решта (решта обраний-виклик)))))
                (без-повторів? (однакові? залишок (список виклик-з-іншим-джерелом)))
                (стан-спокою-правильний?
                  (однакові?
                    (життя-спокій
                      (як-є ())
                      (як-є ())
                      (як-є no-transition-required))
                    (як-є (quiescence-state quiescent))))
                (хибні-проєкції-відхилено?
                  (однакові?
                    (список помилкове-походження помилковий-міст)
                    (як-є (absent absent)))))
           (за-умовою
             ((однакові?
                (список готове без-повторів? стан-спокою-правильний? хибні-проєкції-відхилено?)
                (як-є (ready (1) (1) (1))))
              (список
                (як-є life-1-scheduler-witness)
                (список (як-є status) (як-є pass))
                (список (як-є detail)
                      (як-є deduplicated-activation-and-quiescence))))
             (так
              (список
                (як-є life-1-scheduler-witness)
                (список (як-є status) (як-є fail))
                (список (як-є detail) (як-є scheduler-invariant-mismatch)))))))))))

; Історична зовнішня назва лишається посиланням на українську.
(визначити life-1-scheduler-witness свідок-планувальника-життя-1)

(свідок-планувальника-життя-1)
