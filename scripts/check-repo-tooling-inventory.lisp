; #382 — Lisp-owned repository tooling inventory validator.
; Policy and inventory data are Lisp-owned. This checker never defines language semantics.

(def repo-tooling-required-fields
  (quote (path kind language role lifecycle callers authority-source
               migration-issue replacement removal-condition)))

(def repo-tooling-kinds
  (quote (check generator migration benchmark deploy release helper other)))

(def repo-tooling-languages
  (quote (lisp python shell javascript powershell other)))

(def repo-tooling-lifecycles
  (quote (active transitional legacy generated-helper archive-candidate)))

(def repo-tooling-violation
  (lambda (kind detail)
    (list (quote repo-tooling-violation) kind detail)))

(def repo-tooling-field-from
  (lambda (name fields)
    (cond
      ((atom? fields) () (quote missing))
      ((atom? fields) (1) (quote missing))
      ((atom? fields) (0)
       (let ((field (car fields)))
         (cond
           ((atom? field) ()
            (repo-tooling-field-from name (cdr fields)))
           ((atom? field) (1)
            (repo-tooling-field-from name (cdr fields)))
           ((atom? field) (0)
            (cond
              ((eq? (car field) name) (1) (second field))
              ((eq? (car field) name) (0)
               (repo-tooling-field-from name (cdr fields)))))))))))

(def repo-tooling-field
  (lambda (name row)
    (cond
      ((atom? row) () (quote missing))
      ((atom? row) (1) (quote missing))
      ((atom? row) (0)
       (repo-tooling-field-from name (cdr row))))))

(def repo-tooling-verdict-ok-state
  (lambda (verdict)
    (cond
      ((equal? verdict (list (quote repo-tooling-ok)))
       (1)
       (quote yes))
      ((equal? verdict (list (quote repo-tooling-ok)))
       (0)
       (quote no)))))

(def repo-tooling-field-presence
  (lambda (value)
    (cond
      ((atom? value) () (quote present))
      ((atom? value) (1)
       (cond
         ((eq? value (quote missing)) (1) (quote missing))
         ((eq? value (quote missing)) (0) (quote present))))
      ((atom? value) (0) (quote present)))))

(def repo-tooling-required-fields-verdict
  (lambda (required row)
    (cond
      ((atom? required) () (list (quote repo-tooling-ok)))
      ((atom? required) (1)
       (repo-tooling-violation (quote malformed-required-field-list) required))
      ((atom? required) (0)
       (cond
         ((eq? (repo-tooling-field-presence
                (repo-tooling-field (car required) row))
              (quote missing))
          (1)
          (repo-tooling-violation (quote missing-field) (car required)))
         ((eq? (repo-tooling-field-presence
                (repo-tooling-field (car required) row))
              (quote missing))
          (0)
          (repo-tooling-required-fields-verdict (cdr required) row)))))))

(def repo-tooling-row-required-verdict
  (lambda (row)
    (cond
      ((atom? row) ()
       (repo-tooling-violation (quote malformed-row) row))
      ((atom? row) (1)
       (repo-tooling-violation (quote malformed-row) row))
      ((atom? row) (0)
       (cond
         ((eq? (car row) (quote tool)) (1)
          (repo-tooling-required-fields-verdict repo-tooling-required-fields row))
         ((eq? (car row) (quote tool)) (0)
          (repo-tooling-violation (quote malformed-row-kind) (car row))))))))

(def repo-tooling-required-verdict
  (lambda (rows)
    (cond
      ((atom? rows) () (list (quote repo-tooling-ok)))
      ((atom? rows) (1)
       (repo-tooling-violation (quote malformed-inventory-list) rows))
      ((atom? rows) (0)
       (let ((row-verdict (repo-tooling-row-required-verdict (car rows))))
         (cond
           ((eq? (repo-tooling-verdict-ok-state row-verdict) (quote yes))
            (1)
            (repo-tooling-required-verdict (cdr rows)))
           ((eq? (repo-tooling-verdict-ok-state row-verdict) (quote no))
            (1)
            row-verdict)))))))

