; #549 / #76 — Lisp-owned replacement for scripts/check_trilingual_surface.py.
; Governance checker only. Semantic authority remains:
;   lib/surface/semantic-registry.lisp
;
; The checker reads the canonical registry structurally, validates the
; UK/EN/SA status matrix, emits a machine-readable report, and fails closed
; for malformed/duplicate/missing human surfaces. --require-complete keeps
; the historical release gate behavior.

(def tri-statuses
  (quote (stable candidate missing compatibility-only)))

(def tri-human-surfaces
  (quote (uk en sa)))

(def tri-fail
  (lambda (kind detail)
    (let ((shown
            (print
              (list
                (quote trilingual-surface-error)
                kind
                detail))))
      ; Intentional unbound diagnostic: file-mode CLI returns non-zero.
      (trilingual-surface-check-failed kind detail))))

(def tri-member-state
  (lambda (value values)
    (cond
      ((atom values) (structural-kind empty-list) (quote absent))
      ((atom values) (structural-kind atom) (quote malformed))
      ((atom values) (structural-kind pair)
       (cond
         ((equal? value (car values)) (structural-relation same)
          (quote present))
         ((equal? value (car values)) (structural-relation distinct)
          (tri-member-state value (cdr values))))))))

(def tri-triple-state
  (lambda (value)
    (cond
      ((atom value) (structural-kind empty-list) (quote no))
      ((atom value) (structural-kind atom) (quote no))
      ((atom value) (structural-kind pair)
       (let ((rest1 (cdr value)))
         (cond
           ((atom rest1) (structural-kind pair)
            (let ((rest2 (cdr rest1)))
              (cond
                ((atom rest2) (structural-kind pair)
                 (let ((rest3 (cdr rest2)))
                   (cond
                     ((atom rest3) (structural-kind empty-list) (quote yes))
                     ((atom rest3) (structural-kind atom) (quote no))
                     ((atom rest3) (structural-kind pair) (quote no)))))
                ((atom rest2) (structural-kind empty-list) (quote no))
                ((atom rest2) (structural-kind atom) (quote no)))))
           ((atom rest1) (structural-kind empty-list) (quote no))
           ((atom rest1) (structural-kind atom) (quote no))))))))

(def tri-special-quote-sym-state
  (lambda (field)
    (cond
      ((equal?
         field
         (list (quote sym) (list (quote quote) (quote stable))))
       (structural-relation same)
       (quote yes))
      ((equal?
         field
         (list (quote sym) (list (quote quote) (quote stable))))
       (structural-relation distinct)
       (quote no)))))

(def tri-field-language
  (lambda (field)
    (let ((special (tri-special-quote-sym-state field)))
      (cond
        ((eq special (quote yes)) (identity-relation same) (quote sym))
        ((eq special (quote yes)) (identity-relation distinct) (car field))))))

(def tri-field-status
  (lambda (field)
    (let ((special (tri-special-quote-sym-state field)))
      (cond
        ((eq special (quote yes)) (identity-relation same) (quote stable))
        ((eq special (quote yes)) (identity-relation distinct) (third field))))))

(def tri-valid-ordinary-field
  (lambda (field)
    (let ((shape (tri-triple-state field)))
      (cond
        ((eq shape (quote yes)) (identity-relation distinct)
         (tri-fail (quote malformed-surface) field))
        ((eq shape (quote yes)) (identity-relation same)
         (let* ((language (car field))
                (name (second field))
                (status (third field)))
           (cond
             ((atom language) (structural-kind atom)
              (cond
                ((atom name) (structural-kind atom)
                 (cond
                   ((atom status) (structural-kind atom)
                    (let ((state (tri-member-state status tri-statuses)))
                      (cond
                        ((eq state (quote present)) (identity-relation same)
                         (quote valid))
                        ((eq state (quote present)) (identity-relation distinct)
                         (tri-fail (quote unknown-status) field))))
                   ((atom status) (structural-kind empty-list)
                    (tri-fail (quote malformed-status) field))
                   ((atom status) (structural-kind pair)
                    (tri-fail (quote malformed-status) field))))
                ((atom name) (structural-kind empty-list)
                 (tri-fail (quote malformed-name) field))
                ((atom name) (structural-kind pair)
                 (tri-fail (quote malformed-name) field))))
             ((atom language) (structural-kind empty-list)
              (tri-fail (quote malformed-surface-name) field))
             ((atom language) (structural-kind pair)
              (tri-fail (quote malformed-surface-name) field))))))))))

