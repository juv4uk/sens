; Канонічний машинний блок: точні D3 QUOTE та D4 DEFINE/LAMBDA/LIST/APPEND.
; Original witness: docs/archive/historical/machine-block-original-200201b7.source.txt; саме історичне джерело не є виконавчим.
; Повна фізична міграція: lib/machine/block.bits -> lib/machine/block.sens.
; Зв'язані змінні f/x/b/l/r — рівно один D7:W7 ASCII-символ у D2,
; лише оскільки ці локальні імена відсутні у драбині функцій.
; Стара локальна назва block НЕ використовується: вона є D10:0000011011
; (ратифікований BLOCK) і фізичний T5 не допускає D10:W10.
; Публічні імена функцій не змінено; семантика належить SENS.

(0011 machine-block
  (0010 (f)
    f))

(0011 machine-block-empty
  (0010 ()
    (001 ())))

(0011 machine-block-one
  (0010 (x)
    (1110 x)))

(0011 machine-block-append
  (0010 (b x)
    (1111 b (1110 x))))

(0011 machine-block-concat
  (0010 (l r)
    (1111 l r)))

(0011 machine-block-forms
  (0010 (b)
    b))
