; Файлова гвардія SENS. Вердикт допуска — лише виконуваний мовний код.
; Вхідні шляхи недовірені: це дані Git, а не джерело політики.

(визначити fg-field
  (функція (key rows)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) ())
      ((атом? rows) (structural-kind pair)
        (за-умовою
          ((тотожне? key (перше (перше rows))) (решта (перше rows)))
          (так (fg-field key (решта rows)))))
      ((атом? rows) (structural-kind atom) ()))))

(визначити fg-not
  (функція (bit)
    (за-умовою
      ((однакові? bit 1) 0)
      (так 1))))

(визначити fg-has-field?
  (функція (key rows)
    (fg-not (однакові? (знайти-за-ключем key rows) (як-є ())))))

(визначити fg-string-list?
  (функція (values)
    (за-умовою
      ((атом? values) (structural-kind empty-list) 1)
      ((атом? values) (structural-kind pair)
        (та (рядок? (перше values)) (fg-string-list? (решта values))))
      ((атом? values) (structural-kind atom) 0))))

(визначити fg-suffix?
  (функція (text suffix)
    (за-умовою
      ((рядок-порожній? suffix) 1)
      ((рядок-порожній? text) 0)
      ((менше? (рядок-довжина text) (рядок-довжина suffix)) 0)
      ((однакові? (рядок-довжина text) (рядок-довжина suffix))
        (однакові? text suffix))
      (так (fg-suffix? (рядок-решта text) suffix)))))

(визначити fg-path-canonical?
  (функція (path)
    (та
      (рядок? path)
      (fg-not (рядок-порожній? path))
      (fg-not (рядок-префікс? "/" path))
      (fg-not (рядок-містить? "\\" path))
      (fg-not (рядок-містить? "//" path))
      (fg-not (рядок-містить? "/../" path))
      (fg-not (рядок-префікс? "../" path))
      (fg-not (рядок-містить? "/./" path))
      (fg-not (рядок-префікс? "./" path))
      (fg-not (fg-suffix? path "/.."))
      (fg-not (fg-suffix? path "/."))
      (fg-not (однакові? path "."))
      (fg-not (однакові? path "..")))))

(визначити fg-path-list?
  (функція (paths)
    (за-умовою
      ((атом? paths) (structural-kind empty-list) 1)
      ((атом? paths) (structural-kind pair)
        (та
          (fg-path-canonical? (перше paths))
          (fg-path-list? (решта paths))))
      ((атом? paths) (structural-kind atom) 0))))

(визначити fg-tools-path-list?
  (функція (paths)
    (за-умовою
      ((атом? paths) (structural-kind empty-list) 1)
      ((атом? paths) (structural-kind pair)
        (та
          (рядок-префікс? "tools/" (перше paths))
          (fg-tools-path-list? (решта paths))))
      ((атом? paths) (structural-kind atom) 0))))

(визначити fg-count
  (функція (needle values)
    (за-умовою
      ((атом? values) (structural-kind empty-list) 0)
      ((атом? values) (structural-kind pair)
        (додати
          (за-умовою ((однакові? needle (перше values)) 1) (так 0))
          (fg-count needle (решта values))))
      ((атом? values) (structural-kind atom) 0))))

(визначити fg-mode-count
  (функція (path modes)
    (за-умовою
      ((атом? modes) (structural-kind empty-list) 0)
      ((атом? modes) (structural-kind pair)
        (додати
          (за-умовою ((однакові? path (перше (перше modes))) 1) (так 0))
          (fg-mode-count path (решта modes))))
      ((атом? modes) (structural-kind atom) 0))))

(визначити fg-find-mode
  (функція (path modes)
    (за-умовою
      ((атом? modes) (structural-kind empty-list) ())
      ((атом? modes) (structural-kind pair)
        (за-умовою
          ((однакові? path (перше (перше modes))) (решта (перше modes)))
          (так (fg-find-mode path (решта modes)))))
      ((атом? modes) (structural-kind atom) ()))))

