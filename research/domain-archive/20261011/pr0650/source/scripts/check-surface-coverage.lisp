; #76 — Lisp-owned replacement for scripts/check_surface_coverage.py.
; Integration refresh after #536 is provenance-only; checker behavior is unchanged.
; Governance/tooling check only: semantic authority remains
; lib/surface/semantic-registry.lisp.
;
; Contract preserved from the Python checker:
;   registry names := every admitted (surface name status) row
;   eligible names := named inventory groups U top-level core def/defmacro
;   internal helper markers are excluded
;   any eligible name absent from numeric registry fails closed.

(def surface-coverage-statuses
  (quote (stable candidate missing compatibility-only)))

(def surface-coverage-inventory-groups
  (quote (canon necessary-forms language-macros compatibility-forms
          root-builtins core-library)))

(def surface-coverage-internal-markers
  (quote ("-onto" "-iter" "-step" "make-" "-helper" "-aux" "my-postcore-")))

(def surface-coverage-member-state
  (lambda (value values)
    (cond
      ((atom values) (structural-kind empty-list) (quote absent))
      ((atom values) (structural-kind atom) (quote malformed))
      ((atom values) (structural-kind pair)
       (cond
         ((equal? value (car values)) (structural-relation same) (quote present))
         ((equal? value (car values)) (structural-relation distinct)
          (surface-coverage-member-state value (cdr values))))))))

(def surface-coverage-uniq-onto
  (lambda (values acc)
    (cond
      ((atom values) (structural-kind empty-list) (reverse acc))
      ((atom values) (structural-kind atom) (reverse acc))
      ((atom values) (structural-kind pair)
       (let ((state (surface-coverage-member-state (car values) acc)))
         (cond
           ((eq state (quote present)) (identity-relation same)
            (surface-coverage-uniq-onto (cdr values) acc))
           ((eq state (quote present)) (identity-relation distinct)
            (surface-coverage-uniq-onto
              (cdr values)
              (cons (car values) acc)))))))))

(def surface-coverage-uniq
  (lambda (values)
    (surface-coverage-uniq-onto values (quote ()))))

(def surface-coverage-triple?
  (lambda (value)
    (cond
      ((atom value) (structural-kind empty-list) (quote ()))
      ((atom value) (structural-kind atom) (quote ()))
      ((atom value) (structural-kind pair)
       (let ((rest1 (cdr value)))
         (cond
           ((atom rest1) (structural-kind pair)
            (let ((rest2 (cdr rest1)))
              (cond
                ((atom rest2) (structural-kind pair)
                 (let ((rest3 (cdr rest2)))
                   (cond
                     ((atom rest3) (structural-kind empty-list) t)
                     ((atom rest3) (structural-kind atom) (quote ()))
                     ((atom rest3) (structural-kind pair) (quote ())))))
                ((atom rest2) (structural-kind empty-list) (quote ()))
                ((atom rest2) (structural-kind atom) (quote ())))))
           ((atom rest1) (structural-kind empty-list) (quote ()))
           ((atom rest1) (structural-kind atom) (quote ()))))))))

