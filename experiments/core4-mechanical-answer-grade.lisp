; #1391 — minimal mechanical grader for the 15-state Core4 logic.
;
; Inputs are observations, not confidence scores:
;   direction:     -1 = no, 0 = undirected, 1 = yes
;   open-steps:     0..6 unresolved mandatory checks
;   contradiction:  0 = absent, 1 = present
;
; 0 open -> strongest directed answer (0/1).
; Each additional open mandatory check appends the same bit.
; Unknown, contradiction, or a state beyond seven directed grades -> ().
;
; This experiment never enters the 8-bit SENS function space.

(def ag-scale-form
  (car (read-all (read-file "contracts/core4-predicate-answer-scale.lisp"))))

(def ag-sections (cdr ag-scale-form))
(def ag-no-section (second ag-sections))
(def ag-boundary-section (third ag-sections))
(def ag-yes-section (fourth ag-sections))

(def ag-levels
  (lambda (section)
    (cdr (assoc (quote levels) section))))

(def ag-boundary
  (cdr (assoc (quote boundary) ag-boundary-section)))

(def answer-grade
  (lambda (direction open-steps contradiction)
    (cond
      ((= contradiction 1) 1 ag-boundary)
      ((= direction 0) 1 ag-boundary)
      ((< open-steps 0) 1 ag-boundary)
      ((> open-steps 6) 1 ag-boundary)
      ((= direction 1) 1
       (nth open-steps (ag-levels ag-yes-section)))
      ((= direction -1) 1
       (nth open-steps (ag-levels ag-no-section)))
      ((= 1 1) 1 ag-boundary))))

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
    (answer-grade 1 -1 0)))

(def ag-expected
  (list
    (nth 0 (ag-levels ag-yes-section))
    (nth 1 (ag-levels ag-yes-section))
    (nth 6 (ag-levels ag-yes-section))
    (nth 0 (ag-levels ag-no-section))
    (nth 1 (ag-levels ag-no-section))
    (nth 6 (ag-levels ag-no-section))
    ag-boundary
    ag-boundary
    ag-boundary
    ag-boundary
    ag-boundary
    ag-boundary))

(cond
  ((equal? ag-observed ag-expected)
   (structural-relation same)
   (quote (core4-mechanical-answer-grade-ok)))
  ((= 1 1) 1
   (list (quote core4-mechanical-answer-grade-mismatch)
         ag-expected
         ag-observed)))
