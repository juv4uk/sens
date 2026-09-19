; #793 LIFE-2 — evidence-based architecture pattern catalog.
;
; This catalog aggregates accepted research directions. It is not a runtime
; implementation and does not redefine island semantics.
;
; Source audits:
; #787 Poplog
; #788 GraalVM/Truffle
; #789 MetaCall
; #790 Blackboard/Hearsay-II
; #791 OpenCog AtomSpace
; #792 KIF
;
; Decision vocabulary:
;   borrow
;   adapt
;   reject

(life-2-pattern-catalog/1
  ((concern . runtime-availability)
   (precedent . poplog)
   (decision . borrow)
   (pattern . subsystem-loaded-observation)
   (my-lisp-shape . kernel-capability-observation)
   (issue . 797))

  ((concern . runtime-lifecycle)
   (precedent . metacall)
   (decision . borrow)
   (pattern . loader-handle-start-stop-unload)
   (my-lisp-shape . explicit-kernel-handle-lifecycle)
   (issue . 799))

  ((concern . orchestration)
   (precedent . blackboard)
   (decision . adapt)
   (pattern . activation-agenda-separate-scheduler-quiescence)
   (my-lisp-shape . pending-invocation-plus-provenance-aware-ready-queue)
   (issue . 801))

  ((concern . bridge-admission)
   (precedent . kif)
   (decision . borrow)
   (pattern . declarative-interchange-contract)
   (my-lisp-shape . explicit-partial-bridge-contract)
   (issue . 803))

  ((concern . provenance-graph)
   (precedent . atomspace)
   (decision . adapt)
   (pattern . stable-node-link-identity-plus-lightweight-metadata)
   (my-lisp-shape . observation-ref-plus-provenance-edge)
   (issue . 805))

  ((concern . native-result-inspection)
   (precedent . graalvm-truffle)
   (decision . adapt)
   (pattern . capability-probe-plus-operation-specific-message)
   (my-lisp-shape . producer-neutral-mechanical-observation-capabilities)
   (issue . proposed))

  ((concern . universal-runtime-substrate)
   (precedents . (poplog graalvm))
   (decision . reject)
   (pattern . one-shared-vm-or-memory-space)
   (reason . islands-remain-autonomous-execution-witnesses))

  ((concern . universal-result-ontology)
   (precedents . (metacall graalvm atomspace))
   (decision . reject)
   (pattern . one-foreign-value-or-truthvalue-domain)
   (reason . native-result-domains-remain-producer-owned))

  ((concern . universal-interlingua)
   (precedents . (kif atomspace))
   (decision . reject)
   (pattern . mandatory-central-knowledge-representation)
   (reason . explicit-partial-bridges-only))

  ((concern . implicit-cross-language-conversion)
   (precedents . (graalvm metacall))
   (decision . reject)
   (pattern . automatic-foreign-value-coercion)
   (reason . projection-must-be-explicit-and-auditable))

  ((concern . direct-island-awareness)
   (precedent . blackboard)
   (decision . reject)
   (pattern . kernel-calls-kernel-directly)
   (reason . coordination-goes-through-visible-orchestration-and-provenance))

  ((life-1-execution-order
     (step-1 . capability-observation)
     (step-2 . explicit-runtime-lifecycle)
     (step-3 . native-source-invocation)
     (step-4 . admitted-explicit-projection)
     (step-5 . pending-target-invocation)
     (step-6 . native-target-invocation)
     (step-7 . provenance-edge)
     (step-8 . quiescence)))

  ((implementation-rule
     (new-mechanism-requires . precedent-or-existing-my-lisp-artifact)
     (decision-record-required . yes)
     (allowed-decisions . (borrow adapt reject))
     (semantic-ownership-must-not-weaken . yes)))
)
