; Semantic oracle: binary SENS decides whether the index-shape predicate
; incorrectly feeds a compound rule head to EQ. Rust only runs this witness.
(0011 reason-index-head-atom-witness
  (0010 ()
    (001001
      ((nested-rules (001 (((mortal socrates))
                           ((parent bob alice)))))
       (nested-tag (reason-index? nested-rules))
       (empty-tag (reason-index? (001 ())))
       (atom-tag (reason-index? (001 not-an-index)))
       (known-index (reason-index-linear nested-rules))
       (known-tag (reason-index? known-index)))
      (110
        ((101 nested-tag #d1:0)
         (110
           ((101 empty-tag #d1:0)
            (110
              ((101 atom-tag #d1:0)
               (110
                 ((101 known-tag #d1:1)
                  (001 (reason-index-head-atom-witness (status pass))))
                 (#d1:1
                  (001 (reason-index-head-atom-witness (status fail) (law known-schema-tag))))))
              (#d1:1
               (001 (reason-index-head-atom-witness (status fail) (law atom-negative))))))
           (#d1:1
            (001 (reason-index-head-atom-witness (status fail) (law empty-list-negative))))))
        (#d1:1
         (001 (reason-index-head-atom-witness (status fail) (law nested-rule-list-negative)))))))
(reason-index-head-atom-witness)
