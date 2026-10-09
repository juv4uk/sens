; #220 — decimal comma semantic expectations belong to Lisp, not Rust.
; Rust may continue to observe parser mechanics, but equivalence/identity
; verdicts for comma/dot exact numbers and numeric buffers are language data.

(00001001 decimal-comma-authority-rows
  (00001000 ()
    (00100111
      (00100111 (00000001 comma-dot-exact)
            (00000011 12,455 12.455)
            (00000001 (1)))
      (00100111 (00000001 comma-dot-negative-exact)
            (00000011 -0,25 -0.25)
            (00000001 (1)))
      (00100111 (00000001 comma-exponent-exact)
            (00000011 1,5e3 1500)
            (00000001 (1)))
      (00100111 (00000001 read-comma-exact)
            (00000011 (01001010 "12,455") 12.455)
            (00000001 (1)))
      (00100111 (00000001 comma-arithmetic-exact)
            (00000011 (00001100 1,5 2,5) 4)
            (00000001 (1)))
      (00100111 (00000001 f32-comma-signed-zero-distinct)
            (00000011 #f32(-0,0) #f32(0,0))
            (00000001 (0)))
      (00100111 (00000001 f32-dot-signed-zero-distinct)
            (00000011 #f32(-0.0) #f32(0.0))
            (00000001 (0))))))

(00001001 decimal-comma-authority-check
  (00001000 (rows)
    (00000111
      ((00000010 rows) ()
       (00000001 (decimal-comma-authority-witness (status pass))))
      ((00000010 rows) (0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00100010 (00101111 row) (00110000 row))
            (decimal-comma-authority-check (00000110 rows)))
           ((00000001 decimal-authority-fallback) decimal-authority-fallback
            (00100111
              (00000001 decimal-comma-authority-witness)
              (00100111 (00000001 status) (00000001 fail))
              (00100111 (00000001 case) (00000101 row))
              (00100111 (00000001 actual) (00101111 row))
              (00100111 (00000001 expected) (00110000 row))))))))))

(00001001 decimal-comma-authority-witness
  (00001000 ()
    (decimal-comma-authority-check (decimal-comma-authority-rows))))