(def tri-require-human-surfaces
  (lambda (seen)
    (let ((uk-state (tri-member-state (quote uk) seen)))
      (cond
        ((eq uk-state (quote present)) (identity-relation distinct)
         (tri-fail (quote missing-human-surface) (quote uk)))
        ((eq uk-state (quote present)) (identity-relation same)
         (let ((en-state (tri-member-state (quote en) seen)))
           (cond
             ((eq en-state (quote present)) (identity-relation distinct)
              (tri-fail (quote missing-human-surface) (quote en)))
             ((eq en-state (quote present)) (identity-relation same)
              (let ((sa-state (tri-member-state (quote sa) seen)))
                (cond
                  ((eq sa-state (quote present)) (identity-relation distinct)
                   (tri-fail (quote missing-human-surface) (quote sa)))
                  ((eq sa-state (quote present)) (identity-relation same)
                   (quote valid))))))))))))

(def tri-validate-fields
  (lambda (fields seen)
    (cond
      ((atom fields) (structural-kind empty-list)
       (tri-require-human-surfaces seen))
      ((atom fields) (structural-kind atom)
       (tri-fail (quote malformed-field-tail) fields))
      ((atom fields) (structural-kind pair)
       (let* ((field (car fields))
              (special (tri-special-quote-sym-state field)))
         (cond
           ((eq special (quote yes)) (identity-relation same)
            (let ((dup (tri-member-state (quote sym) seen)))
              (cond
                ((eq dup (quote present)) (identity-relation same)
                 (tri-fail (quote duplicate-surface) (quote sym)))
                ((eq dup (quote present)) (identity-relation distinct)
                 (tri-validate-fields
                   (cdr fields)
                   (cons (quote sym) seen))))))
           ((eq special (quote yes)) (identity-relation distinct)
            (let ((valid (tri-valid-ordinary-field field)))
              (let* ((language (tri-field-language field))
                     (dup (tri-member-state language seen)))
                (cond
                  ((eq dup (quote present)) (identity-relation same)
                   (tri-fail (quote duplicate-surface) language))
                  ((eq dup (quote present)) (identity-relation distinct)
                   (tri-validate-fields
                     (cdr fields)
                     (cons language seen)))))))))))))

(def tri-validate-row
  (lambda (row)
    (cond
      ((atom row) (structural-kind empty-list)
       (tri-fail (quote malformed-entry) row))
      ((atom row) (structural-kind atom)
       (tri-fail (quote malformed-entry) row))
      ((atom row) (structural-kind pair)
       (let ((identity (car row)))
         (cond
           ((atom identity) (structural-kind atom)
            (let ((valid (tri-validate-fields (cdr row) (quote ()))))
              identity))
           ((atom identity) (structural-kind empty-list)
            (tri-fail (quote malformed-identity) row))
           ((atom identity) (structural-kind pair)
            (tri-fail (quote malformed-identity) row))))))))

(def tri-validate-rows
  (lambda (rows seen-identities)
    (cond
      ((atom rows) (structural-kind empty-list)
       (cond
         ((atom seen-identities) (structural-kind empty-list)
          (tri-fail (quote empty-registry) (quote ())))
         ((atom seen-identities) (structural-kind pair)
          (quote valid))
         ((atom seen-identities) (structural-kind atom)
          (tri-fail (quote malformed-seen-identities) seen-identities))))
      ((atom rows) (structural-kind atom)
       (tri-fail (quote malformed-entry-tail) rows))
      ((atom rows) (structural-kind pair)
       (let* ((identity (tri-validate-row (car rows)))
              (dup (tri-member-state identity seen-identities)))
         (cond
           ((eq dup (quote present)) (identity-relation same)
            (tri-fail (quote duplicate-semantic-id) identity))
           ((eq dup (quote present)) (identity-relation distinct)
            (tri-validate-rows
              (cdr rows)
              (cons identity seen-identities)))))))))

(def tri-surface-status
  (lambda (fields wanted)
    (cond
      ((atom fields) (structural-kind empty-list) (quote ()))
      ((atom fields) (structural-kind atom) (quote ()))
      ((atom fields) (structural-kind pair)
       (let* ((field (car fields))
              (language (tri-field-language field)))
         (cond
           ((eq language wanted) (identity-relation same)
            (tri-field-status field))
           ((eq language wanted) (identity-relation distinct)
            (tri-surface-status (cdr fields) wanted))))))))

