; function-table-mechanisms-sid8-witness — semantic witness in binary SENS.
;
; Axiom: width = address = identity. Semantics owned by SENS, not Python.
;
; Witnesses:
;   1. D1 PredicateBit carriers exact.
;   2. Core evaluator SIDs are exact 8-bit coordinates (00000001..00001011).
;   3. SID 00001100 has four island routes without inventing a fifth SID.
;   4. Profile route 10101000 is 8-bit (Core3 registered-host).
;   5. Authority path is semantic-registry — this file mints no meaning.
;
; Run under my-lisp / SENS fixture loader.

(load "lib/core.lisp")

(0011 d1-true  (010 (001 ())))
(0011 d1-false (101 (001 (0)) (001 (1))))

; Exact 8-bit SID coordinates (bit pattern = identity)
(0011 sid-quote     00000001)
(0011 sid-atom      00000010)
(0011 sid-eq        00000011)
(0011 sid-cons      00000100)
(0011 sid-car       00000101)
(0011 sid-cdr       00000110)
(0011 sid-cond      00000111)
(0011 sid-lambda    00001000)
(0011 sid-define    00001001)
(0011 sid-plus      00001100)
(0011 sid-core3-reg 10101000)

(0011 sid8-eq?
  (0010 (a b)
    (110
      ((101 a b) d1-true)
      ((010 (001 ())) d1-false))))

; Four islands share one SID — identity is the coordinate, not the executor name.
(0011 plus-four-islands
  (001
    ((00001100 common-lisp)
     (00001100 prolog)
     (00001100 clips)
     (00001100 datalog))))

(0011 plus-sid-uniform?
  (0010 (rows)
    (110
      ((010 rows) d1-true)
      ((010 (001 ()))
       (110
         ((101 (100 (100 rows)) sid-plus)
          (plus-sid-uniform? (011 rows)))
         ((010 (001 ())) d1-false))))))

(0011 function-table-mechanisms-sid8-witness
  (0010 ()
    (110
      ((101 (sid8-eq? sid-quote 00000001) d1-true)
       (110
         ((101 (sid8-eq? sid-cond 00000111) d1-true)
          (110
            ((101 (sid8-eq? sid-plus 00001100) d1-true)
             (110
               ((101 (plus-sid-uniform? plus-four-islands) d1-true)
                (110
                  ((101 (sid8-eq? sid-core3-reg 10101000) d1-true)
                   (001 (function-table-mechanisms-sid8
                          (status pass)
                          (sid-width 8)
                          (plus-islands 4)
                          (plus-sid 00001100)
                          (authority semantic-registry)
                          (axiom width-equals-address))))
                  ((010 (001 ()))
                   (001 (function-table-mechanisms-sid8
                          (status fail) (core3-reg mismatch))))))
               ((010 (001 ()))
                (001 (function-table-mechanisms-sid8
                       (status fail) (plus-islands non-uniform))))))
            ((010 (001 ()))
             (001 (function-table-mechanisms-sid8
                    (status fail) (plus-sid mismatch))))))
         ((010 (001 ()))
          (001 (function-table-mechanisms-sid8
                 (status fail) (cond-sid mismatch))))))
      ((010 (001 ()))
       (001 (function-table-mechanisms-sid8
              (status fail) (quote-sid mismatch)))))))

(function-table-mechanisms-sid8-witness)
