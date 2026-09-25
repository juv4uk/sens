; contract-consumers.lisp — direct consumers of sens (СЕНС) language semantics.
; The source contract is authoritative; consumer snapshots are pinned observations.

(contract-consumers
  (source
    (repository juv4uk/sens)
    (branch main)
    (path language-contract.lisp))

  (consumer
    (repository juv4uk/cml)
    (role compiler))

  (consumer
    (repository juv4uk/fpga-lisp)
    (role fpga-backend))

  (consumer
    (repository juv4uk/wsm-os-lisp)
    (role bare-metal-lisp-target))

  ; wsm-os belongs to the independent wsm hardware line and is intentionally
  ; not a direct consumer of the sens language contract.
  (excluded
    (repository juv4uk/wsm-os)
    (reason independent-wsm-line)))
