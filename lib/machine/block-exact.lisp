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
