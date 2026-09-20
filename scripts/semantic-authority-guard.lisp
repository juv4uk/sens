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
      ((generated-projection? source) (quote allowed-generated-projection))
      ((not (active-host-source? path)) (quote not-active-host-source))
      ((and
         (string-contains? "SemanticId" source)
         (contains-any? source (quote ("CanonicalIdentity" "semantic_id" "Meaning" "Operation")))
         (contains-any? source (quote ("match" "HashMap" "BTreeMap" "enum"))))
       (quote sid-to-meaning-authority))
      ((and
         (contains-any? source (quote ("surface" "surface_name" "namespace")))
         (contains-any? source (quote ("SemanticId" "semantic_id" "CanonicalIdentity")))
         (string-contains? "match" source))
       (quote surface-name-to-meaning-dispatch))
      ((and
         (contains-any? source (quote ("prolog" "datalog" "clips" "common-lisp")))
         (contains-any? source (quote ("SemanticId" "semantic_id")))
         (contains-any? source (quote ("match" "operator" "opcode"))))
       (quote island-native-operator-to-sid))
      ((and
         (contains-any? source (quote ("opcode" "mnemonic" "x86")))
         (contains-any? source (quote ("SemanticId" "semantic_id")))
         (contains-any? source (quote ("match" "HashMap" "BTreeMap"))))
       (quote isa-to-sid-authority))
      ((and
         (contains-any? source (quote ("unwrap_or" "unwrap_or_else" "fallback" "default")))
         (contains-any? source (quote ("SemanticId" "semantic_id" "CanonicalIdentity")))
         (contains-any? source (quote ("unknown" "meaning" "operation" "canonical"))))
       (quote host-fallback-meaning))
      (t (quote allowed)))))

(def scan
  (lambda (rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote semantic-authority-ok))
      ((atom rows) (structural-kind pair)
       (let* ((row (car rows))
              (path (second row))
              (source (read-file path))
              (class (violation-class path source)))
         (cond
           ((eq class (quote allowed)) (identity-relation same)
            (scan (cdr rows)))
           ((eq class (quote not-active-host-source)) (identity-relation same)
            (scan (cdr rows)))
           ((eq class (quote allowed-generated-projection)) (identity-relation same)
            (scan (cdr rows)))
           ((eq class (quote allowed)) (identity-relation distinct)
            (scan (cdr rows)))
           (t
            (list (quote semantic-authority-violation)
                  path class
                  "new host-side semantic authority requires explicit review")))))))))

(scan changed)
