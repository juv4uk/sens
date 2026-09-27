; #1275 — Core4 result law for the existing EQ identity.
;
; Authority scope:
;   * exact SID 00000011 remains the only semantic identity for EQ;
;   * the irreducible equality mechanism may observe same/distinct;
;   * Core4 owns how that observation projects into the predicate-answer model;
;   * this contract does NOT define the final runtime carrier for 0/1/00/11/...
;   * Core1/Core2/Core3 are not modified by this document.
;
; The projection deliberately targets the already-proven mechanical grader
; inputs from #1266 instead of inventing another truth/result hierarchy:
;
;   same     -> direction yes, open-steps 0, contradiction 0
;   distinct -> direction no,  open-steps 0, contradiction 0
;
; Therefore the current #1255 scale selects its strongest directed entries:
;   yes -> 1
;   no  -> 0
;
; The quoted spellings in #1255 remain contract transport only until #1257
; ratifies a runtime carrier.  This file does not make String the answer type.

(core4-eq-result-law/1

  ((profile . core4)
   (sid . 00000011)
   (surface-authority . "lib/surface/semantic-registry.lisp")
   (raw-observation-domain . identity-relation)
   (grader-evidence . "experiments/core4-mechanical-answer-grade.lisp")
   (answer-scale . "contracts/core4-predicate-answer-scale.lisp")
   (runtime-carrier . unresolved-1257)
   (new-sid . forbidden)
   (surface-alias-eq? . forbidden)
   (host-profile-law-table . forbidden)
   (core1-core2-core3-impact . none))

  ((case . same)
   (observation . (1))
   (direction . yes)
   (open-steps . 0)
   (contradiction . 0)
   (expected-strength . strongest-directed-answer))

  ((case . distinct)
   (observation . (0))
   (direction . no)
   (open-steps . 0)
   (contradiction . 0)
   (expected-strength . strongest-directed-answer))

  ((outside-domain . type-error)
   (outside-domain-is-no . forbidden)
   (outside-domain-is-unknown . forbidden)
   (outside-domain-is-boundary . forbidden))

  ((integration . pending-selected-core)
   (selected-core-mechanism . issue-1272)
   (runtime-replay . issue-1275)
   (experiment-residue . "experiments/core4-eq-answer-1258.lisp")
   (experiment-residue-authority . test-only)))