(def repo-tooling-symbol-admission
  (lambda (value admitted)
    (cond
      ((atom? admitted) () (quote rejected))
      ((atom? admitted) (1) (quote malformed-admitted-set))
      ((atom? admitted) (0)
       (cond
         ((eq? value (car admitted)) (1) (quote admitted))
         ((eq? value (car admitted)) (0)
          (repo-tooling-symbol-admission value (cdr admitted))))))))

(def repo-tooling-row-enum-verdict
  (lambda (row)
    (let* ((kind (repo-tooling-field (quote kind) row))
           (language (repo-tooling-field (quote language) row))
           (lifecycle (repo-tooling-field (quote lifecycle) row))
           (kind-state (repo-tooling-symbol-admission kind repo-tooling-kinds)))
      (cond
        ((eq? kind-state (quote admitted)) (1)
         (let ((language-state
                 (repo-tooling-symbol-admission language repo-tooling-languages)))
           (cond
             ((eq? language-state (quote admitted)) (1)
              (let ((lifecycle-state
                      (repo-tooling-symbol-admission lifecycle repo-tooling-lifecycles)))
                (cond
                  ((eq? lifecycle-state (quote admitted)) (1)
                   (list (quote repo-tooling-ok)))
                  ((eq? lifecycle-state (quote rejected)) (1)
                   (repo-tooling-violation (quote invalid-lifecycle) lifecycle))
                  ((eq? lifecycle-state (quote malformed-admitted-set))
                   (1)
                   (repo-tooling-violation
                     (quote malformed-lifecycle-vocabulary)
                     lifecycle)))))
             ((eq? language-state (quote rejected)) (1)
              (repo-tooling-violation (quote invalid-language) language))
             ((eq? language-state (quote malformed-admitted-set))
              (1)
              (repo-tooling-violation
                (quote malformed-language-vocabulary)
                language)))))
        ((eq? kind-state (quote rejected)) (1)
         (repo-tooling-violation (quote invalid-kind) kind))
        ((eq? kind-state (quote malformed-admitted-set)) (1)
         (repo-tooling-violation (quote malformed-kind-vocabulary) kind))))))

(def repo-tooling-enum-verdict
  (lambda (rows)
    (cond
      ((atom? rows) () (list (quote repo-tooling-ok)))
      ((atom? rows) (1)
       (repo-tooling-violation (quote malformed-inventory-list) rows))
      ((atom? rows) (0)
       (let ((row-verdict (repo-tooling-row-enum-verdict (car rows))))
         (cond
           ((eq? (repo-tooling-verdict-ok-state row-verdict) (quote yes))
            (1)
            (repo-tooling-enum-verdict (cdr rows)))
           ((eq? (repo-tooling-verdict-ok-state row-verdict) (quote no))
            (1)
            row-verdict)))))))

(def repo-tooling-python-migration-required-state
  (lambda (row)
    (let ((language (repo-tooling-field (quote language) row))
          (lifecycle (repo-tooling-field (quote lifecycle) row)))
      (cond
        ((eq? language (quote python)) (1)
         (cond
           ((eq? lifecycle (quote active)) (1) (quote required))
           ((eq? lifecycle (quote active)) (0)
            (cond
              ((eq? lifecycle (quote transitional))
               (1)
               (quote required))
              ((eq? lifecycle (quote transitional))
               (0)
               (quote not-required))))))
        ((eq? language (quote python)) (0)
         (quote not-required))))))

(def repo-tooling-migration-owner-state
  (lambda (owner)
    (cond
      ((atom? owner) () (quote missing))
      ((atom? owner) (1)
       (cond
         ((eq? owner (quote missing)) (1) (quote missing))
         ((eq? owner (quote missing)) (0) (quote present))))
      ((atom? owner) (0) (quote present)))))

