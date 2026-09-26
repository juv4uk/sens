; #382 — Lisp-owned repository tooling inventory validator.
; Policy and inventory data are Lisp-owned. This checker never defines language semantics.

(00001001 repo-tooling-required-fields
  (00000001 (path kind language role lifecycle callers authority-source
               migration-issue replacement removal-condition)))

(00001001 repo-tooling-kinds
  (00000001 (check generator migration benchmark deploy release helper other)))

(00001001 repo-tooling-languages
  (00000001 (lisp python shell javascript powershell other)))

(00001001 repo-tooling-lifecycles
  (00000001 (active transitional legacy generated-helper archive-candidate)))

(00001001 repo-tooling-violation
  (00001000 (kind detail)
    (list (00000001 repo-tooling-violation) kind detail)))

(00001001 repo-tooling-field-from
  (00001000 (name fields)
    (00000111
      ((00000010 fields) (structural-kind empty-list) (00000001 missing))
      ((00000010 fields) (structural-kind atom) (00000001 missing))
      ((00000010 fields) (structural-kind pair)
       (let ((field (00000101 fields)))
         (00000111
           ((00000010 field) (structural-kind empty-list)
            (repo-tooling-field-from name (00000110 fields)))
           ((00000010 field) (structural-kind atom)
            (repo-tooling-field-from name (00000110 fields)))
           ((00000010 field) (structural-kind pair)
            (00000111
              ((00000011 (00000101 field) name) (identity-relation same) (second field))
              ((00000011 (00000101 field) name) (identity-relation distinct)
               (repo-tooling-field-from name (00000110 fields)))))))))))

(00001001 repo-tooling-field
  (00001000 (name row)
    (00000111
      ((00000010 row) (structural-kind empty-list) (00000001 missing))
      ((00000010 row) (structural-kind atom) (00000001 missing))
      ((00000010 row) (structural-kind pair)
       (repo-tooling-field-from name (00000110 row))))))

(00001001 repo-tooling-verdict-ok-state
  (00001000 (verdict)
    (00000111
      ((equal? verdict (list (00000001 repo-tooling-ok)))
       (structural-relation same)
       (00000001 yes))
      ((equal? verdict (list (00000001 repo-tooling-ok)))
       (structural-relation distinct)
       (00000001 no)))))

(00001001 repo-tooling-field-presence
  (00001000 (value)
    (00000111
      ((00000010 value) (structural-kind empty-list) (00000001 present))
      ((00000010 value) (structural-kind atom)
       (00000111
         ((00000011 value (00000001 missing)) (identity-relation same) (00000001 missing))
         ((00000011 value (00000001 missing)) (identity-relation distinct) (00000001 present))))
      ((00000010 value) (structural-kind pair) (00000001 present)))))

(00001001 repo-tooling-required-fields-verdict
  (00001000 (required row)
    (00000111
      ((00000010 required) (structural-kind empty-list) (list (00000001 repo-tooling-ok)))
      ((00000010 required) (structural-kind atom)
       (repo-tooling-violation (00000001 malformed-required-field-list) required))
      ((00000010 required) (structural-kind pair)
       (00000111
         ((00000011 (repo-tooling-field-presence
                (repo-tooling-field (00000101 required) row))
              (00000001 missing))
          (identity-relation same)
          (repo-tooling-violation (00000001 missing-field) (00000101 required)))
         ((00000011 (repo-tooling-field-presence
                (repo-tooling-field (00000101 required) row))
              (00000001 missing))
          (identity-relation distinct)
          (repo-tooling-required-fields-verdict (00000110 required) row)))))))

(00001001 repo-tooling-row-required-verdict
  (00001000 (row)
    (00000111
      ((00000010 row) (structural-kind empty-list)
       (repo-tooling-violation (00000001 malformed-row) row))
      ((00000010 row) (structural-kind atom)
       (repo-tooling-violation (00000001 malformed-row) row))
      ((00000010 row) (structural-kind pair)
       (00000111
         ((00000011 (00000101 row) (00000001 tool)) (identity-relation same)
          (repo-tooling-required-fields-verdict repo-tooling-required-fields row))
         ((00000011 (00000101 row) (00000001 tool)) (identity-relation distinct)
          (repo-tooling-violation (00000001 malformed-row-kind) (00000101 row))))))))

