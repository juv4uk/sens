; Постанова власника SENS: файлова влада, 2026-10-10.
; Це політика допуску НОВИХ шляхів, не ратифікація значення за розширенням.
; Старі формати тримаються як явно названий борг до окремої міграції.
(00001001 *file-authority-policy*
  (00000001
    ((schema . file-authority-policy/1)
     (status . owner-directed)
     (activation-git-commit . "9c94727eb1c45378f3debccf633aad2366e13599")
     (governing-domains . (D1 D2 D3 D4 D5 D6 D7 D8 D9))
     (important-roots . ("lib/" "knowledge/" "witnesses/"))
     (new-important-extensions . (".lisp" ".sens"))
     (physical-sens . packed-T5-only)
     (new-python-root . "tools/")
     (new-python-independence-status . foreign)
     (foreign-census . "knowledge/foreign-tools-census.lisp")
     (file-guard . "tools/file-authority-guard.sh")
     (baseline-existing-paths . grandfathered-migration-debt)
     (baseline-important-noncanonical-count . 261)
     (baseline-python-count . 741)
     (scope . added-paths-in-Git-tree)
     (rename-or-copy . treat-new-path-as-added)
     (failure . fail-closed)
     (human-surface . ukrainian)
     (semantic-admission-from-extension . ())
     (semantic-admission-from-host-guard . ())
     (migration . 
       ((old-json-tsv-fasl-xed . staged-oracle-parity-before-retirement)
        (old-python-outside-tools . move-or-reimplement-after-proof)
        (new-foreign-tool . census-plus-explicit-SENS-cutover-plan)
        (independent-ci . GitHub-hosted-negative-witnesses)
        (final-authority . SENS-Lisp-or-physical-T5-oracle))))))
