; Lisp-owned Rust projection of the canonical semantic registry.
;
; Authority: lib/surface/semantic-registry.lisp
;
; This generator reads the registry as ordinary Lisp data. It emits only a
; mechanical Rust runtime projection. Rust never parses the canonical Lisp
; source text at runtime.
;
; Usage:
;   cargo run -p my-lisp-cli -- scripts/generate-rust-semantic-registry.lisp
;   cargo run -p my-lisp-cli -- scripts/generate-rust-semantic-registry.lisp --check

(def source-path "lib/surface/semantic-registry.lisp")
(def output-path "crates/my-lisp/src/semantic_registry_generated.rs")

(def str+
  (lambda args
    (reduce (lambda (acc s) (string-append acc s)) "" args)))

(def registry-form
  (car (read-all (read-file source-path))))

(def rows (cdr registry-form))

(def rust-string
  (lambda (value)
    (cond
      ((string-membership-helper value)
       (class-membership string member)
       (write-to-string value))
      ((string-membership-helper value)
       (class-membership string nonmember)
       (write-to-string (symbol->string value))))))


(def render-surface
  (lambda (entry)
    (let ((name (second entry)))
      (cond
        ((equal? name (quote ()))
         (structural-relation same)
         "")
        ((equal? name (quote ()))
         (structural-relation distinct)
         (str+
           "SemanticSurface { namespace: "
           (rust-string (car entry))
           ", name: "
           (rust-string name)
           " }, "))))))

(def render-surfaces
  (lambda (surfaces)
    (cond
      ((atom surfaces)
       (structural-kind empty-list)
       "")
      ((atom surfaces)
       (structural-kind pair)
       (str+
         (render-surface (car surfaces))
         (render-surfaces (cdr surfaces)))))))

(def render-row
  (lambda (row)
    (str+
      "    SemanticRow { semantic_id: crate::sid!("
      (write-to-string (car row))
      "), surfaces: &["
      (render-surfaces (cdr row))
      "] },\n")))

(def render-rows
  (lambda (remaining)
    (cond
      ((atom remaining)
       (structural-kind empty-list)
       "")
      ((atom remaining)
       (structural-kind pair)
       (str+
         (render-row (car remaining))
         (render-rows (cdr remaining)))))))

(def header
  (str+
    "// GENERATED — DO NOT EDIT BY HAND.\n"
    "// Authority: lib/surface/semantic-registry.lisp\n"
    "// Generator: scripts/generate-rust-semantic-registry.lisp\n"
    "//\n"
    "// Binary identities below are an implementation projection only.\n"
    "// Canonical semantic identity remains the bare binary token in the Lisp registry.\n"
    "\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(super) struct SemanticSurface {\n"
    "    pub(super) namespace: &'static str,\n"
    "    pub(super) name: &'static str,\n"
    "}\n"
    "\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(super) struct SemanticRow {\n"
    "    pub(super) semantic_id: u8,\n"
    "    pub(super) surfaces: &'static [SemanticSurface],\n"
    "}\n"
    "\n"
    "pub(super) const SEMANTIC_ROWS: &[SemanticRow] = &[\n"))

(def generated
  (str+ header (render-rows rows) "];\n"))

(cond
  ((atom *argv*)
   (structural-kind empty-list)
   (second
     (list
       (write-file output-path generated)
       (print "Rust semantic registry projection written"))))
  ((equal? (car *argv*) "--check")
   (structural-relation same)
   (let ((current (read-file output-path)))
     (cond
       ((equal? current generated)
        (structural-relation same)
        (print "Rust semantic registry projection is current"))
       ((equal? current generated)
        (structural-relation distinct)
        (second
          (list
            (print "Rust semantic registry projection is stale")
            (car (quote ()))))))))
  ((quote write-projection)
   write-projection
   (second
     (list
       (write-file output-path generated)
       (print "Rust semantic registry projection written")))))
