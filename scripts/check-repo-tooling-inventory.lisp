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

(00001001 repo-tooling-field-from
  (00001000 (name fields)
    (00000111
      ((00000010 fields) () (00000001 missing))
      ((00000010 fields) (1) (00000001 missing))
      ((00000010 fields) (0)
       (10011100 ((field (00000101 fields)))
         (00000111
           ((00000010 field) ()
            (repo-tooling-field-from name (00000110 fields)))
           ((00000010 field) (1)
            (repo-tooling-field-from name (00000110 fields)))
           ((00000010 field) (0)
            (00000111
              ((00000011 (00000101 field) name) (1) (00101111 field))
              ((00000011 (00000101 field) name) (0)
               (repo-tooling-field-from name (00000110 fields)))))))))))

(00001001 repo-tooling-field
  (00001000 (name row)
    (00000111
      ((00000010 row) () (00000001 missing))
      ((00000010 row) (1) (00000001 missing))
      ((00000010 row) (0)
       (repo-tooling-field-from name (00000110 row))))))

(00001001 repo-tooling-verdict-ok-state
  (00001000 (verdict)
    (00000111
      ((00100010 verdict (00100111 (00000001 repo-tooling-ok)))
       (1)
       (00000001 yes))
      ((00100010 verdict (00100111 (00000001 repo-tooling-ok)))
       (0)
       (00000001 no)))))

(00001001 repo-tooling-field-presence
  (00001000 (value)
    (00000111
      ((00000010 value) () (00000001 present))
      ((00000010 value) (1)
       (00000111
         ((00000011 value (00000001 missing)) (1) (00000001 missing))
         ((00000011 value (00000001 missing)) (0) (00000001 present))))
      ((00000010 value) (0) (00000001 present)))))

(00001001 repo-tooling-required-fields-verdict
  (00001000 (required row)
    (00000111
      ((00000010 required) () (00100111 (00000001 repo-tooling-ok)))
      ((00000010 required) (1)
       (repo-tooling-violation (00000001 malformed-required-field-list) required))
      ((00000010 required) (0)
       (00000111
         ((00000011 (repo-tooling-field-presence
                (repo-tooling-field (00000101 required) row))
              (00000001 missing))
          (1)
          (repo-tooling-violation (00000001 missing-field) (00000101 required)))
         ((00000011 (repo-tooling-field-presence
                (repo-tooling-field (00000101 required) row))
              (00000001 missing))
          (0)
          (repo-tooling-required-fields-verdict (00000110 required) row)))))))

(00001001 repo-tooling-row-required-verdict
  (00001000 (row)
    (00000111
      ((00000010 row) ()
       (repo-tooling-violation (00000001 malformed-row) row))
      ((00000010 row) (1)
       (repo-tooling-violation (00000001 malformed-row) row))
      ((00000010 row) (0)
       (00000111
         ((00000011 (00000101 row) (00000001 tool)) (1)
          (repo-tooling-required-fields-verdict repo-tooling-required-fields row))
         ((00000011 (00000101 row) (00000001 tool)) (0)
          (repo-tooling-violation (00000001 malformed-row-kind) (00000101 row))))))))

(00001001 repo-tooling-required-verdict
  (00001000 (rows)
    (00000111
      ((00000010 rows) () (00100111 (00000001 repo-tooling-ok)))
      ((00000010 rows) (1)
       (repo-tooling-violation (00000001 malformed-inventory-list) rows))
      ((00000010 rows) (0)
       (10011100 ((row-verdict (repo-tooling-row-required-verdict (00000101 rows))))
         (00000111
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 yes))
            (1)
            (repo-tooling-required-verdict (00000110 rows)))
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 no))
            (1)
            row-verdict)))))))

(00001001 repo-tooling-symbol-admission
  (00001000 (value admitted)
    (00000111
      ((00000010 admitted) () (00000001 rejected))
      ((00000010 admitted) (1) (00000001 malformed-admitted-set))
      ((00000010 admitted) (0)
       (00000111
         ((00000011 value (00000101 admitted)) (1) (00000001 admitted))
         ((00000011 value (00000101 admitted)) (0)
          (repo-tooling-symbol-admission value (00000110 admitted))))))))

