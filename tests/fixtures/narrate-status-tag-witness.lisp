; Binary-SENS semantic oracle for status-tag preservation in narrate.
; D8 EQUAL compares the actual presentation with the expected Lisp data.
; Rust only executes this witness and checks its final status envelope.
(0011 narrate-status-tag-rows
  (0010 ()
    (1110
      (1110
        (001 invalid-status-kept)
        (narrate-outcome (make-invalid (001 invalid-goal) 42))
        (001 (invalid because invalid-goal payload 42)))
      (1110
        (001 unknown-status-kept)
        (narrate-outcome (make-unknown (001 subject)))
        (001 (unknown because no-proof-found-for subject)))
      (1110
        (001 partial-status-kept)
        (narrate-outcome (make-partial (001 ()) (001 (depth . 12))))
        (001 (partial value () bound (depth . 12))))
      (1110
        (001 blocked-status-kept)
        (narrate-outcome (make-blocked (001 (depends-on corpus))))
        (001 (blocked because (depends-on corpus)))))))

(0011 narrate-status-tag-check-rows
  (0010 (rows)
    (110
      ((010 rows) () (001 (narrate-status-tag-witness (status pass))))
      ((010 rows) #d1:1
       (1110
         (001 narrate-status-tag-witness)
         (001 (status fail))
         (001 (law malformed-row-tail))
         (1110 (001 actual) rows)))
      ((010 rows) #d1:0
       (001001 ((row (100 rows)))
         (110
           ((11110111 (1001 row) (10011 row)) #d1:1
            (narrate-status-tag-check-rows (011 rows)))
           ((11110111 (1001 row) (10011 row)) #d1:0
            (1110
              (001 narrate-status-tag-witness)
              (001 (status fail))
              (1110 (001 law) (100 row))
              (1110 (001 expected) (10011 row))
              (1110 (001 actual) (1001 row))))))))))

(0011 narrate-status-tag-witness
  (0010 ()
    (narrate-status-tag-check-rows
      (narrate-status-tag-rows))))

(narrate-status-tag-witness)
