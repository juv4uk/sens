; #508 — machine-readable native-first coverage ledger.
;
; Diagnostic/projection data only. This file is NOT a semantic registry and
; MUST NOT participate in класифікувати-нативний-вираз dispatch. The classifier remains
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

(визначити native-first-coverage-ledger
  (001
    ((native-coverage
       (class car-cons-u64-literals)
       (representative (перше (сполучити 2 3)))
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
       (representative (перше (сполучити "native-limits" 3)))
       (status fallback-required)
       (reason current-native-island-holds-all-exact-integers)
       (evidence native-first-dispatch-witness))

     (native-coverage
       (class dynamic-pair-result)
       (representative (сполучити 2 3))
       (status blocked-runtime-prerequisite)
       (reason native-pair-result-needs-managed-lifetime)
       (evidence native-first-dispatch-witness)
       (prerequisite native-pair-allocation-and-managed-lifetime))

     (native-coverage
       (class lambda-application)
       (representative ((функція (x) (+ x 1)) 41))
       (status blocked-runtime-prerequisite)
       (reason user-callable-native-path-needs-closure-abi)
       (evidence native-first-dispatch-witness)
       (prerequisite native-closure-and-call-abi))

     (native-coverage
       (class general-control-flow)
       (representative (110 ((101 (001 000) (001 001)) 0) ((010 (001 000)) 1)))
       (status blocked-runtime-prerequisite)
       (reason source-control-native-path-needs-label-graph)
       (evidence native-first-dispatch-witness)
       (prerequisite native-label-layout-and-general-control-lowering)))))
