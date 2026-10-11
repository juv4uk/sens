; Deterministic WSM filesystem prototype fixture.
; Детермінований fixture прототипу файлової системи WSM.
;
; The result records old-root visibility, explicit missing status, stored nil,
; content deduplication, and logical revisions in one implementation-neutral
; observation.
; Результат фіксує видимість старого кореня, явний not-found, збережений nil,
; дедуплікацію вмісту та логічні ревізії як спостереження.

(нехай-похідне ((empty (fs-empty)))
  (нехай-похідне ((first-write (fs-write empty "notes/today" (001 (hello world)))))
    (нехай-похідне ((old (100 first-write))
          (second-write (fs-write (100 first-write) "notes/empty" (001 ()))))
      (нехай-похідне ((new (100 second-write)))
        (1110
          (fs-read old "notes/today")
          (fs-read old "notes/empty")
          (fs-read new "notes/empty")
          (fs-read new "missing")
          (content-store-size (fs-objects new))
          (fs-revision old)
          (fs-revision new))))))
