; Мовний контракт результатів переходів світу, задача #1312.
; Історичні англомовні ключі записів є незмінними іменами протоколу.
;
; Контракт описує результати переходів стану, збереження історії
; та спостереження рівності незмінних світів:
;
; 1. Батьківський зв'язок і відновлення знімків перевіряємо
;    структурною рівністю, а не універсальним маркером істини.
; 2. Адреси вмісту порівнюємо за тотожністю. Різні історії світів
;    можуть мати однакові чинні клаузи, але різні адреси вмісту.
; 3. Квитанції accepted, rejected, conflict зберігають власну
;    структурну форму разом із результатом перевірки.
; 4. Заборонено приводити всі відповіді переходів до універсальної істини.
; Точна предикатна істина й хиба належать D1; форма даних від них відмінна.

(world-transition-contract-1
  ((domain . world-system)
   (universal-truth-forbidden . t)
   (laws .
     ((parent-preservation-equality . (1))
      (content-address-same . (1))
      (content-address-distinct . (0))
      (transaction-rollback-journal-equality . (1))
      (snapshot-conflict-preservation-equality . (1))
      (snapshot-rejection-preservation-equality . (1))))
   (categories .
     ((world-snapshot-structure
        (each-world-keeps-its-immediate-parent
          (relation . structural-relation)
          (expected . (1)))
        (world-at-depth-recovers-exact-historical-snapshot
          (relation . structural-relation)
          (expected . ((1)
                       (1)
                       (1))))
        (world-common-ancestor-finds-branch-point
          (relation . structural-relation)
          (expected . (1)))
        (world-common-ancestor-aligns-unequal-branch-depths
          (relation . structural-relation)
          (expected . (1))))

      (content-address-identity
        (equal-knowledge-has-same-canonical-content-address
          (relation . identity-relation)
          (expected . (1)))
        (different-knowledge-has-different-content-address
          (relation . identity-relation)
          (expected . (0)))
        (independently-reconstructed-worlds-have-same-content-address
          (relation . identity-relation)
          (expected . (1)))
        (knowledge-content-addresses-round-trip-to-same-structure
          (relation . structural-relation)
          (expected . (1)))
        (equal-current-clauses-do-not-erase-distinct-world-histories
          (structural-relation . (1))
          (identity-relation . (0))
          (expected . ((1)
                       (0)))))

      (world-package-and-batch-transitions
        (world-package-import-atomically-creates-queryable-child
          (status . accepted)
          (parent-equality . (1))
          (query . yes))
        (world-package-import-rejects-unsupported-versions-without-transition
          (status . rejected)
          (reason . unsupported-version)
          (target-equality . (1)))
        (world-package-import-conflict-preserves-target-snapshot
          (status . conflict)
          (target-equality . (1)))
        (advise-world-rejection-returns-unchanged-world
          (status . rejected)
          (target-equality . (1)))
        (advise-world-conflict-preserves-existing-snapshot
          (status . conflict)
          (target-equality . (1)))
        (advise-all-world-accepts-one-atomic-dependent-batch
          (status . accepted)
          (parent-equality . (1)))
        (advise-all-world-rejects-whole-malformed-batch
          (status . rejected)
          (target-equality . (1)))
        (advise-all-world-rejects-empty-batch-without-new-world
          (status . rejected)
          (reason . invalid-batch)
          (target-equality . (1)))
        (advise-all-world-detects-internal-conflict-without-partial-writes
          (status . conflict)
          (target-equality . (1))))

      (compatibility-wrappers
        (defmodule-compatibility-wrapper-uses-world-transition
          (journal-equality . (1)))
        (tell-knowledge-compatibility-wrapper-uses-world-transition
          (journal-equality . (1)))
        (retract-knowledge-compatibility-wrapper-uses-world-transition
          (journal-equality . (1)))
        (conflicting-tell-knowledge-keeps-legacy-journal-unchanged
          (status . Conflict-detected)
          (journal-equality . (1)))
        (advise-compatibility-wrapper-preserves-journal-on-conflict
          (status . conflict)
          (journal-equality . (1)))
        (advise-all-compatibility-wrapper-rolls-back-invalid-batch
          (status . rejected)
          (journal-equality . (1)))
        (package-import-compatibility-wrapper-preserves-journal-on-rejection
          (status . rejected)
          (journal-equality . (1)))
        (package-import-compatibility-wrapper-preserves-journal-on-conflict
          (status . conflict)
          (journal-equality . (1))))))))
