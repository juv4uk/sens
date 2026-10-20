; #469 — executable post-core peer materialization witness.
; Ukrainian projection only.

(load "lib/generated/meta-semantic-registry.lisp")

(визначити postcore-authority-form
  (перше (прочитати-форми (шлях-файлу "lib/surface/semantic-registry.lisp"))))

(визначити postcore-authority-rows postcore-authority-form)

(визначити postcore-member-status
  (функція (needle items)
    (за-умовою
      ((атом? items) (як-є absent))
      (так
       (за-умовою
         ((тотожне? needle (перше items)) (як-є present))
         (так (postcore-member-status needle (решта items))))))))

(визначити postcore-find-authority-row
  (функція (semantic-id rows)
    (за-умовою
      ((атом? rows) (як-є ()))
      (так
       (нехай ((row (перше rows)))
         (за-умовою
           ((однакові? semantic-id (перше row)) row)
           (так (postcore-find-authority-row semantic-id (решта rows)))))))))

(визначити postcore-surfaces-with-status-onto
  (функція (status surfaces acc)
    (за-умовою
      ((атом? surfaces) (реверс acc))
      (так
       (нехай ((surface (перше surfaces))
              (word (друге surface))
              (surface-status (третє surface)))
         (за-умовою
           ((тотожне? surface-status status)
            (за-умовою
              ((тотожне? word (як-є —))
               (postcore-surfaces-with-status-onto status (решта surfaces) acc))
              (так
               (за-умовою
                 ((тотожне? (postcore-member-status word acc) (як-є present))
                  (postcore-surfaces-with-status-onto status (решта surfaces) acc))
                 ((тотожне? (postcore-member-status word acc) (як-є absent))
                  (postcore-surfaces-with-status-onto
                    status (решта surfaces) (сполучити word acc)))))))
           (так (postcore-surfaces-with-status-onto status (решта surfaces) acc))))))))

(визначити postcore-surfaces-with-status
  (функція (status registry-row)
    (за-умовою
      ((атом? registry-row) (як-є ()))
      (так (postcore-surfaces-with-status-onto status (решта registry-row) (як-є ()))))))

(визначити postcore-witness-failure
  (функція (case actual expected)
    (список
      (як-є postcore-peer-materialization-witness)
      (як-є (status fail))
      (список (як-є case) case)
      (список (як-є actual) actual)
      (список (як-є expected) expected))))

(визначити postcore-check-rows
  (функція (rows)
    (за-умовою
      ((атом? rows)
       (як-є (postcore-peer-materialization-witness (status pass))))
      (так
       (нехай ((row (перше rows)))
         (за-умовою
           ((однакові? (друге row) (третє row))
            (postcore-check-rows (решта rows)))
           (так
            (postcore-witness-failure
              (перше row)
              (друге row)
              (третє row)))))))))

(визначити postcore-phase-one
  (postcore-check-rows
    (список
      (список
        (як-є semantic-id-en)
        (my-semantic-id-for-surface (як-є utc-from-unix))
        "1080")
      (список
        (як-є semantic-id-uk)
        (my-semantic-id-for-surface (як-є всч-із-юнікс))
        "1080")
      (список
        (як-є candidate-not-admitted)
        (атом?
          (my-semantic-id-for-surface
            (як-є всесвітній-координований-час-із-часу-юнікс)))
        (як-є ()))
      (список
        (як-є initial-peer-identity)
        (тотожне? utc-from-unix всч-із-юнікс)
        (як-є (1))))))

postcore-phase-one
