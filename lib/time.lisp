; Explicit timezone data for WSM. This is configuration, not an OS mutation.
; Явні дані часового поясу для WSM. Це конфігурація, а не мутація ОС.

; Convert whole UTC days since 1970-01-01 to a proleptic Gregorian date.
; This deliberately mirrors the current host-side utc-now calendar transform,
; but lives in Lisp so we can prove that calendar semantics do not belong to
; the host. Scope is non-negative Unix days; utc-now already rejects times
; before the Unix epoch.
(визначити грегоріанська-дата-з-числа-днів
  (функція (дні-від-епохи)
    ((функція (зміщені-дні)
      ((функція (ера)
        ((функція (дні-ери)
          ((функція (роки-ери)
            ((функція (рік-в-ері)
              ((функція (дні-року)
                ((функція (місяць-проміжний)
                  ((функція (день)
                    ((функція (місяць)
                      ((функція (рік)
                        (сполучити рік (сполучити місяць (сполучити день (як-є ()))))
                      )
                        (додати рік-в-ері (за-умовою ((менше? місяць 3) 1) (так 0))))
                    )
                      (додати місяць-проміжний (за-умовою ((менше? місяць-проміжний 10) 3) (так -9))))
                  )
                    (додати (відняти дні-року (частка (додати (помножити 153 місяць-проміжний) 2) 5)) 1))
                )
                  (частка (додати (помножити 5 дні-року) 2) 153))
              )
                (відняти дні-ери (додати (помножити 365 роки-ери) (відняти (частка роки-ери 4) (частка роки-ери 100)))))
            )
              (додати роки-ери (помножити ера 400)))
          )
            (частка (відняти (додати дні-ери (частка дні-ери 36524)) (додати (частка дні-ери 1460) (частка дні-ери 146096))) 365))
        )
          (відняти зміщені-дні (помножити ера 146097)))
      )
        (частка зміщені-дні 146097))
    )
      (додати дні-від-епохи 719468))
  ))


; Канонічна D10:1010111110 проєкція укр того самого Lisp-замикання.

; Pure language-level conversion from an exact Unix timestamp into UTC calendar
; data. The host owns clock observation; this function owns deterministic
; calendar semantics.
(визначити узгоджений-час-з-юнікс
  (функція (секунди-юнікс наносекунди)
    ((функція (дні)
      ((функція (секунди-доби)
        ((функція (цивільна-дата)
          ((функція (година)
            ((функція (хвилина)
              ((функція (секунда-хвилини)
                (сполучити (як-є utc) (сполучити (перше цивільна-дата) (сполучити (перше (решта цивільна-дата)) (сполучити (перше (решта (решта цивільна-дата))) (сполучити година (сполучити хвилина (сполучити секунда-хвилини (сполучити наносекунди (як-є ())))))))))
              )
                (модульна-остача секунди-доби 60))
            )
              (частка (модульна-остача секунди-доби 3600) 60))
          )
            (частка секунди-доби 3600))
        )
          (грегоріанська-дата-з-числа-днів дні))
      )
        (модульна-остача секунди-юнікс 86400))
    )
      (частка секунди-юнікс 86400))
  ))


; Minimal wall-clock host capability contract:
;   (unix-time-now) -> (unix-time seconds nanosecond)
; The host observes only the Unix clock. Calendar meaning stays here in Lisp.
(визначити юнікс-час-спостереження-узгоджений-час
  (функція (observation)
    (за-умовою
      ((тотожне? (перше observation) (як-є unix-time))
       (узгоджений-час-з-юнікс (перше (решта observation)) (перше (решта (решта observation)))))
      (так
       (сполучити (як-є rejected) (сполучити (як-є invalid-unix-time-observation) (як-є ()))))))
)

; Public UTC clock meaning is language-owned. The only host fact needed here is
; the raw Unix observation above.
(визначити узгоджений-час-зараз
  (функція ()
    (юнікс-час-спостереження-узгоджений-час (юнікс-час-зараз))))


; Interpret protocol fields from one complete NTP response. Packet I/O and
; extracting fixed-width fields are host mechanisms; deciding whether those
; fields are acceptable, mapping the NTP epoch to Unix, and converting the
; 32-bit fractional second into nanoseconds are language semantics.
;
; Expected host-side field contract for a complete response:
;   host, mode, stratum, ntp-seconds, fraction
; Successful interpretation preserves the existing public observation shape:
;   (accepted host unix-seconds nanosecond)
; Current control law: numeric comparisons produce exact D1 PredicateBit;
; AND/OR consume only that typed answer. All COND clauses are two-field
; (test expression). Predicate constants are direct one-bit values, not
; Number 0/1, T/NIL, structural () or rich classifiers used as truth.
(визначити інтернет-час-режим-припустимий?
  (функція (mode)
    (за-умовою
      ((тотожне? mode 4) так)
      ((тотожне? mode 5) так)
      (так ні)))
)

