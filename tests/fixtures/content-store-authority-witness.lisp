; #114/#220/#275 — Lisp owns the semantic relation verdicts used by the
; content-store regression evidence. Rust may observe serialization bytes and
; store cardinality, but it must not freeze `equal?` as historical t/().
;
; This witness deliberately says nothing about host mechanics. It only asks
; the language whether the two deterministic images are structurally the same
; and whether two Worlds with equal current clauses have the same projection.
; The negative-result adapter constructs an exact D1:0 by comparing against
; ATOM of a non-empty quoted list. No three-part expected-result COND remains.

(0011 content-store-no?
  (0010 (value)
    (11110111 value (11110111 (001 d1-no-left) (001 d1-no-right)))))

; Canonical three-part COND uses structural expected-result data, not truthiness.
(0011
  content-store-authority-witness
  (0010
    ()
    (001001
      ((value
          (001
            (lambda
              (x)
              x
            )
          )
        )
        (written
          (fs-write
            (fs-empty)
            "code"
            value
          )
        )
        (fs
          (100 written)
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
          (11110111 root-a root-b)
        )
        (object-relation
          (11110111 object-a object-b)
        )
        (direct
          (world-tell
            (empty-world)
            (001 zoo)
            (001
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
                (001 zoo)
                (001
                  ((has-fur cat)
                  )
                )
              )
              (001 zoo)
              (001
                ((has-fur cat)
                )
              )
            )
            (001 zoo)
            (001
              ((has-fur cat)
              )
            )
          )
        )
        (projection-relation
          (11110111
            (world-clauses
              direct
              (001 zoo)
            )
            (world-clauses
              retold
              (001 zoo)
            )
          )
        )
      )
      (110
        (root-relation
          (110
            (object-relation
              (110
                (projection-relation
                  (001
                    (content-store-authority-witness
                      (status pass)
                      (laws
                        root-image-deterministic
                        object-image-deterministic
                        equal-current-projection
                      )
                    )
                  )
                )
                ((content-store-no? projection-relation)
                  (001
                    (content-store-authority-witness
                      (status fail)
                      (law equal-current-projection)
                    )
                  )
                )
              )
            )
            ((content-store-no? object-relation)
              (001
                (content-store-authority-witness
                  (status fail)
                  (law object-image-deterministic)
                )
              )
            )
          )
        )
        ((content-store-no? root-relation)
          (001
            (content-store-authority-witness
              (status fail)
              (law root-image-deterministic)
            )
          )
        )
      )
    )
  )
)
