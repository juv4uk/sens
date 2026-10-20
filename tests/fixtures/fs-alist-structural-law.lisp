; Фізичний SENS-закон всередині Lisp: D3 COND вирішує наслідки.
; Хост не встановлює truth table. Українська проєкція.
; Правильний об'єкт = (objects bindings revision).

(за-умовою
  ((тотожне? (fs-objects (список (як-є objects) (як-є bindings) (як-є revision)))
             (як-є objects))
   так)
  (так (перше (як-є ()))))

(за-умовою
  ((тотожне? (fs-bindings (список (як-є objects) (як-є bindings) (як-є revision)))
             (як-є bindings))
   так)
  (так (перше (як-є ()))))

(за-умовою
  ((тотожне? (fs-revision (список (як-є objects) (як-є bindings) (як-є revision)))
             (як-є revision))
   так)
  (так (перше (як-є ()))))

(за-умовою
  ((fs-package-has-field? (як-є format) (як-є ((format . wsm-fs-event))))
   (за-умовою
     ((хибне? (fs-package-has-field? (як-є format) (як-є (broken))))
      (за-умовою
        ((порожній? (fs-package-field (як-є format) (як-є (broken))))
         (за-умовою
           ((хибне? (fs-package-has-field? (як-є format) (як-є (((broken-key) . value)))))
            (за-умовою
              ((порожній? (fs-package-field (як-є format) (як-є (((broken-key) . value)))))
               (за-умовою
                 ((тотожне? (перше (fs-journal-event-decision (як-є (broken))))
                            (як-є rejected))
                  (як-є structural-law-pass))
                 (так (перше (як-є ())))))
              (так (перше (як-є ())))))
           (так (перше (як-є ())))))
        (так (перше (як-є ())))))
     (так (перше (як-є ())))))
  (так (перше (як-є ()))))
