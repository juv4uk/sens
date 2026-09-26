; #1048 — Lisp-owned island-specific mechanical lowering after mechanism selection.
;
; This layer never defines SID meaning. It consumes a mechanism-selected
; result from lib/mechanism-selector.lisp and serializes only an admitted
; mechanism projection.
; For bounded exact addition, admitted semantic transports carry arguments only.
; The operation itself is never serialized as "+", "add", a Lisp form, or a
; Prolog goal: exact SID8 plus the selected mechanism already owns that choice.
;
; CLIPS semantic boundary under #1169:
; raw native Eval remains diagnostic-only. Semantic CLIPS addition is admitted
; only as exact SID8 + arguments; the adapter builds private native syntax after
; SID selection and never accepts operator text across this boundary.

(00001001 island-lowering-append4
  (00001000 (a b c d)
    (string-append a (string-append b (string-append c d)))))

(00001001 island-lowering-add-payload
  (00001000 (executor left right)
    (10011100 ((l (write-to-string left))
          (r (write-to-string right)))
      (00000111
        ((00000011 executor (00000001 common-lisp)) (identity-relation same)
         (island-lowering-append4 "" l " " r))
        ((00000011 executor (00000001 prolog)) (identity-relation same)
         (island-lowering-append4 "" l " " r))
        ((00000011 executor (00000001 datalog)) (identity-relation same)
         (island-lowering-append4 "" l " " r))
        ((00000011 executor (00000001 clips)) (identity-relation same)
         (island-lowering-append4 "" l " " r))
        ((00000001 island-lowering-fallback) island-lowering-fallback
         (00000001 ()))))))

(00001001 island-lower-binary
  (00001000 (sid executor left right)
    (10011100 ((selection (mechanism-select sid executor)))
      (00000111
        ((00000010 selection) (structural-kind pair)
         (00000111
           ((00000011 (00000101 selection) (00000001 mechanism-selected))
            (identity-relation same)
            (10011100 ((mechanism (00110001 selection)))
              (00000111
                ((00000011 mechanism (00000001 bounded-exact-add))
                 (identity-relation same)
                 (10011100 ((payload
                         (island-lowering-add-payload executor left right)))
                   (00000111
                     ((00000010 payload) (structural-kind empty-list)
                      (00100111
                        (00000001 island-lowering-failure)
                        (00000001 unsupported-executor)
                        sid executor mechanism))
                     ((00000010 payload) (structural-kind atom)
                      (00100111
                        (00000001 island-lowering-result)
                        sid executor mechanism payload)))))
                ((00000001 island-lowering-other-mechanism) island-lowering-other-mechanism
                 (00100111
                   (00000001 island-lowering-failure)
                   (00000001 unsupported-selected-mechanism)
                   sid executor mechanism)))))
           ((00000001 island-lowering-selection-not-selected)
            island-lowering-selection-not-selected
            selection)))
        ((00000001 island-lowering-malformed) island-lowering-malformed
         (00100111
           (00000001 island-lowering-failure)
           (00000001 malformed-selection)
           sid executor))))))
