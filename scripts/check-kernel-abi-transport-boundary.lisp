; #1117 — executable Lisp-owned policy for kernel ABI identity scope.
; Host tooling may mechanically inspect files, but the admitted direction and
; forbidden reverse authority are owned here.

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
      ((atom? rows)
       (structural-kind empty-list)
       (quote ()))
      ((atom? rows)
       (structural-kind pair)
       (cond
         ((eq? (car (car rows)) name)
          (identity-relation same)
          (car rows))
         ((eq? (car (car rows)) name)
          (identity-relation distinct)
          (kab-find name (cdr rows))))))))

(def kab-find-kernel
  (lambda (kernel-name rows)
    (cond
      ((atom? rows)
       (structural-kind empty-list)
       (quote ()))
      ((atom? rows)
       (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((eq? (car row) (quote kernel))
            (identity-relation same)
            (cond
              ((eq? (second row) kernel-name)
               (identity-relation same)
               row)
              ((eq? (second row) kernel-name)
               (identity-relation distinct)
               (kab-find-kernel kernel-name (cdr rows)))))
           ((eq? (car row) (quote kernel))
            (identity-relation distinct)
            (kab-find-kernel kernel-name (cdr rows)))))))))

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

(def kab-kernel-row-check
  (lambda (kernel-name expected)
    (let ((actual (kab-find-kernel kernel-name kab-rows)))
      (cond
        ((equal? actual expected)
         (structural-relation same)
         (quote ()))
        ((equal? actual expected)
         (structural-relation distinct)
         (list (quote kernel-row-mismatch) kernel-name expected actual))))))

(def kab-first-failure
  (lambda (checks)
    (cond
      ((atom? checks)
       (structural-kind empty-list)
       (quote ()))
      ((atom? (car checks))
       (structural-kind empty-list)
       (kab-first-failure (cdr checks)))
      ((atom? (car checks))
       (structural-kind pair)
       (car checks))
      ((atom? (car checks))
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
                  (quote (language-identity-type Sens8)))
                (kab-row-check
                  (quote shared-abi-type)
                  (quote (shared-abi-type WsmKernelRequest)))
                (kab-row-check
                  (quote shared-abi-field)
                  (quote (shared-abi-field semantic_id)))
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
                  (quote kernel-may-mint-semantic-identity)
                  (quote (kernel-may-mint-semantic-identity forbidden)))
                (kab-row-check
                  (quote reverse-direction)
                  (quote
                    (reverse-direction
                      kernel-transport-to-language-meaning
                      forbidden)))
                (kab-row-check
                  (quote native-result-role)
                  (quote (native-result-role observation-only)))
                (kab-row-check
                  (quote shared-abi-source)
                  (quote
                    (shared-abi-source
                      "crates/wsm-kernel-c-abi/src/lib.rs"
                      "crates/wsm-kernel-c-abi/Cargo.toml")))
                (kab-kernel-row-check
                  (quote common-lisp)
                  (quote
                    (kernel common-lisp
                      "crates/wsm-common-lisp-kernel/src/lib.rs"
                      "crates/wsm-common-lisp-kernel/Cargo.toml")))
                (kab-kernel-row-check
                  (quote prolog)
                  (quote
                    (kernel prolog
                      "crates/wsm-prolog-kernel/src/lib.rs"
                      "crates/wsm-prolog-kernel/Cargo.toml")))
                (kab-kernel-row-check
                  (quote clips)
                  (quote
                    (kernel clips
                      "crates/wsm-clips-kernel/src/lib.rs"
                      "crates/wsm-clips-kernel/Cargo.toml")))
                (kab-kernel-row-check
                  (quote datalog)
                  (quote
                    (kernel datalog
                      "crates/wsm-datalog-kernel/src/lib.rs"
                      "crates/wsm-datalog-kernel/Cargo.toml")))))))
      (cond
        ((atom? failure)
         (structural-kind empty-list)
         (quote
           (kernel-abi-transport-boundary-ok
             (kernels 4)
             (language-type Sens8)
             (abi-wrapper SemanticId))))
        ((atom? failure)
         (structural-kind pair)
         (list
           (quote kernel-abi-transport-boundary-violation)
           failure))
        ((atom? failure)
         (structural-kind atom)
         (list
           (quote kernel-abi-transport-boundary-violation)
           failure))))))

(kab-verdict)