(00001001 repo-tooling-row-enum-verdict
  (00001000 (row)
    (10011101 ((kind (repo-tooling-field (00000001 kind) row))
           (language (repo-tooling-field (00000001 language) row))
           (lifecycle (repo-tooling-field (00000001 lifecycle) row))
           (kind-state (repo-tooling-symbol-admission kind repo-tooling-kinds)))
      (00000111
        ((00000011 kind-state (00000001 admitted)) (1)
         (10011100 ((language-state
                 (repo-tooling-symbol-admission language repo-tooling-languages)))
           (00000111
             ((00000011 language-state (00000001 admitted)) (1)
              (10011100 ((lifecycle-state
                      (repo-tooling-symbol-admission lifecycle repo-tooling-lifecycles)))
                (00000111
                  ((00000011 lifecycle-state (00000001 admitted)) (1)
                   (00100111 (00000001 repo-tooling-ok)))
                  ((00000011 lifecycle-state (00000001 rejected)) (1)
                   (repo-tooling-violation (00000001 invalid-lifecycle) lifecycle))
                  ((00000011 lifecycle-state (00000001 malformed-admitted-set))
                   (1)
                   (repo-tooling-violation
                     (00000001 malformed-lifecycle-vocabulary)
                     lifecycle)))))
             ((00000011 language-state (00000001 rejected)) (1)
              (repo-tooling-violation (00000001 invalid-language) language))
             ((00000011 language-state (00000001 malformed-admitted-set))
              (1)
              (repo-tooling-violation
                (00000001 malformed-language-vocabulary)
                language)))))
        ((00000011 kind-state (00000001 rejected)) (1)
         (repo-tooling-violation (00000001 invalid-kind) kind))
        ((00000011 kind-state (00000001 malformed-admitted-set)) (1)
         (repo-tooling-violation (00000001 malformed-kind-vocabulary) kind))))))

(00001001 repo-tooling-enum-verdict
  (00001000 (rows)
    (00000111
      ((00000010 rows) () (00100111 (00000001 repo-tooling-ok)))
      ((00000010 rows) (1)
       (repo-tooling-violation (00000001 malformed-inventory-list) rows))
      ((00000010 rows) (0)
       (10011100 ((row-verdict (repo-tooling-row-enum-verdict (00000101 rows))))
         (00000111
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 yes))
            (1)
            (repo-tooling-enum-verdict (00000110 rows)))
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 no))
            (1)
            row-verdict)))))))

(00001001 repo-tooling-python-migration-required-state
  (00001000 (row)
    (10011100 ((language (repo-tooling-field (00000001 language) row))
          (lifecycle (repo-tooling-field (00000001 lifecycle) row)))
      (00000111
        ((00000011 language (00000001 python)) (1)
         (00000111
           ((00000011 lifecycle (00000001 active)) (1) (00000001 required))
           ((00000011 lifecycle (00000001 active)) (0)
            (00000111
              ((00000011 lifecycle (00000001 transitional))
               (1)
               (00000001 required))
              ((00000011 lifecycle (00000001 transitional))
               (0)
               (00000001 not-required))))))
        ((00000011 language (00000001 python)) (0)
         (00000001 not-required))))))

(00001001 repo-tooling-migration-owner-state
  (00001000 (owner)
    (00000111
      ((00000010 owner) () (00000001 missing))
      ((00000010 owner) (1)
       (00000111
         ((00000011 owner (00000001 missing)) (1) (00000001 missing))
         ((00000011 owner (00000001 missing)) (0) (00000001 present))))
      ((00000010 owner) (0) (00000001 present)))))

