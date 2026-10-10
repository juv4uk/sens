; Постанова власника SENS, 2026-10-10. Інструменти мають перейти до SENS.
; Цей запис — структурні дані політики, НЕ доказ виконання оракулом.
; До появи виконавчого свідка CI використовує окремий тимчасовий механізм.
; Не змінювати D1–D9, T5 і ратифіковану extensionless-проєкцію без окремого закону.
(00000001
  ((schema . tooling-file-placement/1)
   (status . owner-directed)
   (scope . new-paths)
   (protected-roots . ("lib/" "knowledge/" "witnesses/"))
   (required-extensions . (".lisp" ".sens"))
   (foreign-extension . ".py")
   (foreign-directory . "tools/")
   (foreign-census . "knowledge/foreign-tool-census.lisp")
   (independence-status . foreign)
   (migration-plan . required)
   (missing-census . blocked)
   (missing-diff-base . blocked)
   (existing-foreign-files . inherited-migration-debt)
   (rename-or-copy-to-new-path . inspect)
   (extensionless-T5-view . needs-paired-physical-proof)
   (authority . SENS)
   (temporary-host-mechanism . git-filesystem-only)
   (implementing-task . 5397)
   (negative-cases .
     ("lib/new.py" "knowledge/new.json" "witnesses/new.rs"
      "scripts/new.py" "tools/uncensused.py"))
   (positive-cases . ("lib/new.lisp" "lib/new.sens"))))
