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

(def island-lowering-append4
  (lambda (a b c d)
    (string-append a (string-append b (string-append c d)))))

(def island-lowering-add-payload
  (lambda (executor left right)
    (let ((l (write-to-string left))
          (r (write-to-string right)))
      (cond
        ((eq? executor (quote common-lisp)) (1)
         (island-lowering-append4 "" l " " r))
        ((eq? executor (quote prolog)) (1)
         (island-lowering-append4 "" l " " r))
        ((eq? executor (quote datalog)) (1)
         (island-lowering-append4 "" l " " r))
        ((eq? executor (quote clips)) (1)
         (island-lowering-append4 "" l " " r))
        ((quote island-lowering-fallback) island-lowering-fallback
         (quote ()))))))

(def island-lower-binary
  (lambda (sid executor left right)
    (let ((selection (mechanism-select sid executor)))
      (cond
        ((atom? selection) (0)
         (cond
           ((eq? (car selection) (quote mechanism-selected))
            (1)
            (let ((mechanism (fourth selection)))
              (cond
                ((eq? mechanism (quote bounded-exact-add))
                 (1)
                 (let ((payload
                         (island-lowering-add-payload executor left right)))
                   (cond
                     ((atom? payload) ()
                      (list
                        (quote island-lowering-failure)
                        (quote unsupported-executor)
                        sid executor mechanism))
                     ((atom? payload) (1)
                      (list
                        (quote island-lowering-result)
                        sid executor mechanism payload)))))
                ((quote island-lowering-other-mechanism) island-lowering-other-mechanism
                 (list
                   (quote island-lowering-failure)
                   (quote unsupported-selected-mechanism)
                   sid executor mechanism)))))
           ((quote island-lowering-selection-not-selected)
            island-lowering-selection-not-selected
            selection)))
        ((quote island-lowering-malformed) island-lowering-malformed
         (list
           (quote island-lowering-failure)
           (quote malformed-selection)
           sid executor))))))
