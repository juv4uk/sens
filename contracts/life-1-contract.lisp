; LIFE-1 — Lisp-owned living-spine contract.
;
; This document defines what must remain true when one producer-native
; observation is explicitly projected into input for another execution island.
; It does not define Prolog, Datalog, CLIPS or Common Lisp semantics.
;
; Outer form:
;   (life-1-contract/1 ENTRY ...)
;
; A LIFE trace is provenance/causality data, never a truth value.

(life-1-contract/1
  ((identity . life-trace)
   (owner . my-lisp)
   (kind . provenance-observation)
   (truth-value . forbidden)
   (producer-required . yes)
   (target-required . yes)
   (semantic-id-required . yes))

  ((identity . source-observation)
   (native-domain-preserved . yes)
   (producer-preserved . yes)
   (provenance-preserved . yes)
   (universal-result-normalization . forbidden))

  ((identity . projection)
   (owner . my-lisp)
   (explicit . yes)
   (partial . yes)
   (source-native-result-preserved . yes)
   (semantic-equivalence-assumed . no))

  ((identity . target-invocation)
   (input-origin-recorded . yes)
   (target-native-domain-preserved . yes)
   (semantic-id-meaning-source . my-lisp-registry-and-laws)
   (kernel-reinterpretation . forbidden))

  ((identity . missing-source-kernel)
   (kind . execution-unavailability)
   (legal . yes)
   (changes-semantic-id-meaning . no)
   (changes-registry-numbering . no))

  ((identity . first-vertical-slice)
   (source . prolog)
   (projection . prolog-substitutions-to-datalog-facts)
   (target . datalog)
   (source-result-domain . native-prolog-answer-list)
   (target-result-domain . native-datalog-relation)
   (shared-result-type . forbidden))

  ((identity . liveness)
   (fresh-checkout . required)
   (manual-semantic-patching . forbidden)
   (focused-ci-question . does-life-1-still-live)))
)
