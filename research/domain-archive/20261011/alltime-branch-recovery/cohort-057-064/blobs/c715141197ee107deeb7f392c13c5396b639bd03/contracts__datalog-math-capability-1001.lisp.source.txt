; datalog-math-capability-1001.lisp — current execution capability after #1001.
;
; This is an execution projection, not semantic authority. It says which
; numeric forms the Datalog kernel can now execute; my-lisp still owns the
; meaning and semantic identities.
;
(datalog-math-capability/1
  ((kernel . wsm-datalog-kernel)
   (numeric-domain . signed-i64)
   (expression-evaluator . native)
   (semantic-authority . my-lisp)
   (unsupported-extension-policy . explicit)
   (witness . crates/wsm-datalog-kernel/tests/arithmetic_execution_1001.rs))

  ((operation . "+") (native . present) (domain . signed-i64))
  ((operation . "-") (native . present) (domain . signed-i64))
  ((operation . "*") (native . present) (domain . signed-i64))
  ((operation . "/") (native . present) (domain . signed-i64-integer-quotient))
  ((operation . "mod") (native . present) (domain . signed-i64-remainder))
  ((operation . "quotient") (native . present) (domain . signed-i64-integer-quotient))
  ((operation . "abs") (native . present) (domain . signed-i64))
  ((operation . "min") (native . present) (domain . signed-i64))
  ((operation . "max") (native . present) (domain . signed-i64))

  ((operation . "sqrt") (native . absent) (reason . outside-1001-slice))
  ((operation . "exp") (native . absent) (reason . outside-1001-slice))
  ((operation . "log") (native . absent) (reason . outside-1001-slice))
  ((operation . "sin") (native . absent) (reason . outside-1001-slice))
  ((operation . "cos") (native . absent) (reason . outside-1001-slice))
  ((operation . "tan") (native . absent) (reason . outside-1001-slice))
  ((operation . "power") (native . absent) (reason . outside-1001-slice))

  ((failure . division-by-zero)
   (status . typed-kernel-error)
   (identity . datalog-math-division-by-zero))

  ((failure . overflow)
   (status . typed-kernel-error)
   (identity . datalog-math-overflow))
)
