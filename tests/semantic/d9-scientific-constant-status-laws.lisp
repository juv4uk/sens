; D9 scientific constant status: eight native D1 YES witnesses.
; Valid exact-by-definition/measured, invalid derived/unknown/compound,
; and fourth-field projection preserved even for unadmitted values.
(список
  (науковий-константа-стан-чинний? (як-є exact-by-definition))
  (науковий-константа-стан-чинний? (як-є measured))
  (хибне? (науковий-константа-стан-чинний? (як-є derived)))
  (хибне? (науковий-константа-стан-чинний? (як-є невідомо)))
  (хибне? (науковий-константа-стан-чинний? (список (як-є measured))))
  (тотожне? (науковий-константа-стан (список (як-є scientific-constant/1) (як-є світло) (як-є величина) (як-є exact-by-definition) (як-є physical-defining) (як-є SI) (як-є джерело))) (як-є exact-by-definition))
  (тотожне? (науковий-константа-стан (список (як-є scientific-constant/1) (як-є світло) (як-є величина) (як-є measured) (як-є physical-defining) (як-є SI) (як-є джерело))) (як-є measured))
  (тотожне? (науковий-константа-стан (список (як-є scientific-constant/1) (як-є світло) (як-є величина) (як-є derived) (як-є physical-defining) (як-є SI) (як-є джерело))) (як-є derived)))
