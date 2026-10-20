; #305 — presentation of an explicitly established epistemic unknown is a
; Lisp-owned law. Ukrainian projection only.
;
; #369 additionally preserves the public rejection of a non-symbol outcome tag
; before narrate-outcome stops consuming the historical t/() shape of symbol?.

(load "lib/result-status.lisp")
(load "lib/narrate.lisp")

(визначити рядки-свідка-результату
  (функція ()
    (список
      (список
        (як-є explicit-unknown-presentation)
        (narrate-outcome
          (make-unknown (як-є (parent bob alice))))
        (як-є
          (unknown because no-proof-found-for (parent bob alice))))
      (список
        (як-є non-symbol-tag-is-invalid)
        (narrate-outcome (як-є (42 payload)))
        (як-є (invalid outcome-tag 42)))
      (список
        (як-є pair-tag-is-invalid)
        (narrate-outcome (як-є ((bad-tag) payload)))
        (як-є (invalid outcome-tag (bad-tag))))
      (список
        (як-є empty-list-tag-is-invalid)
        (narrate-outcome (як-є (() payload)))
        (як-є (invalid outcome-tag ()))))))

(визначити перевірити-рядки-свідка-результату
  (функція (рядки)
    (за-умовою
      ((атом? рядки)
       (як-є (narrate-outcome-authority-witness (status pass))))
      (так
       (нехай ((рядок (перше рядки)))
         (за-умовою
           ((однакові? (друге рядок) (третє рядок))
            (перевірити-рядки-свідка-результату (решта рядки)))
           (так
            (список
              (як-є narrate-outcome-authority-witness)
              (як-є (status fail))
              (список (як-є law) (перше рядок))
              (список (як-є expected) (третє рядок))
              (список (як-є actual) (друге рядок))))))))))

(визначити перевірити-свідок-результату
  (функція ()
    (перевірити-рядки-свідка-результату
      (рядки-свідка-результату))))

(перевірити-свідок-результату)
