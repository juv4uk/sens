; island-math-lowering-991.lisp — semantic-to-machine projection for ratified four-island math.
;
; This file is NOT a semantic registry, capability matrix, or execution corpus.
; #990 owns semantic/domain ratification, #992 owns execution witnesses,
; #993 owns the generated capability matrix. This contract only projects
; already-ratified semantic identities toward existing machine evidence.
;
; Fail-closed rule:
;   no row may appear until the corresponding operation is explicitly ratified
;   by #990 with a shared domain and existing semantic ID.
;
; Machine realization comes from lib/machine/intel-core-i5-6400.lisp.
; ISA names never mint language meaning or semantic identity.

(island-math-lowering/1
  (semantic-authority "lib/surface/semantic-registry.lisp")
  (ratification-authority "#990")
  (ratification-candidate "#1042")
  (capability-evidence "#988/#993")
  (execution-evidence "#992")
  (machine-profile "lib/machine/intel-core-i5-6400.lisp")
  (machine-boundary "machine-lowering-boundary.lisp")
  (lowering-direction semantic-to-machine)
  (reverse-authority forbidden)
  (semantic-id-from-isa forbidden)
  (unratified-operation-policy reject)
  (missing-machine-row-policy not-yet-lowered)
  (rows
    ; Candidate projection from #1042. These rows do not become final shared
    ; lowering claims until #990 lands; the machine side is joined only by the
    ; already-existing semantic ID into lib/machine/intel-core-i5-6400.lisp.
    (row
      (semantic-id "00001100")
      (operation "+")
      (ratification-status candidate-pending-990-merge)
      (machine-profile-status existing-row))
    (row
      (semantic-id "00001101")
      (operation "-")
      (ratification-status candidate-pending-990-merge)
      (machine-profile-status existing-row))
    (row
      (semantic-id "00001110")
      (operation "*")
      (ratification-status candidate-pending-990-merge)
      (machine-profile-status existing-row))
    (row
      (semantic-id "00010000")
      (operation "abs")
      (ratification-status candidate-pending-990-merge)
      (machine-profile-status existing-row))
    (row
      (semantic-id "00010001")
      (operation "min")
      (ratification-status candidate-pending-990-merge)
      (machine-profile-status existing-row))
    (row
      (semantic-id "00010010")
      (operation "max")
      (ratification-status candidate-pending-990-merge)
      (machine-profile-status existing-row))
  ))
