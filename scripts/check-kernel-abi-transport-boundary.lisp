; #1117 — executable proof that kernel ABI identity is transport-only.

(def second (lambda (x) (car (cdr x))))
(def third (lambda (x) (car (cdr (cdr x)))))
(def fourth (lambda (x) (car (cdr (cdr (cdr x))))))

(def kab-contract
  (car
    (read-all
      (read-file "contracts/kernel-abi-transport-boundary.lisp"))))

(def kab-rows (cdr kab-contract))

(def kab-find
  (lambda (name rows)
    (cond
      ((atom rows)
       (structural-kind empty-list)
       (quote ()))
      ((atom rows)
       (structural-kind pair)
       (cond
         ((eq (car (car rows)) name)
          (identity-relation same)
          (car rows))
         ((eq (car (car rows)) name)
          (identity-relation distinct)
          (kab-find name (cdr rows))))))))

(def kab-row-check
  (lambda (name expected)
    (let ((actual (kab-find name kab-rows)))
      (cond
        ((equal? actual expected)
         (structural-relation same)
         (quote ()))
        ((equal? actual expected)
         (structural-relation distinct)
         (list (quote policy-mismatch) name expected actual))))))

(def kab-kernel-source-state
  (lambda (source manifest)
    (cond
      ((not (string? source)) t (quote unreadable-source))
      ((not (string? manifest)) t (quote unreadable-manifest))
      ((not (string-contains? "pub struct SemanticId(pub u8);" source))
       t
       (quote missing-transport-wrapper))
      ((string-contains? "Sid8" source)
       t
       (quote imports-language-sid-type))
      ((string-contains? "my_lisp::" source)
       t
       (quote language-crate-coupling))
      ((string-contains? "use my_lisp" source)
       t
       (quote language-crate-coupling))
      ((string-contains? "semantic_registry" source)
       t
       (quote reverse-registry-authority))
      ((string-contains? "CanonicalIdentity" source)
       t
       (quote reverse-canon-authority))
      ((string-contains? "my-lisp" manifest)
       t
       (quote language-crate-dependency))
      (t t (quote admitted)))))

(def kab-shared-abi-state
  (lambda (source manifest)
    (cond
      ((not (string? source)) t (quote unreadable-shared-abi-source))
      ((not (string? manifest)) t (quote unreadable-shared-abi-manifest))
      ((not (string-contains? "pub semantic_id: u8," source))
       t
       (quote shared-abi-not-opaque-u8))
      ((string-contains? "Sid8" source)
       t
       (quote shared-abi-imports-language-sid))
      ((string-contains? "my_lisp::" source)
       t
       (quote shared-abi-language-coupling))
      ((string-contains? "semantic_registry" source)
       t
       (quote shared-abi-registry-coupling))
      ((string-contains? "CanonicalIdentity" source)
       t
       (quote shared-abi-canon-coupling))
      ((string-contains? "my-lisp" manifest)
       t
       (quote shared-abi-language-dependency))
      (t t (quote admitted)))))

(def kab-check-kernel-row
  (lambda (row)
    (let* ((kernel-name (second row))
           (source-path (third row))
           (manifest-path (fourth row))
           (state
             (kab-kernel-source-state
               (read-file source-path)
               (read-file manifest-path))))
      (cond
        ((eq state (quote admitted))
         (identity-relation same)
         (quote ()))
        ((eq state (quote admitted))
         (identity-relation distinct)
         (list
           (quote kernel-boundary-violation)
           kernel-name
           state
           source-path))))))

(def kab-check-kernels
  (lambda (rows)
    (cond
      ((atom rows)
       (structural-kind empty-list)
       (quote ()))
      ((atom rows)
       (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((eq (car row) (quote kernel))
            (identity-relation same)
            (let ((failure (kab-check-kernel-row row)))
              (cond
                ((atom failure)
                 (structural-kind empty-list)
                 (kab-check-kernels (cdr rows)))
                ((atom failure)
                 (structural-kind pair)
                 failure))))
           ((eq (car row) (quote kernel))
            (identity-relation distinct)
            (kab-check-kernels (cdr rows)))))))))

(def kab-check-shared-abi
  (lambda ()
    (let* ((row (kab-find (quote shared-abi-source) kab-rows))
           (source-path (second row))
           (manifest-path (third row))
           (state
             (kab-shared-abi-state
               (read-file source-path)
               (read-file manifest-path))))
      (cond
        ((eq state (quote admitted))
         (identity-relation same)
         (quote ()))
        ((eq state (quote admitted))
         (identity-relation distinct)
         (list
           (quote shared-abi-boundary-violation)
           state
           source-path))))))

(def kab-first-failure
  (lambda (checks)
    (cond
      ((atom checks)
       (structural-kind empty-list)
       (quote ()))
      ((atom (car checks))
       (structural-kind empty-list)
       (kab-first-failure (cdr checks)))
      ((atom (car checks))
       (structural-kind pair)
       (car checks))
      ((atom (car checks))
       (structural-kind atom)
       (car checks)))))

(def kab-verdict
  (lambda ()
    (let ((failure
            (kab-first-failure
              (list
                (kab-row-check
                  (quote owner)
                  (quote (owner my-lisp)))
                (kab-row-check
                  (quote language-identity-type)
                  (quote (language-identity-type Sid8)))
                (kab-row-check
                  (quote shared-abi-storage)
                  (quote (shared-abi-storage opaque-u8)))
                (kab-row-check
                  (quote kernel-wrapper-type)
                  (quote (kernel-wrapper-type SemanticId)))
                (kab-row-check
                  (quote kernel-wrapper-role)
                  (quote (kernel-wrapper-role transport-coordinate-only)))
                (kab-row-check
                  (quote wrapper-language-type-equivalence)
                  (quote (wrapper-language-type-equivalence forbidden)))
                (kab-row-check
                  (quote kernel-to-language-authority)
                  (quote (kernel-to-language-authority forbidden)))
                (kab-row-check
                  (quote kernel-may-query-semantic-registry)
                  (quote (kernel-may-query-semantic-registry forbidden)))
                (kab-row-check
                  (quote kernel-may-import-language-sid-type)
                  (quote (kernel-may-import-language-sid-type forbidden)))
                (kab-row-check
                  (quote reverse-direction)
                  (quote
                    (reverse-direction
                      kernel-transport-to-language-meaning
                      forbidden)))
                (kab-check-shared-abi)
                (kab-check-kernels kab-rows)
                ; Guard self-tests: language coupling must be rejected.
                (cond
                  ((eq
                     (kab-kernel-source-state
                       "pub struct SemanticId(pub u8); use my_lisp::Sid8;"
                       "[dependencies]")
                     (quote imports-language-sid-type))
                   (identity-relation same)
                   (quote ()))
                  (t t (quote self-test-language-sid-import-not-rejected)))
                (cond
                  ((eq
                     (kab-kernel-source-state
                       "pub struct SemanticId(pub u8); semantic_registry::lookup();"
                       "[dependencies]")
                     (quote reverse-registry-authority))
                   (identity-relation same)
                   (quote ()))
                  (t t (quote self-test-registry-edge-not-rejected)))))))
      (cond
        ((atom failure)
         (structural-kind empty-list)
         (quote
           (kernel-abi-transport-boundary-ok
             (kernels 4)
             (language-type Sid8)
             (abi-wrapper SemanticId))))
        ((atom failure)
         (structural-kind pair)
         (list
           (quote kernel-abi-transport-boundary-violation)
           failure))
        ((atom failure)
         (structural-kind atom)
         (list
           (quote kernel-abi-transport-boundary-violation)
           failure))))))

(kab-verdict)