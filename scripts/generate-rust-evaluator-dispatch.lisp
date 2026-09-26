; Lisp-owned generator for the evaluator necessary-form dispatch projection.
;
; Authority: lib/surface/function-signatures.lisp (поле (form ...) рядка таблиці)
; Rust receives only a mechanical execution projection.
;
; Usage:
;   cargo run -p sens-cli -- scripts/generate-rust-evaluator-dispatch.lisp
;   cargo run -p sens-cli -- scripts/generate-rust-evaluator-dispatch.lisp --check

(def source-path "lib/surface/function-signatures.lisp")
(def output-path "crates/sens/src/eval/necessary_forms_generated.rs")

(def str+
  (lambda args
    (reduce (lambda (acc s) (string-append acc s)) "" args)))

;; Особливі форми — рядки таблиці з полем (form lambda|define).
(def all-rows
  (car (read-all (read-file source-path))))

(def row-form
  (lambda (row)
    (second (assoc (quote form) (cdr row)))))

(def form-rows
  (lambda (remaining)
    (cond
      ((atom? remaining)
       ()
       (quote ()))
      ((atom? remaining)
       (0)
       (cond
         ((atom? (assoc (quote form) (cdr (car remaining))))
          ()
          (form-rows (cdr remaining)))
         ((atom? (assoc (quote form) (cdr (car remaining))))
          (0)
          (cons (car remaining) (form-rows (cdr remaining)))))))))

(def rows (form-rows all-rows))

(def rust-mechanism
  (lambda (name)
    (cond
      ((equal? name (quote lambda))
       (1)
       "NecessaryFormMechanism::Lambda")
      ((equal? name (quote define))
       (1)
       "NecessaryFormMechanism::Define")
      ((quote no-known-mechanism)
       no-known-mechanism
       (car (quote ()))))))

(def render-row
  (lambda (row)
    (let ((mechanism (rust-mechanism (row-form row))))
      (cond
        ((atom? mechanism)
         ()
         (car (quote ())))
        ((atom? mechanism)
         (1)
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
       ()
       "")
      ((atom? remaining)
       (0)
       (str+ (render-row (car remaining))
             (render-rows (cdr remaining)))))))

(def header
  (str+
    "// GENERATED — DO NOT EDIT BY HAND.\n"
    "// Authority: lib/surface/function-signatures.lisp\n"
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
   ()
   (second
     (list
       (write-file output-path generated)
       (print "Rust evaluator dispatch projection written"))))
  ((equal? (car *argv*) "--check")
   (1)
   (let ((current (read-file output-path)))
     (cond
       ((equal? current generated)
        (1)
        (print "Rust evaluator dispatch projection is current"))
       ((equal? current generated)
        (0)
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
