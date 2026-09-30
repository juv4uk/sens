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
    (00100111 (00000001 repo-tooling-violation) kind detail)))

; Local structural predicates preserve the retired three-state ATOM
; classification without reintroducing generic truthiness.
(00001001 repo-tooling-predicate-yes
  (00001000 ()
    (00000010 (00000001 ()))))

(00001001 repo-tooling-predicate-no
  (00001000 ()
    (00000010 (00000001 (00000000)))))

(00001001 repo-tooling-predicate-no?
  (00001000 (value)
    (00000011 value (repo-tooling-predicate-no))))

(00001001 repo-tooling-empty-list?
  (00001000 (value)
    (00100010 value (00000001 ()))))

(00001001 repo-tooling-nonempty-atom?
  (00001000 (value)
    (00000111
      ((00000010 value)
       (repo-tooling-predicate-no? (repo-tooling-empty-list? value)))
      ((repo-tooling-predicate-yes)
       (repo-tooling-predicate-no)))))

(00001001 repo-tooling-pair?
  (00001000 (value)
    (00000111
      ((00000010 value)
       (repo-tooling-predicate-no))
      ((repo-tooling-predicate-yes)
       (repo-tooling-predicate-yes)))))

(00001001 repo-tooling-field-from
  (00001000 (name fields)
    (00000111
      ((repo-tooling-empty-list? fields) (00000001 missing))
      ((repo-tooling-nonempty-atom? fields) (00000001 missing))
      ((repo-tooling-pair? fields)
       (10011100 ((field (00000101 fields)))
         (00000111
           ((repo-tooling-empty-list? field)
            (repo-tooling-field-from name (00000110 fields)))
           ((repo-tooling-nonempty-atom? field)
            (repo-tooling-field-from name (00000110 fields)))
           ((repo-tooling-pair? field)
            (00000111
              ((00000011 (00000101 field) name) (00101111 field))
              ((repo-tooling-predicate-no? (00000011 (00000101 field) name))
               (repo-tooling-field-from name (00000110 fields)))))))))))

(00001001 repo-tooling-field
  (00001000 (name row)
    (00000111
      ((repo-tooling-empty-list? row) (00000001 missing))
      ((repo-tooling-nonempty-atom? row) (00000001 missing))
      ((repo-tooling-pair? row)
       (repo-tooling-field-from name (00000110 row))))))

(00001001 repo-tooling-verdict-ok-state
  (00001000 (verdict)
    (00000111
      ((00100010 verdict (00100111 (00000001 repo-tooling-ok)))
       (00000001 yes))
      ((repo-tooling-predicate-no? (00100010 verdict (00100111 (00000001 repo-tooling-ok))))
       (00000001 no)))))

(00001001 repo-tooling-field-presence
  (00001000 (value)
    (00000111
      ((repo-tooling-empty-list? value) (00000001 present))
      ((repo-tooling-nonempty-atom? value)
       (00000111
         ((00000011 value (00000001 missing)) (00000001 missing))
         ((repo-tooling-predicate-no? (00000011 value (00000001 missing))) (00000001 present))))
      ((repo-tooling-pair? value) (00000001 present)))))

(00001001 repo-tooling-required-fields-verdict
  (00001000 (required row)
    (00000111
      ((repo-tooling-empty-list? required) (00100111 (00000001 repo-tooling-ok)))
      ((repo-tooling-nonempty-atom? required)
       (repo-tooling-violation (00000001 malformed-required-field-list) required))
      ((repo-tooling-pair? required)
       (00000111
         ((00000011 (repo-tooling-field-presence
                (repo-tooling-field (00000101 required) row))
              (00000001 missing))
          (repo-tooling-violation (00000001 missing-field) (00000101 required)))
         ((repo-tooling-predicate-no? (00000011 (repo-tooling-field-presence
                (repo-tooling-field (00000101 required) row))
              (00000001 missing)))
          (repo-tooling-required-fields-verdict (00000110 required) row)))))))

