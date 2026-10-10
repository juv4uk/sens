; Файлова гвардія SENS. Вердикт допуска — лише виконуваний мовний код.
; Вхідні шляхи недовірені: це дані Git, а не джерело політики.

(def fg-field
  (lambda (key rows)
    (cond
      ((atom rows) (structural-kind empty-list) ())
      ((atom rows) (structural-kind pair)
        (cond
          ((eq key (car (car rows))) (cdr (car rows)))
          (t (fg-field key (cdr rows)))))
      ((atom rows) (structural-kind atom) ()))))

(def fg-not
  (lambda (bit)
    (cond
      ((equal? bit 1) 0)
      (t 1))))

(def fg-has-field?
  (lambda (key rows)
    (fg-not (equal? (assoc key rows) (quote ())))))

(def fg-string-list?
  (lambda (values)
    (cond
      ((atom values) (structural-kind empty-list) 1)
      ((atom values) (structural-kind pair)
        (and (string? (car values)) (fg-string-list? (cdr values))))
      ((atom values) (structural-kind atom) 0))))

(def fg-suffix?
  (lambda (text suffix)
    (cond
      ((string-empty? suffix) 1)
      ((string-empty? text) 0)
      ((< (string-length text) (string-length suffix)) 0)
      ((equal? (string-length text) (string-length suffix))
        (equal? text suffix))
      (t (fg-suffix? (string-rest text) suffix)))))

(def fg-path-canonical?
  (lambda (path)
    (and
      (string? path)
      (fg-not (string-empty? path))
      (fg-not (string-prefix? "/" path))
      (fg-not (string-contains? "\\" path))
      (fg-not (string-contains? "//" path))
      (fg-not (string-contains? "/../" path))
      (fg-not (string-prefix? "../" path))
      (fg-not (string-contains? "/./" path))
      (fg-not (string-prefix? "./" path))
      (fg-not (fg-suffix? path "/.."))
      (fg-not (fg-suffix? path "/."))
      (fg-not (equal? path "."))
      (fg-not (equal? path "..")))))

(def fg-path-list?
  (lambda (paths)
    (cond
      ((atom paths) (structural-kind empty-list) 1)
      ((atom paths) (structural-kind pair)
        (and
          (fg-path-canonical? (car paths))
          (fg-path-list? (cdr paths))))
      ((atom paths) (structural-kind atom) 0))))

(def fg-tools-path-list?
  (lambda (paths)
    (cond
      ((atom paths) (structural-kind empty-list) 1)
      ((atom paths) (structural-kind pair)
        (and
          (string-prefix? "tools/" (car paths))
          (fg-tools-path-list? (cdr paths))))
      ((atom paths) (structural-kind atom) 0))))

(def fg-count
  (lambda (needle values)
    (cond
      ((atom values) (structural-kind empty-list) 0)
      ((atom values) (structural-kind pair)
        (+
          (cond ((equal? needle (car values)) 1) (t 0))
          (fg-count needle (cdr values))))
      ((atom values) (structural-kind atom) 0))))

(def fg-mode-count
  (lambda (path modes)
    (cond
      ((atom modes) (structural-kind empty-list) 0)
      ((atom modes) (structural-kind pair)
        (+
          (cond ((equal? path (car (car modes))) 1) (t 0))
          (fg-mode-count path (cdr modes))))
      ((atom modes) (structural-kind atom) 0))))

(def fg-find-mode
  (lambda (path modes)
    (cond
      ((atom modes) (structural-kind empty-list) ())
      ((atom modes) (structural-kind pair)
        (cond
          ((equal? path (car (car modes))) (cdr (car modes)))
          (t (fg-find-mode path (cdr modes)))))
      ((atom modes) (structural-kind atom) ()))))

(def fg-mode-rows-valid?
  (lambda (modes paths)
    (cond
      ((atom modes) (structural-kind empty-list) 1)
      ((atom modes) (structural-kind pair)
        (and
          (string? (car (car modes)))
          (string? (cdr (car modes)))
          (equal? (fg-count (car (car modes)) paths) 1)
          (equal? (fg-mode-count (car (car modes)) modes) 1)
          (fg-mode-rows-valid? (cdr modes) paths)))
      ((atom modes) (structural-kind atom) 0))))