(00001001 repo-tooling-required-verdict
  (00001000 (rows)
    (00000111
      ((00000010 rows) (structural-kind empty-list) (list (00000001 repo-tooling-ok)))
      ((00000010 rows) (structural-kind atom)
       (repo-tooling-violation (00000001 malformed-inventory-list) rows))
      ((00000010 rows) (structural-kind pair)
       (let ((row-verdict (repo-tooling-row-required-verdict (00000101 rows))))
         (00000111
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 yes))
            (identity-relation same)
            (repo-tooling-required-verdict (00000110 rows)))
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 no))
            (identity-relation same)
            row-verdict)))))))

(00001001 repo-tooling-symbol-admission
  (00001000 (value admitted)
    (00000111
      ((00000010 admitted) (structural-kind empty-list) (00000001 rejected))
      ((00000010 admitted) (structural-kind atom) (00000001 malformed-admitted-set))
      ((00000010 admitted) (structural-kind pair)
       (00000111
         ((00000011 value (00000101 admitted)) (identity-relation same) (00000001 admitted))
         ((00000011 value (00000101 admitted)) (identity-relation distinct)
          (repo-tooling-symbol-admission value (00000110 admitted))))))))

(00001001 repo-tooling-row-enum-verdict
  (00001000 (row)
    (let* ((kind (repo-tooling-field (00000001 kind) row))
           (language (repo-tooling-field (00000001 language) row))
           (lifecycle (repo-tooling-field (00000001 lifecycle) row))
           (kind-state (repo-tooling-symbol-admission kind repo-tooling-kinds)))
      (00000111
        ((00000011 kind-state (00000001 admitted)) (identity-relation same)
         (let ((language-state
                 (repo-tooling-symbol-admission language repo-tooling-languages)))
           (00000111
             ((00000011 language-state (00000001 admitted)) (identity-relation same)
              (let ((lifecycle-state
                      (repo-tooling-symbol-admission lifecycle repo-tooling-lifecycles)))
                (00000111
                  ((00000011 lifecycle-state (00000001 admitted)) (identity-relation same)
                   (list (00000001 repo-tooling-ok)))
                  ((00000011 lifecycle-state (00000001 rejected)) (identity-relation same)
                   (repo-tooling-violation (00000001 invalid-lifecycle) lifecycle))
                  ((00000011 lifecycle-state (00000001 malformed-admitted-set))
                   (identity-relation same)
                   (repo-tooling-violation
                     (00000001 malformed-lifecycle-vocabulary)
                     lifecycle)))))
             ((00000011 language-state (00000001 rejected)) (identity-relation same)
              (repo-tooling-violation (00000001 invalid-language) language))
             ((00000011 language-state (00000001 malformed-admitted-set))
              (identity-relation same)
              (repo-tooling-violation
                (00000001 malformed-language-vocabulary)
                language)))))
        ((00000011 kind-state (00000001 rejected)) (identity-relation same)
         (repo-tooling-violation (00000001 invalid-kind) kind))
        ((00000011 kind-state (00000001 malformed-admitted-set)) (identity-relation same)
         (repo-tooling-violation (00000001 malformed-kind-vocabulary) kind))))))

(00001001 repo-tooling-enum-verdict
  (00001000 (rows)
    (00000111
      ((00000010 rows) (structural-kind empty-list) (list (00000001 repo-tooling-ok)))
      ((00000010 rows) (structural-kind atom)
       (repo-tooling-violation (00000001 malformed-inventory-list) rows))
      ((00000010 rows) (structural-kind pair)
       (let ((row-verdict (repo-tooling-row-enum-verdict (00000101 rows))))
         (00000111
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 yes))
            (identity-relation same)
            (repo-tooling-enum-verdict (00000110 rows)))
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 no))
            (identity-relation same)
            row-verdict)))))))

(00001001 repo-tooling-python-migration-required-state
  (00001000 (row)
    (let ((language (repo-tooling-field (00000001 language) row))
          (lifecycle (repo-tooling-field (00000001 lifecycle) row)))
      (00000111
        ((00000011 language (00000001 python)) (identity-relation same)
         (00000111
           ((00000011 lifecycle (00000001 active)) (identity-relation same) (00000001 required))
           ((00000011 lifecycle (00000001 active)) (identity-relation distinct)
            (00000111
              ((00000011 lifecycle (00000001 transitional))
               (identity-relation same)
               (00000001 required))
              ((00000011 lifecycle (00000001 transitional))
               (identity-relation distinct)
               (00000001 not-required))))))
        ((00000011 language (00000001 python)) (identity-relation distinct)
         (00000001 not-required))))))

