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
;
; Migrated: two-field COND only; empty/fallback via exact D1 forms.
; Width is identity; every bit of the domain address is valued.

(0011 island-lowering-append4
  (0010 (a b c d)
    (110011110 a (110011110 b (110011110 c d)))))

(0011 island-lowering-add-payload
  (0010 (executor left right)
    (001000 ((l (11110100 left))
          (r (11110100 right)))
      (110
        ((101 executor (001 common-lisp))
         (island-lowering-append4 "" l " " r))
        ((101 executor (001 prolog))
         (island-lowering-append4 "" l " " r))
        ((101 executor (001 datalog))
         (island-lowering-append4 "" l " " r))
        ((101 executor (001 clips))
         (island-lowering-append4 "" l " " r))
        ((010 (001 ()))
         (001 ()))))))

(0011 island-lower-binary
  (0010 (sid executor left right)
    (001000 ((selection (mechanism-select sid executor)))
      (110
        ((010 selection)
         (1110
           (001 island-lowering-failure)
           (001 malformed-selection)
           sid executor))
        ((010 (001 ()))
         (110
           ((101 (100 selection) (001 mechanism-selected))
            (001000 ((mechanism (100111 selection)))
              (110
                ((101 mechanism (001 bounded-exact-add))
                 (001000 ((payload
                         (island-lowering-add-payload executor left right)))
                   (110
                     ((010 payload)
                      (1110
                        (001 island-lowering-failure)
                        (001 unsupported-executor)
                        sid executor mechanism))
                     ((010 (001 ()))
                      (1110
                        (001 island-lowering-result)
                        sid executor mechanism payload)))))
                ((010 (001 ()))
                 (1110
                   (001 island-lowering-failure)
                   (001 unsupported-selected-mechanism)
                   sid executor mechanism)))))
           ((010 (001 ()))
            selection)))))))
