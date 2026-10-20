; #834 — executable bounded mathematical-law witness.
; Expected semantic law evidence stays in Lisp.
; The Rust observer checks only structure and the named pass envelope.
(load "lib/core.lisp")

(визначити semantic-coordinate-math-834
  (функція ()
    (за-умовою
      ((однакові? (+ 1/3 1/6) 1/2)
       (як-є (structural-relation same))
       (за-умовою
         ((однакові? (тотожне? (як-є radio) (як-є radio))
                  (як-є (identity-relation same)))
          (як-є (structural-relation same))
          (за-умовою
            ((однакові? (сполучити 41 42) (як-є (41 . 42)))
             (як-є (structural-relation same))
             (за-умовою
               ((однакові? (перше (сполучити 41 42)) 41)
                (як-є (structural-relation same))
                (за-умовою
                  ((однакові? (решта (сполучити 41 42)) 42)
                   (як-є (structural-relation same))
                   (як-є
                     (semantic-coordinate-math-834
                       (status pass)
                       (sid 00001100 exact-rational-addition)
                       (sid 00000011 atom-identity)
                       (sid 00000100 cons-car-equation)
                       (sid 00000101 car-cons-equation)
                       (sid 00000111 no-mathematical-law-witness))))
                  ((як-є fallback) (як-є migration-only))
                  ((як-є fallback) (як-є migration-only))))
               ((як-є fallback) (як-є migration-only))
               ((як-є fallback) (як-є migration-only))))
            ((як-є fallback) (як-є migration-only))
            ((як-є fallback) (як-є migration-only))))
         ((як-є fallback) (як-є migration-only))
         ((як-є fallback) (як-є migration-only))))
      ((як-є fallback) (як-є migration-only))
      ((як-є fallback) (як-є migration-only)))))

(semantic-coordinate-math-834)