(00001001 repo-tooling-row-required-verdict
  (00001000 (row)
    (00000111
      ((repo-tooling-empty-list? row)
       (repo-tooling-violation (00000001 malformed-row) row))
      ((repo-tooling-nonempty-atom? row)
       (repo-tooling-violation (00000001 malformed-row) row))
      ((repo-tooling-pair? row)
       (00000111
         ((00000011 (00000101 row) (00000001 tool))
          (repo-tooling-required-fields-verdict repo-tooling-required-fields row))
         ((repo-tooling-predicate-no? (00000011 (00000101 row) (00000001 tool)))
          (repo-tooling-violation (00000001 malformed-row-kind) (00000101 row))))))))

(00001001 repo-tooling-required-verdict
  (00001000 (rows)
    (00000111
      ((repo-tooling-empty-list? rows) (00100111 (00000001 repo-tooling-ok)))
      ((repo-tooling-nonempty-atom? rows)
       (repo-tooling-violation (00000001 malformed-inventory-list) rows))
      ((repo-tooling-pair? rows)
       (10011100 ((row-verdict (repo-tooling-row-required-verdict (00000101 rows))))
         (00000111
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 yes))
            (repo-tooling-required-verdict (00000110 rows)))
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 no))
            row-verdict)))))))

(00001001 repo-tooling-symbol-admission
  (00001000 (value admitted)
    (00000111
      ((repo-tooling-empty-list? admitted) (00000001 rejected))
      ((repo-tooling-nonempty-atom? admitted) (00000001 malformed-admitted-set))
      ((repo-tooling-pair? admitted)
       (00000111
         ((00000011 value (00000101 admitted)) (00000001 admitted))
         ((repo-tooling-predicate-no? (00000011 value (00000101 admitted)))
          (repo-tooling-symbol-admission value (00000110 admitted))))))))

(00001001 repo-tooling-row-enum-verdict
  (00001000 (row)
    (10011101 ((kind (repo-tooling-field (00000001 kind) row))
           (language (repo-tooling-field (00000001 language) row))
           (lifecycle (repo-tooling-field (00000001 lifecycle) row))
           (kind-state (repo-tooling-symbol-admission kind repo-tooling-kinds)))
      (00000111
        ((00000011 kind-state (00000001 admitted))
         (10011100 ((language-state
                 (repo-tooling-symbol-admission language repo-tooling-languages)))
           (00000111
             ((00000011 language-state (00000001 admitted))
              (10011100 ((lifecycle-state
                      (repo-tooling-symbol-admission lifecycle repo-tooling-lifecycles)))
                (00000111
                  ((00000011 lifecycle-state (00000001 admitted))
                   (00100111 (00000001 repo-tooling-ok)))
                  ((00000011 lifecycle-state (00000001 rejected))
                   (repo-tooling-violation (00000001 invalid-lifecycle) lifecycle))
                  ((00000011 lifecycle-state (00000001 malformed-admitted-set))
                   (repo-tooling-violation
                     (00000001 malformed-lifecycle-vocabulary)
                     lifecycle)))))
             ((00000011 language-state (00000001 rejected))
              (repo-tooling-violation (00000001 invalid-language) language))
             ((00000011 language-state (00000001 malformed-admitted-set))
              (repo-tooling-violation
                (00000001 malformed-language-vocabulary)
                language)))))
        ((00000011 kind-state (00000001 rejected))
         (repo-tooling-violation (00000001 invalid-kind) kind))
        ((00000011 kind-state (00000001 malformed-admitted-set))
         (repo-tooling-violation (00000001 malformed-kind-vocabulary) kind))))))

(00001001 repo-tooling-enum-verdict
  (00001000 (rows)
    (00000111
      ((repo-tooling-empty-list? rows) (00100111 (00000001 repo-tooling-ok)))
      ((repo-tooling-nonempty-atom? rows)
       (repo-tooling-violation (00000001 malformed-inventory-list) rows))
      ((repo-tooling-pair? rows)
       (10011100 ((row-verdict (repo-tooling-row-enum-verdict (00000101 rows))))
         (00000111
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 yes))
            (repo-tooling-enum-verdict (00000110 rows)))
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 no))
            row-verdict)))))))

