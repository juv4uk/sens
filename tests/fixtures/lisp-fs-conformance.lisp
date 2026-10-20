; Deterministic WSM filesystem prototype fixture.
; Детермінований fixture прототипу файлової системи WSM. Українська проєкція.

(нехай-похідне ((malformed-decision
                  (fs-journal-replay (список (список (як-є broken))))))
  (за-умовою
    ((тотожне? (перше malformed-decision) (як-є rejected))
     (за-умовою
       ((тотожне? (друге malformed-decision) (як-є invalid-event))
         (нехай-похідне ((empty (fs-empty)))
           (нехай-похідне ((first-write (fs-write empty "notes/today" (як-є (hello world)))))
             (нехай-похідне ((old (перше first-write))
                   (second-write (fs-write (перше first-write) "notes/empty" (як-є ()))))
               (нехай-похідне ((new (перше second-write)))
                 (список
                   (fs-read old "notes/today")
                   (fs-read old "notes/empty")
                   (fs-read new "notes/empty")
                   (fs-read new "missing")
                   (content-store-size (fs-objects new))
                   (fs-revision old)
                   (fs-revision new)))))))
       (так (як-є wrong-rejection-reason))))
    (так (як-є malformed-event-accepted))))
