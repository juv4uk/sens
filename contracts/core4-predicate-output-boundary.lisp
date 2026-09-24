; #1260 — Core4 final predicate-answer output boundary.
;
; This is a small guard policy, not a truth framework.
;
; Rich records are allowed as raw observations and classifier data.
; A Core4 predicate-question may publish only the predicate-answer domain after
; an explicit Lisp-owned projection law.  This policy deliberately does NOT
; decide performance, native mechanism availability, host capability dispatch,
; SID width, FPGA layout, or bootstrap strategy.

(core4-predicate-output-boundary/1

  ((profile . core4)
   (role-inventory . "knowledge/core4-predicate-record-inventory.lisp")
   (answer-authority . "contracts/core4-predicate-answer-scale.lisp")
   (boundary-authority . "contracts/core4-predicate-answer-boundary.lisp")
   (policy-role . final-output-only)
   (runtime-semantic-authority . forbidden)
   (mass-rewrite . forbidden))

  ((raw-observation-domains .
     (structural-kind
      identity-relation
      structural-relation
      class-membership
      text-order))
   (raw-observation-policy . allowed)
   (classifier-data-policy . allowed))

  ((predicate-question-final-domain . predicate-answer-domain)
   (rich-observation-as-final . forbidden)
   (explicit-lisp-projection . required-when-raw-domain-is-rich)
   (outside-domain-collapse-to-no . forbidden)
   (outside-domain-collapse-to-boundary . forbidden))

  ((independent-axes .
     (wrapper-performance-1277-1278
      host-capability-sid-gap-1276
      native-mechanism-availability-1288
      sid-width-fpga-economics-1279-1280
      table-first-bootstrap-vision-1281))
   (independent-axis-may-change-semantic-verdict . no))

  ((endpoint-flow .
     ((no  00000000 ())
      (yes 11111111 ())))
   (endpoint-sid-identity . distinct)
   (endpoint-projection . shared-empty-list)))
