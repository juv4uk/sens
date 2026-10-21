; Вісім точних законів запису наукової сталої D9.
; Числове значення 11 записане людським десятковим числом
; із точною інтерпретацією математичного домену D24+.
; quantity-1, scientific-constant-1, science-source-1,
; статуси та назви джерел залишаються цитованими
; протокольними даними без перейменування.

(список
  (однакові? (створити-науковий-константа (як-є g) (як-є (quantity-1 11 unit-x)) (як-є measured) (як-є physical-derived) (як-є si) (як-є (science-source-1 org edition))) (як-є (scientific-constant-1 g (quantity-1 11 unit-x) measured physical-derived si (science-source-1 org edition))))
  (тотожне? (науковий-константа-ім'я (створити-науковий-константа (як-є g) (як-є (quantity-1 11 unit-x)) (як-є measured) (як-є physical-derived) (як-є si) (як-є (science-source-1 org edition)))) (як-є g))
  (однакові? (науковий-константа-величина (створити-науковий-константа (як-є g) (як-є (quantity-1 11 unit-x)) (як-є measured) (як-є physical-derived) (як-є si) (як-є (science-source-1 org edition)))) (як-є (quantity-1 11 unit-x)))
  (однакові? (науковий-константа-значення (створити-науковий-константа (як-є g) (як-є (quantity-1 11 unit-x)) (як-є measured) (як-є physical-derived) (як-є si) (як-є (science-source-1 org edition)))) 11)
  (тотожне? (науковий-константа-одиниця (створити-науковий-константа (як-є g) (як-є (quantity-1 11 unit-x)) (як-є measured) (як-є physical-derived) (як-є si) (як-є (science-source-1 org edition)))) (як-є unit-x))
  (тотожне? (науковий-константа-вид (створити-науковий-константа (як-є g) (як-є (quantity-1 11 unit-x)) (як-є measured) (як-є physical-derived) (як-є si) (як-є (science-source-1 org edition)))) (як-є physical-derived))
  (тотожне? (науковий-константа-система (створити-науковий-константа (як-є g) (як-є (quantity-1 11 unit-x)) (як-є measured) (як-є physical-derived) (як-є si) (як-є (science-source-1 org edition)))) (як-є si))
  (однакові? (науковий-константа-джерело (створити-науковий-константа (як-є g) (як-є (quantity-1 11 unit-x)) (як-є measured) (як-є physical-derived) (як-є si) (як-є (science-source-1 org edition)))) (як-є (science-source-1 org edition)))
)
