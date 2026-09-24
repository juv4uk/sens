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

(def cam-symbol (string->symbol "00"))
(def cam-symbol-written (write-to-string cam-symbol))
(def cam-symbol-read (read cam-symbol-written))

(def cam-string "00")
(def cam-string-written (write-to-string cam-string))
(def cam-string-read (read cam-string-written))

(def cam-sid 00000011)
(def cam-sid-written (write-to-string cam-sid))
(def cam-sid-read (read cam-sid-written))

(def cam-binary-descriptor (binary 2))

(def cam-observed
  (list
    (list (quote binary-descriptor) cam-binary-descriptor)
    (list (quote symbol-written) cam-symbol-written)
    (list (quote symbol-read) cam-symbol-read)
    (list (quote symbol-roundtrip)
          (equal? cam-symbol cam-symbol-read))
    (list (quote string-written) cam-string-written)
    (list (quote string-read) cam-string-read)
    (list (quote string-roundtrip)
          (equal? cam-string cam-string-read))
    (list (quote sid-written) cam-sid-written)
    (list (quote sid-read) cam-sid-read)
    (list (quote sid-roundtrip)
          (equal? cam-sid cam-sid-read))))

(def cam-expected
  (list
    (list (quote binary-descriptor) (list (quote binary) 2))
    (list (quote symbol-written) "00")
    (list (quote symbol-read) 0)
    (list (quote symbol-roundtrip) (quote (structural-relation distinct)))
    (list (quote string-written) "\"00\"")
    (list (quote string-read) "00")
    (list (quote string-roundtrip) (quote (structural-relation same)))
    (list (quote sid-written) "00000011")
    (list (quote sid-read) 00000011)
    (list (quote sid-roundtrip) (quote (structural-relation same)))))

(cond
  ((equal? cam-observed cam-expected)
   (structural-relation same)
   (quote (core4-answer-carrier-matrix-ok)))
  ((= 1 1) 1
   (list (quote core4-answer-carrier-matrix-mismatch)
         cam-expected
         cam-observed)))
