; Д10 CLIPS ALL-ASSERTS?: D1:ні як CONS-хвіст НЕ є D3:().
; Після правильного assert-повідомлення очікується саме D3 CAR Type;
; попередня реалізація помилково повертала D1:так.
; SENS_SOURCE=tests/semantic/d10-clips-all-asserts-improper-tail-negative.lisp
(усі-твердження-кліпс?
  (сполучити (як-є (assert а)) ні))
