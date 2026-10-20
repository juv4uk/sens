; #114/#220/#275 — Lisp owns the semantic relation verdicts used by the
; content-store regression evidence. Ukrainian projection only.

(визначити content-store-no?
  (функція (value)
    (тотожне? value (як-є (d1-no-left d1-no-right)))))

(визначити content-store-authority-witness
  (функція ()
    (нехай ((value
              (як-є
                (функція
                  (x)
                  x
                )
              ))
            (written
              (fs-write
                (fs-empty)
                "code"
                value
              ))
            (fs
              (перше written)
            )
            (root-a
              (fs-serialize-root fs)
            )
            (root-b
              (fs-serialize-root fs)
            )
            (object-a
              (fs-serialize-object value)
            )
            (object-b
              (fs-serialize-object value)
            )
            (root-relation
              (однакові? root-a root-b)
            )
            (object-relation
              (однакові? object-a object-b)
            )
            (direct
              (world-tell
                (empty-world)
                (як-є zoo)
                (як-є
                  ((has-fur cat)
                  )
                )
              )
            )
            (retold
              (world-tell
                (world-retract
                  (world-tell
                    (empty-world)
                    (як-є zoo)
                    (як-є
                      ((has-fur cat)
                      )
                    )
                  )
                  (як-є zoo)
                  (як-є
                    ((has-fur cat)
                    )
                  )
                )
                (як-є zoo)
                (як-є
                  ((has-fur cat)
                  )
                )
              )
            )
            (projection-relation
              (однакові?
                (world-clauses
                  direct
                  (як-є zoo)
                )
                (world-clauses
                  retold
                  (як-є zoo)
                )
              )
            ))
      (за-умовою
        (root-relation
          (за-умовою
            (object-relation
              (за-умовою
                (projection-relation
                  (як-є
                    (content-store-authority-witness
                      (status pass)
                      (laws
                        root-image-deterministic
                        object-image-deterministic
                        equal-current-projection
                      )
                    )
                  ))
                ((content-store-no? projection-relation)
                  (як-є
                    (content-store-authority-witness
                      (status fail)
                      (law equal-current-projection)
                    )
                  ))
              ))
            ((content-store-no? object-relation)
              (як-є
                (content-store-authority-witness
                  (status fail)
                  (law object-image-deterministic)
                )
              ))
          ))
        ((content-store-no? root-relation)
          (як-є
            (content-store-authority-witness
              (status fail)
              (law root-image-deterministic)
            )
          ))
      ))))
