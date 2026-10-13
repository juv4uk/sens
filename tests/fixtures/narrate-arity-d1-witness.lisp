; Binary-SENS semantic oracle for exact D1 arity results.
; The runner loads canonical Core and lib/narrate.lisp; this file alone
; decides whether valid, too-short, too-long, atomic and dotted forms pass.
(0011 narrate-arity-d1-rows
  (0010 ()
    (1110
      (1110
        (001 exact-two-accepted)
        (narrate-list-exact-two? (001 (unknown subject)))
        #d1:1)
      (1110
        (001 exact-three-accepted)
        (narrate-list-exact-three? (001 (proved statement results)))
        #d1:1)
      (1110
        (001 short-two-rejected)
        (narrate-list-exact-two? (001 (unknown)))
        #d1:0)
      (1110
        (001 long-three-rejected)
        (narrate-list-exact-three? (001 (partial value bound extra)))
        #d1:0)
      (1110
        (001 atom-rejected)
        (narrate-list-exact-two? 42)
        #d1:0)
      (1110
        (001 dotted-list-rejected)
        (narrate-list-exact-two? (001 (unknown . subject)))
        #d1:0))))

(0011 narrate-arity-d1-check-rows
  (0010 (rows)
    (110
      ((010 rows) () (001 (narrate-arity-d1-witness (status pass))))
      ((010 rows) #d1:1
       (1110
         (001 narrate-arity-d1-witness)
         (001 (status fail))
         (001 (law malformed-row-tail))
         (1110 (001 actual) rows)))
      ((010 rows) #d1:0
       (001001 ((row (100 rows)))
         (110
           ((11110111 (1001 row) (10011 row)) #d1:1
            (narrate-arity-d1-check-rows (011 rows)))
           ((11110111 (1001 row) (10011 row)) #d1:0
            (1110
              (001 narrate-arity-d1-witness)
              (001 (status fail))
              (1110 (001 law) (100 row))
              (1110 (001 expected) (10011 row))
              (1110 (001 actual) (1001 row))))))))))

(0011 narrate-arity-d1-witness
  (0010 ()
    (narrate-arity-d1-check-rows
      (narrate-arity-d1-rows))))

(narrate-arity-d1-witness)
