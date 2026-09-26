; Машинно-читаний marker для retired coordination operations старого :9999 API.
; Coordination authority належить swarm-node :910x / swarm/1.
; Стару coordination surface на my-lisp :9999 фізично видалено; ці назви
; лишаються тут як migration data та не мають dispatch path у semantic oracle.

(00001001 *swarm-legacy-coordination*
  (00000001
    ((schema . swarm-legacy-deprecation/1)
     (status . deprecated)
     (physical-status . removed)
     (semantic-plane . my-lisp-9999)
     (coordination-authority . swarm-node)
     (coordination-protocol . swarm/1)
     (legacy-operations .
       (hello
        heartbeat
        claim
        release
        complete-task
        define-task
        validate-tasks
        sync-tasks
        sync-milestone
        next-best-action
        list-task-state
        list-tasks
        presence
        list-claims
        capability-request
        subscribe
        publish
        notify
        poll))
     (replacement-map .
       ((hello . join)
        (claim . claim-task)
        (release . release-task)
        (complete-task . complete-task)
        (next-best-action . next-best-action)
        (list-task-state . list-task-state)
        (presence . list-members)
        (list-claims . list-members)
        (sync-tasks . sync-tasks)
        (subscribe . event-journal-gossip)
        (publish . event-journal-gossip)
        (notify . event-journal-gossip)
        (poll . event-journal-gossip)))
     (runtime-rejection . confirmed)
     (removal-evidence .
       ((physical-removal-commit . 32a087f)
        (caller-inventory . crates/my-lisp/tests/swarm_live_caller_inventory.rs)
        (runtime-rejection-witness . crates/my-lisp-cli/tests/legacy_coordination_rejected.rs)
        (semantic-preservation-shield . crates/my-lisp-cli/tests/semantic_oracle_preservation.rs)))
     (removal-gate .
       (migration-regression
        no-live-callers
        preserve-eval-parse-diagnose
        runtime-rejection)))))
