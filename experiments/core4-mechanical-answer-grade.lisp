; #1266 — minimal mechanical grader experiment for Core4 predicate answers.
;
; This experiment does NOT define a new predicate-answer runtime type.
; It does NOT reinterpret source numbers and does NOT ratify String as the
; final semantic carrier.  It proves only that a tiny Lisp function can
; choose one already-authoritative entry from #1255 mechanically.
;
; Inputs are mechanism-only observations:
;   direction:     -1 = no, 0 = unknown, 1 = yes
;   open-steps:     0..7 unresolved mandatory checks
;   contradiction:  0 = absent, 1 = present
;
; Law:
;   contradiction or unknown/invalid -> independent undirected ()
;   directed open-steps 0..6 -> nth short grade
;   directed open-steps 7 -> corresponding function-SID endpoint
;
; No confidence score, weights, probability, predicate-specific rule table,
; backend policy, or duplicate answer scale exists here.

(def ag-scale-form
  (car (read-all (read-file "contracts/core4-predicate-answer-scale.lisp"))))

(def ag-sections (cdr ag-scale-form))
(def ag-no-section (second ag-sections))
(def ag-boundary-section (third ag-sections))
(def ag-yes-section (fourth ag-sections))

(def ag-boundary-field
  (lambda (name)
    (cdr (assoc name ag-boundary-section))))

(def ag-undirected-answer
  (ag-boundary-field (quote undirected-answer)))
(def ag-no-endpoint
  (ag-boundary-field (quote no-sid-endpoint)))
(def ag-yes-endpoint
  (ag-boundary-field (quote yes-sid-endpoint)))

(def ag-levels
  (lambda (section)
    (cdr (assoc (quote levels) section))))

(def answer-grade
  (lambda (direction open-steps contradiction)
    (cond
      ((= contradiction 1) 1 ag-undirected-answer)
      ((= direction 0) 1 ag-undirected-answer)
      ((< open-steps 0) 1 ag-undirected-answer)
      ((> open-steps 7) 1 ag-undirected-answer)
      ((= direction 1) 1
       (cond
         ((= open-steps 7) 1 ag-yes-endpoint)
         ((= 1 1) 1
          (nth open-steps (ag-levels ag-yes-section)))))
      ((= direction -1) 1
       (cond
         ((= open-steps 7) 1 ag-no-endpoint)
         ((= 1 1) 1
          (nth open-steps (ag-levels ag-no-section)))))
      ((= 1 1) 1 ag-undirected-answer))))

(def ag-observed
  (list
    (answer-grade 1 0 0)
    (answer-grade 1 1 0)
    (answer-grade 1 6 0)
    (answer-grade -1 0 0)
    (answer-grade -1 1 0)
    (answer-grade -1 6 0)
    (answer-grade 0 0 0)
    (answer-grade 1 0 1)
    (answer-grade -1 0 1)
    (answer-grade 1 7 0)
    (answer-grade -1 7 0)
    (answer-grade 1 8 0)
    (answer-grade -1 -1 0)))

(def ag-expected
  (list
    (nth 0 (ag-levels ag-yes-section))
    (nth 1 (ag-levels ag-yes-section))
    (nth 6 (ag-levels ag-yes-section))
    (nth 0 (ag-levels ag-no-section))
    (nth 1 (ag-levels ag-no-section))
    (nth 6 (ag-levels ag-no-section))
    ag-undirected-answer
    ag-undirected-answer
    ag-undirected-answer
    ag-yes-endpoint
    ag-no-endpoint
    ag-undirected-answer
    ag-undirected-answer))

(cond
  ((equal? ag-observed ag-expected)
   (structural-relation same)
   (quote (core4-mechanical-answer-grade-ok)))
  ((= 1 1) 1
   (list (quote core4-mechanical-answer-grade-mismatch)
         ag-expected
         ag-observed)))
