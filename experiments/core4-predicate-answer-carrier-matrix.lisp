; #1257 — Core4 predicate-answer carrier matrix.
;
; Research only.  This file does not choose the final public carrier.
; It asks the running language to prove what today's smallest existing
; representations actually do across write -> read.
;
; Invariants under test:
; - exact eight bare bits remain Sid8 and round-trip unchanged;
; - the existing Lisp `binary` binding is currently a descriptor constructor,
;   not a carrier for one concrete short bit spelling;
; - a numeric-looking Symbol such as "00" cannot be a transparent source
;   carrier if write/read changes its identity;
; - String preserves exact spelling and is therefore a collision-free
;   transport baseline only, not automatically the final semantic answer.

(0011 cam-symbol (11101101 "00"))
(0011 cam-symbol-written (11110100 cam-symbol))
(0011 cam-symbol-read (11101010 cam-symbol-written))

(визначити cam-string "00")
(0011 cam-string-written (11110100 cam-string))
(0011 cam-string-read (11101010 cam-string-written))

(визначити cam-sid 00000011)
(0011 cam-sid-written (11110100 cam-sid))
(0011 cam-sid-read (11101010 cam-sid-written))

(0011 cam-binary-descriptor (110110110 2))

(визначити cam-observed
  (список
    (список (як-є binary-descriptor) cam-binary-descriptor)
    (список (як-є symbol-written) cam-symbol-written)
    (список (як-є symbol-read) cam-symbol-read)
    (список (як-є symbol-roundtrip)
          (11110111 cam-symbol cam-symbol-read))
    (список (як-є string-written) cam-string-written)
    (список (як-є string-read) cam-string-read)
    (список (як-є string-roundtrip)
          (11110111 cam-string cam-string-read))
    (список (як-є sid-written) cam-sid-written)
    (список (як-є sid-read) cam-sid-read)
    (список (як-є sid-roundtrip)
          (11110111 cam-sid cam-sid-read))))

(визначити cam-expected
  (список
    (список (як-є binary-descriptor) (список (як-є binary) 2))
    (список (як-є symbol-written) "00")
    (список (як-є symbol-read) 0)
    (1110 (001 symbol-roundtrip) (001 (0)))
    (список (як-є string-written) "\"00\"")
    (список (як-є string-read) "00")
    (1110 (001 string-roundtrip) (001 (1)))
    (список (як-є sid-written) "00000011")
    (список (як-є sid-read) 00000011)
    (1110 (001 sid-roundtrip) (001 (1)))))

(за-умовою
  ((11110111 cam-observed cam-expected)
   (як-є (core4-answer-carrier-matrix-ok)))
  ((атом? (як-є ()))
   (список (як-є core4-answer-carrier-matrix-mismatch)
         cam-expected
         cam-observed)))
