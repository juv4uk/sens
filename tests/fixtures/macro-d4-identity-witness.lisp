; macro-d4-identity-witness — semantic/logic witness in binary SENS.
;
; Axiom: width = address = identity. Semantics is owned by SENS, not by a
; host Python harness. This file is the test: exact D1/D4 forms only.
;
; Witnesses:
;   1. D1:1 fallback form is (010 (001 ())) — PredicateBit true carrier.
;   2. D4 LAMBDA identity is 0010; D4 DEFINE identity is 0011.
;   3. macro bootstrap COND is two-field with exact D1 else-branch.
;   4. make-macro is substrate tag only — no invented SENS SID.
;
; Run under my-lisp / SENS loader that evaluates fixture witnesses.

(load "lib/core.lisp")
(load "lib/macro.lisp")

; --- D1 PredicateBit carriers (exact width 1) -----------------------------
(0011 d1-true  (010 (001 ())))
(0011 d1-false (101 (001 (0)) (001 (1))))

; --- D4 domain coordinates (exact width 4) -------------------------------
; LAMBDA = 0010, DEFINE = 0011 — bit pattern is the identity.
(0011 d4-lambda 0010)
(0011 d4-define 0011)

; --- Equality of D4 coordinates via D3 EQ --------------------------------
(0011 d4-lambda-id?
  (0010 (x)
    (110
      ((101 x d4-lambda) d1-true)
      ((010 (001 ())) d1-false))))

(0011 d4-define-id?
  (0010 (x)
    (110
      ((101 x d4-define) d1-true)
      ((010 (001 ())) d1-false))))

; --- Two-field COND discipline probe -------------------------------------
; Else-branch must be exact D1:1, never host t/T/NIL.
(0011 cond-else-is-d1?
  (0010 ()
    (110
      ((101 (001 no) (001 yes)) d1-false)
      ((010 (001 ())) d1-true))))

; --- Aggregate witness ---------------------------------------------------
(0011 macro-d4-identity-witness
  (0010 ()
    (110
      ((101 (d4-lambda-id? 0010) d1-true)
       (110
         ((101 (d4-define-id? 0011) d1-true)
          (110
            ((101 (cond-else-is-d1?) d1-true)
             (001 (macro-d4-identity
                    (status pass)
                    (d4-lambda 0010)
                    (d4-define 0011)
                    (d1-true (010 (001 ())))
                    (cond-else exact-d1))))
            ((010 (001 ()))
             (001 (macro-d4-identity (status fail) (cond-else not-d1))))))
         ((010 (001 ()))
          (001 (macro-d4-identity (status fail) (d4-define mismatch))))))
      ((010 (001 ()))
       (001 (macro-d4-identity (status fail) (d4-lambda mismatch)))))))

(macro-d4-identity-witness)
