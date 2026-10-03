; Explicit timezone data for WSM. This is configuration, not an OS mutation.
; Явні дані часового поясу для WSM. Це конфігурація, а не мутація ОС.

; Convert whole UTC days since 1970-01-01 to a proleptic Gregorian date.
; This deliberately mirrors the current host-side utc-now calendar transform,
; but lives in Lisp so we can prove that calendar semantics do not belong to
; the host. Scope is non-negative Unix days; utc-now already rejects times
; before the Unix epoch.
(0011 civil-from-days
  (0010 (days)
    (let* ((z (01010 days 719468))
           (era (quotient z 146097))
           (doe (01011 z (10010 era 146097)))
           (yoe (quotient (01011 (01010 doe (quotient doe 36524))
                              (01010 (quotient doe 1460) (quotient doe 146096)))
                           365))
           (y (01010 yoe (10010 era 400)))
           (doy (01011 doe (01010 (10010 365 yoe)
                           (01011 (quotient yoe 4) (quotient yoe #d100)))))
           (mp (quotient (01010 (10010 5 doy) 2) 153))
           (day (01010 (01011 doy (quotient (01010 (10010 153 mp) 2) 5)) 1))
           (month (01010 mp (011 ((01110 mp #d10) 1 3) ((01110 mp #d10) 0 -9))))
           (year (01010 y (011 ((not-greaterp? month 2) 1 1) ((not-greaterp? month 2) 0 0)))))
      (list year month day))))

; Pure language-level conversion from an exact Unix timestamp into UTC calendar
; data. The host owns clock observation; this function owns deterministic
; calendar semantics.
(0011 utc-from-unix
  (0010 (seconds nanosecond)
    (let* ((days (quotient seconds 86400))
           (day-seconds (mod seconds 86400))
           (civil (civil-from-days days))
           (hour (quotient day-seconds 3600))
           (minute (quotient (mod day-seconds 3600) 60))
           (second-of-minute (mod day-seconds 60)))
      (list (001 utc)
            (101 civil)
            (second civil)
            (third civil)
            hour minute second-of-minute nanosecond))))

; Minimal wall-clock host capability contract:
;   (unix-time-now) -> (unix-time seconds nanosecond)
; The host observes only the Unix clock. Calendar meaning stays here in Lisp.
(0011 unix-time-observation->utc
  (0010 (observation)
    (011
      ((111 (101 observation) (001 unix-time))
       (utc-from-unix (second observation) (third observation)))
      (t (list (001 rejected) (001 invalid-unix-time-observation))))))

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
; Exact-Q answers 1 (так) / 0 (ні), and 0 is truthy, so `or` / `and` / `not`
; over comparison results no longer decide anything (or collapses every
; operand, falsy or not, to t). E1 (#216): validity is decided by explicit
; three-part gates whose queries answer 1/0 and are consumed by expected
; 1/0 slots; canonical cond accepts no bare t/() clause query.
(0011 internet-time-mode-valid?
  (0010 (mode)
    (011
      ((equalp? mode 4) 1 1)
      ((equalp? mode 4) 0
       (011
         ((equalp? mode 5) 1 1)
         ((equalp? mode 5) 0 0))))))

(0011 internet-time-stratum-valid?
  (0010 (stratum)
    (011
      ((equalp? stratum 0) 1 0)
      ((equalp? stratum 0) 0
       (011
         ((01111 stratum 15) 1 0)
         ((01111 stratum 15) 0 1))))))

(0011 internet-time-fields->observation
  (0010 (host mode stratum ntp-seconds fraction)
    (011
      ((internet-time-mode-valid? mode) 1
        (011
          ((internet-time-stratum-valid? stratum) 1
            (011
              ((01110 ntp-seconds 2208988800) 1
               (list (001 rejected) (001 invalid-epoch)))
              ((01110 ntp-seconds 2208988800) 0
               (list (001 accepted)
                     host
                     (01011 ntp-seconds 2208988800)
                     (quotient (10010 fraction #d1000000000) 4294967296)))))
          ((internet-time-stratum-valid? stratum) 0
            (list (001 rejected) (001 invalid-response)))))
      ((internet-time-mode-valid? mode) 0
        (list (001 rejected) (001 invalid-response))))))

; Adapter for the raw host boundary. The host returns either:
;   (ntp-fields host mode stratum ntp-seconds fraction)
; or a transport-level rejection such as (rejected receive-failed).
; Lisp owns every protocol interpretation after that raw observation boundary.
(0011 internet-time-raw->observation
  (0010 (raw)
    (011
      ((111 (101 raw) (001 ntp-fields))
       (internet-time-fields->observation
         (second raw)
         (third raw)
         (101 (110 (110 (110 raw))))
         (101 (110 (110 (110 (110 raw)))))
         (101 (110 (110 (110 (110 (110 raw))))))))
      (t raw))))

; Public internet-time meaning is language-owned. Rust exposes only the raw NTP
; query mechanism under the deliberately mechanical name `ntp-query-raw`.
(0011 internet-time-sync
  (0010 (host timeout-ms)
    (internet-time-raw->observation
      (ntp-query-raw host timeout-ms))))

; Turning an accepted timestamp into calendar meaning is also language policy.
(0011 internet-time-observation->utc
  (0010 (observation)
    (011
      ((111 (101 observation) (001 accepted))
       (list (001 accepted)
             (second observation)
             (utc-from-unix
               (third observation)
               (101 (110 (110 (110 observation)))))))
      (t observation))))

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
    (not-lessp? now-ns deadline-ns)))

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
    (011
      ((nonempty-string-membership-helper tz-value)
       (class-membership string nonempty-member)
       (list (001 detected) tz-value (001 TZ)))
      ((nonempty-string-membership-helper etc-timezone-value)
       (class-membership string nonempty-member)
       (list (001 detected) etc-timezone-value (001 etc-timezone)))
      (t
       (list (001 unknown) (001 host-declaration-unavailable))))))

; Adapt the mechanism-only host observation to public timezone meaning.
(0011 timezone-raw->observation
  (0010 (raw)
    (011
      ((111 (101 raw) (001 timezone-declarations))
       (timezone-declarations->observation
         (second raw)
         (third raw)))
      (t
       (list (001 rejected) (001 invalid-timezone-observation))))))

(0011 timezone-detect
  (0010 ()
    (timezone-raw->observation
      (timezone-declarations-raw))))

(0011 timezone-config
  (0010 (name offset-seconds)
    (011
      ((string-membership-helper name)
       (class-membership string nonmember)
       (list (001 rejected) (001 invalid-name)))
      ((01110 offset-seconds -86400) 1
       (list (001 rejected) (001 invalid-offset)))
      ((01110 offset-seconds -86400) 0
       (011
         ((01111 offset-seconds 86400) 1
          (list (001 rejected) (001 invalid-offset)))
         ((01111 offset-seconds 86400) 0
          (list (001 accepted) (list (001 timezone) name offset-seconds))))))))

(0011 timezone-name
  (0010 (config)
    (second config)))

(0011 timezone-offset-seconds
  (0010 (config)
    (third config)))

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
