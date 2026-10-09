; Explicit timezone data for WSM. This is configuration, not an OS mutation.
; Явні дані часового поясу для WSM. Це конфігурація, а не мутація ОС.

; Convert whole UTC days since 1970-01-01 to a proleptic Gregorian date.
; This deliberately mirrors the current host-side utc-now calendar transform,
; but lives in Lisp so we can prove that calendar semantics do not belong to
; the host. Scope is non-negative Unix days; utc-now already rejects times
; before the Unix epoch.
(00001001 civil-from-days
  (00001000 (days)
    (10011101 ((z (00001100 days 719468))
           (era (00010100 z 146097))
           (doe (00001101 z (00001110 era 146097)))
           (yoe (00010100 (00001101 (00001100 doe (00010100 doe 36524))
                              (00001100 (00010100 doe 1460) (00010100 doe 146096)))
                           365))
           (y (00001100 yoe (00001110 era 400)))
           (doy (00001101 doe (00001100 (00001110 365 yoe)
                           (00001101 (00010100 yoe 4) (00010100 yoe #d100)))))
           (mp (00010100 (00001100 (00001110 5 doy) 2) 153))
           (day (00001100 (00001101 doy (00010100 (00001100 (00001110 153 mp) 2) 5)) 1))
           (month (00001100 mp
  (00000111
    ((00011010 mp #d10) (00001100 mp 3))
    ((00000010 (00000001 ())) (00001100 mp -9))
  )
))
           (year (00001100 y
  (00000111
    ((00011101 month 2) 1)
    ((00000010 (00000001 ())) 0)
  )
)))
      (00100111 year month day))))

; Pure language-level conversion from an exact Unix timestamp into UTC calendar
; data. The host owns clock observation; this function owns deterministic
; calendar semantics.
(00001001 utc-from-unix
  (00001000 (seconds nanosecond)
    (10011101 ((days (00010100 seconds 86400))
           (day-seconds (00010011 seconds 86400))
           (civil (civil-from-days days))
           (hour (00010100 day-seconds 3600))
           (minute (00010100 (00010011 day-seconds 3600) 60))
           (second-of-minute (00010011 day-seconds 60)))
      (00100111 (00000001 utc)
            (00000101 civil)
            (00101111 civil)
            (00110000 civil)
            hour minute second-of-minute nanosecond))))

; Minimal wall-clock host capability contract:
;   (unix-time-now) -> (unix-time seconds nanosecond)
; The host observes only the Unix clock. Calendar meaning stays here in Lisp.
(00001001 unix-time-observation->utc
  (00001000 (observation)
    (00000111
      ((00000011 (00000101 observation) (00000001 unix-time))
       (00100111
         (00000001 utc)
         (00000101 observation)
         (00101111 observation)
         (00110000 observation)))
      ((00000010 (00000001 ()))
       (00100111 (00000001 rejected) (00000001 invalid-unix-time-observation)))))
)

; Public UTC clock meaning is language-owned. The only host fact needed here is
; the raw Unix observation above.
(00001001 utc-now
  (00001000 ()
    (01100000 (01011011))))

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
(00001001 internet-time-mode-valid?
  (00001000 (mode)
    (or
      (00011100 mode 4)
      (00011100 mode 5)))
)

(00001001 internet-time-stratum-valid?
  (00001000 (stratum)
    (and
      (00011011 stratum 0)
      (00011010 stratum 16)))
)

(00001001 internet-time-fields->observation
  (00001000 (host mode stratum ntp-seconds fraction)
    (00000111
      ((internet-time-mode-valid? mode)
       (00000111
         ((internet-time-stratum-valid? stratum)
          (00000111
            ((00011010 ntp-seconds 2208988800)
             (00100111 (00000001 rejected) (00000001 invalid-epoch)))
            ((00000010 (00000001 ()))
             (00100111 (00000001 accepted) host
               (00001101 ntp-seconds 2208988800)
               (00010100 (00001110 fraction #d1000000000) 4294967296))
            )
          )
         )
         ((00000010 (00000001 ()))
          (00100111 (00000001 rejected) (00000001 invalid-response)))
       )
      )
      ((00000010 (00000001 ()))
       (00100111 (00000001 rejected) (00000001 invalid-response)))
    )
  )
)
(00001001 internet-time-raw->observation
  (00001000 (raw)
    (00000111
      ((00000011 (00000101 raw) (00000001 ntp-fields))
       (internet-time-fields->observation
         (00101111 raw)
         (00110000 raw)
         (00000101 (00000110 (00000110 (00000110 raw))))
         (00000101 (00000110 (00000110 (00000110 (00000110 raw)))))
         (00000101 (00000110 (00000110 (00000110 (00000110 (00000110 raw))))))))
      ((00000010 (00000001 ())) raw)))
)

; Public internet-time meaning is language-owned. Rust exposes only the raw NTP
; query mechanism under the deliberately mechanical name `ntp-query-raw`.
(00001001 internet-time-sync
  (00001000 (host timeout-ms)
    (internet-time-raw->observation
      (01011100 host timeout-ms))))

; Turning an accepted timestamp into calendar meaning is also language policy.
(00001001 internet-time-observation->utc
  (00001000 (observation)
    (00000111
      ((00000011 (00000101 observation) (00000001 accepted))
       (00100111 (00000001 accepted) (00101111 observation)
         (01011111 (00110000 observation)
           (00000101 (00000110 (00000110 (00000110 observation)))))))
      ((00000010 (00000001 ())) observation)
    )
  )
)
(00001001 milliseconds-from-nanoseconds
  (00001000 (nanoseconds)
    (00010100 nanoseconds #d1000000)))

(00001001 mono-ms
  (00001000 ()
    (01100001 (01011010))))

; Monotonic counters are host observations; deadline arithmetic is language
; semantics. Keep a pure pair of helpers so scheduler logic can be tested
; without sleeping, then expose convenience wrappers over the host counter.
(00001001 deadline-from
  (00001000 (now-ns delta-ns)
    (00001100 now-ns delta-ns)))

(00001001 deadline-reached-at?
  (00001000 (now-ns deadline-ns)
    (00011110 now-ns deadline-ns)))

(00001001 deadline-after-ns
  (00001000 (delta-ns)
    (01101001 (01011010) delta-ns)))

(00001001 deadline-reached?
  (00001000 (deadline-ns)
    (01100111 (01011010) deadline-ns)))

(00001001 elapsed-ns
  (00001000 (started-ns)
    (00001101 (01011010) started-ns)))

; Interpret raw host timezone declarations without performing host I/O here.
; The host contract is:
;   (timezone-declarations tz-value etc-timezone-value)
; where each value is either a non-empty string or (). Lisp owns source
; precedence and the public detected/unknown result shape.
(00001001 timezone-declarations->observation
  (00001000 (tz-value etc-timezone-value)
    (00000111
      ((and (00100100 tz-value) (00011011 (00111011 tz-value) 0))
       (00100111 (00000001 detected) tz-value (00000001 TZ)))
      ((and (00100100 etc-timezone-value) (00011011 (00111011 etc-timezone-value) 0))
       (00100111 (00000001 detected) etc-timezone-value (00000001 etc-timezone)))
      ((00000010 (00000001 ()))
       (00100111 (00000001 unknown) (00000001 host-declaration-unavailable)))))
)

; Adapt the mechanism-only host observation to public timezone meaning.
(00001001 timezone-raw->observation
  (00001000 (raw)
    (00000111
      ((00000011 (00000101 raw) (00000001 timezone-declarations))
       (timezone-declarations->observation
         (00101111 raw)
         (00110000 raw)))
      ((00000010 (00000001 ()))
       (00100111 (00000001 rejected) (00000001 invalid-timezone-observation)))))
)

(00001001 timezone-detect
  (00001000 ()
    (timezone-raw->observation
      (01011101))))

(00001001 timezone-config
  (00001000 (name offset-seconds)
    (00000111
      ((00100100 name)
       (00000111
         ((00011010 offset-seconds -86400)
          (00100111 (00000001 rejected) (00000001 invalid-offset)))
         ((00011011 offset-seconds 86400)
          (00100111 (00000001 rejected) (00000001 invalid-offset)))
         ((00000010 (00000001 ()))
          (00100111 (00000001 accepted)
            (00100111 (00000001 timezone) name offset-seconds))
         )
       )
      )
      ((00000010 (00000001 ()))
       (00100111 (00000001 rejected) (00000001 invalid-name)))
    )
  )
)
(00001001 timezone-name
  (00001000 (config)
    (00101111 config)))

(00001001 timezone-offset-seconds
  (00001000 (config)
    (00110000 config)))

; Registry-driven peer materialization for the stable public time identities.
; The numeric IDs are authority; this file does not name or implement any
; language-to-language alias. Candidate surfaces remain unavailable.
(my-postcore-materialize-stable-peers 1079 utc-now)
(my-postcore-materialize-stable-peers 1080 utc-from-unix)
(my-postcore-materialize-stable-peers 1081 unix-time-observation->utc)
(my-postcore-materialize-stable-peers 1082 milliseconds-from-nanoseconds)
(my-postcore-materialize-stable-peers 1083 mono-ms)
(my-postcore-materialize-stable-peers 1084 timezone-name)
(my-postcore-materialize-stable-peers 1085 timezone-detect)
(my-postcore-materialize-stable-peers 1086 timezone-offset-seconds)
(my-postcore-materialize-stable-peers 1087 deadline-reached?)
(my-postcore-materialize-stable-peers 1088 deadline-reached-at?)
(my-postcore-materialize-stable-peers 1089 elapsed-ns)
(my-postcore-materialize-stable-peers 1090 deadline-from)
(my-postcore-materialize-stable-peers 1091 deadline-after-ns)
(my-postcore-materialize-stable-peers 1092 internet-time-sync)
