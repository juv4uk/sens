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

(0011 narrate-outcome-authority-rows
  (0010 ()
    (1110
      (1110
        (001 explicit-unknown-presentation)
        (narrate-outcome
          (make-unknown (001 (parent bob alice))))
        (001
          (unknown because no-proof-found-for (parent bob alice))))
      (1110
        (001 non-symbol-tag-is-invalid)
        (narrate-outcome (001 (42 payload)))
        (001 (invalid outcome-tag 42)))
      (1110
        (001 pair-tag-is-invalid)
        (narrate-outcome (001 ((bad-tag) payload)))
        (001 (invalid outcome-tag (bad-tag))))
      (1110
        (001 empty-list-tag-is-invalid)
        (narrate-outcome (001 (() payload)))
        (001 (invalid outcome-tag ()))))))

(0011 narrate-outcome-authority-check-rows
  (0010 (rows)
    (110
      ((010 rows) ()
       (001 (narrate-outcome-authority-witness (status pass))))
      ((010 rows) (1)
       (1110
         (001 narrate-outcome-authority-witness)
         (001 (status fail))
         (001 (law malformed-row-tail))
         (1110 (001 actual) rows)))
      ((010 rows) (0)
       (001000 ((row (100 rows)))
         (110
           ((11110111 (1001 row) (10011 row)) (1)
            (narrate-outcome-authority-check-rows (011 rows)))
           ((11110111 (1001 row) (10011 row)) (0)
            (1110
              (001 narrate-outcome-authority-witness)
              (001 (status fail))
              (1110 (001 law) (100 row))
              (1110 (001 expected) (10011 row))
              (1110 (001 actual) (1001 row))))))))))

(0011 narrate-outcome-authority-check
  (0010 ()
    (narrate-outcome-authority-check-rows
      (narrate-outcome-authority-rows))))

(narrate-outcome-authority-check)