(def repo-tooling-row-python-migration-verdict
  (lambda (row)
    (let ((required-state (repo-tooling-python-migration-required-state row)))
      (cond
        ((eq? required-state (quote not-required)) (1)
         (list (quote repo-tooling-ok)))
        ((eq? required-state (quote required)) (1)
         (let* ((owner (repo-tooling-field (quote migration-issue) row))
                (owner-state (repo-tooling-migration-owner-state owner)))
           (cond
             ((eq? owner-state (quote present)) (1)
              (list (quote repo-tooling-ok)))
             ((eq? owner-state (quote missing)) (1)
              (repo-tooling-violation
                (quote python-migration-unowned)
                (repo-tooling-field (quote path) row))))))))))

(def repo-tooling-python-migration-verdict
  (lambda (rows)
    (cond
      ((atom? rows) () (list (quote repo-tooling-ok)))
      ((atom? rows) (1)
       (repo-tooling-violation (quote malformed-inventory-list) rows))
      ((atom? rows) (0)
       (let ((row-verdict (repo-tooling-row-python-migration-verdict (car rows))))
         (cond
           ((eq? (repo-tooling-verdict-ok-state row-verdict) (quote yes))
            (1)
            (repo-tooling-python-migration-verdict (cdr rows)))
           ((eq? (repo-tooling-verdict-ok-state row-verdict) (quote no))
            (1)
            row-verdict)))))))

(def repo-tooling-find-row-by-path
  (lambda (path rows)
    (cond
      ((atom? rows) () (quote ()))
      ((atom? rows) (1) (quote ()))
      ((atom? rows) (0)
       (let ((row (car rows)))
         (cond
           ((equal? path (repo-tooling-field (quote path) row))
            (1)
            row)
           ((equal? path (repo-tooling-field (quote path) row))
            (0)
            (repo-tooling-find-row-by-path path (cdr rows)))))))))

(def repo-tooling-duplicate-path-verdict
  (lambda (rows)
    (cond
      ((atom? rows) () (list (quote repo-tooling-ok)))
      ((atom? rows) (1)
       (repo-tooling-violation (quote malformed-inventory-list) rows))
      ((atom? rows) (0)
       (let* ((row (car rows))
              (path (repo-tooling-field (quote path) row))
              (found (repo-tooling-find-row-by-path path (cdr rows))))
         (cond
           ((atom? found) ()
            (repo-tooling-duplicate-path-verdict (cdr rows)))
           ((atom? found) (1)
            (repo-tooling-violation (quote malformed-row) path))
           ((atom? found) (0)
            (repo-tooling-violation (quote duplicate-path) path))))))))

(def repo-tooling-observed-path-state
  (lambda (path observed)
    (cond
      ((atom? observed) () (quote absent))
      ((atom? observed) (1) (quote malformed))
      ((atom? observed) (0)
       (let ((observed-path (string-append "scripts/" (car observed))))
         (cond
           ((equal? path observed-path) (1) (quote present))
           ((equal? path observed-path) (0)
            (repo-tooling-observed-path-state path (cdr observed)))))))))

(def repo-tooling-stale-path-verdict
  (lambda (rows observed)
    (cond
      ((atom? rows) () (list (quote repo-tooling-ok)))
      ((atom? rows) (1)
       (repo-tooling-violation (quote malformed-inventory-list) rows))
      ((atom? rows) (0)
       (let* ((row (car rows))
              (path (repo-tooling-field (quote path) row))
              (state (repo-tooling-observed-path-state path observed)))
         (cond
           ((eq? state (quote present)) (1)
            (repo-tooling-stale-path-verdict (cdr rows) observed))
           ((eq? state (quote absent)) (1)
            (repo-tooling-violation (quote stale-path) path))
           ((eq? state (quote malformed)) (1)
            (repo-tooling-violation (quote malformed-observed-list) observed))))))))

(def repo-tooling-observed-coverage-verdict
  (lambda (rows observed)
    (cond
      ((atom? observed) () (list (quote repo-tooling-ok)))
      ((atom? observed) (1)
       (repo-tooling-violation (quote malformed-observed-list) observed))
      ((atom? observed) (0)
       (let* ((name (car observed))
              (path (string-append "scripts/" name))
              (found (repo-tooling-find-row-by-path path rows)))
         (cond
           ((atom? found) ()
            (repo-tooling-violation (quote unregistered-tool) path))
           ((atom? found) (1)
            (repo-tooling-violation (quote malformed-row) path))
           ((atom? found) (0)
            (repo-tooling-observed-coverage-verdict rows (cdr observed)))))))))

