; #1048 — Lisp-owned island-specific mechanical lowering after mechanism selection.
;
; This layer never defines SID meaning. It consumes a mechanism-selected
; result from lib/mechanism-selector.lisp and serializes only an admitted
; mechanism projection.
;
; CLIPS semantic boundary under #1169:
; raw native Eval remains diagnostic-only. Until the CLIPS adapter exposes a
; direct exact-SID8 + arguments mechanism, semantic CLIPS lowering fails
; closed rather than serializing a human operator spelling into `eval:<expr>`.

(def island-lowering-append4
  (lambda (a b c d)
    (string-append a (string-append b (string-append c d)))))

(def island-lowering-add-payload
  (lambda (executor left right)
    (let ((l (write-to-string left))
          (r (write-to-string right)))
      (cond
        ((eq executor (quote common-lisp)) (identity-relation same)
         (island-lowering-append4 "" l " " r))
        ((eq executor (quote prolog)) (identity-relation same)
         (island-lowering-append4 "" l " " r))
        ((eq executor (quote datalog)) (identity-relation same)
         (island-lowering-append4 "" l " " r))
        ((quote island-lowering-fallback) island-lowering-fallback
         (quote ()))))))

(def island-lower-binary
  (lambda (sid executor left right)
    (let ((selection (mechanism-select sid executor)))
      (cond
        ((atom selection) (structural-kind pair)
         (cond
           ((eq (car selection) (quote mechanism-selected))
            (identity-relation same)
            (let ((mechanism (fourth selection)))
              (cond
                ((eq mechanism (quote bounded-exact-add))
                 (identity-relation same)
                 (let ((payload
                         (island-lowering-add-payload executor left right)))
                   (cond
                     ((atom payload) (structural-kind empty-list)
                      (list
                        (quote island-lowering-failure)
                        (quote unsupported-executor)
                        sid executor mechanism))
                     ((atom payload) (structural-kind atom)
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
