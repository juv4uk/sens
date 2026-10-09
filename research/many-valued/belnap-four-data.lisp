; Research data for #223 — NOT language semantics.
; Branch: research/223-many-valued-logic
;
; Purpose:
;   represent the standard Belnap FOUR information states and both lattice
;   orderings as ordinary Lisp data, without using global truthiness.
;
; IMPORTANT:
;   () is NOT one of these four states.
;   () remains the upper canonical empty/no-answer result from #222.
;
; Sources / leads:
;   Belnap/Dunn FOUR; Fitting bilattices.
;   https://plato.stanford.edu/entries/truth-values/
;   https://doi.org/10.1016/0743-1066(91)90014-G
;
; This file is deliberately data-first. It does not ratify FOUR as the
; my-lisp richer logic and does not install any evaluator semantics.

(def research-belnap-four-values
  (quote
    (neither
     false-only
     true-only
     both)))

; Evidence reading of the four states.
; Shape: (state positive-support negative-support)
; Empty support lists are structural empty lists, not FALSE.
(def research-belnap-support-shapes
  (quote
    ((neither    ()       ())
     (false-only ()       (not-p))
     (true-only  (p)      ())
     (both       (p)      (not-p)))))

; Covering relations for the TRUTH ordering.
;
;          true-only
;          /       \
;     neither     both
;          \       /
;         false-only
;
; Pair (a b) means: a is immediately <=_truth b.
(def research-belnap-truth-covers
  (quote
    ((false-only neither)
     (false-only both)
     (neither true-only)
     (both true-only))))

; Covering relations for the KNOWLEDGE / INFORMATION ordering.
;
;             both
;            /    \
;    false-only  true-only
;            \    /
;            neither
;
; Pair (a b) means: a is immediately <=_knowledge b.
(def research-belnap-knowledge-covers
  (quote
    ((neither false-only)
     (neither true-only)
     (false-only both)
     (true-only both))))

; Standard Belnap negation: swap true-only / false-only,
; leave information gap and information glut fixed.
; Shape: (input output)
(def research-belnap-negation
  (quote
    ((neither neither)
     (false-only true-only)
     (true-only false-only)
     (both both))))

; Truth-lattice conjunction (meet under <=_truth).
; Each row shape: (left right result).
(def research-belnap-truth-meet
  (quote
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
  (quote
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
  (quote
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
  (quote
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

; Pyramid boundary witnesses as DATA, not executable assertions yet.
(def research-pyramid-boundary-cases
  (quote
    ((outer-no-answer
       expected ())

     (rational-exact-yes
       domain q-binary
       expected 1/1)

     (rational-exact-no
       domain q-binary
       expected 0/1)

     (non-rational-math
       example (> pi 3)
       domain richer
       expected-kind richer-result-or-empty)

     (richer-neither
       domain belnap-four
       expected neither
       note neither-is-an-answer-not-empty)

     (richer-conflict
       domain belnap-four
       expected both
       note conflict-does-not-explode)

     (no-richer-answer
       expected ()))))