(визначити fg-mode-rows-valid?
  (функція (modes paths)
    (за-умовою
      ((атом? modes) (structural-kind empty-list) 1)
      ((атом? modes) (structural-kind pair)
        (та
          (рядок? (перше (перше modes)))
          (рядок? (решта (перше modes)))
          (однакові? (fg-count (перше (перше modes)) paths) 1)
          (однакові? (fg-mode-count (перше (перше modes)) modes) 1)
          (fg-mode-rows-valid? (решта modes) paths)))
      ((атом? modes) (structural-kind atom) 0))))

(визначити fg-paths-have-mode?
  (функція (paths modes)
    (за-умовою
      ((атом? paths) (structural-kind empty-list) 1)
      ((атом? paths) (structural-kind pair)
        (та
          (однакові? (fg-mode-count (перше paths) modes) 1)
          (fg-paths-have-mode? (решта paths) modes)))
      ((атом? paths) (structural-kind atom) 0))))

(визначити fg-mode-required?
  (функція (path)
    (або
      (рядок-префікс? "lib/" path)
      (рядок-префікс? "knowledge/" path)
      (рядок-префікс? "witnesses/" path)
      (та
        (рядок-префікс? "tools/" path)
        (fg-suffix? path ".py")))))

(визначити fg-mode-allowed?
  (функція (path modes)
    (та
      (однакові? (fg-mode-count path modes) 1)
      (або
        (однакові? (fg-find-mode path modes) "100644:blob")
        (однакові? (fg-find-mode path modes) "100755:blob")))))

; Existing paths with Git T status are not new paths.  Keep them out of
; extension admission and apply only the existing regular-blob invariant.
(визначити fg-check-typechanged
  (функція (paths modes)
    (за-умовою
      ((атом? paths) (structural-kind empty-list) 1)
      ((атом? paths) (structural-kind pair)
        (нехай ((path (перше paths)))
          (за-умовою
            ((та (fg-mode-required? path) (fg-not (fg-mode-allowed? path modes)))
              (fg-block (як-є git-mode) (список path (fg-find-mode path modes))))
            (так (fg-check-typechanged (решта paths) modes)))))
      ((атом? paths) (structural-kind atom)
        (fg-block (як-є input) "typechanged-paths is not a proper list")))))

(визначити fg-row-path
  (функція (row)
    (fg-field (як-є path) row)))

(визначити fg-count-row
  (функція (path rows)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) 0)
      ((атом? rows) (structural-kind pair)
        (додати
          (за-умовою ((однакові? path (fg-row-path (перше rows))) 1) (так 0))
          (fg-count-row path (решта rows))))
      ((атом? rows) (structural-kind atom) 0))))

(визначити fg-find-row
  (функція (path rows)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) ())
      ((атом? rows) (structural-kind pair)
        (за-умовою
          ((однакові? path (fg-row-path (перше rows))) (перше rows))
          (так (fg-find-row path (решта rows)))))
      ((атом? rows) (structural-kind atom) ()))))

(визначити fg-row-valid?
  (функція (row)
    (нехай ((path (fg-field (як-є path) row)))
      (нехай ((issue (fg-field (як-є owner-issue) row)))
        (нехай ((plan (fg-field (як-є migration_plan) row)))
          (та
            (fg-has-field? (як-є path) row)
            (fg-has-field? (як-є independence_status) row)
            (fg-has-field? (як-є owner-issue) row)
            (fg-has-field? (як-є migration_plan) row)
            (fg-path-canonical? path)
            (рядок-префікс? "tools/" path)
            (fg-suffix? path ".py")
            (однакові? (fg-field (як-є independence_status) row) (як-є foreign))
            (рядок? issue)
            (рядок-префікс? "#" issue)
            (більше? (рядок-довжина issue) 1)
            (рядок? plan)
            (більше? (рядок-довжина plan) 40)
            (рядок-містить? "SENS" plan)
            (рядок-містить? "T5" plan)))))))

