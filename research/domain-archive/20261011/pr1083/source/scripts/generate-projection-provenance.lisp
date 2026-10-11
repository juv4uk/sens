; #1061 — deterministic provenance manifest for generated Canon projections.
; This is tooling, not semantic authority. Canon identity remains solely in
; lib/surface/semantic-registry.lisp. The manifest binds source bytes and
; generated target bytes so neither side may drift silently.

(def provenance-source-path "lib/surface/semantic-registry.lisp")
(def provenance-output-path "knowledge/projection-provenance.lisp")
(def provenance-sid-text "00001100")

(def provenance-str+
  (lambda args
    (reduce (lambda (acc value) (string-append acc value)) "" args)))

(def provenance-source-text (read-file provenance-source-path))
(def provenance-registry
  (car (read-all provenance-source-text)))
(def provenance-registry-rows (cdr provenance-registry))

(def provenance-find-row
  (lambda (sid-text rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote ()))
      ((atom rows) (structural-kind pair)
       (cond
         ((equal? (write-to-string (car (car rows))) sid-text)
          (structural-relation same)
          (car rows))
         ((equal? (write-to-string (car (car rows))) sid-text)
          (structural-relation distinct)
          (provenance-find-row sid-text (cdr rows))))))))

(def provenance-source-row
  (provenance-find-row provenance-sid-text provenance-registry-rows))

(def provenance-source-digest
  (string-append "sha256:" (sha256-hex provenance-source-text)))

; target, producer, purpose, input-api-policy
(def provenance-specs
  (quote
    (("crates/my-lisp/src/semantic_registry_generated.rs"
      "scripts/generate-rust-semantic-registry.lisp"
      runtime-surface-sid
      internal-runtime-readonly)
     ("lib/generated/function-table.lisp"
      "scripts/generate-function-table.lisp"
      function-table-review
      forbidden)
     ("docs/generated/function-table.md"
      "scripts/generate-function-table.lisp"
      human-documentation
      forbidden)
     ("lib/generated/meta-semantic-registry.lisp"
      "scripts/generate-meta-semantic-registry.lisp"
      meta-evaluator-surface-projection
      check-only)
     ("lib/generated/uk-surface-audit.lisp"
      "scripts/generate-uk-surface-audit.lisp"
      ukrainian-surface-review
      review-only))))

(def provenance-render-spec
  (lambda (spec)
    (let* ((target (car spec))
           (producer (second spec))
           (purpose (third spec))
           (input-api (fourth spec))
           (target-digest
             (string-append "sha256:" (sha256-hex (read-file target)))))
      (provenance-str+
        "    (projection\n"
        "      (target " (write-to-string target) ")\n"
        "      (target-digest " (write-to-string target-digest) ")\n"
        "      (source " (write-to-string provenance-source-path) ")\n"
        "      (source-digest " (write-to-string provenance-source-digest) ")\n"
        "      (source-sids (00001100))\n"
        "      (producer " (write-to-string producer) ")\n"
        "      (generator-version projection-provenance/1)\n"
        "      (purpose " (write-to-string purpose) ")\n"
        "      (input-api " (write-to-string input-api) "))"))))

(def provenance-render-specs
  (lambda (remaining)
    (cond
      ((atom remaining) (structural-kind empty-list) "")
      ((atom remaining) (structural-kind pair)
       (cond
         ((atom (cdr remaining)) (structural-kind empty-list)
          (provenance-render-spec (car remaining)))
         ((atom (cdr remaining)) (structural-kind pair)
          (provenance-str+
            (provenance-render-spec (car remaining))
            "\n"
            (provenance-render-specs (cdr remaining)))))))))

(def provenance-generated
  (provenance-str+
    "; GENERATED — DO NOT EDIT BY HAND.\n"
    "; Authority: lib/surface/semantic-registry.lisp\n"
    "; Generator: scripts/generate-projection-provenance.lisp\n"
    "; This manifest is provenance/evidence only; it cannot mint SID meaning.\n"
    "\n"
    "(binary 8)\n"
    "\n"
    "(projection-provenance/1\n"
    "  (authority " (write-to-string provenance-source-path) ")\n"
    "  (source-digest " (write-to-string provenance-source-digest) ")\n"
    "  (bounded-source-sids (00001100))\n"
    "  (rows\n"
    (provenance-render-specs provenance-specs)
    "))\n"))

(cond
  ((atom provenance-source-row) (structural-kind empty-list)
   (print
     (list
       (quote projection-provenance-violation)
       (quote source-sid-missing)
       provenance-sid-text))
   (car (quote ())))
  ((atom provenance-source-row) (structural-kind pair)
   (cond
     ((atom *argv*) (structural-kind empty-list)
      (write-file provenance-output-path provenance-generated)
      (print (quote projection-provenance-written)))
     ((atom *argv*) (structural-kind pair)
      (cond
        ((equal? (car *argv*) "--check") (structural-relation same)
         (let ((current (read-file provenance-output-path)))
           (cond
             ((equal? current provenance-generated) (structural-relation same)
              (print (quote projection-provenance-current)))
             ((equal? current provenance-generated) (structural-relation distinct)
              (print
                (quote
                  (projection-provenance-violation stale-projection-provenance)))
              (car (quote ()))))))
        ((equal? (car *argv*) "--check") (structural-relation distinct)
         (write-file provenance-output-path provenance-generated)
         (print (quote projection-provenance-written))))))))
