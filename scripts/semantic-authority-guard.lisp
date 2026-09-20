(def changed
  (read-all (read-file "tests/semantic-authority-changes.lisp")))

(def contains-any?
  (lambda (source needles)
    (cond
      ((atom needles) (structural-kind empty-list) ())
      ((string-contains? (car needles) source) t)
      (t (contains-any? source (cdr needles))))))

(def active-host-source?
  (lambda (path)
    (or
      (string-contains? ".rs" path)
      (string-contains? ".c" path)
      (string-contains? ".cc" path)
      (string-contains? ".cpp" path)
      (string-contains? ".h" path)
      (string-contains? ".hpp" path)
      (string-contains? ".java" path)
      (string-contains? ".js" path)
      (string-contains? ".mjs" path)
      (string-contains? ".py" path)
      (string-contains? ".ps1" path))))

(def generated-projection?
  (lambda (source)
    (and
      (string-contains? "GENERATED" source)
      (string-contains? "Authority:" source)
      (string-contains? "Generator:" source))))

(def violation-class
  (lambda (path source)
    (cond
      ((string-prefix? "tests/fixtures/semantic-authority-guard/" path)
       (quote allowed-adversarial-fixture))
      ((generated-projection? source) (quote allowed-generated-projection))
      ((not (active-host-source? path)) (quote not-active-host-source))
      ; High-risk authority shapes are deliberately structural and conservative:
      ; this guard requests review; it does not attempt to understand Rust semantics.
      ((and
         (string-contains? "SemanticId" source)
         (string-contains? "CanonicalIdentity" source))
       (quote sid-to-meaning-authority))
      ((and
         (contains-any? source (quote ("surface" "surface_name" "namespace")))
         (contains-any? source (quote ("SemanticId" "semantic_id" "CanonicalIdentity")))
         (string-contains? "match" source))
       (quote surface-name-to-meaning-dispatch))
      ((and
         (contains-any? source (quote ("prolog" "datalog" "clips" "common-lisp")))
         (contains-any? source (quote ("SemanticId" "semantic_id"))))
       (quote island-native-operator-to-sid))
      ((and
         (contains-any? source (quote ("opcode" "mnemonic" "x86")))
         (contains-any? source (quote ("SemanticId" "semantic_id"))))
       (quote isa-to-sid-authority))
      ((and
         (contains-any? source (quote ("unwrap_or" "unwrap_or_else" "fallback" "default")))
         (string-contains? "CanonicalIdentity" source))
       (quote host-fallback-meaning))
      (t (quote allowed)))))

(def scan
  (lambda (rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote (semantic-authority-ok)))
      ((atom rows) (structural-kind pair)
       (let* ((row (car rows))
              (path (second row))
              (raw-source (read-file path)))
         (cond
           ((and (active-host-source? path)
                 (not (string? raw-source)))
            (list (quote semantic-authority-violation)
                  path
                  (quote unreadable-active-host-source)
                  "active host source must be readable text for authority review"))
           (t
            (let* ((source
                     (cond
                       ((string? raw-source) raw-source)
                       (t (write-to-string raw-source))))
                   (class (violation-class path source)))
              (cond
           ((eq class (quote allowed)) (identity-relation same)
            (scan (cdr rows)))
           ((eq class (quote not-active-host-source)) (identity-relation same)
            (scan (cdr rows)))
           ((eq class (quote allowed-generated-projection)) (identity-relation same)
            (scan (cdr rows)))
           ((eq class (quote allowed-adversarial-fixture)) (identity-relation same)
            (scan (cdr rows)))
           ((eq class (quote allowed)) (identity-relation distinct)
            (scan (cdr rows)))
                (t
                 (list (quote semantic-authority-violation)
                       path class
                       "new host-side semantic authority requires explicit review"))))))))))

(print (scan changed))
