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

(00001001 cam-symbol (01000011 "00"))
(00001001 cam-symbol-written (01001100 cam-symbol))
(00001001 cam-symbol-read (01001010 cam-symbol-written))

(00001001 cam-string "00")
(00001001 cam-string-written (01001100 cam-string))
(00001001 cam-string-read (01001010 cam-string-written))

(00001001 cam-sid 00000011)
(00001001 cam-sid-written (01001100 cam-sid))
(00001001 cam-sid-read (01001010 cam-sid-written))

(00001001 cam-binary-descriptor (10101001 2))

(00001001 cam-observed
  (00100111
    (00100111 (00000001 binary-descriptor) cam-binary-descriptor)
    (00100111 (00000001 symbol-written) cam-symbol-written)
    (00100111 (00000001 symbol-read) cam-symbol-read)
    (00100111 (00000001 symbol-roundtrip)
          (00100010 cam-symbol cam-symbol-read))
    (00100111 (00000001 string-written) cam-string-written)
    (00100111 (00000001 string-read) cam-string-read)
    (00100111 (00000001 string-roundtrip)
          (00100010 cam-string cam-string-read))
    (00100111 (00000001 sid-written) cam-sid-written)
    (00100111 (00000001 sid-read) cam-sid-read)
    (00100111 (00000001 sid-roundtrip)
          (00100010 cam-sid cam-sid-read))))

(00001001 cam-expected
  (00100111
    (00100111 (00000001 binary-descriptor) (00100111 (00000001 binary) 2))
    (00100111 (00000001 symbol-written) "00")
    (00100111 (00000001 symbol-read) 0)
    (00100111 (00000001 symbol-roundtrip) (00000001 (0)))
    (00100111 (00000001 string-written) "\"00\"")
    (00100111 (00000001 string-read) "00")
    (00100111 (00000001 string-roundtrip) (00000001 (1)))
    (00100111 (00000001 sid-written) "00000011")
    (00100111 (00000001 sid-read) 00000011)
    (00100111 (00000001 sid-roundtrip) (00000001 (1)))))

(00000111
  ((00100010 cam-observed cam-expected)
   (1)
   (00000001 (core4-answer-carrier-matrix-ok)))
  ((00011100 1 1) 1
   (00100111 (00000001 core4-answer-carrier-matrix-mismatch)
         cam-expected
         cam-observed)))
