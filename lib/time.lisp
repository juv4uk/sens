; Explicit timezone data for WSM. This is configuration, not an OS mutation.
; Явні дані часового поясу для WSM. Це конфігурація, а не мутація ОС.

; Convert whole UTC days since 1970-01-01 to a proleptic Gregorian date.
; This deliberately mirrors the current host-side utc-now calendar transform,
; but lives in Lisp so we can prove that calendar semantics do not belong to
; the host. Scope is non-negative Unix days; utc-now already rejects times
; before the Unix epoch.
(0011 civil-from-days
  (0010 (days)
    ((0010 (z)
      ((0010 (era)
        ((0010 (doe)
          ((0010 (yoe)
            ((0010 (y)
              ((0010 (doy)
                ((0010 (mp)
                  ((0010 (day)
                    ((0010 (month)
                      ((0010 (year)
                        (111 year (111 month (111 day (001 ()))))
                      )
                        (01010 y (110 ((11010 month 3) 1) ((010 (001 ())) 0))))
                    )
                      (01010 mp (110 ((11010 mp #d10) 3) ((010 (001 ())) -9))))
                  )
                    (01010 (01011 doy (quotient (01010 (10110 153 mp) 2) 5)) 1))
                )
                  (quotient (01010 (10110 5 doy) 2) 153))
              )
                (01011 doe (01010 (10110 365 yoe) (01011 (quotient yoe 4) (quotient yoe #d100)))))
            )
              (01010 yoe (10110 era 400)))
          )
            (quotient (01011 (01010 doe (quotient doe 36524)) (01010 (quotient doe 1460) (quotient doe 146096))) 365))
        )
          (01011 z (10110 era 146097)))
      )
        (quotient z 146097))
    )
      (01010 days 719468))
  ))


; Pure language-level conversion from an exact Unix timestamp into UTC calendar
; data. The host owns clock observation; this function owns deterministic
; calendar semantics.
(0011 utc-from-unix
  (0010 (seconds nanosecond)
    ((0010 (days)
      ((0010 (day-seconds)
        ((0010 (civil)
          ((0010 (hour)
            ((0010 (minute)
              ((0010 (second-of-minute)
                (111 (001 utc) (111 (100 civil) (111 (100 (011 civil)) (111 (100 (011 (011 civil))) (111 hour (111 minute (111 second-of-minute (111 nanosecond (001 ())))))))))
              )
                (mod day-seconds 60))
            )
              (quotient (mod day-seconds 3600) 60))
          )
            (quotient day-seconds 3600))
        )
          (civil-from-days days))
      )
        (mod seconds 86400))
    )
      (quotient seconds 86400))
  ))


; Minimal wall-clock host capability contract:
;   (unix-time-now) -> (unix-time seconds nanosecond)
; The host observes only the Unix clock. Calendar meaning stays here in Lisp.
(0011 unix-time-observation->utc
  (0010 (observation)
    (110
      ((101 (100 observation) (001 unix-time))
       (utc-from-unix (100 (011 observation)) (100 (011 (011 observation)))))
      ((010 (001 ()))
       (111 (001 rejected) (111 (001 invalid-unix-time-observation) (001 ()))))))
)

; Public UTC clock meaning is language-owned. The only host fact needed here is
; the raw Unix observation above.
(0011 utc-now
  (0010 ()
    (unix-time-observation->utc (unix-time-now))))


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
; (test expression). Explicit (ATOM ()) is the D1:1 fallback expression;
; neither Number 1/0, T/NIL, structural () nor rich classifiers act as tests.
(0011 internet-time-mode-valid?
  (0010 (mode)
    (110
      ((101 mode 4) (101 1 1))
      ((101 mode 5) (101 1 1))
      ((010 (001 ())) (101 1 0))))
)

(0011 internet-time-stratum-valid?
  (0010 (stratum)
    (110
      ((11011 stratum 0)
       (110
         ((11010 stratum 16) (101 1 1))
         ((010 (001 ())) (101 1 0))))
      ((010 (001 ())) (101 1 0))))
)

(0011 internet-time-fields->observation
  (0010 (host mode stratum ntp-seconds fraction)
    (110
      ((internet-time-mode-valid? mode)
       (110
         ((internet-time-stratum-valid? stratum)
          (110
            ((11010 ntp-seconds 2208988800)
             (111 (001 rejected) (111 (001 invalid-epoch) (001 ()))))
            ((010 (001 ()))
             (111 (001 accepted) (111 host (111 (01011 ntp-seconds 2208988800) (111 (quotient (10110 fraction #d1000000000) 4294967296) (001 ()))))))))
         ((010 (001 ()))
          (111 (001 rejected) (111 (001 invalid-response) (001 ()))))))
      ((010 (001 ()))
       (111 (001 rejected) (111 (001 invalid-response) (001 ())))))))


; Adapter for the raw host boundary. The host returns either:
;   (ntp-fields host mode stratum ntp-seconds fraction)
; or a transport-level rejection such as (rejected receive-failed).
; Lisp owns every protocol interpretation after that raw observation boundary.
(0011 internet-time-raw->observation
  (0010 (raw)
    (110
      ((101 (100 raw) (001 ntp-fields))
       (internet-time-fields->observation
         (100 (011 raw))
         (100 (011 (011 raw)))
         (100 (011 (011 (011 raw))))
         (100 (011 (011 (011 (011 raw)))))
         (100 (011 (011 (011 (011 (011 raw))))))))
      ((010 (001 ())) raw)))
)

; Public internet-time meaning is language-owned. Rust exposes only the raw NTP
; query mechanism under the deliberately mechanical name `ntp-query-raw`.
(0011 internet-time-sync
  (0010 (host timeout-ms)
    (internet-time-raw->observation
      (ntp-query-raw host timeout-ms))))


; Turning an accepted timestamp into calendar meaning is also language policy.
(0011 internet-time-observation->utc
  (0010 (observation)
    (110
      ((101 (100 observation) (001 accepted))
       (111 (001 accepted)
         (111 (100 (011 observation))
           (111 (utc-from-unix
                  (100 (011 (011 observation)))
                  (100 (011 (011 (011 observation)))))
             (001 ())))))
      ((010 (001 ())) observation))))



; Nanoseconds are the one monotonic host observation. Milliseconds are only a
; coarser language-level view, so derive them instead of requiring a second
; host clock primitive. For the non-negative monotonic counter, quotient gives
; whole elapsed milliseconds (floor toward zero == floor here).
(0011 milliseconds-from-nanoseconds
  (0010 (nanoseconds)
    (quotient nanoseconds #d1000000)))

(0011 mono-ms
  (0010 ()
    (milliseconds-from-nanoseconds (mono-ns))))


; Monotonic counters are host observations; deadline arithmetic is language
; semantics. Keep a pure pair of helpers so scheduler logic can be tested
; without sleeping, then expose convenience wrappers over the host counter.
(0011 deadline-from
  (0010 (now-ns delta-ns)
    (01010 now-ns delta-ns)))

(0011 deadline-reached-at?
  (0010 (now-ns deadline-ns)
    (110
      ((11011 now-ns deadline-ns) (101 1 1))
      ((101 now-ns deadline-ns) (101 1 1))
      ((010 (001 ())) (101 1 0))))
)

(0011 deadline-after-ns
  (0010 (delta-ns)
    (deadline-from (mono-ns) delta-ns)))


(0011 deadline-reached?
  (0010 (deadline-ns)
    (deadline-reached-at? (mono-ns) deadline-ns)))


(0011 elapsed-ns
  (0010 (started-ns)
    (01011 (mono-ns) started-ns)))


; Interpret raw host timezone declarations without performing host I/O here.
; The host contract is:
;   (timezone-declarations tz-value etc-timezone-value)
; where each value is either a non-empty string or (). Lisp owns source
; precedence and the public detected/unknown result shape.
(0011 timezone-declarations->observation
  (0010 (tz-value etc-timezone-value)
    (110
      ((101 tz-value "")
       (110
         ((101 etc-timezone-value "")
          (111 (001 unknown) (111 (001 host-declaration-unavailable) (001 ()))))
         ((101 etc-timezone-value (001 ()))
          (111 (001 unknown) (111 (001 host-declaration-unavailable) (001 ()))))
         ((010 (001 ()))
          (111 (001 detected) (111 etc-timezone-value (111 (001 etc-timezone) (001 ())))))))
      ((101 tz-value (001 ()))
       (110
         ((101 etc-timezone-value "")
          (111 (001 unknown) (111 (001 host-declaration-unavailable) (001 ()))))
         ((101 etc-timezone-value (001 ()))
          (111 (001 unknown) (111 (001 host-declaration-unavailable) (001 ()))))
         ((010 (001 ()))
          (111 (001 detected) (111 etc-timezone-value (111 (001 etc-timezone) (001 ())))))))
      ((010 (001 ()))
       (111 (001 detected) (111 tz-value (111 (001 TZ) (001 ())))))))
)
(0011 timezone-raw->observation
  (0010 (raw)
    (110
      ((101 (100 raw) (001 timezone-declarations))
       (timezone-declarations->observation
         (100 (011 raw))
         (100 (011 (011 raw)))))
      ((010 (001 ()))
       (111 (001 rejected) (111 (001 invalid-timezone-observation) (001 ()))))))
)

(0011 timezone-detect
  (0010 ()
    (timezone-raw->observation
      (timezone-declarations-raw))))


(0011 timezone-config
  (0010 (name offset-seconds)
    (110
      ((110100110 name)
       (110
         ((11010 offset-seconds -86400)
          (111 (001 rejected) (111 (001 invalid-offset) (001 ()))))
         ((11011 offset-seconds 86400)
          (111 (001 rejected) (111 (001 invalid-offset) (001 ()))))
         ((010 (001 ()))
          (111 (001 accepted) (111 (111 (001 timezone) (111 name (111 offset-seconds (001 ())))) (001 ()))))))
      ((010 (001 ()))
       (111 (001 rejected) (111 (001 invalid-name) (001 ())))))))


(0011 timezone-name
  (0010 (config)
    (1001 config)))

(0011 timezone-offset-seconds
  (0010 (config)
    (10011 config)))

; Реєстр містить стабільні поверхні всіх наведених часових функцій.
; Після визначення Lisp-замикань load_time_library застосовує чинну механічну
; проєкцію stable peers із цього реєстру до наявних значень. Повторні
; my-postcore-виклики тут застаріли: їхній шлях зупиняв завантаження,
; хоча не створював жодного нового мовного закону. Часова семантика вище
; залишається власністю SENS.
