; D6:000011 MAX-LIST · перевіряти числовість УСІХ D3-комірок до GREATERP.
; Після правильного D12+ значення йде D1:ні ЯК ЕЛЕМЕНТ, не як хвіст;
; очікування — арифметичний D5 Type, не CAR/CDR Type структури.
; SENS_SOURCE=tests/semantic/d6-max-list-interior-nonnumeric-type-negative.lisp
(найбільше-у-списку
  (список число-нуль ні число-один))