(00001001 repo-tooling-migration-owner-state
  (00001000 (owner)
    (00000111
      ((00000010 owner) (structural-kind empty-list) (00000001 missing))
      ((00000010 owner) (structural-kind atom)
       (00000111
         ((00000011 owner (00000001 missing)) (identity-relation same) (00000001 missing))
         ((00000011 owner (00000001 missing)) (identity-relation distinct) (00000001 present))))
      ((00000010 owner) (structural-kind pair) (00000001 present)))))

(00001001 repo-tooling-row-python-migration-verdict
  (00001000 (row)
    (let ((required-state (repo-tooling-python-migration-required-state row)))
      (00000111
        ((00000011 required-state (00000001 not-required)) (identity-relation same)
         (list (00000001 repo-tooling-ok)))
        ((00000011 required-state (00000001 required)) (identity-relation same)
         (let* ((owner (repo-tooling-field (00000001 migration-issue) row))
                (owner-state (repo-tooling-migration-owner-state owner)))
           (00000111
             ((00000011 owner-state (00000001 present)) (identity-relation same)
              (list (00000001 repo-tooling-ok)))
             ((00000011 owner-state (00000001 missing)) (identity-relation same)
              (repo-tooling-violation
                (00000001 python-migration-unowned)
                (repo-tooling-field (00000001 path) row))))))))))

(00001001 repo-tooling-python-migration-verdict
  (00001000 (rows)
    (00000111
      ((00000010 rows) (structural-kind empty-list) (list (00000001 repo-tooling-ok)))
      ((00000010 rows) (structural-kind atom)
       (repo-tooling-violation (00000001 malformed-inventory-list) rows))
      ((00000010 rows) (structural-kind pair)
       (let ((row-verdict (repo-tooling-row-python-migration-verdict (00000101 rows))))
         (00000111
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 yes))
            (identity-relation same)
            (repo-tooling-python-migration-verdict (00000110 rows)))
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 no))
            (identity-relation same)
            row-verdict)))))))

(00001001 repo-tooling-find-row-by-path
  (00001000 (path rows)
    (00000111
      ((00000010 rows) (structural-kind empty-list) (00000001 ()))
      ((00000010 rows) (structural-kind atom) (00000001 ()))
      ((00000010 rows) (structural-kind pair)
       (let ((row (00000101 rows)))
         (00000111
           ((equal? path (repo-tooling-field (00000001 path) row))
            (structural-relation same)
            row)
           ((equal? path (repo-tooling-field (00000001 path) row))
            (structural-relation distinct)
            (repo-tooling-find-row-by-path path (00000110 rows)))))))))

(00001001 repo-tooling-duplicate-path-verdict
  (00001000 (rows)
    (00000111
      ((00000010 rows) (structural-kind empty-list) (list (00000001 repo-tooling-ok)))
      ((00000010 rows) (structural-kind atom)
       (repo-tooling-violation (00000001 malformed-inventory-list) rows))
      ((00000010 rows) (structural-kind pair)
       (let* ((row (00000101 rows))
              (path (repo-tooling-field (00000001 path) row))
              (found (repo-tooling-find-row-by-path path (00000110 rows))))
         (00000111
           ((00000010 found) (structural-kind empty-list)
            (repo-tooling-duplicate-path-verdict (00000110 rows)))
           ((00000010 found) (structural-kind atom)
            (repo-tooling-violation (00000001 malformed-row) path))
           ((00000010 found) (structural-kind pair)
            (repo-tooling-violation (00000001 duplicate-path) path))))))))

(00001001 repo-tooling-observed-path-state
  (00001000 (path observed)
    (00000111
      ((00000010 observed) (structural-kind empty-list) (00000001 absent))
      ((00000010 observed) (structural-kind atom) (00000001 malformed))
      ((00000010 observed) (structural-kind pair)
       (let ((observed-path (string-append "scripts/" (00000101 observed))))
         (00000111
           ((equal? path observed-path) (structural-relation same) (00000001 present))
           ((equal? path observed-path) (structural-relation distinct)
            (repo-tooling-observed-path-state path (00000110 observed)))))))))

