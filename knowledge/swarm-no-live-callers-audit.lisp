; Ecosystem-scoped C5 audit після фізичного видалення legacy :9999 coordination.
; Coordination authority — swarm-node :910x / swarm/1. my-lisp :9999 лишається
; semantic oracle; semantic-oracle callers навмисно не входять у цей removal gate.
;
; status=removed описує фізичний стан API. Сильніший claim про повністю
; підтверджений C5 робиться лише після зеленого C5 gate та full CI на цьому стані.

(00001001 *swarm-no-live-callers-audit*
  (00000001
    ((schema . swarm-no-live-callers-audit/1)
     (as-of . "2026-09-07")
     (scope . ecosystem)
     (status . removed)
     (safe-to-remove . t)
     (coordination-authority . swarm-node)
     (semantic-oracle . my-lisp-9999)
     (semantic-operations . (eval parse diagnose contract-version oracle-status oracle-result))
     (checked-heads .
       ((cml . f96fc754e8fd5563bf01c5ae63ea371bc8adf2bb)
        (fpga-lisp . 502e43bbcb248d2ddbdfb15f8742a1bedd4f4e37)
        (my-idea . cb5dd10fccfe788e101bd6d63bc2e4c8c0a136c3)))
     (live-caller-proof .
       ((my-lisp-production-operational . confirmed)
        (my-lisp-production-operational-callers . ())
        (my-lisp-compatibility-callers . ())
        (method . crates/my-lisp/tests/swarm_live_caller_inventory.rs)
        (sibling-repositories . targeted-search-confirmed)
        (sibling-observed-executable-legacy-callers . ())))
     (guidance-proof .
       ((my-lisp-agent-guide . confirmed)
        (my-lisp-migration-authority . confirmed)
        (my-lisp-ecosystem-status-guidance . swarm-node-only)
        (my-lisp-swarm-autonomy-v1 . superseded-quarantined)
        (cml-agent-guide . swarm-node-only)
        (cml-tasks-guidance . swarm-node-only)
        (fpga-lisp-agent-guide . swarm-node-only)
        (my-idea-agent-guide . swarm-node-only)))
     (confirmed .
       ((primary-agent-guide . AGENTS.md)
        (migration-authority . docs/swarm-mesh-v2.md)
        (deprecation-marker . knowledge/swarm-legacy-deprecation.lisp)
        (semantic-callers-allowed . "fpga-lisp oracle crosscheck and my-idea oracle client use :9999 only as semantic oracle")
        (sibling-executable-legacy-caller-search . "no executable legacy :9999 coordination request observed in cml/fpga-lisp/my-idea at the checked heads")
        (active-guidance-legacy-callers . ())))
     (removal-proof .
       ((physical-status . removed)
        (physical-removal-commit . 32a087f)
        (static-caller-inventory . crates/my-lisp/tests/swarm_live_caller_inventory.rs)
        (runtime-rejection-witness . crates/my-lisp-cli/tests/legacy_coordination_rejected.rs)
        (semantic-preservation-shield . crates/my-lisp-cli/tests/semantic_oracle_preservation.rs)))
     (blockers . ())
     (legacy-compatibility-tests . ())
     (physical-surface-still-present . ())
     (next-proof .
       (run-c5-removal-gate-and-full-ci)))))