(def fg-paths-have-mode?
  (lambda (paths modes)
    (cond
      ((atom paths) (structural-kind empty-list) 1)
      ((atom paths) (structural-kind pair)
        (and
          (equal? (fg-mode-count (car paths) modes) 1)
          (fg-paths-have-mode? (cdr paths) modes)))
      ((atom paths) (structural-kind atom) 0))))

(def fg-mode-required?
  (lambda (path)
    (or
      (string-prefix? "lib/" path)
      (string-prefix? "knowledge/" path)
      (string-prefix? "witnesses/" path)
      (and
        (string-prefix? "tools/" path)
        (fg-suffix? path ".py")))))

(def fg-mode-allowed?
  (lambda (path modes)
    (and
      (equal? (fg-mode-count path modes) 1)
      (or
        (equal? (fg-find-mode path modes) "100644:blob")
        (equal? (fg-find-mode path modes) "100755:blob")))))

(def fg-row-path
  (lambda (row)
    (fg-field (quote path) row)))

(def fg-count-row
  (lambda (path rows)
    (cond
      ((atom rows) (structural-kind empty-list) 0)
      ((atom rows) (structural-kind pair)
        (+
          (cond ((equal? path (fg-row-path (car rows))) 1) (t 0))
          (fg-count-row path (cdr rows))))
      ((atom rows) (structural-kind atom) 0))))

(def fg-find-row
  (lambda (path rows)
    (cond
      ((atom rows) (structural-kind empty-list) ())
      ((atom rows) (structural-kind pair)
        (cond
          ((equal? path (fg-row-path (car rows))) (car rows))
          (t (fg-find-row path (cdr rows)))))
      ((atom rows) (structural-kind atom) ()))))

(def fg-row-valid?
  (lambda (row)
    (let ((path (fg-field (quote path) row)))
      (let ((issue (fg-field (quote owner-issue) row)))
        (let ((plan (fg-field (quote migration_plan) row)))
          (and
            (fg-has-field? (quote path) row)
            (fg-has-field? (quote independence_status) row)
            (fg-has-field? (quote owner-issue) row)
            (fg-has-field? (quote migration_plan) row)
            (fg-path-canonical? path)
            (string-prefix? "tools/" path)
            (fg-suffix? path ".py")
            (equal? (fg-field (quote independence_status) row) (quote foreign))
            (string? issue)
            (string-prefix? "#" issue)
            (> (string-length issue) 1)
            (string? plan)
            (> (string-length plan) 40)
            (string-contains? "SENS" plan)
            (string-contains? "T5" plan)))))))

(def fg-foreign-path?
  (lambda (path rows)
    (and
      (equal? (fg-count-row path rows) 1)
      (fg-row-valid? (fg-find-row path rows)))))

(def fg-rows-valid?
  (lambda (rows tracked)
    (cond
      ((atom rows) (structural-kind empty-list) 1)
      ((atom rows) (structural-kind pair)
        (and
          (fg-row-valid? (car rows))
          (equal? (fg-count-row (fg-row-path (car rows)) rows) 1)
          (equal? (fg-count (fg-row-path (car rows)) tracked) 1)
          (fg-rows-valid? (cdr rows) tracked)))
      ((atom rows) (structural-kind atom) 0))))

(def fg-census-covers-tracked?
  (lambda (tracked rows)
    (cond
      ((atom tracked) (structural-kind empty-list) 1)
      ((atom tracked) (structural-kind pair)
        (cond
          ((fg-suffix? (car tracked) ".py")
            (and
              (fg-foreign-path? (car tracked) rows)
              (fg-census-covers-tracked? (cdr tracked) rows)))
          (t (fg-census-covers-tracked? (cdr tracked) rows))))
      ((atom tracked) (structural-kind atom) 0))))

