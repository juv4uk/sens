; #1347 ASYMMETRIC-SEMANTIC-FIREWALL
;
; This guard no longer restricts local semantics in Rust/host/backend code.
; The protected direction is only:
;
;   host/backend implementation semantics -> Lisp language authority
;
; Rust may depend on my-lisp. Lisp language authority must not become
; semantically derived from Rust implementation artifacts.

(def changed
  (read-all (read-file "tests/semantic-authority-changes.lisp")))

(def exact-text?
  (lambda (left right)
    (cond
      ((equal? left right) (structural-relation same) t)
      (t t ()))))

(def contains-any?
  (lambda (source needles)
    (cond
      ((atom needles) (structural-kind empty-list) ())
      ((string-contains? (car needles) source) t)
      (t (contains-any? source (cdr needles))))))

(def language-authority-source?
  (lambda (path)
    (or
      (string-prefix? "lib/" path)
      (string-prefix? "contracts/" path)
      (exact-text? path "language-contract.lisp")
      (exact-text? path "my-lisp-constitution.lisp")
      ; Synthetic protected path used only by the guard self-test.
      (exact-text? path "tests/semantic-authority-guard-probe.lisp")
      ; Підтримувані (не канонічні) розширення СЕНС теж захищені.
      (exact-text? path "tests/semantic-authority-guard-probe.сенс"))))

(def host-marker?
  (lambda (source)
    (contains-any?
      source
      (quote
        (".rs"
         "crates/"
         "Rust"
         "rust::"
         "Value::"
         "ExprKind::"
         "CanonicalIdentity"
         "NecessaryFormIdentity")))))

(def semantic-authority-claim?
  (lambda (source)
    (contains-any?
      source
      (quote
        ("semantic-authority-source"
         "authority-source"
         "source-of-truth"
         "semantic-source"
         "Authority:"
         "generated-from-host")))))

(def violation-class
  (lambda (path source)
    (cond
      ; Host/runtime/compiler/backend files are intentionally unrestricted.
      ; They may have local meaning tables, enums, fallbacks, dispatch, etc.
      ((not (language-authority-source? path))
       (quote allowed-local-implementation))
      ; A protected Lisp-owned source may mention Rust as evidence/history.
      ; It becomes a violation only when host implementation is explicitly
      ; claimed as a semantic authority/source of truth.
      ((and
         (host-marker? source)
         (semantic-authority-claim? source))
       (quote host-to-language-authority-leak))
      (t (quote allowed-language-source)))))

(def scan
  (lambda (rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote (semantic-authority-ok)))
      (t
       (let* ((row (car rows))
              (path (second row)))
         (cond
           ; Crucial asymmetry: do not even inspect host implementation text.
           ((not (language-authority-source? path))
            (scan (cdr rows)))
           (t
            (let ((raw-source (read-file path)))
              (cond
                ((not (string? raw-source))
                 (list
                   (quote semantic-authority-violation)
                   path
                   (quote unreadable-language-authority-source)
                   "protected Lisp language source must be readable text"))
                (t
                 (let ((class (violation-class path raw-source)))
                   (cond
                     ((eq class (quote host-to-language-authority-leak))
                      (list
                        (quote semantic-authority-violation)
                        path
                        class
                        "Lisp language authority must not derive semantic truth from host/Rust implementation artifacts"))
                     (t
                      (scan (cdr rows)))))))))))))))

(print (scan changed))
