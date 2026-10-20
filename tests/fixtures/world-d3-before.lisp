;; Незмінний світ — звичайні дані SENS (українська проєкція).
;; (world батько журнал-знань-від-нових-до-старих метадані)

(визначити make-world
  (функція (parent journal metadata)
    (список (як-є world) parent journal metadata)))

(визначити empty-world
  (функція ()
    (make-world (як-є ()) (як-є ()) (як-є ()))))

(визначити world?
  (функція (value)
    (за-умовою
      ((атом? value) ні)
      ((тотожне? (перше value) (як-є world)) так)
      (так ні))))

(визначити world-parent (функція (world) (друге world)))
(визначити world-journal (функція (world) (третє world)))
(визначити world-metadata (функція (world) (четверте world)))

(визначити world-record
  (функція (kind payload)
    (список kind payload)))

(визначити world-tell
  (функція (world clause)
    (make-world world
                (сполучити (world-record (як-є tell) clause)
                          (world-journal world))
                (world-metadata world))))

(визначити world-retract
  (функція (world clause)
    (make-world world
                (сполучити (world-record (як-є retract) clause)
                          (world-journal world))
                (world-metadata world))))

(визначити world-module-events
  (функція (world)
    (world-journal world)))

(визначити world-remove-first
  (функція (needle items)
    (за-умовою
      ((атом? items) (як-є ()))
      ((однакові? (перше items) needle) (решта items))
      (так (сполучити (перше items)
                     (world-remove-first needle (решта items)))))))

(визначити world-apply-event
  (функція (clauses event)
    (нехай ((kind (перше event))
          (payload (друге event)))
      (за-умовою
        ((тотожне? kind (як-є tell))
         (сполучити payload clauses))
        ((тотожне? kind (як-є retract))
         (world-remove-first payload clauses))
        (так clauses)))))

(визначити world-module-known?
  (функція (world)
    (не (атом? (world-journal world)))))

(визначити world-module-missing?
  (функція (world)
    (атом? (world-journal world))))

(визначити world-clauses
  (функція (world)
    (нехай ((events (реверс (world-journal world))))
      (нехай ((loop (функція (evs acc)
                     (за-умовою
                       ((атом? evs) acc)
                       (так (loop (решта evs)
                                  (world-apply-event acc (перше evs))))))))
        (loop events (як-є ()))))))

(визначити reason-in-world
  (функція (world goal)
    (міркувати-за-індексом goal (world-clauses world))))

(визначити forward-in-world
  (функція (world rules)
    (forward-chain rules (world-clauses world))))

(визначити world-depth
  (функція (world)
    (за-умовою
      ((атом? (world-parent world)) 0)
      (так (додати 1 (world-depth (world-parent world)))))))

(визначити world-at-depth
  (функція (world depth)
    (за-умовою
      ((тотожне? (world-depth world) depth) world)
      ((атом? (world-parent world)) world)
      (так (world-at-depth (world-parent world) depth)))))

(визначити world-content-address
  (функція (world)
    (друк (список (як-є world-history)
                (world-journal world)
                (world-metadata world)))))

(визначити world-d3-before-witness
  (функція ()
    (нехай ((w0 (empty-world))
          (w1 (world-tell w0 (як-є (fact a))))
          (w2 (world-tell w1 (як-є (fact b)))))
      (за-умовою
        ((world? w2)
         (за-умовою
           ((тотожне? (world-parent w2) w1)
            (як-є (world-d3-before-witness (status pass))))
           (так (як-є (world-d3-before-witness (status fail parent))))))
        (так (як-є (world-d3-before-witness (status fail not-world))))))))

(world-d3-before-witness)