(def fg-policy-valid?
  (lambda (policy)
    (and
      (equal? (fg-field (quote schema) policy) (quote file-authority-policy/1))
      (equal? (fg-field (quote status) policy) (quote owner-directed))
      (equal? (fg-field (quote activation-git-commit) policy)
              "9c94727eb1c45378f3debccf633aad2366e13599")
      (equal? (fg-field (quote governing-domains) policy)
              (quote (D1 D2 D3 D4 D5 D6 D7 D8 D9)))
      (equal? (fg-field (quote important-roots) policy)
              (quote ("lib/" "knowledge/" "witnesses/")))
      (equal? (fg-field (quote new-important-extensions) policy)
              (quote (".lisp" ".sens")))
      (equal? (fg-field (quote physical-sens) policy) (quote packed-T5-only))
      (equal? (fg-field (quote new-python-root) policy) "tools/")
      (equal? (fg-field (quote new-python-independence-status) policy) (quote foreign))
      (equal? (fg-field (quote foreign-census) policy)
              "knowledge/foreign-tools-census.lisp")
      (equal? (fg-field (quote file-guard) policy)
              "knowledge/file-authority-guard.lisp")
      (equal? (fg-field (quote baseline-existing-paths) policy)
              (quote grandfathered-migration-debt))
      (equal? (fg-field (quote baseline-important-noncanonical-count) policy) 261)
      (equal? (fg-field (quote baseline-python-count) policy) 741)
      (equal? (fg-field (quote scope) policy) (quote added-paths-in-Git-tree))
      (equal? (fg-field (quote rename-or-copy) policy)
              (quote treat-new-path-as-added))
      (equal? (fg-field (quote failure) policy) (quote fail-closed))
      (equal? (fg-field (quote semantic-admission-from-extension) policy) (quote ()))
      (equal? (fg-field (quote semantic-admission-from-host-guard) policy) (quote ())))))

(def fg-census-valid?
  (lambda (census tracked)
    (let ((rows (fg-field (quote new-foreign-tools) census)))
      (and
        (equal? (fg-field (quote schema) census) (quote foreign-tools-census/1))
        (equal? (fg-field (quote status) census) (quote staged-migration))
        (equal? (fg-field (quote authority) census)
                "knowledge/file-authority-policy.lisp")
        (equal? (fg-field (quote per-file-census) census)
                "knowledge/foreign-tools-census.lisp")
        (equal? (fg-field (quote new-python-without-entry) census) (quote blocked))
        (equal? (fg-field (quote new-python-outside-tools) census) (quote blocked))
        (equal? (fg-field (quote oracle-parity-before-host-retirement) census)
                (quote required))
        (equal? (fg-field (quote new-tool-does-not-own-semantics) census) 1)
        (fg-rows-valid? rows tracked)
        (fg-census-covers-tracked? tracked rows)))))

(def fg-classify
  (lambda (path policy rows)
    (cond
      ((fg-not (fg-path-canonical? path)) (quote blocked-noncanonical-path))
      ((string-prefix? "lib/" path)
        (cond
          ((or (fg-suffix? path ".lisp") (fg-suffix? path ".sens")) (quote allowed))
          (t (quote blocked-important-extension))))
      ((string-prefix? "knowledge/" path)
        (cond
          ((or (fg-suffix? path ".lisp") (fg-suffix? path ".sens")) (quote allowed))
          (t (quote blocked-important-extension))))
      ((string-prefix? "witnesses/" path)
        (cond
          ((or (fg-suffix? path ".lisp") (fg-suffix? path ".sens")) (quote allowed))
          (t (quote blocked-important-extension))))
      ((fg-suffix? path ".py")
        (cond
          ((string-prefix? "tools/" path)
            (cond
              ((fg-foreign-path? path rows) (quote allowed))
              (t (quote blocked-foreign-census))))
          (t (quote blocked-python-outside-tools))))
      ((or
         (and (string-prefix? "tools/" path) (fg-suffix? path ".sh"))
         (and (string-prefix? "scripts/" path) (fg-suffix? path ".sh")))
        (quote blocked-new-shell-tool))
      (t (quote allowed)))))

(def fg-check-added
  (lambda (paths policy rows modes)
    (cond
      ((atom paths) (structural-kind empty-list) 1)
      ((atom paths) (structural-kind pair)
        (let ((path (car paths)))
          (cond
            ((and (fg-mode-required? path) (fg-not (fg-mode-allowed? path modes)))
              (fg-block (quote git-mode) (list path (fg-find-mode path modes))))
            (t
              (let ((verdict (fg-classify path policy rows)))
                (cond
                  ((equal? verdict (quote allowed))
                    (fg-check-added (cdr paths) policy rows modes))
                  (t (fg-block (quote path) (list path verdict)))))))))
      ((atom paths) (structural-kind atom)
        (fg-block (quote input) "added-paths is not a proper list")))))

