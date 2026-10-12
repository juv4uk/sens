; lib/macro.lisp — bootstrap macro: exact-domain outer forms, historical quoted template.
;
; Migration boundary:
;   executable outer heads use ratified D3/D4 coordinates;
;   the nested macro template beginning with D3 COND remains unchanged quoted
;   historical data until independent macro-expansion parity is established.
;
; Historical record, not current semantic authority:
;   old SID 00001010 was explained through the former mechanism set
;   00001001 + 00001000 + 00000100 and the host Closure->Macro substrate.
;
; `make-macro` is a host substrate, not a ratified SENS function identity.
; This source makes no claim that its macro-expansion law has been admitted.
;
; The exact-domain outer-head migration never rewrites quoted template bytes.

(make-macro
  (0001
    (111 (001 00001000)
      (111 (001 args)
        (001
          ((00000111
             ((00000010 args)
              (make-macro))
             ((00000010 (00000110 args))
              (make-macro))
             ((00000010 (00000001 ()))
              (00000100 (00000001 00001001)
                (00000100 (00000101 args)
                  (00000100
                    (00000100 (00000001 make-macro)
                      (00000100
                        (00000100 (00000001 00001000)
                          (00000100
                            (00000101 (00000110 args))
                            (00000110 (00000110 args))))
                        (00000001 ())))
                    (00000001 ()))))))))))))