(def tri-all-status-state
  (lambda (fields languages wanted)
    (cond
      ((atom languages) (structural-kind empty-list) (quote all))
      ((atom languages) (structural-kind atom) (quote not-all))
      ((atom languages) (structural-kind pair)
       (let ((current
               (tri-surface-status fields (car languages))))
         (cond
           ((eq current wanted) (identity-relation same)
            (tri-all-status-state
              fields
              (cdr languages)
              wanted))
           ((eq current wanted) (identity-relation distinct)
            (quote not-all))))))))

(def tri-public-kind
  (lambda (row)
    (let ((state
            (tri-all-status-state
              (cdr row)
              tri-human-surfaces
              (quote compatibility-only))))
      (cond
        ((eq state (quote all)) (identity-relation same)
         (quote compatibility-only))
        ((eq state (quote all)) (identity-relation distinct)
         (quote public))))))

(def tri-stable-kind
  (lambda (row)
    (let ((state
            (tri-all-status-state
              (cdr row)
              tri-human-surfaces
              (quote stable))))
      (cond
        ((eq state (quote all)) (identity-relation same)
         (quote all-stable))
        ((eq state (quote all)) (identity-relation distinct)
         (quote not-all-stable))))))

(def tri-surface-presence
  (lambda (fields wanted)
    (let ((value (tri-surface-status fields wanted)))
      (cond
        ((atom value) (structural-kind empty-list) (quote absent))
        ((atom value) (structural-kind atom) (quote present))
        ((atom value) (structural-kind pair) (quote present))))))

(def tri-count-status
  (lambda (rows language wanted acc)
    (cond
      ((atom rows) (structural-kind empty-list) acc)
      ((atom rows) (structural-kind atom) acc)
      ((atom rows) (structural-kind pair)
       (let ((status
               (tri-surface-status (cdr (car rows)) language)))
         (cond
           ((eq status wanted) (identity-relation same)
            (tri-count-status (cdr rows) language wanted (+ acc 1)))
           ((eq status wanted) (identity-relation distinct)
            (tri-count-status (cdr rows) language wanted acc))))))))

(def tri-count-public
  (lambda (rows acc)
    (cond
      ((atom rows) (structural-kind empty-list) acc)
      ((atom rows) (structural-kind atom) acc)
      ((atom rows) (structural-kind pair)
       (let ((kind (tri-public-kind (car rows))))
         (cond
           ((eq kind (quote public)) (identity-relation same)
            (tri-count-public (cdr rows) (+ acc 1)))
           ((eq kind (quote public)) (identity-relation distinct)
            (tri-count-public (cdr rows) acc))))))))

(def tri-count-symbolic
  (lambda (rows acc)
    (cond
      ((atom rows) (structural-kind empty-list) acc)
      ((atom rows) (structural-kind atom) acc)
      ((atom rows) (structural-kind pair)
       (let ((state
               (tri-surface-presence
                 (cdr (car rows))
                 (quote sym))))
         (cond
           ((eq state (quote present)) (identity-relation same)
            (tri-count-symbolic (cdr rows) (+ acc 1)))
           ((eq state (quote present)) (identity-relation distinct)
            (tri-count-symbolic (cdr rows) acc))))))))

(def tri-count-common-stable
  (lambda (rows acc)
    (cond
      ((atom rows) (structural-kind empty-list) acc)
      ((atom rows) (structural-kind atom) acc)
      ((atom rows) (structural-kind pair)
       (let ((public (tri-public-kind (car rows))))
         (cond
           ((eq public (quote public)) (identity-relation distinct)
            (tri-count-common-stable (cdr rows) acc))
           ((eq public (quote public)) (identity-relation same)
            (let ((stable (tri-stable-kind (car rows))))
              (cond
                ((eq stable (quote all-stable)) (identity-relation same)
                 (tri-count-common-stable (cdr rows) (+ acc 1)))
                ((eq stable (quote all-stable)) (identity-relation distinct)
                 (tri-count-common-stable (cdr rows) acc)))))))))))

(def tri-release-state
  (lambda (rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote confirmed))
      ((atom rows) (structural-kind atom) (quote open))
      ((atom rows) (structural-kind pair)
       (let ((public (tri-public-kind (car rows))))
         (cond
           ((eq public (quote public)) (identity-relation distinct)
            (tri-release-state (cdr rows)))
           ((eq public (quote public)) (identity-relation same)
            (let ((stable (tri-stable-kind (car rows))))
              (cond
                ((eq stable (quote all-stable)) (identity-relation same)
                 (tri-release-state (cdr rows)))
                ((eq stable (quote all-stable)) (identity-relation distinct)
                 (quote open)))))))))))

