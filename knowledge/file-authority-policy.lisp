; Постанова власника SENS: файлова влада, 2026-10-10.
; Політика допускає НОВІ шляхи, а не надає семантичну владу розширенням.
; Історичні формати збережено як debt до окремої міграції з oracle parity.
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
     (file-guard . "tools/important_file_guard.py")
     (baseline-existing-paths . grandfathered-migration-debt)
     (baseline-important-noncanonical-count . 261)
     (baseline-python-count . 741)
     (scope . changed-paths-plus-complete-tools-python-census)
     (rename-or-copy . inspect-destination-as-new)
     (failure . fail-closed)
     (human-surface . ukrainian)
     (semantic-admission-from-extension . ())
     (semantic-admission-from-host-guard . ())
     (migration .
       ((old-json-tsv-fasl-xed . staged-oracle-parity-before-retirement)
        (old-python-outside-tools . move-or-reimplement-after-proof)
        (new-foreign-tool . census-plus-explicit-SENS-cutover-plan)
        (independent-ci . GitHub-hosted-negative-witnesses)
        (temporary-host-role . untrusted-Git-path-transport-only)
        (final-authority . SENS-Lisp-or-physical-T5-oracle))))))