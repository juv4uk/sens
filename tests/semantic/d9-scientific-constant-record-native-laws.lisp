; D9 scientific-constant/1: eight exact resident constructor/projection laws.
; Retain D24 value and immutable source/epistemic metadata as data.
(список
  (однакові? (створити-науковий-константа (як-є g) (як-є (quantity/1 #d24:000000000000000000001011 unit-x)) (як-є measured) (як-є physical-derived) (як-є si) (як-є (science-source/1 org edition))) (як-є (scientific-constant/1 g (quantity/1 #d24:000000000000000000001011 unit-x) measured physical-derived si (science-source/1 org edition))))
  (тотожне? (науковий-константа-ім'я (створити-науковий-константа (як-є g) (як-є (quantity/1 #d24:000000000000000000001011 unit-x)) (як-є measured) (як-є physical-derived) (як-є si) (як-є (science-source/1 org edition)))) (як-є g))
  (однакові? (науковий-константа-величина (створити-науковий-константа (як-є g) (як-є (quantity/1 #d24:000000000000000000001011 unit-x)) (як-є measured) (як-є physical-derived) (як-є si) (як-є (science-source/1 org edition)))) (як-є (quantity/1 #d24:000000000000000000001011 unit-x)))
  (однакові? (науковий-константа-значення (створити-науковий-константа (як-є g) (як-є (quantity/1 #d24:000000000000000000001011 unit-x)) (як-є measured) (як-є physical-derived) (як-є si) (як-є (science-source/1 org edition)))) #d24:000000000000000000001011)
  (тотожне? (науковий-константа-одиниця (створити-науковий-константа (як-є g) (як-є (quantity/1 #d24:000000000000000000001011 unit-x)) (як-є measured) (як-є physical-derived) (як-є si) (як-є (science-source/1 org edition)))) (як-є unit-x))
  (тотожне? (науковий-константа-вид (створити-науковий-константа (як-є g) (як-є (quantity/1 #d24:000000000000000000001011 unit-x)) (як-є measured) (як-є physical-derived) (як-є si) (як-є (science-source/1 org edition)))) (як-є physical-derived))
  (тотожне? (науковий-константа-система (створити-науковий-константа (як-є g) (як-є (quantity/1 #d24:000000000000000000001011 unit-x)) (як-є measured) (як-є physical-derived) (як-є si) (як-є (science-source/1 org edition)))) (як-є si))
  (однакові? (науковий-константа-джерело (створити-науковий-константа (як-є g) (як-є (quantity/1 #d24:000000000000000000001011 unit-x)) (як-є measured) (як-є physical-derived) (як-є si) (як-є (science-source/1 org edition)))) (як-є (science-source/1 org edition)))
)