(визначити інтернет-час-рівень-припустимий?
  (функція (stratum)
    (за-умовою
      ((більше? stratum 0)
       (за-умовою
         ((менше? stratum 16) так)
         (так ні)))
      (так ні)))
)

(визначити тлумачити-поля-відповіді-часу
  (функція (host mode stratum ntp-seconds fraction)
    (за-умовою
      ((інтернет-час-режим-припустимий? mode)
       (за-умовою
         ((інтернет-час-рівень-припустимий? stratum)
          (за-умовою
            ((менше? ntp-seconds 2208988800)
             (сполучити (як-є rejected) (сполучити (як-є invalid-epoch) (як-є ()))))
            (так
             (сполучити (як-є accepted) (сполучити host (сполучити (відняти ntp-seconds 2208988800) (сполучити (частка (помножити fraction 1000000000) 4294967296) (як-є ()))))))))
         (так
          (сполучити (як-є rejected) (сполучити (як-є invalid-response) (як-є ()))))))
      (так
       (сполучити (як-є rejected) (сполучити (як-є invalid-response) (як-є ())))))))


; Adapter for the raw host boundary. The host returns either:
;   (ntp-fields host mode stratum ntp-seconds fraction)
; or a transport-level rejection such as (rejected receive-failed).
; Lisp owns every protocol interpretation after that raw observation boundary.
(визначити перетворити-сирі-дані-часу-на-спостереження
  (функція (raw)
    (за-умовою
      ((тотожне? (перше raw) (як-є ntp-fields))
       (тлумачити-поля-відповіді-часу
         (друге raw)
         (перше (решта (решта raw)))
         (перше (решта (решта (решта raw))))
         (перше (решта (решта (решта (решта raw)))))
         (перше (решта (решта (решта (решта (решта raw))))))))
      (так raw)))
)

; Public internet-time meaning is language-owned. Rust exposes only the raw NTP
; query mechanism under the deliberately mechanical name `ntp-query-raw`.
(визначити інтернет-час-синхронізувати
  (функція (host timeout-ms)
    (перетворити-сирі-дані-часу-на-спостереження
      (мережевий-протокол-часу-запит-сирий host timeout-ms))))


; Turning an accepted timestamp into calendar meaning is also language policy.
(визначити дати-календарне-значення-схваленому-часу
  (функція (observation)
    (за-умовою
      ((тотожне? (перше observation) (як-є accepted))
       (сполучити (як-є accepted)
         (сполучити (перше (решта observation))
           (сполучити (узгоджений-час-з-юнікс
                  (перше (решта (решта observation)))
                  (перше (решта (решта (решта observation)))))
             (як-є ())))))
      (так observation))))



; Nanoseconds are the one monotonic host observation. Milliseconds are only a
; coarser language-level view, so derive them instead of requiring a second
; host clock primitive. For the non-negative monotonic counter, quotient gives
; whole elapsed milliseconds (floor toward zero == floor here).
(визначити мілісекунди-з-наносекунди
  (функція (nanoseconds)
    (частка nanoseconds 1000000)))

(визначити монотонний-мс
  (функція ()
    (мілісекунди-з-наносекунди (монотонний-наносекунди))))


; Monotonic counters are host observations; deadline arithmetic is language
; semantics. Keep a pure pair of helpers so scheduler logic can be tested
; without sleeping, then expose convenience wrappers over the host counter.
(визначити крайній-час-з
  (функція (now-ns delta-ns)
    (додати now-ns delta-ns)))

(визначити крайній-час-досягнуто-у?
  (функція (now-ns deadline-ns)
    (за-умовою
      ((більше? now-ns deadline-ns) так)
      ((тотожне? now-ns deadline-ns) так)
      (так ні)))
)

(визначити крайній-час-після-нс
  (функція (delta-ns)
    (крайній-час-з (монотонний-наносекунди) delta-ns)))


(визначити крайній-час-досягнуто?
  (функція (deadline-ns)
    (крайній-час-досягнуто-у? (монотонний-наносекунди) deadline-ns)))


(визначити минуло-нс
  (функція (started-ns)
    (відняти (монотонний-наносекунди) started-ns)))


