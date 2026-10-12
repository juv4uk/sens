; #220 — decimal comma semantic expectations belong to Lisp, not Rust.
; Rust may continue to observe parser mechanics, but equivalence/identity
; verdicts for comma/dot exact numbers and numeric buffers are language data.

(0011 decimal-comma-authority-rows
  (0010 ()
    (1110
      (1110 (001 comma-dot-exact)
            (101 12,455 12.455)
            (001 (1)))
      (1110 (001 comma-dot-negative-exact)
            (101 -0,25 -0.25)
            (001 (1)))
      (1110 (001 comma-exponent-exact)
            (101 1,5e3 1500)
            (001 (1)))
      (1110 (001 read-comma-exact)
            (101 (11101010 "12,455") 12.455)
            (001 (1)))
      (1110 (001 comma-arithmetic-exact)
            (101 (01010 1,5 2,5) 4)
            (001 (1)))
      (1110 (001 f32-comma-signed-zero-distinct)
            (101 #f32(-0,0) #f32(0,0))
            (001 (0)))
      (1110 (001 f32-dot-signed-zero-distinct)
            (101 #f32(-0.0) #f32(0.0))
            (001 (0))))))

(0011 decimal-comma-authority-check
  (0010 (rows)
    (110
      ((010 rows) ()
       (001 (decimal-comma-authority-witness (status pass))))
      ((010 rows) (0)
       (001000 ((row (100 rows)))
         (110
           ((11110111 (1001 row) (10011 row)) (1)
            (decimal-comma-authority-check (011 rows)))
           ((11110111 (1001 row) (10011 row)) (0)
            (1110
              (001 decimal-comma-authority-witness)
              (1110 (001 status) (001 fail))
              (1110 (001 case) (100 row))
              (1110 (001 actual) (1001 row))
              (1110 (001 expected) (10011 row))))))))))

(0011 decimal-comma-authority-witness
  (0010 ()
    (decimal-comma-authority-check (decimal-comma-authority-rows))))
