; Lisp-owned generator for the evaluator necessary-form dispatch projection.
;
; Authority: lib/evaluator-dispatch.lisp
; Rust receives only mechanical SID-keyed mechanism sets.
; Function identity remains the exact eight-bit SID; this projection emits no
; named Rust function-identity enum.
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

(def render-sids-for
  (lambda (remaining wanted-mechanism)
    (cond
      ((atom remaining)
       (structural-kind empty-list)
       "")
      ((atom remaining)
       (structural-kind pair)
       (let ((row (car remaining)))
         (cond
           ((equal? (second row) wanted-mechanism)
            (structural-relation same)
            (str+
              "    0b"
              (write-to-string (car row))
              ",\n"
              (render-sids-for (cdr remaining) wanted-mechanism)))
           ((equal? (second row) wanted-mechanism)
            (structural-relation distinct)
            (render-sids-for (cdr remaining) wanted-mechanism))))))))

(def header
  (str+
    "// GENERATED — DO NOT EDIT BY HAND.\n"
    "// Authority: lib/evaluator-dispatch.lisp\n"
    "// Generator: scripts/generate-rust-evaluator-dispatch.lisp\n"
    "//\n"
    "// Function identity remains only Sid8. These arrays are mechanical\n"
    "// evaluator-routing facts keyed by the exact SID byte.\n\n"))

(def generated
  (str+
    header
    "pub(super) const LAMBDA_FORM_SIDS: &[u8] = &[\n"
    (render-sids-for rows (quote lambda-form))
    "];\n\n"
    "pub(super) const DEFINE_FORM_SIDS: &[u8] = &[\n"
    (render-sids-for rows (quote define-form))
    "];\n"))

(cond
  ((atom *argv*)
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
