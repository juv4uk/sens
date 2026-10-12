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