; Interpret raw host timezone declarations without performing host I/O here.
; The host contract is:
;   (timezone-declarations tz-value etc-timezone-value)
; where each value is either a non-empty string or (). Lisp owns source
; precedence and the public detected/unknown result shape.
(визначити обрати-достовірне-джерело-часового-поясу
  (функція (tz-value etc-timezone-value)
    ; D3 COND is exactly two clauses. First distinguish absent TZ; for a
    ; present TZ, distinguish empty from non-empty in a nested two-clause COND.
    (за-умовою
      ((тотожне? tz-value (як-є ()))
       ; TZ is absent: ETC is the only fallback source.
       (за-умовою
         ((тотожне? etc-timezone-value (як-є ()))
          (сполучити (як-є unknown) (сполучити (як-є host-declaration-unavailable) (як-є ())))
         )
         ((хибне? (тотожне? etc-timezone-value (як-є ())))
          (за-умовою
            ((тотожне? etc-timezone-value "")
             (сполучити (як-є unknown) (сполучити (як-є host-declaration-unavailable) (як-є ())))
            )
            ((хибне? (тотожне? etc-timezone-value ""))
             (сполучити (як-є detected) (сполучити etc-timezone-value (сполучити (як-є etc-timezone) (як-є ()))))
            )
          )
         )
       )
      )
      ((хибне? (тотожне? tz-value (як-є ())))
       ; TZ is present: empty string still permits the ETC fallback.
       (за-умовою
         ((тотожне? tz-value "")
          (за-умовою
            ((тотожне? etc-timezone-value (як-є ()))
             (сполучити (як-є unknown) (сполучити (як-є host-declaration-unavailable) (як-є ())))
            )
            ((хибне? (тотожне? etc-timezone-value (як-є ())))
             (за-умовою
               ((тотожне? etc-timezone-value "")
                (сполучити (як-є unknown) (сполучити (як-є host-declaration-unavailable) (як-є ())))
               )
               ((хибне? (тотожне? etc-timezone-value ""))
                (сполучити (як-є detected) (сполучити etc-timezone-value (сполучити (як-є etc-timezone) (як-є ()))))
               )
             )
            )
          )
         )
         ((хибне? (тотожне? tz-value ""))
          (сполучити (як-є detected) (сполучити tz-value (сполучити (як-є TZ) (як-є ()))))
         )
       )
      )
    )
  )
)
(визначити часовий-пояс-сирий-до-спостереження
  (функція (raw)
    (за-умовою
      ((тотожне? (перше raw) (як-є timezone-declarations))
       (обрати-достовірне-джерело-часового-поясу
         (перше (решта raw))
         (перше (решта (решта raw)))))
      (так
       (сполучити (як-є rejected) (сполучити (як-є invalid-timezone-observation) (як-є ()))))))
)

(визначити часовий-пояс-визначити
  (функція ()
    (часовий-пояс-сирий-до-спостереження
      (часовий-пояс-оголошення-сирий))))


(визначити створити-перевірене-значення-поясу
  (функція (name offset-seconds)
    (за-умовою
      ((string? name)
       (за-умовою
         ((менше? offset-seconds -86400)
          (сполучити (як-є rejected) (сполучити (як-є invalid-offset) (як-є ()))))
         ((більше? offset-seconds 86400)
          (сполучити (як-є rejected) (сполучити (як-є invalid-offset) (як-є ()))))
         (так
          (сполучити (як-є accepted) (сполучити (сполучити (як-є timezone) (сполучити name (сполучити offset-seconds (як-є ())))) (як-є ()))))))
      (так
       (сполучити (як-є rejected) (сполучити (як-є invalid-name) (як-є ())))))))


(визначити часовий-пояс-ім'я
  (функція (config)
    (друге config)))

(визначити часовий-пояс-зсув-секунди
  (функція (config)
    (третє config)))

; Реєстр містить стабільні поверхні всіх наведених часових функцій.
; Після визначення Lisp-замикань load_time_library застосовує чинну механічну
; проєкцію stable peers із цього реєстру до наявних значень. Повторні
; my-postcore-виклики тут застаріли: їхній шлях зупиняв завантаження,
; хоча не створював жодного нового мовного закону. Часова семантика вище
; залишається власністю SENS.

; Монотонний D10-механізм задає bootstrap; тут лишаються окремі raw host wrappers.

; Окремі D10-обгортки raw host операцій; іншим резидентам ці механізми
; не передаються лише через сусідство в таблиці домену.
(визначити мережевий-протокол-часу-запит-сирий
  (функція (вузол час-очікування-мс)
    (мережевий-протокол-часу-запит-сирий вузол час-очікування-мс)))
(визначити часовий-пояс-оголошення-сирий
  (функція () (часовий-пояс-оголошення-сирий)))
(визначити юнікс-час-зараз
  (функція () (юнікс-час-зараз)))