(визначити fg-foreign-path?
  (функція (path rows)
    (та
      (однакові? (fg-count-row path rows) 1)
      (fg-row-valid? (fg-find-row path rows)))))

(визначити fg-rows-valid?
  (функція (rows tracked)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) 1)
      ((атом? rows) (structural-kind pair)
        (та
          (fg-row-valid? (перше rows))
          (однакові? (fg-count-row (fg-row-path (перше rows)) rows) 1)
          (однакові? (fg-count (fg-row-path (перше rows)) tracked) 1)
          (fg-rows-valid? (решта rows) tracked)))
      ((атом? rows) (structural-kind atom) 0))))

(визначити fg-census-covers-tracked?
  (функція (tracked rows)
    (за-умовою
      ((атом? tracked) (structural-kind empty-list) 1)
      ((атом? tracked) (structural-kind pair)
        (за-умовою
          ((fg-suffix? (перше tracked) ".py")
            (та
              (fg-foreign-path? (перше tracked) rows)
              (fg-census-covers-tracked? (решта tracked) rows)))
          (так (fg-census-covers-tracked? (решта tracked) rows))))
      ((атом? tracked) (structural-kind atom) 0))))

(визначити fg-policy-valid?
  (функція (policy)
    (та
      (однакові? (fg-field (як-є schema) policy) (як-є file-authority-policy/1))
      (однакові? (fg-field (як-є status) policy) (як-є owner-directed))
      (однакові? (fg-field (як-є activation-git-commit) policy)
              "9c94727eb1c45378f3debccf633aad2366e13599")
      (однакові? (fg-field (як-є governing-domains) policy)
              (як-є (D1 D2 D3 D4 D5 D6 D7 D8 D9)))
      (однакові? (fg-field (як-є important-roots) policy)
              (як-є ("lib/" "knowledge/" "witnesses/")))
      (однакові? (fg-field (як-є new-important-extensions) policy)
              (як-є (".lisp" ".sens")))
      (однакові? (fg-field (як-є physical-sens) policy) (як-є packed-T5-only))
      (однакові? (fg-field (як-є new-python-root) policy) "tools/")
      (однакові? (fg-field (як-є new-python-independence-status) policy) (як-є foreign))
      (однакові? (fg-field (як-є foreign-census) policy)
              "knowledge/foreign-tools-census.lisp")
      (однакові? (fg-field (як-є file-guard) policy)
              "knowledge/file-authority-guard.lisp")
      (однакові? (fg-field (як-є baseline-existing-paths) policy)
              (як-є grandfathered-migration-debt))
      (однакові? (fg-field (як-є baseline-important-noncanonical-count) policy) 261)
      (однакові? (fg-field (як-є baseline-python-count) policy) 741)
      (однакові? (fg-field (як-є scope) policy) (як-є added-paths-in-Git-tree))
      (однакові? (fg-field (як-є rename-or-copy) policy)
              (як-є treat-new-path-as-added))
      (однакові? (fg-field (як-є failure) policy) (як-є fail-closed))
      (однакові? (fg-field (як-є semantic-admission-from-extension) policy) (як-є ()))
      (однакові? (fg-field (як-є semantic-admission-from-host-guard) policy) (як-є ())))))

(визначити fg-census-valid?
  (функція (census tracked)
    (нехай ((rows (fg-field (як-є new-foreign-tools) census)))
      (та
        (однакові? (fg-field (як-є schema) census) (як-є foreign-tools-census/1))
        (однакові? (fg-field (як-є status) census) (як-є staged-migration))
        (однакові? (fg-field (як-є authority) census)
                "knowledge/file-authority-policy.lisp")
        (однакові? (fg-field (як-є per-file-census) census)
                "knowledge/foreign-tools-census.lisp")
        (однакові? (fg-field (як-є new-python-without-entry) census) (як-є blocked))
        (однакові? (fg-field (як-є new-python-outside-tools) census) (як-є blocked))
        (однакові? (fg-field (як-є oracle-parity-before-host-retirement) census)
                (як-є required))
        (однакові? (fg-field (як-є new-tool-does-not-own-semantics) census) 1)
        (fg-rows-valid? rows tracked)
        (fg-census-covers-tracked? tracked rows)))))

