; lib/macro.lisp — bootstrap derivation on exact 8-bit function identities.
;
; #1325: the language has one function-identity space: 00000000..11111111.
; Human words are not function identities.
;
; SID 00001010 is derived here from mechanisms already selected by:
;   00001001 + 00001000 + 00000100 + the narrow host Closure->Macro mechanism.
;
; `make-macro` below is NOT a my-lisp function identity. It is an explicit
; temporary host substrate with no SID and is tracked by #1330/#1328 until that
; boundary is removed or represented without creating a second function ontology.
;
; Every actual my-lisp function used below is invoked only by its eight bits.
; No SID is wrapped in a string, symbol, quote-label, or named identity.

(make-macro
  (01001101
    (00000100 (00000001 00001000)
      (00000100 (00000001 args)
        (00000001
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
