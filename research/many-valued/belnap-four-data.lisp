; Research data for #223 -- NOT language semantics.
; Branch: research/223-many-valued-logic
;
; Purpose: fixed Belnap four-valued tables so a future my-lisp
; implementation can compare against published lattice facts.
; These forms are DATA ONLY. They must not be installed into the
; Core4/W4 dispatch path and must not change EVAL of ordinary SENS forms.
;
; Encoding (four values):
;   neither     -- no information (gap)
;   false-only  -- only negative support
;   true-only   -- only positive support
;   both        -- conflict (glut)
;
; Lattice references follow standard Belnap FOUR / A4:
;   truth order:     false-only < neither,both < true-only
;   knowledge order: neither < false-only,true-only < both
;
; No evaluator, no reader macros, no new call-heads.
; Any code that consumes these tables lives outside Core4 and outside
; my-lisp richer logic and does not install any evaluator semantics.

(def research-belnap-four-values
  (як-є
    (neither
     false-only
     true-only
     both)))

; Shape: (state positive-support negative-support)
; Empty support lists are structural empty lists, not FALSE.
(def research-belnap-support-shapes
  (як-є
    ((neither    ()       ())
     (false-only ()       (not-p))
     (true-only  (p)      ())
     (both       (p)      (not-p)))))

; Covering relation for the truth lattice (approximation order).
; Pair (a b) means: a is immediately <=_truth b.
;
; Pair (a b) means: a is immediately <=_truth b.
(def research-belnap-truth-covers
  (як-є
    ((false-only neither)
     (false-only both)
     (neither true-only)
     (both true-only))))

; Covering relation for the knowledge lattice (information order).
;
; Pair (a b) means: a is immediately <=_knowledge b.
(def research-belnap-knowledge-covers
  (як-є
    ((neither false-only)
     (neither true-only)
     (false-only both)
     (true-only both))))

; Negation swaps positive and negative support;
; leave information gap and information glut fixed.
; Shape: (input output)
(def research-belnap-negation
  (як-є
    ((neither neither)
     (false-only true-only)
     (true-only false-only)
     (both both))))

; Truth-lattice conjunction (meet under <=_truth).
; Each row shape: (left right result).
(def research-belnap-truth-meet
  (як-є
    ((neither neither neither)
     (neither false-only false-only)
     (neither true-only neither)
     (neither both false-only)
     (false-only neither false-only)
     (false-only false-only false-only)
     (false-only true-only false-only)
     (false-only both false-only)
     (true-only neither neither)
     (true-only false-only false-only)
     (true-only true-only true-only)
     (true-only both both)
     (both neither false-only)
     (both false-only false-only)
     (both true-only both)
     (both both both))))

; Truth-lattice disjunction (join under <=_truth).
(def research-belnap-truth-join
  (як-є
    ((neither neither neither)
     (neither false-only neither)
     (neither true-only true-only)
     (neither both true-only)
     (false-only neither neither)
     (false-only false-only false-only)
     (false-only true-only true-only)
     (false-only both both)
     (true-only neither true-only)
     (true-only false-only true-only)
     (true-only true-only true-only)
     (true-only both true-only)
     (both neither true-only)
     (both false-only both)
     (both true-only true-only)
     (both both both))))

; Knowledge-lattice meet / consensus: keep only information common to both.
(def research-belnap-knowledge-meet
  (як-є
    ((neither neither neither)
     (neither false-only neither)
     (neither true-only neither)
     (neither both neither)
     (false-only neither neither)
     (false-only false-only false-only)
     (false-only true-only neither)
     (false-only both false-only)
     (true-only neither neither)
     (true-only false-only neither)
     (true-only true-only true-only)
     (true-only both true-only)
     (both neither neither)
     (both false-only false-only)
     (both true-only true-only)
     (both both both))))

; Knowledge-lattice join / information accumulation: combine support.
(def research-belnap-knowledge-join
  (як-є
    ((neither neither neither)
     (neither false-only false-only)
     (neither true-only true-only)
     (neither both both)
     (false-only neither false-only)
     (false-only false-only false-only)
     (false-only true-only both)
     (false-only both both)
     (true-only neither true-only)
     (true-only false-only both)
     (true-only true-only true-only)
     (true-only both both)
     (both neither both)
     (both false-only both)
     (both true-only both)
     (both both both))))

; Boundary cases that a future my-lisp layer must not treat as Core4 answers.
; Shape: (tag expected-result-description)
; expected is a comment-like symbol list, not evaluated.
(def research-belnap-invalid-boundary-cases
  (як-є
    ((outer-no-answer
       expected ())

     (note conflict-does-not-explode)

     (no-richer-answer
       expected ()))))