(визначити fg-classify
  (функція (path policy rows)
    (за-умовою
      ((fg-not (fg-path-canonical? path)) (як-є blocked-noncanonical-path))
      ((рядок-префікс? "lib/" path)
        (за-умовою
          ((або (fg-suffix? path ".lisp") (fg-suffix? path ".sens")) (як-є allowed))
          (так (як-є blocked-important-extension))))
      ((рядок-префікс? "knowledge/" path)
        (за-умовою
          ((або (fg-suffix? path ".lisp") (fg-suffix? path ".sens")) (як-є allowed))
          (так (як-є blocked-important-extension))))
      ((рядок-префікс? "witnesses/" path)
        (за-умовою
          ((або (fg-suffix? path ".lisp") (fg-suffix? path ".sens")) (як-є allowed))
          (так (як-є blocked-important-extension))))
      ((fg-suffix? path ".py")
        (за-умовою
          ((рядок-префікс? "tools/" path)
            (за-умовою
              ((fg-foreign-path? path rows) (як-є allowed))
              (так (як-є blocked-foreign-census))))
          (так (як-є blocked-python-outside-tools))))
      ((або
         (та (рядок-префікс? "tools/" path) (fg-suffix? path ".sh"))
         (та (рядок-префікс? "scripts/" path) (fg-suffix? path ".sh")))
        (як-є blocked-new-shell-tool))
      (так (як-є allowed)))))

(визначити fg-check-added
  (функція (paths policy rows modes)
    (за-умовою
      ((атом? paths) (structural-kind empty-list) 1)
      ((атом? paths) (structural-kind pair)
        (нехай ((path (перше paths)))
          (за-умовою
            ((та (fg-mode-required? path) (fg-not (fg-mode-allowed? path modes)))
              (fg-block (як-є git-mode) (список path (fg-find-mode path modes))))
            (так
              (нехай ((verdict (fg-classify path policy rows)))
                (за-умовою
                  ((однакові? verdict (як-є allowed))
                    (fg-check-added (решта paths) policy rows modes))
                  (так (fg-block (як-є path) (список path verdict)))))))))
      ((атом? paths) (structural-kind atom)
        (fg-block (як-є input) "added-paths is not a proper list")))))

(визначити fg-check-tracked
  (функція (paths rows)
    (за-умовою
      ((атом? paths) (structural-kind empty-list) 1)
      ((атом? paths) (structural-kind pair)
        (нехай ((path (перше paths)))
          (за-умовою
            ((fg-not (fg-path-canonical? path))
              (fg-block (як-є input-path) path))
            ((fg-not (рядок-префікс? "tools/" path))
              (fg-block (як-є tracked-tools-path) path))
            (так (fg-check-tracked (решта paths) rows)))))
      ((атом? paths) (structural-kind atom)
        (fg-block (як-є input) "tracked-tools-paths is not a proper list")))))

(визначити fg-test-equal
  (функція (label actual expected)
    (за-умовою
      ((однакові? actual expected) 1)
      (так (fg-block (як-є self-test) label)))))

(визначити fg-fixture-good
  (як-є
    (((path . "tools/fixture.py")
      (independence_status . foreign)
      (owner-issue . "#5397")
      (migration_plan . "Move file policy into executable SENS T5; keep Git facts as untrusted transport and prove hosted positive and negative parity before retiring Python.")))))

(визначити fg-fixture-bad-status
  (як-є
    (((path . "tools/fixture.py")
      (independence_status . local)
      (owner-issue . "#5397")
      (migration_plan . "Move file policy into executable SENS T5; keep Git facts as untrusted transport and prove hosted positive and negative parity before retiring Python.")))))