(def tri-mode
  (lambda (argv)
    (cond
      ((atom argv) (structural-kind empty-list) (quote report))
      ((atom argv) (structural-kind atom)
       (tri-fail (quote malformed-argv) argv))
      ((atom argv) (structural-kind pair)
       (let ((rest (cdr argv)))
         (cond
           ((atom rest) (structural-kind empty-list)
            (cond
              ((equal? (car argv) "--require-complete")
               (structural-relation same)
               (quote require-complete))
              ((equal? (car argv) "--require-complete")
               (structural-relation distinct)
               (tri-fail (quote unknown-argument) (car argv)))))
           ((atom rest) (structural-kind atom)
            (tri-fail (quote malformed-argv) argv))
           ((atom rest) (structural-kind pair)
            (tri-fail (quote too-many-arguments) argv))))))))

(def tri-registry-form
  (car
    (read-all
      (read-file "lib/surface/semantic-registry.lisp"))))

(def tri-rows
  (cond
    ((atom tri-registry-form) (structural-kind empty-list)
     (tri-fail (quote malformed-registry-root) tri-registry-form))
    ((atom tri-registry-form) (structural-kind atom)
     (tri-fail (quote malformed-registry-root) tri-registry-form))
    ((atom tri-registry-form) (structural-kind pair)
     (cond
       ((eq (car tri-registry-form) (quote sr/1))
        (identity-relation same)
        (cdr tri-registry-form))
       ((eq (car tri-registry-form) (quote sr/1))
        (identity-relation distinct)
        (tri-fail
          (quote malformed-registry-root)
          (car tri-registry-form)))))))

(def tri-validation
  (tri-validate-rows tri-rows (quote ())))

(def tri-public-count
  (tri-count-public tri-rows 0))

(def tri-symbolic-count
  (tri-count-symbolic tri-rows 0))

(def tri-common-stable-count
  (tri-count-common-stable tri-rows 0))

(def tri-release
  (tri-release-state tri-rows))

(def tri-report
  (list
    (quote trilingual-surface-report)
    (list (quote entries) (length tri-rows))
    (list (quote public-semantic-identities) tri-public-count)
    (list (quote shared-symbolic-identities) tri-symbolic-count)
    (list
      (quote uk)
      (list (quote stable)
            (tri-count-status tri-rows (quote uk) (quote stable) 0))
      (list (quote candidate)
            (tri-count-status tri-rows (quote uk) (quote candidate) 0))
      (list (quote missing)
            (tri-count-status tri-rows (quote uk) (quote missing) 0))
      (list (quote compatibility-only)
            (tri-count-status
              tri-rows
              (quote uk)
              (quote compatibility-only)
              0)))
    (list
      (quote en)
      (list (quote stable)
            (tri-count-status tri-rows (quote en) (quote stable) 0))
      (list (quote candidate)
            (tri-count-status tri-rows (quote en) (quote candidate) 0))
      (list (quote missing)
            (tri-count-status tri-rows (quote en) (quote missing) 0))
      (list (quote compatibility-only)
            (tri-count-status
              tri-rows
              (quote en)
              (quote compatibility-only)
              0)))
    (list
      (quote sa)
      (list (quote stable)
            (tri-count-status tri-rows (quote sa) (quote stable) 0))
      (list (quote candidate)
            (tri-count-status tri-rows (quote sa) (quote candidate) 0))
      (list (quote missing)
            (tri-count-status tri-rows (quote sa) (quote missing) 0))
      (list (quote compatibility-only)
            (tri-count-status
              tri-rows
              (quote sa)
              (quote compatibility-only)
              0)))
    (list
      (quote trilingual-stable-identities)
      tri-common-stable-count
      tri-public-count)
    (list (quote release-parity) tri-release)))

(def tri-shown
  (print tri-report))

(def tri-selected-mode
  (tri-mode *argv*))

(cond
  ((eq tri-selected-mode (quote require-complete))
   (identity-relation same)
   (cond
     ((eq tri-release (quote confirmed))
      (identity-relation same)
      tri-report)
     ((eq tri-release (quote confirmed))
      (identity-relation distinct)
      (tri-fail (quote release-parity-open) tri-report))))
  ((eq tri-selected-mode (quote require-complete))
   (identity-relation distinct)
   tri-report))
