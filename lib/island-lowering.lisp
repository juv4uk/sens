; #1048 — island-specific mechanical lowering after Canon/function-table selection.
; Exact parent: #1047 selector over #1046 admitted mechanisms.
; This layer does not define '+' or any other Lisp meaning. It consumes the
; mechanism-selected result from #1047 and only serializes an admitted route.

(def island-lowering-append4
  (lambda (a b c d)
    (string-append a (string-append b (string-append c d)))))

(def island-lowering-add-payload
  (lambda (executor left right)
    (let ((l (write-to-string left))
          (r (write-to-string right)))
      (cond
        ((eq executor (quote common-lisp)) (identity-relation same)
         (island-lowering-append4 "(+ " l " " (string-append r ")")))
        ((eq executor (quote prolog)) (identity-relation same)
         (island-lowering-append4 "Result is " l " + " r))
        ((eq executor (quote clips)) (identity-relation same)
         (island-lowering-append4 "(+ " l " " (string-append r ")")))
        ((eq executor (quote datalog)) (identity-relation same)
         (island-lowering-append4 "math + " l " " r))
        (t (quote ()))))))

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
                        sid executor))
                     ((atom payload) (structural-kind atom)
                      (list
                        (quote island-lowering-result)
                        sid executor mechanism payload)))))
                (t
                 (list
                   (quote island-lowering-failure)
                   (quote unsupported-selected-mechanism)
                   sid executor mechanism)))))
           ((eq (car selection) (quote mechanism-selected))
            (identity-relation distinct)
            selection)))
        (t
         (list
           (quote island-lowering-failure)
           (quote malformed-selection)
           sid executor))))))

