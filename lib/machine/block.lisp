; Канонічний машинний блок: точні D3 QUOTE та D4 DEFINE/LAMBDA/LIST/APPEND.
; Original witness: docs/archive/historical/machine-block-original-200201b7.source.txt; саме історичне джерело не є виконавчим.
; Same-stem фізична міграція: lib/machine/block.bits -> lib/machine/block.sens.
; Цей людський source збережено AST-еквівалентним історичному cutover.
; Лише у фізичному SENS локальні зв'язування α-перейменовано до f/x/b/l/r,
; які є D7:W7 ASCII тільки для справді відсутніх у драбині назв.
; Тутешнє локальне block НЕ стає D7-цитатою: BLOCK = D10:0000011011;
; D10:W10 поки не підтримується фізичним T5 (W1..W9).
; Публічні імена та поведінка шести функцій збережені без змін.

(0011 machine-block
  (0010 (forms)
    forms))

(0011 machine-block-empty
  (0010 ()
    (001 ())))

(0011 machine-block-one
  (0010 (form)
    (1110 form)))

(0011 machine-block-append
  (0010 (block form)
    (1111 block (1110 form))))

(0011 machine-block-concat
  (0010 (left right)
    (1111 left right)))

(0011 machine-block-forms
  (0010 (block)
    block))