(def fg-check-tracked
  (lambda (paths rows)
    (cond
      ((atom paths) (structural-kind empty-list) 1)
      ((atom paths) (structural-kind pair)
        (let ((path (car paths)))
          (cond
            ((fg-not (fg-path-canonical? path))
              (fg-block (quote input-path) path))
            ((fg-not (string-prefix? "tools/" path))
              (fg-block (quote tracked-tools-path) path))
            (t (fg-check-tracked (cdr paths) rows)))))
      ((atom paths) (structural-kind atom)
        (fg-block (quote input) "tracked-tools-paths is not a proper list")))))

(def fg-test-equal
  (lambda (label actual expected)
    (cond
      ((equal? actual expected) 1)
      (t (fg-block (quote self-test) label)))))

(def fg-fixture-good
  (quote
    (((path . "tools/fixture.py")
      (independence_status . foreign)
      (owner-issue . "#5397")
      (migration_plan . "Move file policy into executable SENS T5; keep Git facts as untrusted transport and prove hosted positive and negative parity before retiring Python.")))))

(def fg-fixture-bad-status
  (quote
    (((path . "tools/fixture.py")
      (independence_status . local)
      (owner-issue . "#5397")
      (migration_plan . "Move file policy into executable SENS T5; keep Git facts as untrusted transport and prove hosted positive and negative parity before retiring Python.")))))

(def fg-self-test
  (lambda (real-rows)
    (and
      (fg-test-equal "native lisp" (fg-classify "lib/native.lisp" *file-authority-policy* real-rows) (quote allowed))
      (fg-test-equal "native physical SENS" (fg-classify "lib/native.sens" *file-authority-policy* real-rows) (quote allowed))
      (fg-test-equal "new JSON is blocked" (fg-classify "knowledge/new.json" *file-authority-policy* real-rows) (quote blocked-important-extension))
      (fg-test-equal "FASL is not native source" (fg-classify "lib/legacy.lisp.fasl" *file-authority-policy* real-rows) (quote blocked-important-extension))
      (fg-test-equal "witness extension is blocked" (fg-classify "witnesses/new.rs" *file-authority-policy* real-rows) (quote blocked-important-extension))
      (fg-test-equal "Python outside tools is blocked" (fg-classify "scripts/new.py" *file-authority-policy* real-rows) (quote blocked-python-outside-tools))
      (fg-test-equal "unregistered Python is blocked" (fg-classify "tools/unlisted.py" *file-authority-policy* real-rows) (quote blocked-foreign-census))
      (fg-test-equal "registered Python is admitted" (fg-classify "tools/fixture.py" *file-authority-policy* fg-fixture-good) (quote allowed))
      (fg-test-equal "non-foreign census is blocked" (fg-classify "tools/fixture.py" *file-authority-policy* fg-fixture-bad-status) (quote blocked-foreign-census))
      (fg-test-equal "duplicate census row is blocked"
        (fg-classify "tools/fixture.py" *file-authority-policy* (append fg-fixture-good fg-fixture-good))
        (quote blocked-foreign-census))
      (fg-test-equal "regular Git blob is admitted"
        (fg-mode-allowed? "lib/example.sens" (quote (("lib/example.sens" . "100644:blob")))) 1)
      (fg-test-equal "symlink disguised as SENS is blocked"
        (fg-mode-allowed? "lib/example.sens" (quote (("lib/example.sens" . "120000:blob")))) 0)
      (fg-test-equal "gitlink disguised as SENS is blocked"
        (fg-mode-allowed? "lib/example.sens" (quote (("lib/example.sens" . "160000:commit")))) 0)
      (fg-test-equal "missing Git mode is blocked"
        (fg-mode-allowed? "lib/example.sens" (quote ())) 0)
      (fg-test-equal "new shell tooling is blocked" (fg-classify "tools/new.sh" *file-authority-policy* real-rows) (quote blocked-new-shell-tool))
      (fg-test-equal "ordinary docs data is outside this policy" (fg-classify "docs/research.json" *file-authority-policy* real-rows) (quote allowed))
      (fg-test-equal "missing policy is invalid" (fg-policy-valid? (quote ())) 0)
      (fg-test-equal "missing census is invalid" (fg-census-valid? (quote ()) (quote ("tools/fixture.py"))) 0))))

