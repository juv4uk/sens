; #845 — read-only semantic coordinate matrix.
;
; This is a composition view only. It does not define meaning and does not
; Final current-main replay: source references only; no duplicated axis truth.
; allocate semantic IDs. Each axis keeps its own authority and this matrix
; stores only source references for the same SID. An axis with no admitted
; row is represented explicitly as `absent`; absence does not mint evidence.
;
(semantic-coordinate-matrix/1
  (identity-source . "lib/surface/semantic-registry.lisp")
  (math-axis-source . "tests/fixtures/semantic-coordinate-law-axis-v1.lisp")
  (kernel-axis-source . "contracts/sid-kernel-witness-735.lisp")
  (machine-axis-source . "lib/machine/capability-axis.lisp")
  (rows
    (((sid . "00001100")
      (math-entry-sid . "00001100")
      (kernel-entry-sid . absent)
      (machine-entry-sid . "00001100"))
     ((sid . "00000011")
      (math-entry-sid . "00000011")
      (kernel-entry-sid . "00000011")
      (machine-entry-sid . "00000011"))
     ((sid . "00000100")
      (math-entry-sid . "00000100")
      (kernel-entry-sid . "00000100")
      (machine-entry-sid . "00000100"))
     ((sid . "00000101")
      (math-entry-sid . "00000101")
      (kernel-entry-sid . "00000101")
      (machine-entry-sid . "00000101"))
     ((sid . "00000111")
      (math-entry-sid . "00000111")
      (kernel-entry-sid . "00000111")
      (machine-entry-sid . "00000111")))))