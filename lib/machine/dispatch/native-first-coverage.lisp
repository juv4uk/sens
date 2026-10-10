; #508 — machine-readable native-first coverage ledger.
;
; Diagnostic/projection data only. This file is NOT a semantic registry and
; MUST NOT participate in native-first-plan dispatch. The classifier remains
; the execution-routing authority; this ledger only records observed coverage
; classes, explicit fallback reasons, and concrete missing prerequisites.
;
; Each row:
;   (native-coverage
;     (class <diagnostic-class>)
;     (representative <expression-data>)
;     (status native-supported|fallback-required|blocked-runtime-prerequisite)
;     (reason <bounded-reason>)
;     (evidence <witness-name>)
;     [(prerequisite <concrete-prerequisite>)]
;     [(expected <independent-expected-value>)]
;     [(effect <effect-class>)]
;     [(error <error-class>)])

(00001001 native-first-coverage-ledger
  (00000001
    ((native-coverage
       (class car-cons-u64-literals)
       (representative (car (cons 2 3)))
       (status native-supported)
       (reason bounded-car-cons-u64-lowering-admitted)
       (evidence native-first-parity-witness)
       (expected 2)
       (effect pure)
       (error not-applicable))

     (native-coverage
       (class general-application)
       (representative (+ 2 3))
       (status fallback-required)
       (reason no-native-plan-for-general-application)
       (evidence native-first-dispatch-witness))

     (native-coverage
       (class car-cons-outside-native-literal-domain)
       (representative (car (cons "native-limits" 3)))
       (status fallback-required)
       (reason current-native-island-holds-all-exact-integers)
       (evidence native-first-dispatch-witness))

     (native-coverage
       (class dynamic-pair-result)
       (representative (cons 2 3))
       (status blocked-runtime-prerequisite)
       (reason native-pair-result-needs-managed-lifetime)
       (evidence native-first-dispatch-witness)
       (prerequisite native-pair-allocation-and-managed-lifetime))

     (native-coverage
       (class lambda-application)
       (representative ((lambda (x) (+ x 1)) 41))
       (status blocked-runtime-prerequisite)
       (reason user-callable-native-path-needs-closure-abi)
       (evidence native-first-dispatch-witness)
       (prerequisite native-closure-and-call-abi))

     (native-coverage
       (class general-control-flow)
       (representative (cond ((eq? 1 1) 42) (1 0)))
       (status blocked-runtime-prerequisite)
       (reason source-control-native-path-needs-label-graph)
       (evidence native-first-dispatch-witness)
       (prerequisite native-label-layout-and-general-control-lowering)))))