(def repo-tooling-verdict-after-required
  (lambda (rows observed)
    (let ((enum-verdict (repo-tooling-enum-verdict rows)))
      (cond
        ((eq? (repo-tooling-verdict-ok-state enum-verdict) (quote yes))
         (1)
         (let ((migration-verdict (repo-tooling-python-migration-verdict rows)))
           (cond
             ((eq? (repo-tooling-verdict-ok-state migration-verdict) (quote yes))
              (1)
              (let ((duplicate-verdict (repo-tooling-duplicate-path-verdict rows)))
                (cond
                  ((eq? (repo-tooling-verdict-ok-state duplicate-verdict) (quote yes))
                   (1)
                   (let ((stale-verdict (repo-tooling-stale-path-verdict rows observed)))
                     (cond
                       ((eq? (repo-tooling-verdict-ok-state stale-verdict) (quote yes))
                        (1)
                        (repo-tooling-observed-coverage-verdict rows observed))
                       ((eq? (repo-tooling-verdict-ok-state stale-verdict) (quote no))
                        (1)
                        stale-verdict))))
                  ((eq? (repo-tooling-verdict-ok-state duplicate-verdict) (quote no))
                   (1)
                   duplicate-verdict))))
             ((eq? (repo-tooling-verdict-ok-state migration-verdict) (quote no))
              (1)
              migration-verdict))))
        ((eq? (repo-tooling-verdict-ok-state enum-verdict) (quote no))
         (1)
         enum-verdict)))))

(def repo-tooling-verdict
  (lambda (rows observed)
    (let ((required-verdict (repo-tooling-required-verdict rows)))
      (cond
        ((eq? (repo-tooling-verdict-ok-state required-verdict) (quote yes))
         (1)
         (repo-tooling-verdict-after-required rows observed))
        ((eq? (repo-tooling-verdict-ok-state required-verdict) (quote no))
         (1)
         required-verdict)))))

; ----- pure negative witnesses -----

(def repo-tooling-sample-row-a
  (quote
    (tool
      (path "scripts/a.lisp")
      (kind check)
      (language lisp)
      (role sample)
      (lifecycle active)
      (callers ())
      (authority-source (issue 382))
      (migration-issue ())
      (replacement ())
      (removal-condition ()))))

(def repo-tooling-sample-row-c
  (quote
    (tool
      (path "scripts/c.lisp")
      (kind helper)
      (language lisp)
      (role stale-sample)
      (lifecycle active)
      (callers ())
      (authority-source (issue 382))
      (migration-issue ())
      (replacement ())
      (removal-condition ()))))

(def repo-tooling-sample-bad-kind
  (quote
    (tool
      (path "scripts/a.lisp")
      (kind mystery-kind)
      (language lisp)
      (role sample)
      (lifecycle active)
      (callers ())
      (authority-source (issue 382))
      (migration-issue ())
      (replacement ())
      (removal-condition ()))))

(def repo-tooling-sample-bad-language
  (quote
    (tool
      (path "scripts/a.lisp")
      (kind check)
      (language mystery-language)
      (role sample)
      (lifecycle active)
      (callers ())
      (authority-source (issue 382))
      (migration-issue ())
      (replacement ())
      (removal-condition ()))))

(def repo-tooling-sample-bad-lifecycle
  (quote
    (tool
      (path "scripts/a.lisp")
      (kind check)
      (language lisp)
      (role sample)
      (lifecycle parity-green)
      (callers ())
      (authority-source (issue 382))
      (migration-issue ())
      (replacement ())
      (removal-condition ()))))

