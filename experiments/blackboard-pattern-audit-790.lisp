; #790 BLACKBOARD-1 — аудит координації на основі свідчень.
;
; Лише дослідницькі дані. Вони не роблять спільну дошку семантичною владою.
;
; Класичний прецедент дошки:
; - незалежні джерела знання зі структурою умова/дія
; - спільний стан задачі, який спостерігають опосередковано
; - окремий керівний компонент монітор/планувальник
; - опортуністичне планування для стримування вибуху активацій
; - спокій/завершення як керівна турбота
;
; Рішення:
;   borrow-mechanism
;   adapt-explicitly
;   reject-ontology

(blackboard-pattern-audit/1
  ((pattern . independent-knowledge-sources)
   (decision . borrow-mechanism)
   (blackboard-evidence . mutually-independent-specialists)
   (use-in-my-lisp . autonomous-kernel-witnesses)
   (reason . islands-should-not-call-each-other-directly))

  ((pattern . activation-condition)
   (decision . borrow-mechanism)
   (blackboard-evidence . condition-action-knowledge-source)
   (use-in-my-lisp . explicit-invoke-precondition)
   (reason . schedule-only-when-required-provenance-or-capability-exists))

  ((pattern . separate-control-component)
   (decision . borrow-mechanism)
   (blackboard-evidence . monitor-plus-scheduler)
   (use-in-my-lisp . orchestration-scheduler)
   (reason . control-policy-must-not-live-inside-kernel-semantics))

  ((pattern . opportunistic-scheduling)
   (decision . adapt-explicitly)
   (blackboard-evidence . prioritize-promising-activated-sources)
   (use-in-my-lisp . provenance-aware-ready-queue)
   (reason . avoid-running-every-eligible-island-blindly))

  ((pattern . activation-agenda)
   (decision . borrow-mechanism)
   (blackboard-evidence . invoked-knowledge-source-queue)
   (use-in-my-lisp . pending-invocation-records)
   (reason . make-scheduling-visible-and-auditable))

  ((pattern . quiescence-detection)
   (decision . borrow-mechanism)
   (blackboard-evidence . stop-when-no-useful-activation-remains)
   (use-in-my-lisp . life-trace-quiescence)
   (reason . prevent-unbounded-cross-island-churn))

  ((pattern . shared-central-blackboard-ontology)
   (decision . reject-ontology)
   (blackboard-evidence . global-domain-state)
   (use-in-my-lisp . none)
   (reason . native-result-domains-must-not-be-normalized-into-one-store))

  ((pattern . direct-knowledge-source-awareness)
   (decision . reject-ontology)
   (blackboard-evidence . specialists-communicate-via-indirection)
   (use-in-my-lisp . producer-neutral-result-refs)
   (reason . kernels-must-not-depend-on-other-kernel-identities))

  ((experiment . life-1-ready-queue)
   (proposal .
     (pending-invocation
       (producer datalog)
       (trigger (projection-ready prolog-substitutions-to-datalog-facts))
       (provenance-ref source-observation)
       (priority ordinary)
       (semantic-authority my-lisp)))
   (completion .
     (quiescent-when no-pending-invocations-and-no-new-explicit-projections))
   (implementation-status . proposed))
)
