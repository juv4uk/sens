; Explicit timezone data for WSM. This is configuration, not an OS mutation.
; Явні дані часового поясу для WSM. Це конфігурація, а не мутація ОС.

; Convert whole UTC days since 1970-01-01 to a proleptic Gregorian date.
; This deliberately mirrors the current host-side utc-now calendar transform,
; but lives in Lisp so we can prove that calendar semantics do not belong to
; the host. Scope is non-negative Unix days; utc-now already rejects times
; before the Unix epoch.
(def civil-from-days
  (lambda (days)
    (let* ((z (+ days 719468))
           (era (quotient z 146097))
           (doe (- z (* era 146097)))
           (yoe (quotient (- (+ doe (quotient doe 36524))
                              (+ (quotient doe 1460) (quotient doe 146096)))
                           365))
           (y (+ yoe (* era 400)))
           (doy (- doe (+ (* 365 yoe)
                           (- (quotient yoe 4) (quotient yoe 100)))))
           (mp (quotient (+ (* 5 doy) 2) 153))
           (day (+ (- doy (quotient (+ (* 153 mp) 2) 5)) 1))
           (month (+ mp (cond ((< mp 10) 3) (t -9))))
           (year (+ y (cond ((<= month 2) 1) (t 0)))))
      (list year month day))))

; Pure language-level conversion from an exact Unix timestamp into UTC calendar
; data. The host owns clock observation; this function owns deterministic
; calendar semantics.
(def utc-from-unix
  (lambda (seconds nanosecond)
    (let* ((days (quotient seconds 86400))
           (day-seconds (mod seconds 86400))
           (civil (civil-from-days days))
           (hour (quotient day-seconds 3600))
           (minute (quotient (mod day-seconds 3600) 60))
           (second-of-minute (mod day-seconds 60)))
      (list (quote utc)
            (car civil)
            (second civil)
            (third civil)
            hour minute second-of-minute nanosecond))))

; Minimal wall-clock host capability contract:
;   (unix-time-now) -> (unix-time seconds nanosecond)
; The host observes only the Unix clock. Calendar meaning stays here in Lisp.
(def unix-time-observation->utc
  (lambda (observation)
    (cond
      ((eq (car observation) (quote unix-time))
       (utc-from-unix (second observation) (third observation)))
      (t (list (quote rejected) (quote invalid-unix-time-observation))))))

; Public UTC clock meaning is language-owned. The only host fact needed here is
; the raw Unix observation above.
(def utc-now
  (lambda ()
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
(def internet-time-fields->observation
  (lambda (host mode stratum ntp-seconds fraction)
    (cond
      ((not (or (= mode 4) (= mode 5)))
       (list (quote rejected) (quote invalid-response)))
      ((or (= stratum 0) (> stratum 15))
       (list (quote rejected) (quote invalid-response)))
      ((< ntp-seconds 2208988800)
       (list (quote rejected) (quote invalid-epoch)))
      (t
       (list (quote accepted)
             host
             (- ntp-seconds 2208988800)
             (quotient (* fraction 1000000000) 4294967296))))))

; Adapter for the raw host boundary. The host returns either:
;   (ntp-fields host mode stratum ntp-seconds fraction)
; or a transport-level rejection such as (rejected receive-failed).
; Lisp owns every protocol interpretation after that raw observation boundary.
(def internet-time-raw->observation
  (lambda (raw)
    (cond
      ((eq (car raw) (quote ntp-fields))
       (internet-time-fields->observation
         (second raw)
         (third raw)
         (car (cdr (cdr (cdr raw))))
         (car (cdr (cdr (cdr (cdr raw)))))
         (car (cdr (cdr (cdr (cdr (cdr raw))))))))
      (t raw))))

; Public internet-time meaning is language-owned. Rust exposes only the raw NTP
; query mechanism under the deliberately mechanical name `ntp-query-raw`.
(def internet-time-sync
  (lambda (host timeout-ms)
    (internet-time-raw->observation
      (ntp-query-raw host timeout-ms))))

; Turning an accepted timestamp into calendar meaning is also language policy.
(def internet-time-observation->utc
  (lambda (observation)
    (cond
      ((eq (car observation) (quote accepted))
       (list (quote accepted)
             (second observation)
             (utc-from-unix
               (third observation)
               (car (cdr (cdr (cdr observation)))))))
      (t observation))))

; Nanoseconds are the one monotonic host observation. Milliseconds are only a
; coarser language-level view, so derive them instead of requiring a second
; host clock primitive. For the non-negative monotonic counter, quotient gives
; whole elapsed milliseconds (floor toward zero == floor here).
(def milliseconds-from-nanoseconds
  (lambda (nanoseconds)
    (quotient nanoseconds 1000000)))

(def mono-ms
  (lambda ()
    (milliseconds-from-nanoseconds (mono-ns))))

; Monotonic counters are host observations; deadline arithmetic is language
; semantics. Keep a pure pair of helpers so scheduler logic can be tested
; without sleeping, then expose convenience wrappers over the host counter.
(def deadline-from
  (lambda (now-ns delta-ns)
    (+ now-ns delta-ns)))

(def deadline-reached-at?
  (lambda (now-ns deadline-ns)
    (>= now-ns deadline-ns)))

(def deadline-after-ns
  (lambda (delta-ns)
    (deadline-from (mono-ns) delta-ns)))

(def deadline-reached?
  (lambda (deadline-ns)
    (deadline-reached-at? (mono-ns) deadline-ns)))

(def elapsed-ns
  (lambda (started-ns)
    (- (mono-ns) started-ns)))

; Interpret raw host timezone declarations without performing host I/O here.
; The host contract is:
;   (timezone-declarations tz-value etc-timezone-value)
; where each value is either a non-empty string or (). Lisp owns source
; precedence and the public detected/unknown result shape.
(def timezone-declarations->observation
  (lambda (tz-value etc-timezone-value)
    (cond
      ((nonempty-string-membership-helper tz-value)
       (class-membership string nonempty-member)
       (list (quote detected) tz-value (quote TZ)))
      ((nonempty-string-membership-helper etc-timezone-value)
       (class-membership string nonempty-member)
       (list (quote detected) etc-timezone-value (quote etc-timezone)))
      (t
       (list (quote unknown) (quote host-declaration-unavailable))))))

; Adapt the mechanism-only host observation to public timezone meaning.
(def timezone-raw->observation
  (lambda (raw)
    (cond
      ((eq (car raw) (quote timezone-declarations))
       (timezone-declarations->observation
         (second raw)
         (third raw)))
      (t
       (list (quote rejected) (quote invalid-timezone-observation))))))

(def timezone-detect
  (lambda ()
    (timezone-raw->observation
      (timezone-declarations-raw))))

(def timezone-config
  (lambda (name offset-seconds)
    (cond
      ((string-membership-helper name)
       (class-membership string nonmember)
       (list (quote rejected) (quote invalid-name)))
      ((not (and (= offset-seconds offset-seconds)
                 (>= offset-seconds -86400)
                 (<= offset-seconds 86400)))
       (list (quote rejected) (quote invalid-offset)))
      (t (list (quote accepted) (list (quote timezone) name offset-seconds))))))

(def timezone-name
  (lambda (config)
    (second config)))

(def timezone-offset-seconds
  (lambda (config)
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
