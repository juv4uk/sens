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

(00001001 ag-scale-form
  (00000101 (01001011 (10100110 "contracts/core4-predicate-answer-scale.lisp"))))

(00001001 ag-sections (00000110 ag-scale-form))
(00001001 ag-no-section (00101111 ag-sections))
(00001001 ag-boundary-section (00110000 ag-sections))
(00001001 ag-yes-section (00110001 ag-sections))

(00001001 ag-levels
  (00001000 (section)
    (00000110 (00101101 (00000001 levels) section))))

(00001001 ag-boundary
  (00000110 (00101101 (00000001 boundary) ag-boundary-section)))

(00001001 answer-grade
  (00001000 (direction open-steps contradiction)
    (00000111
      ((00011100 contradiction 1) 1 ag-boundary)
      ((00011100 direction 0) 1 ag-boundary)
      ((00011010 open-steps 0) 1 ag-boundary)
      ((00011011 open-steps 6) 1 ag-boundary)
      ((00011100 direction 1) 1
       (00101011 open-steps (ag-levels ag-yes-section)))
      ((00011100 direction -1) 1
       (00101011 open-steps (ag-levels ag-no-section)))
      ((00011100 1 1) 1 ag-boundary))))

(00001001 ag-observed
  (00100111
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

(00001001 ag-expected
  (00100111
    (00101011 0 (ag-levels ag-yes-section))
    (00101011 1 (ag-levels ag-yes-section))
    (00101011 6 (ag-levels ag-yes-section))
    (00101011 0 (ag-levels ag-no-section))
    (00101011 1 (ag-levels ag-no-section))
    (00101011 6 (ag-levels ag-no-section))
    ag-boundary
    ag-boundary
    ag-boundary
    ag-boundary
    ag-boundary
    ag-boundary))

(00000111
  ((00100010 ag-observed ag-expected)
   (1)
   (00000001 (core4-mechanical-answer-grade-ok)))
  ((00011100 1 1) 1
   (00100111 (00000001 core4-mechanical-answer-grade-mismatch)
         ag-expected
         ag-observed)))
