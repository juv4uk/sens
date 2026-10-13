; Канонічний машинний блок: точні D3 QUOTE та D4 DEFINE/LAMBDA/LIST/APPEND.
; Original witness: docs/archive/historical/machine-block-original-200201b7.source.txt; саме історичне джерело не є виконавчим.
; Імена зв'язувань ще лишаються символами Lisp-проєкції, не D7 wire;
; фізичного .sens тут немає й релізний admission не заявляється.

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
