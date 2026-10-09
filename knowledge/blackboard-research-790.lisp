; #790 BLACKBOARD-1 — research artifact.
; Historical sources:
; - H. Penny Nii, "The Blackboard Model of Problem Solving and the Evolution
;   of Blackboard Architectures", AI Magazine 7(2), 1986.
;   DOI: 10.1609/aimag.v7i2.537
; - Barbara Hayes-Roth, "A blackboard architecture for control",
;   Artificial Intelligence 26(3), 1985, pp. 251-321.
;   DOI: 10.1016/0004-3702(85)90063-3
;
; my-lisp adaptation rule:
; borrow coordination mechanics, reject shared semantic ontology.

(blackboard-research-790
  (authority
    (semantic Canon-function-table)
    (coordination mechanism-only)
    (island-state native-and-opaque-unless-explicitly-bridged))

  (borrow
    (independent-producers publish-references)
    (agenda explicit-activations)
    (control choose-next-activation)
    (provenance preserve-source-and-trigger)
    (cycle-control explicit-activation-key)
    (partial-progress multiple-observations-without-forced-unification))

  (reject
    (shared-normalized-blackboard
      reason would-collapse-native-island-ontologies)
    (blackboard-fact-as-semantic-truth
      reason coordination-state-is-not-Canon-authority)
    (implicit-cross-island-equivalence
      reason requires-explicit-bridge-evidence)
    (confidence-as-truth
      reason scheduling-metadata-cannot-redefine-meaning)
    (absence-as-Canon-empty
      reason no-result-is-not-Canon-ground-by-default))

  (bounded-experiment
    (name provenance-safe-reference-agenda)
    (input
      (native-result-ref producer observation-id)
      (provenance-ref source-id trigger-id))
    (activation
      (activation-key producer observation-id consumer)
      (observation-ref producer observation-id)
      (consumer consumer)
      (provenance source-id trigger-id))
    (scheduler
      deterministic-first-pending
      suppress-duplicate-activation-key)
    (output
      ordered-activation-refs-only)
    (invariants
      no-native-payload-copy
      no-shared-result-ontology
      no-SID-admission
      no-semantic-law-in-scheduler
      repeated-trigger-does-not-loop)))
