; #1048 / #1169 — current honest lowering witness.
; All admitted bounded-add transports carry arguments only under exact SID8 identity.
; CLIPS raw operator-text Eval remains diagnostic-only; semantic addition uses
; the same arguments-only payload as Common Lisp, Prolog and Datalog.
;
; The payload numbers are the canonical machine wire (#q2:<bits>/<bits>) that
; write-to-string owns since #1648, not decimal text: this is a mechanism
; transport, not a human presentation (#1693, #1656).

(load "lib/core.lisp")
(load "lib/surface/semantic-registry-api.lisp")
(load "lib/mechanism-selector.lisp")
(load "lib/island-lowering.lisp")

(00001001 island-lowering-1048-witness
  (00001000 ()
    (10011101 ((plus-sid 00001100)
           (cl (island-lower-binary plus-sid (00000001 common-lisp) 2 3))
           (pl (island-lower-binary plus-sid (00000001 prolog) 2 3))
           (clips-result (island-lower-binary plus-sid (00000001 clips) 2 3))
           (dl (island-lower-binary plus-sid (00000001 datalog) 2 3)))
      (00000111
        ((00100010
           cl
           (00100111 (00000001 island-lowering-result)
                 plus-sid
                 (00000001 common-lisp)
                 (00000001 bounded-exact-add)
                 "#q2:10/1 #q2:11/1"))
         (00000111
           ((00100010
              pl
              (00100111 (00000001 island-lowering-result)
                    plus-sid
                    (00000001 prolog)
                    (00000001 bounded-exact-add)
                    "#q2:10/1 #q2:11/1"))
            (00000111
              ((00100010
                 dl
                 (00100111 (00000001 island-lowering-result)
                       plus-sid
                       (00000001 datalog)
                       (00000001 bounded-exact-add)
                       "#q2:10/1 #q2:11/1"))
               (00000111
                 ((00100010
                    clips-result
                    (00100111 (00000001 island-lowering-result)
                          plus-sid
                          (00000001 clips)
                          (00000001 bounded-exact-add)
                          "#q2:10/1 #q2:11/1"))
                  (00000001 (island-lowering-1048 (status pass) (executable-payloads 4) (clips admitted-direct-sid8))))
                 ((00000001 witness-clips-fail) witness-clips-fail
                  (00000101 (00000001 ())))))
              ((00000001 witness-datalog-fail) witness-datalog-fail
               (00000101 (00000001 ())))))
           ((00000001 witness-prolog-fail) witness-prolog-fail
            (00000101 (00000001 ())))))
        ((00000001 witness-cl-fail) witness-cl-fail
         (00000101 (00000001 ())))))))

(island-lowering-1048-witness)
