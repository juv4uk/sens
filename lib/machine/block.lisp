; Канонічний машинний блок: точні D3 QUOTE та D4 DEFINE/LAMBDA/LIST/APPEND.
; Original witness: docs/archive/historical/machine-block-original-200201b7.source.txt; саме історичне джерело не є виконавчим.
; Same-stem фізична міграція: lib/machine/block.bits -> lib/machine/block.sens.
; Цей людський source збережено AST-еквівалентним історичному cutover.
; Лише у фізичному SENS локальні зв'язування α-перейменовано до f/x/b/l/r,
; які є D7:W7 ASCII тільки для справді відсутніх у драбині назв.
; Тутешнє локальне block НЕ стає D7-цитатою: BLOCK = D10:0000011011;
; D10:W10 поки не підтримується фізичним T5 (W1..W9).
; Публічні імена та поведінка шести функцій збережені без змін.

(визначити machine-block
  (функція (forms)
    forms))

(визначити machine-block-empty
  (функція ()
    (як-є ())))

(визначити machine-block-one
  (функція (form)
    (список form)))

(визначити machine-block-append
  (функція (block form)
    (приєднати block (список form))))

(визначити machine-block-concat
  (функція (left right)
    (приєднати left right)))

(визначити machine-block-forms
  (функція (block)
    block))