(визначити fg-self-test
  (функція (real-rows)
    (та
      (fg-test-equal "native lisp" (fg-classify "lib/native.lisp" *file-authority-policy* real-rows) (як-є allowed))
      (fg-test-equal "native physical SENS" (fg-classify "lib/native.sens" *file-authority-policy* real-rows) (як-є allowed))
      (fg-test-equal "new JSON is blocked" (fg-classify "knowledge/new.json" *file-authority-policy* real-rows) (як-є blocked-important-extension))
      (fg-test-equal "FASL is not native source" (fg-classify "lib/legacy.lisp.fasl" *file-authority-policy* real-rows) (як-є blocked-important-extension))
      (fg-test-equal "witness extension is blocked" (fg-classify "witnesses/new.rs" *file-authority-policy* real-rows) (як-є blocked-important-extension))
      (fg-test-equal "Python outside tools is blocked" (fg-classify "scripts/new.py" *file-authority-policy* real-rows) (як-є blocked-python-outside-tools))
      (fg-test-equal "unregistered Python is blocked" (fg-classify "tools/unlisted.py" *file-authority-policy* real-rows) (як-є blocked-foreign-census))
      (fg-test-equal "registered Python is admitted" (fg-classify "tools/fixture.py" *file-authority-policy* fg-fixture-good) (як-є allowed))
      (fg-test-equal "non-foreign census is blocked" (fg-classify "tools/fixture.py" *file-authority-policy* fg-fixture-bad-status) (як-є blocked-foreign-census))
      (fg-test-equal "duplicate census row is blocked"
        (fg-classify "tools/fixture.py" *file-authority-policy* (append fg-fixture-good fg-fixture-good))
        (як-є blocked-foreign-census))
      (fg-test-equal "regular Git blob is admitted"
        (fg-mode-allowed? "lib/example.sens" (як-є (("lib/example.sens" . "100644:blob")))) 1)
      (fg-test-equal "symlink disguised as SENS is blocked"
        (fg-mode-allowed? "lib/example.sens" (як-є (("lib/example.sens" . "120000:blob")))) 0)
      (fg-test-equal "gitlink disguised as SENS is blocked"
        (fg-mode-allowed? "lib/example.sens" (як-є (("lib/example.sens" . "160000:commit")))) 0)
      (fg-test-equal "missing Git mode is blocked"
        (fg-mode-allowed? "lib/example.sens" (як-є ())) 0)
      (fg-test-equal "new shell tooling is blocked" (fg-classify "tools/new.sh" *file-authority-policy* real-rows) (як-є blocked-new-shell-tool))
      (fg-test-equal "ordinary docs data is outside this policy" (fg-classify "docs/research.json" *file-authority-policy* real-rows) (як-є allowed))
      (fg-test-equal "missing policy is invalid" (fg-policy-valid? (як-є ())) 0)
      (fg-test-equal "missing census is invalid" (fg-census-valid? (як-є ()) (як-є ("tools/fixture.py"))) 0))))

(визначити fg-block
  (функція (kind subject)
    (за-умовою
      ((однакові? kind (як-є policy)) (sens_file_authority_fail_policy_5397 subject))
      ((однакові? kind (як-є census)) (sens_file_authority_fail_census_5397 subject))
      ((однакові? kind (як-є input)) (sens_file_authority_fail_input_5397 subject))
      ((однакові? kind (як-є self-test)) (sens_file_authority_fail_self_test_5397 subject))
      ((однакові? kind (як-є missing-policy)) (sens_file_authority_fail_missing_policy_5397 subject))
      ((однакові? kind (як-є missing-census)) (sens_file_authority_fail_missing_census_5397 subject))
      ((однакові? kind (як-є missing-guard)) (sens_file_authority_fail_missing_guard_5397 subject))
      ((однакові? kind (як-є input-path)) (sens_file_authority_fail_input_path_5397 subject))
      ((однакові? kind (як-є tracked-tools-path)) (sens_file_authority_fail_tracked_tools_path_5397 subject))
      ((однакові? kind (як-є path)) (sens_file_authority_fail_path_5397 subject))
      ((однакові? kind (як-є git-mode)) (sens_file_authority_fail_git_mode_5405 subject))
      (так (sens_file_authority_fail_unknown_5397 subject)))))

