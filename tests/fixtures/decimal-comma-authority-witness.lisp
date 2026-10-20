; #220 — decimal comma semantic expectations belong to Lisp, not Rust.
; Rust may continue to observe parser mechanics, but equivalence/identity
; verdicts for comma/dot exact numbers and numeric buffers are language data.
; Ukrainian projection only. Decimal math uses human decimal digits.

(визначити decimal-comma-authority-rows
  (функція ()
    (список
      (список (як-є comma-dot-exact)
            (тотожне? 12,455 12.455)
            (як-є (1)))
      (список (як-є comma-dot-negative-exact)
            (тотожне? -0,25 -0.25)
            (як-є (1)))
      (список (як-є comma-exponent-exact)
            (тотожне? 1,5e3 1500)
            (як-є (1)))
      (список (як-є comma-arithmetic-exact)
            (тотожне? (додати 1,5 2,5) 4)
            (як-є (1))))))

(визначити decimal-comma-authority-check
  (функція (rows)
    (за-умовою
      ((атом? rows)
       (як-є (decimal-comma-authority-witness (status pass))))
      (так
       (нехай ((row (перше rows)))
         (за-умовою
           ((тотожне? (друге row) (третє row))
            (decimal-comma-authority-check (решта rows)))
           (так
            (список
              (як-є decimal-comma-authority-witness)
              (список (як-є status) (як-є fail))
              (список (як-є case) (перше row))
              (список (як-є actual) (друге row))
              (список (як-є expected) (третє row))))))))))

(визначити decimal-comma-authority-witness
  (функція ()
    (decimal-comma-authority-check (decimal-comma-authority-rows))))
