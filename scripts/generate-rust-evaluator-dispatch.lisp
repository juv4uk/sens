; Lisp-owned generator for the evaluator dispatch execution projection.
;
; Authority: lib/evaluator-dispatch.lisp
; Rust receives only a mechanical execution projection.
;
; Usage:
;   cargo run -p my-lisp-cli -- scripts/generate-rust-evaluator-dispatch.lisp
;   cargo run -p my-lisp-cli -- scripts/generate-rust-evaluator-dispatch.lisp --check

(def source-path "lib/evaluator-dispatch.lisp")
(def output-path "crates/my-lisp/src/eval/evaluator_dispatch_generated.rs")

(def str+
  (lambda args
    (reduce (lambda (acc s) (string-append acc s)) "" args)))

(def dispatch-form
  (car (read-all (read-file source-path))))

(def rows (cdr (cdr dispatch-form)))

(def rust-mechanism
  (lambda (name)
    (cond
      ((equal? name (quote empty-list-ground))
       "EvaluatorMechanism::EmptyListGround")
      ((equal? name (quote quote-form))
       "EvaluatorMechanism::QuoteForm")
      ((equal? name (quote atom-primitive))
       "EvaluatorMechanism::AtomPrimitive")
      ((equal? name (quote eq-primitive))
       "EvaluatorMechanism::EqPrimitive")
      ((equal? name (quote cons-primitive))
       "EvaluatorMechanism::ConsPrimitive")
      ((equal? name (quote car-primitive))
       "EvaluatorMechanism::CarPrimitive")
      ((equal? name (quote cdr-primitive))
       "EvaluatorMechanism::CdrPrimitive")
      ((equal? name (quote cond-form))
       "EvaluatorMechanism::CondForm")
      ((equal? name (quote lambda-form))
       "EvaluatorMechanism::LambdaForm")
      ((equal? name (quote define-form))
       "EvaluatorMechanism::DefineForm")
      (t
       (car (quote ()))))))

(def render-row
  (lambda (row)
    (let ((mechanism (rust-mechanism (second row))))
      (cond
        ((atom mechanism)
         (structural-kind empty-list)
         (car (quote ())))
        (t
         (str+
           "    EvaluatorDispatchRow { semantic_id: 0b"
           (write-to-string (car row))
           ", mechanism: "
           mechanism
           " },\n"))))))

(def render-rows
  (lambda (remaining)
    (cond
      ((atom remaining)
       (structural-kind empty-list)
       "")
      ((atom remaining)
       (structural-kind pair)
       (str+ (render-row (car remaining))
             (render-rows (cdr remaining)))))))

(def header
  (str+
    "// GENERATED — DO NOT EDIT BY HAND.\n"
    "// Authority: lib/evaluator-dispatch.lisp\n"
    "// Generator: scripts/generate-rust-evaluator-dispatch.lisp\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(crate) enum EvaluatorMechanism {\n"
    "    EmptyListGround,\n"
    "    QuoteForm,\n"
    "    AtomPrimitive,\n"
    "    EqPrimitive,\n"
    "    ConsPrimitive,\n"
    "    CarPrimitive,\n"
    "    CdrPrimitive,\n"
    "    CondForm,\n"
    "    LambdaForm,\n"
    "    DefineForm,\n"
    "}\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(crate) struct EvaluatorDispatchRow {\n"
    "    pub(crate) semantic_id: u8,\n"
    "    pub(crate) mechanism: EvaluatorMechanism,\n"
    "}\n\n"
    "pub(crate) const EVALUATOR_DISPATCH: &[EvaluatorDispatchRow] = &[\n"))

(def generated
  (str+ header (render-rows rows) "];\n"))

(cond
  ((atom *argv*)
   (write-file output-path generated)
   (print "Rust evaluator dispatch projection written"))
  ((equal? (car *argv*) "--check")
   (let ((current (read-file output-path)))
     (cond
       ((equal? current generated)
        (print "Rust evaluator dispatch projection is current"))
       (t
        (print "Rust evaluator dispatch projection is stale")
        (car (quote ())))))
  (t
   (write-file output-path generated)
   (print "Rust evaluator dispatch projection written")))
)