(00001001 repo-tooling-python-migration-required-state
  (00001000 (row)
    (10011100 ((language (repo-tooling-field (00000001 language) row))
          (lifecycle (repo-tooling-field (00000001 lifecycle) row)))
      (00000111
        ((00000011 language (00000001 python))
         (00000111
           ((00000011 lifecycle (00000001 active)) (00000001 required))
           ((repo-tooling-predicate-no? (00000011 lifecycle (00000001 active)))
            (00000111
              ((00000011 lifecycle (00000001 transitional))
               (00000001 required))
              ((repo-tooling-predicate-no? (00000011 lifecycle (00000001 transitional)))
               (00000001 not-required))))))
        ((repo-tooling-predicate-no? (00000011 language (00000001 python)))
         (00000001 not-required))))))

(00001001 repo-tooling-migration-owner-state
  (00001000 (owner)
    (00000111
      ((repo-tooling-empty-list? owner) (00000001 missing))
      ((repo-tooling-nonempty-atom? owner)
       (00000111
         ((00000011 owner (00000001 missing)) (00000001 missing))
         ((repo-tooling-predicate-no? (00000011 owner (00000001 missing))) (00000001 present))))
      ((repo-tooling-pair? owner) (00000001 present)))))

(00001001 repo-tooling-row-python-migration-verdict
  (00001000 (row)
    (10011100 ((required-state (repo-tooling-python-migration-required-state row)))
      (00000111
        ((00000011 required-state (00000001 not-required))
         (00100111 (00000001 repo-tooling-ok)))
        ((00000011 required-state (00000001 required))
         (10011101 ((owner (repo-tooling-field (00000001 migration-issue) row))
                (owner-state (repo-tooling-migration-owner-state owner)))
           (00000111
             ((00000011 owner-state (00000001 present))
              (00100111 (00000001 repo-tooling-ok)))
             ((00000011 owner-state (00000001 missing))
              (repo-tooling-violation
                (00000001 python-migration-unowned)
                (repo-tooling-field (00000001 path) row))))))))))

(00001001 repo-tooling-python-migration-verdict
  (00001000 (rows)
    (00000111
      ((repo-tooling-empty-list? rows) (00100111 (00000001 repo-tooling-ok)))
      ((repo-tooling-nonempty-atom? rows)
       (repo-tooling-violation (00000001 malformed-inventory-list) rows))
      ((repo-tooling-pair? rows)
       (10011100 ((row-verdict (repo-tooling-row-python-migration-verdict (00000101 rows))))
         (00000111
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 yes))
            (repo-tooling-python-migration-verdict (00000110 rows)))
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 no))
            row-verdict)))))))

(00001001 repo-tooling-find-row-by-path
  (00001000 (path rows)
    (00000111
      ((repo-tooling-empty-list? rows) (00000001 ()))
      ((repo-tooling-nonempty-atom? rows) (00000001 ()))
      ((repo-tooling-pair? rows)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00100010 path (repo-tooling-field (00000001 path) row))
            row)
           ((repo-tooling-predicate-no? (00100010 path (repo-tooling-field (00000001 path) row)))
            (repo-tooling-find-row-by-path path (00000110 rows)))))))))

(00001001 repo-tooling-duplicate-path-verdict
  (00001000 (rows)
    (00000111
      ((repo-tooling-empty-list? rows) (00100111 (00000001 repo-tooling-ok)))
      ((repo-tooling-nonempty-atom? rows)
       (repo-tooling-violation (00000001 malformed-inventory-list) rows))
      ((repo-tooling-pair? rows)
       (10011101 ((row (00000101 rows))
              (path (repo-tooling-field (00000001 path) row))
              (found (repo-tooling-find-row-by-path path (00000110 rows))))
         (00000111
           ((repo-tooling-empty-list? found)
            (repo-tooling-duplicate-path-verdict (00000110 rows)))
           ((repo-tooling-nonempty-atom? found)
            (repo-tooling-violation (00000001 malformed-row) path))
           ((repo-tooling-pair? found)
            (repo-tooling-violation (00000001 duplicate-path) path))))))))

