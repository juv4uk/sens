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

(00001001 narrate-outcome-authority-rows
  (00001000 ()
    (00100111
      (00100111
        (00000001 explicit-unknown-presentation)
        (narrate-outcome
          (make-unknown (00000001 (parent bob alice))))
        (00000001
          (unknown because no-proof-found-for (parent bob alice))))
      (00100111
        (00000001 non-symbol-tag-is-invalid)
        (narrate-outcome (00000001 (42 payload)))
        (00000001 (invalid outcome-tag 42)))
      (00100111
        (00000001 pair-tag-is-invalid)
        (narrate-outcome (00000001 ((bad-tag) payload)))
        (00000001 (invalid outcome-tag (bad-tag))))
      (00100111
        (00000001 empty-list-tag-is-invalid)
        (narrate-outcome (00000001 (() payload)))
        (00000001 (invalid outcome-tag ()))))))

(00001001 narrate-outcome-authority-check-rows
  (00001000 (rows)
    (00000111
      ((00000010 rows) ()
       (00000001 (narrate-outcome-authority-witness (status pass))))
      ((00000010 rows) (1)
       (00100111
         (00000001 narrate-outcome-authority-witness)
         (00000001 (status fail))
         (00000001 (law malformed-row-tail))
         (00100111 (00000001 actual) rows)))
      ((00000010 rows) (0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00100010 (00101111 row) (00110000 row))
            (narrate-outcome-authority-check-rows (00000110 rows)))
           ((00100010
              (00100010 (00101111 row) (00110000 row))
              (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
            (00100111
              (00000001 narrate-outcome-authority-witness)
              (00000001 (status fail))
              (00100111 (00000001 law) (00000101 row))
              (00100111 (00000001 expected) (00110000 row))
              (00100111 (00000001 actual) (00101111 row))))))))))

(00001001 narrate-outcome-authority-check
  (00001000 ()
    (narrate-outcome-authority-check-rows
      (narrate-outcome-authority-rows))))

(narrate-outcome-authority-check)