(def fg-block
  (lambda (kind subject)
    (cond
      ((equal? kind (quote policy)) (sens_file_authority_fail_policy_5397 subject))
      ((equal? kind (quote census)) (sens_file_authority_fail_census_5397 subject))
      ((equal? kind (quote input)) (sens_file_authority_fail_input_5397 subject))
      ((equal? kind (quote self-test)) (sens_file_authority_fail_self_test_5397 subject))
      ((equal? kind (quote missing-policy)) (sens_file_authority_fail_missing_policy_5397 subject))
      ((equal? kind (quote missing-census)) (sens_file_authority_fail_missing_census_5397 subject))
      ((equal? kind (quote missing-guard)) (sens_file_authority_fail_missing_guard_5397 subject))
      ((equal? kind (quote input-path)) (sens_file_authority_fail_input_path_5397 subject))
      ((equal? kind (quote tracked-tools-path)) (sens_file_authority_fail_tracked_tools_path_5397 subject))
      ((equal? kind (quote path)) (sens_file_authority_fail_path_5397 subject))
      ((equal? kind (quote git-mode)) (sens_file_authority_fail_git_mode_5405 subject))
      (t (sens_file_authority_fail_unknown_5397 subject)))))

(def fg-require
  (lambda (condition kind subject)
    (cond
      ((equal? condition 1) 1)
      (t (fg-block kind subject)))))

(def fg-run
  (lambda (input)
    (let ((input-ok
            (fg-require
              (and
                (equal? (fg-field (quote schema) input) (quote file-authority-input/1))
                (fg-path-list? (fg-field (quote added-paths) input))
                (fg-mode-rows-valid?
                  (fg-field (quote added-modes) input)
                  (fg-field (quote added-paths) input))
                (fg-paths-have-mode?
                  (fg-field (quote added-paths) input)
                  (fg-field (quote added-modes) input))
                (fg-path-list? (fg-field (quote tracked-tools-paths) input))
                (fg-tools-path-list? (fg-field (quote tracked-tools-paths) input)))
              (quote input) "Git path transport")))
      (let ((policy-ok
              (fg-require
                (fg-policy-valid? *file-authority-policy*)
                (quote policy) "knowledge/file-authority-policy.lisp")))
        (let ((census-ok
                (fg-require
                  (fg-census-valid?
                    *foreign-tools-census*
                    (fg-field (quote tracked-tools-paths) input))
                  (quote census) "knowledge/foreign-tools-census.lisp")))
          (let ((tests-ok
                  (fg-require
                    (fg-self-test (fg-field (quote new-foreign-tools) *foreign-tools-census*))
                    (quote self-test) "positive/negative SENS witnesses")))
            (let ((added-ok
                    (fg-check-added
                      (fg-field (quote added-paths) input)
                      *file-authority-policy*
                      (fg-field (quote new-foreign-tools) *foreign-tools-census*)
                      (fg-field (quote added-modes) input))))
              (let ((tracked-ok
                      (fg-check-tracked
                        (fg-field (quote tracked-tools-paths) input)
                        (fg-field (quote new-foreign-tools) *foreign-tools-census*))))
                (print
                  (list
                    (quote SENS_FILE_AUTHORITY_PASS)
                    (quote new-paths)
                    (length (fg-field (quote added-paths) input))
                    (quote tracked-tool-paths)
                    (length (fg-field (quote tracked-tools-paths) input))))))))))))

(cond
  ((equal? (fg-field (quote policy) *file-authority-source-status*) (quote missing))
    (fg-block (quote missing-policy) "knowledge/file-authority-policy.lisp"))
  ((equal? (fg-field (quote census) *file-authority-source-status*) (quote missing))
    (fg-block (quote missing-census) "knowledge/foreign-tools-census.lisp"))
  ((equal? (fg-field (quote guard) *file-authority-source-status*) (quote missing))
    (fg-block (quote missing-guard) "knowledge/file-authority-guard.lisp"))
  (t (fg-run *file-authority-input*)))
