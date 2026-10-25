; Д10 CLIPS DROP-PRINTOUTS: неправильний хвіст D1:ні за правильною парою.
; Коректний D3:() — єдина база, неправильно повернути усічений список.
; Очікується реальна D3 CAR Type з SENS ПЕРШЕ, а не D1/host-вердикт.
; SENS_SOURCE=tests/semantic/d10-clips-drop-printouts-improper-tail-negative.lisp
(прибрати-виведення-кліпс
  (сполучити (як-є (assert а)) ні))