(визначити fg-require
  (функція (condition kind subject)
    (за-умовою
      ((однакові? condition 1) 1)
      (так (fg-block kind subject)))))

(визначити fg-run
  (функція (input)
    (нехай ((input-ok
            (fg-require
              (та
                (однакові? (fg-field (як-є schema) input) (як-є file-authority-input/1))
                (fg-path-list? (fg-field (як-є added-paths) input))
                (fg-mode-rows-valid?
                  (fg-field (як-є added-modes) input)
                  (fg-field (як-є added-paths) input))
                (fg-paths-have-mode?
                  (fg-field (як-є added-paths) input)
                  (fg-field (як-є added-modes) input))
                (fg-path-list? (fg-field (як-є typechanged-paths) input))
                (fg-mode-rows-valid?
                  (fg-field (як-є typechanged-modes) input)
                  (fg-field (як-є typechanged-paths) input))
                (fg-paths-have-mode?
                  (fg-field (як-є typechanged-paths) input)
                  (fg-field (як-є typechanged-modes) input))
                (fg-path-list? (fg-field (як-є tracked-tools-paths) input))
                (fg-tools-path-list? (fg-field (як-є tracked-tools-paths) input)))
              (як-є input) "Git path transport")))
      (нехай ((policy-ok
              (fg-require
                (fg-policy-valid? *file-authority-policy*)
                (як-є policy) "knowledge/file-authority-policy.lisp")))
        (нехай ((census-ok
                (fg-require
                  (fg-census-valid?
                    *foreign-tools-census*
                    (fg-field (як-є tracked-tools-paths) input))
                  (як-є census) "knowledge/foreign-tools-census.lisp")))
          (нехай ((tests-ok
                  (fg-require
                    (fg-self-test (fg-field (як-є new-foreign-tools) *foreign-tools-census*))
                    (як-є self-test) "positive/negative SENS witnesses")))
            (нехай ((added-ok
                    (fg-check-added
                      (fg-field (як-є added-paths) input)
                      *file-authority-policy*
                      (fg-field (як-є new-foreign-tools) *foreign-tools-census*)
                      (fg-field (як-є added-modes) input))))
              (нехай ((typechanged-ok
                      (fg-check-typechanged
                        (fg-field (як-є typechanged-paths) input)
                        (fg-field (як-є typechanged-modes) input))))
                (нехай ((tracked-ok
                        (fg-check-tracked
                          (fg-field (як-є tracked-tools-paths) input)
                          (fg-field (як-є new-foreign-tools) *foreign-tools-census*))))
                  (друкувати
                  (список
                    (як-є SENS_FILE_AUTHORITY_PASS)
                    (як-є new-paths)
                    (довжина (fg-field (як-є added-paths) input))
                    (як-є tracked-tool-paths)
                    (довжина (fg-field (як-є tracked-tools-paths) input)))))))))))))

(за-умовою
  ((однакові? (fg-field (як-є policy) *file-authority-source-status*) (як-є missing))
    (fg-block (як-є missing-policy) "knowledge/file-authority-policy.lisp"))
  ((однакові? (fg-field (як-є census) *file-authority-source-status*) (як-є missing))
    (fg-block (як-є missing-census) "knowledge/foreign-tools-census.lisp"))
  ((однакові? (fg-field (як-є guard) *file-authority-source-status*) (як-є missing))
    (fg-block (як-є missing-guard) "knowledge/file-authority-guard.lisp"))
  (так (fg-run *file-authority-input*)))
