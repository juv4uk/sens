; Deterministic WSM filesystem prototype fixture.
; Детермінований fixture прототипу файлової системи WSM.
;
; The result records old-root visibility, explicit missing status, stored nil,
; content deduplication, and logical revisions in one implementation-neutral
; observation.
; Результат фіксує видимість старого кореня, явний not-found, збережений nil,
; дедуплікацію вмісту та логічні ревізії як спостереження.

(10011100 ((empty (fs-empty)))
  (10011100 ((first-write (fs-write empty "notes/today" (00000001 (hello world)))))
    (10011100 ((old (00000101 first-write))
          (second-write (fs-write (00000101 first-write) "notes/empty" (00000001 ()))))
      (10011100 ((new (00000101 second-write)))
        (00100111
          (fs-read old "notes/today")
          (fs-read old "notes/empty")
          (fs-read new "notes/empty")
          (fs-read new "missing")
          (content-store-size (fs-objects new))
          (fs-revision old)
          (fs-revision new))))))
