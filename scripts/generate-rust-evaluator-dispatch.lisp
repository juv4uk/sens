; Lisp-owned generator for the evaluator necessary-form dispatch projection.
;
; Authority: lib/evaluator-dispatch.lisp
; Rust receives only a mechanical execution projection.
;
; Usage:
;   cargo run -p my-lisp-cli -- scripts/generate-rust-evaluator-dispatch.lisp
;   cargo run -p my-lisp-cli -- scripts/generate-rust-evaluator-dispatch.lisp --check

(def source-path "lib/evaluator-dispatch.lisp")
(def output-path "crates/my-lisp/src/eval/necessary_forms_generated.rs")

(def str+
  (lambda args
    (reduce (lambda (acc s) (string-append acc s)) "" args)))

(def dispatch-form
  (car (read-all (read-file source-path))))

(def rows dispatch-form)

(def rust-mechanism
  (lambda (name)
    (cond
      ((equal? name (quote lambda-form))
       (structural-relation same)
       "NecessaryFormMechanism::Lambda")
      ((equal? name (quote define-form))
       (structural-relation same)
       "NecessaryFormMechanism::Define")
      ((quote no-known-mechanism)
       no-known-mechanism
       (car (quote ()))))))

(def render-row
  (lambda (row)
    (let ((mechanism (rust-mechanism (second row))))
      (cond
        ((atom? mechanism)
         (structural-kind empty-list)
         (car (quote ())))
        ((atom? mechanism)
         (structural-kind atom)
         (str+
           "    NecessaryFormDispatchRow { semantic_id: 0b"
           (write-to-string (car row))
           ", mechanism: "
           mechanism
           " },\n"))))))

(def render-rows
  (lambda (remaining)
    (cond
      ((atom? remaining)
       (structural-kind empty-list)
       "")
      ((atom? remaining)
       (structural-kind pair)
       (str+ (render-row (car remaining))
             (render-rows (cdr remaining)))))))

(def header
  (str+
    "// GENERATED — DO NOT EDIT BY HAND.\n"
    "// Authority: lib/evaluator-dispatch.lisp\n"
    "// Generator: scripts/generate-rust-evaluator-dispatch.lisp\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(super) enum NecessaryFormMechanism {\n"
    "    Define,\n"
    "    Lambda,\n"
    "}\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(super) struct NecessaryFormDispatchRow {\n"
    "    pub(super) semantic_id: u8,\n"
    "    pub(super) mechanism: NecessaryFormMechanism,\n"
    "}\n\n"
    "pub(super) const NECESSARY_FORM_DISPATCH: &[NecessaryFormDispatchRow] = &[\n"))

(def generated
  (str+ header (render-rows rows) "];\n"))

(cond
  ((atom? *argv*)
   (structural-kind empty-list)
   (second
     (list
       (write-file output-path generated)
       (print "Rust evaluator dispatch projection written"))))
  ((equal? (car *argv*) "--check")
   (structural-relation same)
   (let ((current (read-file output-path)))
     (cond
       ((equal? current generated)
        (structural-relation same)
        (print "Rust evaluator dispatch projection is current"))
       ((equal? current generated)
        (structural-relation distinct)
        (second
          (list
            (print "Rust evaluator dispatch projection is stale")
            (car (quote ()))))))))
  ((quote write-projection)
   write-projection
   (second
     (list
       (write-file output-path generated)
       (print "Rust evaluator dispatch projection written")))))
