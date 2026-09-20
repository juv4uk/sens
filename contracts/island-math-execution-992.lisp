; island-math-execution-992.lisp — executable corpus seed for the four-island math lane.
;
; This is an observer corpus, not semantic authority. It references the
; already-admitted + identity from #988 and records native probe forms without
; translating producer-native result domains into one universal value type.
;
(island-math-execution/1
  ((source-contract . "contracts/island-math-intersection-988.lisp")
   (identity-rule . "semantic-id comes from the existing Lisp-owned registry")
   (comparison-policy . "preserve-native-result-then-compare")
   (unsupported-policy . "explicit-not-comparable"))

  ((case-id . "add-small-exact-integer")
   (operation . "+")
   (semantic-id . "00001100")
   (operand-domain . "exact-integer")
   (operands . (2 3))
   (expected-comparison . "5")
   (common-lisp-form . "(+ 2 3)")
   (prolog-goal . "Y is 2+3")
   (prolog-template . "Y")
   (clips-rule . "(defrule arithmetic-witness (probe) (test (= (+ 2 3) 5)) => (assert (math-result 5)))")
   (clips-trigger . "(probe)")
   (datalog-query . "(+ 2 3)")
   (datalog-status . "unsupported-current-kernel")
   (comparison-status . "three-runtime-observed-fourth-explicit-gap"))))