(00001001 repo-tooling-observed-path-state
  (00001000 (path observed)
    (00000111
      ((repo-tooling-empty-list? observed) (00000001 absent))
      ((repo-tooling-nonempty-atom? observed) (00000001 malformed))
      ((repo-tooling-pair? observed)
       (10011100 ((observed-path (00111010 "scripts/" (00000101 observed))))
         (00000111
           ((00100010 path observed-path) (00000001 present))
           ((repo-tooling-predicate-no? (00100010 path observed-path))
            (repo-tooling-observed-path-state path (00000110 observed)))))))))

(00001001 repo-tooling-stale-path-verdict
  (00001000 (rows observed)
    (00000111
      ((repo-tooling-empty-list? rows) (00100111 (00000001 repo-tooling-ok)))
      ((repo-tooling-nonempty-atom? rows)
       (repo-tooling-violation (00000001 malformed-inventory-list) rows))
      ((repo-tooling-pair? rows)
       (10011101 ((row (00000101 rows))
              (path (repo-tooling-field (00000001 path) row))
              (state (repo-tooling-observed-path-state path observed)))
         (00000111
           ((00000011 state (00000001 present))
            (repo-tooling-stale-path-verdict (00000110 rows) observed))
           ((00000011 state (00000001 absent))
            (repo-tooling-violation (00000001 stale-path) path))
           ((00000011 state (00000001 malformed))
            (repo-tooling-violation (00000001 malformed-observed-list) observed))))))))

(00001001 repo-tooling-observed-coverage-verdict
  (00001000 (rows observed)
    (00000111
      ((repo-tooling-empty-list? observed) (00100111 (00000001 repo-tooling-ok)))
      ((repo-tooling-nonempty-atom? observed)
       (repo-tooling-violation (00000001 malformed-observed-list) observed))
      ((repo-tooling-pair? observed)
       (10011101 ((name (00000101 observed))
              (path (00111010 "scripts/" name))
              (found (repo-tooling-find-row-by-path path rows)))
         (00000111
           ((repo-tooling-empty-list? found)
            (repo-tooling-violation (00000001 unregistered-tool) path))
           ((repo-tooling-nonempty-atom? found)
            (repo-tooling-violation (00000001 malformed-row) path))
           ((repo-tooling-pair? found)
            (repo-tooling-observed-coverage-verdict rows (00000110 observed)))))))))

(00001001 repo-tooling-verdict-after-required
  (00001000 (rows observed)
    (10011100 ((enum-verdict (repo-tooling-enum-verdict rows)))
      (00000111
        ((00000011 (repo-tooling-verdict-ok-state enum-verdict) (00000001 yes))
         (10011100 ((migration-verdict (repo-tooling-python-migration-verdict rows)))
           (00000111
             ((00000011 (repo-tooling-verdict-ok-state migration-verdict) (00000001 yes))
              (10011100 ((duplicate-verdict (repo-tooling-duplicate-path-verdict rows)))
                (00000111
                  ((00000011 (repo-tooling-verdict-ok-state duplicate-verdict) (00000001 yes))
                   (10011100 ((stale-verdict (repo-tooling-stale-path-verdict rows observed)))
                     (00000111
                       ((00000011 (repo-tooling-verdict-ok-state stale-verdict) (00000001 yes))
                        (repo-tooling-observed-coverage-verdict rows observed))
                       ((00000011 (repo-tooling-verdict-ok-state stale-verdict) (00000001 no))
                        stale-verdict))))
                  ((00000011 (repo-tooling-verdict-ok-state duplicate-verdict) (00000001 no))
                   duplicate-verdict))))
             ((00000011 (repo-tooling-verdict-ok-state migration-verdict) (00000001 no))
              migration-verdict))))
        ((00000011 (repo-tooling-verdict-ok-state enum-verdict) (00000001 no))
         enum-verdict)))))

