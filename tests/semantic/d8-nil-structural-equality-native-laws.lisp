; D8:11110111 structural EQUAL and strict D3 EQ must not disagree on NIL.
; Eight exact D1 positives/negatives, including proper and dotted pairs.
; No local DEFINE and no direct numeric/English semantic function heads.
(список
  (однакові? (як-є ()) (як-є ()))
  (not? (однакові? (як-є ()) (як-є а)))
  (not? (однакові? (як-є а) (як-є ())))
  (однакові? (як-є а) (як-є а))
  (not? (однакові? (як-є а) (як-є б)))
  (однакові? (список (як-є а) (список (як-є б)))
             (список (як-є а) (список (як-є б))))
  (not? (однакові? (список (як-є а)) (список (як-є а) (як-є б))))
  (однакові? (сполучити (як-є а) (як-є хвіст))
             (сполучити (як-є а) (як-є хвіст))))
