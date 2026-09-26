; #177 — architecture-neutral machine block composition.
; A machine block is deliberately only an ordered list of structured machine
; forms. It owns no ISA facts, opcodes, bytes, feature tables, or semantics.
; Target-specific atoms create the forms; admission decides whether a target
; accepts them; the encoder materializes bytes only after admission.

(00001001 machine-block
  (00001000 (forms)
    forms))

(00001001 machine-block-empty
  (00001000 ()
    (00000001 ())))

(00001001 machine-block-one
  (00001000 (form)
    (list form)))

(00001001 machine-block-append
  (00001000 (block form)
    (append block (list form))))

(00001001 machine-block-concat
  (00001000 (left right)
    (append left right)))

(00001001 machine-block-forms
  (00001000 (block)
    block))