(00001001 repo-tooling-row-python-migration-verdict
  (00001000 (row)
    (10011100 ((required-state (repo-tooling-python-migration-required-state row)))
      (00000111
        ((00000011 required-state (00000001 not-required)) (1)
         (00100111 (00000001 repo-tooling-ok)))
        ((00000011 required-state (00000001 required)) (1)
         (10011101 ((owner (repo-tooling-field (00000001 migration-issue) row))
                (owner-state (repo-tooling-migration-owner-state owner)))
           (00000111
             ((00000011 owner-state (00000001 present)) (1)
              (00100111 (00000001 repo-tooling-ok)))
             ((00000011 owner-state (00000001 missing)) (1)
              (repo-tooling-violation
                (00000001 python-migration-unowned)
                (repo-tooling-field (00000001 path) row))))))))))

(00001001 repo-tooling-python-migration-verdict
  (00001000 (rows)
    (00000111
      ((00000010 rows) () (00100111 (00000001 repo-tooling-ok)))
      ((00000010 rows) (1)
       (repo-tooling-violation (00000001 malformed-inventory-list) rows))
      ((00000010 rows) (0)
       (10011100 ((row-verdict (repo-tooling-row-python-migration-verdict (00000101 rows))))
         (00000111
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 yes))
            (1)
            (repo-tooling-python-migration-verdict (00000110 rows)))
           ((00000011 (repo-tooling-verdict-ok-state row-verdict) (00000001 no))
            (1)
            row-verdict)))))))

(00001001 repo-tooling-find-row-by-path
  (00001000 (path rows)
    (00000111
      ((00000010 rows) () (00000001 ()))
      ((00000010 rows) (1) (00000001 ()))
      ((00000010 rows) (0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00100010 path (repo-tooling-field (00000001 path) row))
            (1)
            row)
           ((00100010 path (repo-tooling-field (00000001 path) row))
            (0)
            (repo-tooling-find-row-by-path path (00000110 rows)))))))))

(00001001 repo-tooling-duplicate-path-verdict
  (00001000 (rows)
    (00000111
      ((00000010 rows) () (00100111 (00000001 repo-tooling-ok)))
      ((00000010 rows) (1)
       (repo-tooling-violation (00000001 malformed-inventory-list) rows))
      ((00000010 rows) (0)
       (10011101 ((row (00000101 rows))
              (path (repo-tooling-field (00000001 path) row))
              (found (repo-tooling-find-row-by-path path (00000110 rows))))
         (00000111
           ((00000010 found) ()
            (repo-tooling-duplicate-path-verdict (00000110 rows)))
           ((00000010 found) (1)
            (repo-tooling-violation (00000001 malformed-row) path))
           ((00000010 found) (0)
            (repo-tooling-violation (00000001 duplicate-path) path))))))))

(00001001 repo-tooling-observed-path-state
  (00001000 (path observed)
    (00000111
      ((00000010 observed) () (00000001 absent))
      ((00000010 observed) (1) (00000001 malformed))
      ((00000010 observed) (0)
       (10011100 ((observed-path (00111010 "scripts/" (00000101 observed))))
         (00000111
           ((00100010 path observed-path) (1) (00000001 present))
           ((00100010 path observed-path) (0)
            (repo-tooling-observed-path-state path (00000110 observed)))))))))

(00001001 repo-tooling-stale-path-verdict
  (00001000 (rows observed)
    (00000111
      ((00000010 rows) () (00100111 (00000001 repo-tooling-ok)))
      ((00000010 rows) (1)
       (repo-tooling-violation (00000001 malformed-inventory-list) rows))
      ((00000010 rows) (0)
       (10011101 ((row (00000101 rows))
              (path (repo-tooling-field (00000001 path) row))
              (state (repo-tooling-observed-path-state path observed)))
         (00000111
           ((00000011 state (00000001 present)) (1)
            (repo-tooling-stale-path-verdict (00000110 rows) observed))
           ((00000011 state (00000001 absent)) (1)
            (repo-tooling-violation (00000001 stale-path) path))
           ((00000011 state (00000001 malformed)) (1)
            (repo-tooling-violation (00000001 malformed-observed-list) observed))))))))