(def surface-coverage-registry-field-names
  (lambda (fields)
    (cond
      ((atom fields) (structural-kind empty-list) (quote ()))
      ((atom fields) (structural-kind atom) (quote ()))
      ((atom fields) (structural-kind pair)
       (let ((field (car fields)))
         (cond
           ((atom field) (structural-kind empty-list)
            (surface-coverage-registry-field-names (cdr fields)))
           ((atom field) (structural-kind atom)
            (surface-coverage-registry-field-names (cdr fields)))
           ((atom field) (structural-kind pair)
            ; The source contains the symbolic quote spelling as
            ; `(sym ' stable)`; canonical reading turns that shorthand into
            ; a two-element form. The historical regex checker simply treated
            ; it as a lexical surface token. It is not an eligible public name,
            ; so non-triples are deliberately ignored here rather than forcing
            ; second/third and crashing.
            (cond
              ((surface-coverage-triple? field)
               (let* ((name (second field))
                      (status (third field))
                      (status-state
                        (surface-coverage-member-state
                          status
                          surface-coverage-statuses)))
                 (cond
                   ((eq status-state (quote present)) (identity-relation same)
                    (cond
                      ((eq name (quote —)) (identity-relation same)
                       (surface-coverage-registry-field-names (cdr fields)))
                      ((eq name (quote —)) (identity-relation distinct)
                       (cons
                         name
                         (surface-coverage-registry-field-names (cdr fields))))))
                   ((eq status-state (quote present)) (identity-relation distinct)
                    (surface-coverage-registry-field-names (cdr fields))))))
              ((equal?
                 field
                 (list (quote sym) (list (quote quote) (quote stable))))
               (structural-relation same)
               ; Canonical reader expands the lexical surface token ' into
               ; (quote stable) here. Recover the literal symbol name so the
               ; registry-name set stays exactly equal to the historical
               ; lexical checker, while still reading the registry canonically.
               (cons
                 (string->symbol "'")
                 (surface-coverage-registry-field-names (cdr fields))))
              ((equal?
                 field
                 (list (quote sym) (list (quote quote) (quote stable))))
               (structural-relation distinct)
               (surface-coverage-registry-field-names (cdr fields)))))))))))

(def surface-coverage-registry-names
  (lambda (rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote ()))
      ((atom rows) (structural-kind atom) (quote ()))
      ((atom rows) (structural-kind pair)
       (append
         (surface-coverage-registry-field-names (cdr (car rows)))
         (surface-coverage-registry-names (cdr rows)))))))

(def surface-coverage-flat-atoms
  (lambda (values)
    (cond
      ((atom values) (structural-kind empty-list) (quote ()))
      ((atom values) (structural-kind atom) (list values))
      ((atom values) (structural-kind pair)
       (let ((value (car values)))
         (cond
           ((atom value) (structural-kind atom)
            (cons value (surface-coverage-flat-atoms (cdr values))))
           ((atom value) (structural-kind empty-list)
            (surface-coverage-flat-atoms (cdr values)))
           ((atom value) (structural-kind pair)
            (append
              (surface-coverage-flat-atoms value)
              (surface-coverage-flat-atoms (cdr values))))))))))

(def surface-coverage-inventory-names
  (lambda (form)
    (cond
      ((atom form) (structural-kind empty-list) (quote ()))
      ((atom form) (structural-kind atom) (quote ()))
      ((atom form) (structural-kind pair)
       (let ((head (car form)))
         (cond
           ((atom head) (structural-kind atom)
            (let ((group-state
                    (surface-coverage-member-state
                      head
                      surface-coverage-inventory-groups)))
              (cond
                ((eq group-state (quote present)) (identity-relation same)
                 (surface-coverage-flat-atoms (cdr form)))
                ((eq group-state (quote present)) (identity-relation distinct)
                 (append
                   (surface-coverage-inventory-names head)
                   (surface-coverage-inventory-names (cdr form)))))))
           ((atom head) (structural-kind empty-list)
            (surface-coverage-inventory-names (cdr form)))
           ((atom head) (structural-kind pair)
            (append
              (surface-coverage-inventory-names head)
              (surface-coverage-inventory-names (cdr form))))))))))

(def surface-coverage-core-definition-names
  (lambda (forms)
    (cond
      ((atom forms) (structural-kind empty-list) (quote ()))
      ((atom forms) (structural-kind atom) (quote ()))
      ((atom forms) (structural-kind pair)
       (let ((form (car forms)))
         (cond
           ((atom form) (structural-kind pair)
            (let ((head (car form)))
              (cond
                ((eq head (quote def)) (identity-relation same)
                 (cons
                   (second form)
                   (surface-coverage-core-definition-names (cdr forms))))
                ((eq head (quote def)) (identity-relation distinct)
                 (cond
                   ((eq head (quote defmacro)) (identity-relation same)
                    (cons
                      (second form)
                      (surface-coverage-core-definition-names (cdr forms))))
                   ((eq head (quote defmacro)) (identity-relation distinct)
                    (surface-coverage-core-definition-names (cdr forms))))))))
           ((atom form) (structural-kind empty-list)
            (surface-coverage-core-definition-names (cdr forms)))
           ((atom form) (structural-kind atom)
            (surface-coverage-core-definition-names (cdr forms)))))))))

