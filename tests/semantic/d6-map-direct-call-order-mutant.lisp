; D6 MAP order mutant: an implementation that reverses mapped output
; must not satisfy this wrong-order claim. Expected native SENS result D1:ні.
(визначити проба-мап-д6-мутант
  (функція (елемент) (сполучити (як-є м) елемент)))
(однакові?
  (відобразити проба-мап-д6-мутант
    (список (як-є а) (як-є б) (як-є а)))
  (список
    (сполучити (як-є м) (як-є б))
    (сполучити (як-є м) (як-є а))
    (сполучити (як-є м) (як-є а))))
