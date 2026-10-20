; Deterministic WSM filesystem prototype fixture.
; Детермінований fixture прототипу файлової системи WSM. Українська проєкція.

(нехай-похідне ((хибне-рішення
                  (fs-journal-replay (список (список (як-є broken))))))
  (за-умовою
    ((тотожне? (перше хибне-рішення) (як-є rejected))
     (за-умовою
       ((тотожне? (друге хибне-рішення) (як-є invalid-event))
         (нехай-похідне ((порожня-файлова-система (fs-empty)))
           (нехай-похідне ((перший-запис (fs-write порожня-файлова-система "notes/today" (як-є (hello world)))))
             (нехай-похідне ((старий-корінь (перше перший-запис))
                   (другий-запис (fs-write (перше перший-запис) "notes/empty" (як-є ()))))
               (нехай-похідне ((новий-корінь (перше другий-запис)))
                 (список
                   (fs-read старий-корінь "notes/today")
                   (fs-read старий-корінь "notes/empty")
                   (fs-read новий-корінь "notes/empty")
                   (fs-read новий-корінь "missing")
                   (content-store-size (fs-objects новий-корінь))
                   (fs-revision старий-корінь)
                   (fs-revision новий-корінь)))))))
       (так (як-є wrong-rejection-reason))))
    (так (як-є malformed-event-accepted))))
