; contracts/world-transition-contract.lisp — Lisp-owned result contract for #1312.
;
; Formalizes the result domains of world state transitions, history preservation,
; and equality observations over immutable worlds:
;
; 1. World snapshot parentage and historical reconstruction are verified via
;    structural-relation (equal?), never universal truth sentinels.
; 2. Content addresses are verified via identity-relation (eq). Distinct world
;    histories with identical current clauses produce distinct content addresses.
; 3. Transition receipts (accepted, rejected, conflict) embed structural-relation
;    records, preserving transition shape without universal-T coercion.
; 4. Universal-T coercion is forbidden across all world transitions.

(world-transition-contract/1
  ((domain . world-system)
   (universal-truth-forbidden . t)
   (laws .
     ((parent-preservation-equality . (structural-relation same))
      (content-address-same . (identity-relation same))
      (content-address-distinct . (identity-relation distinct))
      (transaction-rollback-journal-equality . (structural-relation same))
      (snapshot-conflict-preservation-equality . (structural-relation same))
      (snapshot-rejection-preservation-equality . (structural-relation same))))
   (categories .
     ((world-snapshot-structure
        (each-world-keeps-its-immediate-parent
          (relation . structural-relation)
          (expected . (structural-relation same)))
        (world-at-depth-recovers-exact-historical-snapshot
          (relation . structural-relation)
          (expected . ((structural-relation same)
                       (structural-relation same)
                       (structural-relation same))))
        (world-common-ancestor-finds-branch-point
          (relation . structural-relation)
          (expected . (structural-relation same)))
        (world-common-ancestor-aligns-unequal-branch-depths
          (relation . structural-relation)
          (expected . (structural-relation same))))

      (content-address-identity
        (equal-knowledge-has-same-canonical-content-address
          (relation . identity-relation)
          (expected . (identity-relation same)))
        (different-knowledge-has-different-content-address
          (relation . identity-relation)
          (expected . (identity-relation distinct)))
        (independently-reconstructed-worlds-have-same-content-address
          (relation . identity-relation)
          (expected . (identity-relation same)))
        (knowledge-content-addresses-round-trip-to-same-structure
          (relation . structural-relation)
          (expected . (structural-relation same)))
        (equal-current-clauses-do-not-erase-distinct-world-histories
          (structural-relation . (structural-relation same))
          (identity-relation . (identity-relation distinct))
          (expected . ((structural-relation same)
                       (identity-relation distinct)))))

      (world-package-and-batch-transitions
        (world-package-import-atomically-creates-queryable-child
          (status . accepted)
          (parent-equality . (structural-relation same))
          (query . yes))
        (world-package-import-rejects-unsupported-versions-without-transition
          (status . rejected)
          (reason . unsupported-version)
          (target-equality . (structural-relation same)))
        (world-package-import-conflict-preserves-target-snapshot
          (status . conflict)
          (target-equality . (structural-relation same)))
        (advise-world-rejection-returns-unchanged-world
          (status . rejected)
          (target-equality . (structural-relation same)))
        (advise-world-conflict-preserves-existing-snapshot
          (status . conflict)
          (target-equality . (structural-relation same)))
        (advise-all-world-accepts-one-atomic-dependent-batch
          (status . accepted)
          (parent-equality . (structural-relation same)))
        (advise-all-world-rejects-whole-malformed-batch
          (status . rejected)
          (target-equality . (structural-relation same)))
        (advise-all-world-rejects-empty-batch-without-new-world
          (status . rejected)
          (reason . invalid-batch)
          (target-equality . (structural-relation same)))
        (advise-all-world-detects-internal-conflict-without-partial-writes
          (status . conflict)
          (target-equality . (structural-relation same))))

      (compatibility-wrappers
        (defmodule-compatibility-wrapper-uses-world-transition
          (journal-equality . (structural-relation same)))
        (tell-knowledge-compatibility-wrapper-uses-world-transition
          (journal-equality . (structural-relation same)))
        (retract-knowledge-compatibility-wrapper-uses-world-transition
          (journal-equality . (structural-relation same)))
        (conflicting-tell-knowledge-keeps-legacy-journal-unchanged
          (status . Conflict-detected)
          (journal-equality . (structural-relation same)))
        (advise-compatibility-wrapper-preserves-journal-on-conflict
          (status . conflict)
          (journal-equality . (structural-relation same)))
        (advise-all-compatibility-wrapper-rolls-back-invalid-batch
          (status . rejected)
          (journal-equality . (structural-relation same)))
        (package-import-compatibility-wrapper-preserves-journal-on-rejection
          (status . rejected)
          (journal-equality . (structural-relation same)))
        (package-import-compatibility-wrapper-preserves-journal-on-conflict
          (status . conflict)
          (journal-equality . (structural-relation same))))))))