(00001001 repo-tooling-observed-coverage-verdict
  (00001000 (rows observed)
    (00000111
      ((00000010 observed) () (00100111 (00000001 repo-tooling-ok)))
      ((00000010 observed) (1)
       (repo-tooling-violation (00000001 malformed-observed-list) observed))
      ((00000010 observed) (0)
       (10011101 ((name (00000101 observed))
              (path (00111010 "scripts/" name))
              (found (repo-tooling-find-row-by-path path rows)))
         (00000111
           ((00000010 found) ()
            (repo-tooling-violation (00000001 unregistered-tool) path))
           ((00000010 found) (1)
            (repo-tooling-violation (00000001 malformed-row) path))
           ((00000010 found) (0)
            (repo-tooling-observed-coverage-verdict rows (00000110 observed)))))))))

(00001001 repo-tooling-verdict-after-required
  (00001000 (rows observed)
    (10011100 ((enum-verdict (repo-tooling-enum-verdict rows)))
      (00000111
        ((00000011 (repo-tooling-verdict-ok-state enum-verdict) (00000001 yes))
         (1)
         (10011100 ((migration-verdict (repo-tooling-python-migration-verdict rows)))
           (00000111
             ((00000011 (repo-tooling-verdict-ok-state migration-verdict) (00000001 yes))
              (1)
              (10011100 ((duplicate-verdict (repo-tooling-duplicate-path-verdict rows)))
                (00000111
                  ((00000011 (repo-tooling-verdict-ok-state duplicate-verdict) (00000001 yes))
                   (1)
                   (10011100 ((stale-verdict (repo-tooling-stale-path-verdict rows observed)))
                     (00000111
                       ((00000011 (repo-tooling-verdict-ok-state stale-verdict) (00000001 yes))
                        (1)
                        (repo-tooling-observed-coverage-verdict rows observed))
                       ((00000011 (repo-tooling-verdict-ok-state stale-verdict) (00000001 no))
                        (1)
                        stale-verdict))))
                  ((00000011 (repo-tooling-verdict-ok-state duplicate-verdict) (00000001 no))
                   (1)
                   duplicate-verdict))))
             ((00000011 (repo-tooling-verdict-ok-state migration-verdict) (00000001 no))
              (1)
              migration-verdict))))
        ((00000011 (repo-tooling-verdict-ok-state enum-verdict) (00000001 no))
         (1)
         enum-verdict)))))

(00001001 repo-tooling-verdict
  (00001000 (rows observed)
    (10011100 ((required-verdict (repo-tooling-required-verdict rows)))
      (00000111
        ((00000011 (repo-tooling-verdict-ok-state required-verdict) (00000001 yes))
         (1)
         (repo-tooling-verdict-after-required rows observed))
        ((00000011 (repo-tooling-verdict-ok-state required-verdict) (00000001 no))
         (1)
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
      ((00100010 actual expected) (1)
       (00100111 (00000001 repo-tooling-selftest-ok)))
      ((00100010 actual expected) (0)
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
      ((00000010 forms) () (00000001 ()))
      ((00000010 forms) (1) (00000001 ()))
      ((00000010 forms) (0)
       (10011100 ((form (00000101 forms)))
         (00000111
           ((00000010 form) ()
            (repo-tooling-tool-rows (00000110 forms)))
           ((00000010 form) (1)
            (repo-tooling-tool-rows (00000110 forms)))
           ((00000010 form) (0)
            (00000111
              ((00000011 (00000101 form) (00000001 tool)) (1)
               (00000100 form (repo-tooling-tool-rows (00000110 forms))))
              ((00000011 (00000101 form) (00000001 tool)) (0)
               (repo-tooling-tool-rows (00000110 forms)))))))))))

(00001001 repo-tooling-observed-scripts
  (00001000 (entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries) (1) (00000001 ()))
      ((00000010 entries) (0)
       (10011100 ((name (00000101 entries)))
         (00000111
           ((00100010 name "tests") (1)
            (repo-tooling-observed-scripts (00000110 entries)))
           ((00100010 name "tests") (0)
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
