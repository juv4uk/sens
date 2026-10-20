; Свідок #809: перевірка основи LIFE-1 належить СЕНС.
; Схема й протокольні мітки залишаються незмінними даними.

(визначити схема-паритету-основи-життя
  (функція () (перше life-substrate-parity-document)))

(визначити свідок-паритету-основи-життя
  (функція ()
    (за-умовою
      ((тотожне? (схема-паритету-основи-життя) (як-є life-substrate-parity/1))
       (identity-relation same)
       (список
         (як-є life-substrate-parity-witness)
         (список (як-є status) (як-є pass))
         (список (як-є detail) (як-є awaiting-real-graal-evidence))))
      ((тотожне? (схема-паритету-основи-життя) (як-є life-substrate-parity/1))
       (identity-relation distinct)
       (список
         (як-є life-substrate-parity-witness)
         (список (як-є status) (як-є fail))
         (список (як-є detail) (як-є wrong-schema)))))))

; Сумісність історичних імен без нового машинного закону.
(визначити life-substrate-parity-schema схема-паритету-основи-життя)
(визначити life-substrate-parity-witness свідок-паритету-основи-життя)
