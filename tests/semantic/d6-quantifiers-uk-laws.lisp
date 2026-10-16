; Native SENS positive D6:111100 ANY and D6:111101 ALL.
; Eight independent D1:YES controls including vacuous truth and short circuit.
(list
  (будь-яке? (функція (e) (атом? e)) (list (list (як-є a)) (як-є b)))
  (хибне? (будь-яке? (функція (e) (атом? e)) (list (list (як-є a)))))
  (усі? (функція (e) (атом? e)) (list (як-є a) (як-є b)))
  (хибне? (усі? (функція (e) (атом? e)) (list (як-є a) (list (як-є b)))))
  (хибне? (будь-яке? (функція (e) (атом? e)) (як-є ())))
  (усі? (функція (e) (атом? e)) (як-є ()))
  (будь-яке? (функція (e) (атом? e)) (list (як-є a) (list (як-є b))))
  (хибне? (усі? (функція (e) (атом? e)) (list (list (як-є a)) (як-є b)))))
