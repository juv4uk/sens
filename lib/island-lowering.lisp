; #1048 — Lisp-owned island-specific mechanical lowering after mechanism selection.
;
; This layer never defines SID meaning. It consumes a mechanism-selected
; result from lib/mechanism-selector.lisp and serializes only an admitted
; mechanism projection.
; For bounded exact addition, admitted semantic transports carry arguments only.
; The operation itself is never serialized as "+", "add", a Lisp form, or a
; Prolog goal: exact-domain identity plus the selected mechanism owns that choice.
;
; CLIPS semantic boundary under #1169:
; raw native Eval remains diagnostic-only. Semantic CLIPS addition is admitted
; only as exact SID8 + arguments; the adapter builds private native syntax after
; SID selection and never accepts operator text across this boundary.
;
; Migrated: two-field COND only; empty/fallback via exact D1 forms.
; Width is identity; every bit of the domain address is valued.

(визначити island-lowering-append4
  (функція (a b c d)
    (рядок-додати a (рядок-додати b (рядок-додати c d)))))

(визначити island-lowering-add-payload
  (функція (executor left right)
    ((функція (l r)
      (за-умовою
        ((тотожне? executor (як-є common-lisp))
         (island-lowering-append4 "" l " " r))
        ((тотожне? executor (як-є prolog))
         (island-lowering-append4 "" l " " r))
        ((тотожне? executor (як-є datalog))
         (island-lowering-append4 "" l " " r))
        ((тотожне? executor (як-є clips))
         (island-lowering-append4 "" l " " r))
        ((атом? (як-є ()))
         (як-є ()))))
      (значення-у-текст left)
      (значення-у-текст right))))

(визначити island-lower-binary
  (функція (sid executor left right)
    ((функція (selection) (за-умовою
        ((атом? selection)
         (список
           (як-є island-lowering-failure)
           (як-є malformed-selection)
           sid executor))
        ((атом? (як-є ()))
         (за-умовою
           ((тотожне? (перше selection) (як-є mechanism-selected))
            ((функція (mechanism) (за-умовою
                ((тотожне? mechanism (як-є bounded-exact-add))
                 ((функція (payload) (за-умовою
                     ((атом? payload)
                      (список
                        (як-є island-lowering-failure)
                        (як-є unsupported-executor)
                        sid executor mechanism))
                     ((атом? (як-є ()))
                      (список
                        (як-є island-lowering-result)
                        sid executor mechanism payload)))) (island-lowering-add-payload executor left right)))
                ((атом? (як-є ()))
                 (список
                   (як-є island-lowering-failure)
                   (як-є unsupported-selected-mechanism)
                   sid executor mechanism)))) (четверте selection)))
           ((атом? (як-є ()))
            selection))))) (mechanism-select sid executor))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити значення-у-текст write-to-string)