(00001001 repo-tooling-stale-path-verdict
  (00001000 (rows observed)
    (00000111
      ((00000010 rows) (structural-kind empty-list) (list (00000001 repo-tooling-ok)))
      ((00000010 rows) (structural-kind atom)
       (repo-tooling-violation (00000001 malformed-inventory-list) rows))
      ((00000010 rows) (structural-kind pair)
       (let* ((row (00000101 rows))
              (path (repo-tooling-field (00000001 path) row))
              (state (repo-tooling-observed-path-state path observed)))
         (00000111
           ((00000011 state (00000001 present)) (identity-relation same)
            (repo-tooling-stale-path-verdict (00000110 rows) observed))
           ((00000011 state (00000001 absent)) (identity-relation same)
            (repo-tooling-violation (00000001 stale-path) path))
           ((00000011 state (00000001 malformed)) (identity-relation same)
            (repo-tooling-violation (00000001 malformed-observed-list) observed))))))))

(00001001 repo-tooling-observed-coverage-verdict
  (00001000 (rows observed)
    (00000111
      ((00000010 observed) (structural-kind empty-list) (list (00000001 repo-tooling-ok)))
      ((00000010 observed) (structural-kind atom)
       (repo-tooling-violation (00000001 malformed-observed-list) observed))
      ((00000010 observed) (structural-kind pair)
       (let* ((name (00000101 observed))
              (path (string-append "scripts/" name))
              (found (repo-tooling-find-row-by-path path rows)))
         (00000111
           ((00000010 found) (structural-kind empty-list)
            (repo-tooling-violation (00000001 unregistered-tool) path))
           ((00000010 found) (structural-kind atom)
            (repo-tooling-violation (00000001 malformed-row) path))
           ((00000010 found) (structural-kind pair)
            (repo-tooling-observed-coverage-verdict rows (00000110 observed)))))))))

(00001001 repo-tooling-verdict-after-required
  (00001000 (rows observed)
    (let ((enum-verdict (repo-tooling-enum-verdict rows)))
      (00000111
        ((00000011 (repo-tooling-verdict-ok-state enum-verdict) (00000001 yes))
         (identity-relation same)
         (let ((migration-verdict (repo-tooling-python-migration-verdict rows)))
           (00000111
             ((00000011 (repo-tooling-verdict-ok-state migration-verdict) (00000001 yes))
              (identity-relation same)
              (let ((duplicate-verdict (repo-tooling-duplicate-path-verdict rows)))
                (00000111
                  ((00000011 (repo-tooling-verdict-ok-state duplicate-verdict) (00000001 yes))
                   (identity-relation same)
                   (let ((stale-verdict (repo-tooling-stale-path-verdict rows observed)))
                     (00000111
                       ((00000011 (repo-tooling-verdict-ok-state stale-verdict) (00000001 yes))
                        (identity-relation same)
                        (repo-tooling-observed-coverage-verdict rows observed))
                       ((00000011 (repo-tooling-verdict-ok-state stale-verdict) (00000001 no))
                        (identity-relation same)
                        stale-verdict))))
                  ((00000011 (repo-tooling-verdict-ok-state duplicate-verdict) (00000001 no))
                   (identity-relation same)
                   duplicate-verdict))))
             ((00000011 (repo-tooling-verdict-ok-state migration-verdict) (00000001 no))
              (identity-relation same)
              migration-verdict))))
        ((00000011 (repo-tooling-verdict-ok-state enum-verdict) (00000001 no))
         (identity-relation same)
         enum-verdict)))))

(00001001 repo-tooling-verdict
  (00001000 (rows observed)
    (let ((required-verdict (repo-tooling-required-verdict rows)))
      (00000111
        ((00000011 (repo-tooling-verdict-ok-state required-verdict) (00000001 yes))
         (identity-relation same)
         (repo-tooling-verdict-after-required rows observed))
        ((00000011 (repo-tooling-verdict-ok-state required-verdict) (00000001 no))
         (identity-relation same)
         required-verdict)))))

; ----- pure negative witnesses -----

