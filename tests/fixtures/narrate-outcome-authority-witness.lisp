; #305 — presentation of an explicitly established epistemic `unknown` is a
; Lisp-owned law.  This witness deliberately does not infer `unknown` from
; mere absence of proof: `reason-observe` honesty is owned separately by
; tests/fixtures/reason-observe-honesty-v1.lisp and returns Canon 0 when
; neither side has evidence.
;
; Here the richer status is positively constructed with `make-unknown`; the
; presentation layer must keep that status visible rather than collapse it.
; Rust/shell observers see only the named pass envelope.
;
; #369 additionally preserves the public rejection of a non-symbol outcome tag
; before `narrate-outcome` stops consuming the historical t/() shape of
; `symbol?`. The law is the presentation result, not the predicate's old
; sentinel representation.

(load "lib/result-status.lisp")
(load "lib/narrate.lisp")

(def narrate-outcome-authority-rows
  (lambda ()
    (list
      (list
        (quote explicit-unknown-presentation)
        (narrate-outcome
          (make-unknown (quote (parent bob alice))))
        (quote
          (unknown because no-proof-found-for (parent bob alice))))
      (list
        (quote non-symbol-tag-is-invalid)
        (narrate-outcome (quote (42 payload)))
        (quote (invalid outcome-tag 42)))
      (list
        (quote pair-tag-is-invalid)
        (narrate-outcome (quote ((bad-tag) payload)))
        (quote (invalid outcome-tag (bad-tag))))
      (list
        (quote empty-list-tag-is-invalid)
        (narrate-outcome (quote (() payload)))
        (quote (invalid outcome-tag ()))))))

(def narrate-outcome-authority-check-rows
  (lambda (rows)
    (cond
      ((atom? rows) (structural-kind empty-list)
       (quote (narrate-outcome-authority-witness (status pass))))
      ((atom? rows) (structural-kind atom)
       (list
         (quote narrate-outcome-authority-witness)
         (quote (status fail))
         (quote (law malformed-row-tail))
         (list (quote actual) rows)))
      ((atom? rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((equal? (second row) (third row)) (structural-relation same)
            (narrate-outcome-authority-check-rows (cdr rows)))
           ((equal? (second row) (third row)) (structural-relation distinct)
            (list
              (quote narrate-outcome-authority-witness)
              (quote (status fail))
              (list (quote law) (car row))
              (list (quote expected) (third row))
              (list (quote actual) (second row))))))))))

(def narrate-outcome-authority-check
  (lambda ()
    (narrate-outcome-authority-check-rows
      (narrate-outcome-authority-rows))))

(narrate-outcome-authority-check)
