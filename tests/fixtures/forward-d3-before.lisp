; Рушій прямого виведення (у стилі CLIPS). Лише українська проєкція.
; Робоча пам'ять фактів + правила шаблон/дія. Використовує unify з lib/unify.

(load "lib/unify.lisp")

(визначити *working-memory* (як-є ()))

(визначити fire-rule
  (функція (rule fact)
    (нехай ((pattern (перше rule))
          (action (друге rule))
          (bindings (уніфікувати pattern fact (як-є ()))))
      (за-умовою
        ((атом? bindings) (як-є ()))
        (так (застосувати-підстановку action bindings))))))

(визначити fire-rule-on-facts
  (функція (rule facts)
    (за-умовою
      ((атом? facts) (як-є ()))
      (так
       (нехай ((result (fire-rule rule (перше facts))))
         (за-умовою
           ((атом? result)
            (fire-rule-on-facts rule (решта facts)))
           (так (сполучити result
                          (fire-rule-on-facts rule (решта facts))))))))))

(визначити fire-rule-on-working-memory
  (функція (rule)
    (fire-rule-on-facts rule *working-memory*)))

(визначити fire-rules-on-facts
  (функція (rules facts)
    (за-умовою
      ((атом? rules) (як-є ()))
      (так
       (додати-в-кінець
         (fire-rule-on-facts (перше rules) facts)
         (fire-rules-on-facts (решта rules) facts))))))

(визначити fire-rules-on-working-memory
  (функція (rules)
    (fire-rules-on-facts rules *working-memory*)))

(визначити assert-fact
  (функція (fact)
    (за-умовою
      ((член? fact *working-memory*) *working-memory*)
      (так
       (визначити *working-memory*
         (сполучити fact *working-memory*))
       *working-memory*))))

(визначити retract-fact
  (функція (fact)
    (визначити *working-memory*
      (вилучити fact *working-memory*))
    *working-memory*))

(визначити clear-working-memory
  (функція ()
    (визначити *working-memory* (як-є ()))
    *working-memory*))

(визначити forward-chain
  (функція (rules facts)
    (нехай ((loop (функція (wm)
                   (нехай ((derived (fire-rules-on-facts rules wm))
                         (merged (зчепити wm derived)))
                     (за-умовою
                       ((більше-або-рівне? (довжина merged) (довжина wm))
                        (за-умовою
                          ((тотожне? (довжина merged) (довжина wm)) wm)
                          (так (loop merged))))
                       (так wm))))))
      (loop facts))))

(визначити forward-d3-before-witness
  (функція ()
    (нехай ((rules
            (як-є
              ((((parent ?x ?y)) ((ancestor ?x ?y)))
               (((ancestor ?x ?y) (parent ?y ?z)) ((ancestor ?x ?z))))))
          (facts
            (як-є ((parent alice bob) (parent bob carol))))
          (result (forward-chain rules facts)))
      (за-умовою
        ((член? (як-є (ancestor alice carol)) result)
         (як-є (forward-d3-before-witness (status pass))))
        (так (як-є (forward-d3-before-witness (status fail))))))))

(forward-d3-before-witness)
