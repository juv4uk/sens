; lib/macro.lisp — bootstrap derivation on exact domain identities.
;
; Canonical Core calls use proved exact-width coordinates:
;   D3: QUOTE=001 ATOM=010 COND=011 CONS=100 CAR=101 CDR=110
;   D4: LAMBDA=0010 DEFINE=0011
;
; The historical EVAL byte обчислити has no independently admitted Core.D5/D6
; coordinate here, so this bootstrap uses its admitted Ukrainian surface
; `обчислити` instead of inventing a width/coordinate projection.
;
; `make-macro` remains an explicit temporary host substrate with no language
; identity; it is tracked by #1330/#1328 until represented by a proved law.

(make-macro
  (обчислити
    (100 (001 0010)
      (100 (001 args)
        (001
          ((011
             ((010 args)
              ()
              (make-macro))
             ((010 (110 args))
              ()
              (make-macro))
             (t
              t
              (100 (001 0011)
                (100 (101 args)
                  (100
                    (100 (001 make-macro)
                      (100
                        (100 (001 0010)
                          (100
                            (101 (110 args))
                            (110 (110 args))))
                        (001 ())))
                    (001 ()))))))))))))