(def surface-coverage-internal-name?
  (lambda (name markers)
    (cond
      ((atom markers) (structural-kind empty-list) (quote ()))
      ((atom markers) (structural-kind atom) (quote ()))
      ((atom markers) (structural-kind pair)
       (cond
         ((string-contains? (car markers) (symbol->string name)) t)
         (t (surface-coverage-internal-name? name (cdr markers))))))))

(def surface-coverage-remove-internal
  (lambda (names)
    (cond
      ((atom names) (structural-kind empty-list) (quote ()))
      ((atom names) (structural-kind atom) (quote ()))
      ((atom names) (structural-kind pair)
       (cond
         ((surface-coverage-internal-name?
            (car names)
            surface-coverage-internal-markers)
          (surface-coverage-remove-internal (cdr names)))
         (t
          (cons
            (car names)
            (surface-coverage-remove-internal (cdr names)))))))))

(def surface-coverage-unclassified
  (lambda (eligible registry-names)
    (cond
      ((atom eligible) (structural-kind empty-list) (quote ()))
      ((atom eligible) (structural-kind atom) (quote ()))
      ((atom eligible) (structural-kind pair)
       (let* ((name (car eligible))
              (registry-state
                (surface-coverage-member-state name registry-names)))
         (cond
           ((eq registry-state (quote present)) (identity-relation same)
            (surface-coverage-unclassified (cdr eligible) registry-names))
           ((eq registry-state (quote present)) (identity-relation distinct)
            (cond
              ((surface-coverage-internal-name?
                 name
                 surface-coverage-internal-markers)
               (surface-coverage-unclassified (cdr eligible) registry-names))
              (t
               (cons
                 name
                 (surface-coverage-unclassified
                   (cdr eligible)
                   registry-names)))))))))))

(def surface-coverage-fail
  (lambda (names)
    (let ((shown
            (print
              (list
                (quote surface-drift-detected)
                (quote unclassified)
                names))))
      ; Deliberately call an unbound diagnostic symbol so CI gets non-zero.
      (surface-coverage-unclassified-public-name names))))

(def surface-coverage-registry
  (car (read-all (read-file "lib/surface/semantic-registry.lisp"))))

(def surface-coverage-inventory
  (car (read-all (read-file "lib/surface/uk-inventory.lisp"))))

(def surface-coverage-core-forms
  (read-all (read-file "lib/core.lisp")))

(def surface-coverage-registry-name-set
  (surface-coverage-uniq
    (surface-coverage-registry-names (cdr surface-coverage-registry))))

(def surface-coverage-inventory-name-set
  (surface-coverage-uniq
    (surface-coverage-inventory-names surface-coverage-inventory)))

(def surface-coverage-core-name-set
  (surface-coverage-uniq
    (surface-coverage-remove-internal
      (surface-coverage-core-definition-names surface-coverage-core-forms))))

(def surface-coverage-eligible
  (surface-coverage-uniq
    (append
      surface-coverage-inventory-name-set
      surface-coverage-core-name-set)))

(def surface-coverage-missing
  (surface-coverage-unclassified
    surface-coverage-eligible
    surface-coverage-registry-name-set))

(cond
  ((atom surface-coverage-missing) (structural-kind empty-list)
   (print
     (list
       (quote surface-coverage-ok)
       (list (quote registry-surface-names)
             (length surface-coverage-registry-name-set))
       (list (quote inventory-names)
             (length surface-coverage-inventory-name-set))
       (list (quote core-public-names)
             (length surface-coverage-core-name-set))
       (list (quote total-eligible)
             (length surface-coverage-eligible)))))
  ((atom surface-coverage-missing) (structural-kind atom)
   (surface-coverage-fail (list surface-coverage-missing)))
  ((atom surface-coverage-missing) (structural-kind pair)
   (surface-coverage-fail surface-coverage-missing)))