(00001001 repo-tooling-verdict
  (00001000 (rows observed)
    (10011100 ((required-verdict (repo-tooling-required-verdict rows)))
      (00000111
        ((00000011 (repo-tooling-verdict-ok-state required-verdict) (00000001 yes))
         (repo-tooling-verdict-after-required rows observed))
        ((00000011 (repo-tooling-verdict-ok-state required-verdict) (00000001 no))
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
      ((00100010 actual expected)
       (00100111 (00000001 repo-tooling-selftest-ok)))
      ((repo-tooling-predicate-no? (00100010 actual expected))
       (10011100 ((shown
               (01001000
                 (00100111
                   (00000001 repo-tooling-selftest-failed)
                   actual
                   expected))))
         (00000101 (00000001 ())))))))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (00100111 repo-tooling-sample-row-a) (00000001 ("a.lisp" "b.lisp")))
  (00000001 (repo-tooling-violation unregistered-tool "scripts/b.lisp")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict
    (00100111 repo-tooling-sample-row-a repo-tooling-sample-row-a)
    (00000001 ("a.lisp")))
  (00000001 (repo-tooling-violation duplicate-path "scripts/a.lisp")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict
    (00100111 repo-tooling-sample-row-a repo-tooling-sample-row-c)
    (00000001 ("a.lisp")))
  (00000001 (repo-tooling-violation stale-path "scripts/c.lisp")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (00100111 repo-tooling-sample-bad-kind) (00000001 ("a.lisp")))
  (00000001 (repo-tooling-violation invalid-kind mystery-kind)))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (00100111 repo-tooling-sample-bad-language) (00000001 ("a.lisp")))
  (00000001 (repo-tooling-violation invalid-language mystery-language)))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (00100111 repo-tooling-sample-bad-lifecycle) (00000001 ("a.lisp")))
  (00000001 (repo-tooling-violation invalid-lifecycle parity-green)))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (00100111 repo-tooling-sample-python-unowned) (00000001 ("a.py")))
  (00000001 (repo-tooling-violation python-migration-unowned "scripts/a.py")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (00100111 repo-tooling-sample-missing-role) (00000001 ("a.lisp")))
  (00000001 (repo-tooling-violation missing-field role)))

; ----- real repository observation -----

(00001001 repo-tooling-tool-rows
  (00001000 (forms)
    (00000111
      ((repo-tooling-empty-list? forms) (00000001 ()))
      ((repo-tooling-nonempty-atom? forms) (00000001 ()))
      ((repo-tooling-pair? forms)
       (10011100 ((form (00000101 forms)))
         (00000111
           ((repo-tooling-empty-list? form)
            (repo-tooling-tool-rows (00000110 forms)))
           ((repo-tooling-nonempty-atom? form)
            (repo-tooling-tool-rows (00000110 forms)))
           ((repo-tooling-pair? form)
            (00000111
              ((00000011 (00000101 form) (00000001 tool))
               (00000100 form (repo-tooling-tool-rows (00000110 forms))))
              ((repo-tooling-predicate-no? (00000011 (00000101 form) (00000001 tool)))
               (repo-tooling-tool-rows (00000110 forms)))))))))))

(00001001 repo-tooling-observed-scripts
  (00001000 (entries)
    (00000111
      ((repo-tooling-empty-list? entries) (00000001 ()))
      ((repo-tooling-nonempty-atom? entries) (00000001 ()))
      ((repo-tooling-pair? entries)
       (10011100 ((name (00000101 entries)))
         (00000111
           ((00100010 name "tests")
            (repo-tooling-observed-scripts (00000110 entries)))
           ((repo-tooling-predicate-no? (00100010 name "tests"))
            (00000100 name (repo-tooling-observed-scripts (00000110 entries))))))))))

(00001001 repo-tooling-live-forms
  (01001011 (10100110 "knowledge/repo-tooling-inventory.lisp")))

(00001001 repo-tooling-live-rows
  (repo-tooling-tool-rows repo-tooling-live-forms))

(00001001 repo-tooling-live-observed
  (repo-tooling-observed-scripts (read-dir "scripts")))

(00001001 repo-tooling-live-verdict
  (repo-tooling-verdict repo-tooling-live-rows repo-tooling-live-observed))

(01001000 repo-tooling-live-verdict)

(repo-tooling-assert-verdict
  repo-tooling-live-verdict
  (00000001 (repo-tooling-ok)))
