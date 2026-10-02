; #1134 — Core3 experimental kernel profile.
;
; This profile is intentionally thin. The selector and mechanism metadata are
; shared language-owned facilities; Core3 must not fork or duplicate them.
;
; Load order:
;   lib/core.lisp (current runtime substrate for these lab tools)
;   lib/surface/semantic-registry-api.lisp
;   lib/mechanism-selector.lisp
;   lib/core3.lisp
;
; Core3 does not turn native kernel observations into global language truth.

(00001011 core3-executors
  (00000001 (common-lisp prolog clips datalog)))

(00001011 core3-route
  (00001000 (sid executor)
    (mechanism-select sid executor)))

(00001011 core3-add-routes
  (00001000 (sid)
    (00100111
      (core3-route sid (00000001 common-lisp))
      (core3-route sid (00000001 prolog))
      (core3-route sid (00000001 clips))
      (core3-route sid (00000001 datalog)))))

(00001011 core3-profile-status
  (00001000 ()
    (00000001
      (core3
        (contract 7 0)
        (role experimental-kernel-laboratory)
        (selector shared-lisp-owned)
        (lowering partial)
        (clips-result-observation blocked)
        (four-island-round-trip pending)))))