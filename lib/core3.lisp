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

(def core3-executors
  (quote (common-lisp prolog clips datalog)))

(def core3-route
  (lambda (sid executor)
    (mechanism-select sid executor)))

(def core3-add-routes
  (lambda (sid)
    (list
      (core3-route sid (quote common-lisp))
      (core3-route sid (quote prolog))
      (core3-route sid (quote clips))
      (core3-route sid (quote datalog)))))

(def core3-profile-status
  (lambda ()
    (quote
      (core3
        (contract 7 0)
        (role experimental-kernel-laboratory)
        (selector shared-lisp-owned)
        (lowering partial)
        (clips-result-observation blocked)
        (four-island-round-trip pending)))))