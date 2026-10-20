; Свідок мосту Пролог → Даталог за чинним контрактом проєкції.
; Ратифікований виклик використовує повну українську назву D10.
; Назви полів спостереження та результатів — дані зовнішнього протоколу.
; Завантаження бібліотек поки зберігає чинну назву механізму.

(завантажити-файл "lib/core.lisp")
(завантажити-файл "lib/bridge/prolog-to-datalog.lisp")

(визначити свідок-мосту-пролог-даталог
  (функція ()
    (за-умовою
      ((однакові?
         (перетворити-підстановки-пролог-на-факти-даталог
           (як-є
             (prolog-substitution-observation
               (source-ref observation-42)
               (variable ancestor)
               (values bob dave carol))))
         (як-є
           (projection-result
             (projection prolog-substitutions-to-datalog-facts)
             (source-ref observation-42)
             (facts
               ((ancestor bob)
                (ancestor dave)
                (ancestor carol))))))
       (як-є (prolog-datalog-bridge-witness (status pass))))
      ((однакові?
         (перетворити-підстановки-пролог-на-факти-даталог
           (як-є
             (prolog-substitution-observation
               (variable ancestor)
               (values bob))))
         (як-є (projection-failure missing-source-ref)))
       (як-є (prolog-datalog-bridge-witness (status pass)))))))

(свідок-мосту-пролог-даталог)