(def repo-tooling-sample-python-unowned
  (quote
    (tool
      (path "scripts/a.py")
      (kind check)
      (language python)
      (role python-without-migration-owner)
      (lifecycle transitional)
      (callers ())
      (authority-source (issue 382))
      (migration-issue ())
      (replacement ())
      (removal-condition migration-issue-complete-and-callers-switched))))

(def repo-tooling-sample-missing-role
  (quote
    (tool
      (path "scripts/a.lisp")
      (kind check)
      (language lisp)
      (lifecycle active)
      (callers ())
      (authority-source (issue 382))
      (migration-issue ())
      (replacement ())
      (removal-condition ()))))

(def repo-tooling-assert-verdict
  (lambda (actual expected)
    (cond
      ((equal? actual expected) (1)
       (list (quote repo-tooling-selftest-ok)))
      ((equal? actual expected) (0)
       (let ((shown
               (print
                 (list
                   (quote repo-tooling-selftest-failed)
                   actual
                   expected))))
         (car (quote ())))))))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (list repo-tooling-sample-row-a) (quote ("a.lisp" "b.lisp")))
  (quote (repo-tooling-violation unregistered-tool "scripts/b.lisp")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict
    (list repo-tooling-sample-row-a repo-tooling-sample-row-a)
    (quote ("a.lisp")))
  (quote (repo-tooling-violation duplicate-path "scripts/a.lisp")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict
    (list repo-tooling-sample-row-a repo-tooling-sample-row-c)
    (quote ("a.lisp")))
  (quote (repo-tooling-violation stale-path "scripts/c.lisp")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (list repo-tooling-sample-bad-kind) (quote ("a.lisp")))
  (quote (repo-tooling-violation invalid-kind mystery-kind)))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (list repo-tooling-sample-bad-language) (quote ("a.lisp")))
  (quote (repo-tooling-violation invalid-language mystery-language)))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (list repo-tooling-sample-bad-lifecycle) (quote ("a.lisp")))
  (quote (repo-tooling-violation invalid-lifecycle parity-green)))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (list repo-tooling-sample-python-unowned) (quote ("a.py")))
  (quote (repo-tooling-violation python-migration-unowned "scripts/a.py")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (list repo-tooling-sample-missing-role) (quote ("a.lisp")))
  (quote (repo-tooling-violation missing-field role)))

; ----- real repository observation -----

(def repo-tooling-tool-rows
  (lambda (forms)
    (cond
      ((atom? forms) () (quote ()))
      ((atom? forms) (1) (quote ()))
      ((atom? forms) (0)
       (let ((form (car forms)))
         (cond
           ((atom? form) ()
            (repo-tooling-tool-rows (cdr forms)))
           ((atom? form) (1)
            (repo-tooling-tool-rows (cdr forms)))
           ((atom? form) (0)
            (cond
              ((eq? (car form) (quote tool)) (1)
               (cons form (repo-tooling-tool-rows (cdr forms))))
              ((eq? (car form) (quote tool)) (0)
               (repo-tooling-tool-rows (cdr forms)))))))))))

(def repo-tooling-observed-scripts
  (lambda (entries)
    (cond
      ((atom? entries) () (quote ()))
      ((atom? entries) (1) (quote ()))
      ((atom? entries) (0)
       (let ((name (car entries)))
         (cond
           ((equal? name "tests") (1)
            (repo-tooling-observed-scripts (cdr entries)))
           ((equal? name "tests") (0)
            (cons name (repo-tooling-observed-scripts (cdr entries))))))))))

(def repo-tooling-live-forms
  (read-all (read-file "knowledge/repo-tooling-inventory.lisp")))

(def repo-tooling-live-rows
  (repo-tooling-tool-rows repo-tooling-live-forms))

(def repo-tooling-live-observed
  (repo-tooling-observed-scripts (read-dir "scripts")))

(def repo-tooling-live-verdict
  (repo-tooling-verdict repo-tooling-live-rows repo-tooling-live-observed))

(print repo-tooling-live-verdict)

(repo-tooling-assert-verdict
  repo-tooling-live-verdict
  (quote (repo-tooling-ok)))
