; #2376 — explicit mechanism laboratory under one Core.
;
; This is not a language core or semantic profile.
; It composes the shared SENS mechanism selector with experimental execution
; families while leaving all language meaning in the one Core.
;
; Load order:
;   lib/core.lisp
;   lib/surface/semantic-registry-api.lisp
;   lib/mechanism-selector.lisp
;   lib/mechanism-lab.lisp
;
; Backend observations never become language law through this file.

(00001011 mechanism-lab-executors
  (00000001 (common-lisp prolog clips datalog)))

(00001011 mechanism-lab-route
  (00001000 (sid executor)
    (mechanism-select sid executor)))

(00001011 mechanism-lab-add-routes
  (00001000 (sid)
    (00100111
      (mechanism-lab-route sid (00000001 common-lisp))
      (mechanism-lab-route sid (00000001 prolog))
      (mechanism-lab-route sid (00000001 clips))
      (mechanism-lab-route sid (00000001 datalog)))))

(00001011 mechanism-lab-status
  (00001000 ()
    (00000001
      (mechanism-lab
        (historical-name core3)
        (role experimental-kernel-laboratory)
        (selector shared-lisp-owned)
        (lowering partial)
        (clips-result-observation blocked)
        (four-island-round-trip pending)))))