; #1134 — Core3 experimental kernel profile.
;
; This profile is intentionally thin. The selector and mechanism metadata are
; shared language-owned facilities; Core3 must not fork or duplicate them.
;
; Load order:
;   lib/core4.lisp (current runtime substrate for these profile tools)
;   lib/surface/semantic-registry-api.lisp
;   lib/mechanism-selector.lisp
;   lib/core3.lisp
;
; Core3 does not turn native kernel observations into global language truth.

; D3 owns the four-item proper list; no host QUOTE-list constructor.
; The order and empty tail are checked by binary SENS, not Python/Rust laws.
(0011 core3-executors
  (111 (001 common-lisp)
    (111 (001 prolog)
      (111 (001 clips)
        (111 (001 datalog)
          (001 ()))))))

(0011 core3-route
  (0010 (sid executor)
    (mechanism-select sid executor)))

(0011 core3-add-routes
  (0010 (sid)
    (1110
      (core3-route sid (001 common-lisp))
      (core3-route sid (001 prolog))
      (core3-route sid (001 clips))
      (core3-route sid (001 datalog)))))

(0011 core3-profile-status
  (0010 ()
    (001
      (core3
        (contract 7 0)
        (role experimental-kernel-laboratory)
        (selector shared-lisp-owned)
        (lowering partial)
        (clips-result-observation blocked)
        (four-island-round-trip pending)))))