(00001001 repo-tooling-sample-row-a
  (00000001
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

(00001001 repo-tooling-sample-row-c
  (00000001
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

(00001001 repo-tooling-sample-bad-kind
  (00000001
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

(00001001 repo-tooling-sample-bad-language
  (00000001
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

(00001001 repo-tooling-sample-bad-lifecycle
  (00000001
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

(00001001 repo-tooling-sample-python-unowned
  (00000001
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

(00001001 repo-tooling-sample-missing-role
  (00000001
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

(00001001 repo-tooling-assert-verdict
  (00001000 (actual expected)
    (00000111
      ((equal? actual expected) (structural-relation same)
       (list (00000001 repo-tooling-selftest-ok)))
      ((equal? actual expected) (structural-relation distinct)
       (let ((shown
               (print
                 (list
                   (00000001 repo-tooling-selftest-failed)
                   actual
                   expected))))
         (00000101 (00000001 ())))))))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (list repo-tooling-sample-row-a) (00000001 ("a.lisp" "b.lisp")))
  (00000001 (repo-tooling-violation unregistered-tool "scripts/b.lisp")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict
    (list repo-tooling-sample-row-a repo-tooling-sample-row-a)
    (00000001 ("a.lisp")))
  (00000001 (repo-tooling-violation duplicate-path "scripts/a.lisp")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict
    (list repo-tooling-sample-row-a repo-tooling-sample-row-c)
    (00000001 ("a.lisp")))
  (00000001 (repo-tooling-violation stale-path "scripts/c.lisp")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (list repo-tooling-sample-bad-kind) (00000001 ("a.lisp")))
  (00000001 (repo-tooling-violation invalid-kind mystery-kind)))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (list repo-tooling-sample-bad-language) (00000001 ("a.lisp")))
  (00000001 (repo-tooling-violation invalid-language mystery-language)))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (list repo-tooling-sample-bad-lifecycle) (00000001 ("a.lisp")))
  (00000001 (repo-tooling-violation invalid-lifecycle parity-green)))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (list repo-tooling-sample-python-unowned) (00000001 ("a.py")))
  (00000001 (repo-tooling-violation python-migration-unowned "scripts/a.py")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (list repo-tooling-sample-missing-role) (00000001 ("a.lisp")))
  (00000001 (repo-tooling-violation missing-field role)))

; ----- real repository observation -----

(00001001 repo-tooling-tool-rows
  (00001000 (forms)
    (00000111
      ((00000010 forms) (structural-kind empty-list) (00000001 ()))
      ((00000010 forms) (structural-kind atom) (00000001 ()))
      ((00000010 forms) (structural-kind pair)
       (let ((form (00000101 forms)))
         (00000111
           ((00000010 form) (structural-kind empty-list)
            (repo-tooling-tool-rows (00000110 forms)))
           ((00000010 form) (structural-kind atom)
            (repo-tooling-tool-rows (00000110 forms)))
           ((00000010 form) (structural-kind pair)
            (00000111
              ((00000011 (00000101 form) (00000001 tool)) (identity-relation same)
               (00000100 form (repo-tooling-tool-rows (00000110 forms))))
              ((00000011 (00000101 form) (00000001 tool)) (identity-relation distinct)
               (repo-tooling-tool-rows (00000110 forms)))))))))))

(00001001 repo-tooling-observed-scripts
  (00001000 (entries)
    (00000111
      ((00000010 entries) (structural-kind empty-list) (00000001 ()))
      ((00000010 entries) (structural-kind atom) (00000001 ()))
      ((00000010 entries) (structural-kind pair)
       (let ((name (00000101 entries)))
         (00000111
           ((equal? name "tests") (structural-relation same)
            (repo-tooling-observed-scripts (00000110 entries)))
           ((equal? name "tests") (structural-relation distinct)
            (00000100 name (repo-tooling-observed-scripts (00000110 entries))))))))))

(00001001 repo-tooling-live-forms
  (read-all (read-file "knowledge/repo-tooling-inventory.lisp")))

(00001001 repo-tooling-live-rows
  (repo-tooling-tool-rows repo-tooling-live-forms))

(00001001 repo-tooling-live-observed
  (repo-tooling-observed-scripts (read-dir "scripts")))

(00001001 repo-tooling-live-verdict
  (repo-tooling-verdict repo-tooling-live-rows repo-tooling-live-observed))

(print repo-tooling-live-verdict)

(repo-tooling-assert-verdict
  repo-tooling-live-verdict
  (00000001 (repo-tooling-ok)))
