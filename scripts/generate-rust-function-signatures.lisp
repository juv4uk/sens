; Генерує Rust-проєкцію метаданих функцій таблиці за кодом СЕНС.
; Authority: lib/surface/function-signatures.lisp
; Output: crates/sens/src/function_signatures_generated.rs
; Usage:
;   sens scripts/generate-rust-function-signatures.lisp
;   sens scripts/generate-rust-function-signatures.lisp --check

(def source-path "lib/surface/function-signatures.lisp")
(def output-path "crates/sens/src/function_signatures_generated.rs")

(def str+
  (lambda args
    (reduce (lambda (acc s) (string-append acc s)) "" args)))

(def rows (car (read-all (read-file source-path))))

(def field
  (lambda (key row)
    (second (assoc key (cdr row)))))

(def has-field?
  (lambda (key row)
    (cond
      ((atom? (assoc key (cdr row))) (structural-kind empty-list) (quote ()))
      ((atom? (assoc key (cdr row))) (structural-kind pair) t))))

(def render-kind
  (lambda (kind)
    (cond
      ((equal? kind (quote builtin)) (structural-relation same) "LanguageItemKind::Builtin")
      ((equal? kind (quote syntax)) (structural-relation same) "LanguageItemKind::SyntaxForm")
      ((equal? kind (quote macro)) (structural-relation same) "LanguageItemKind::Macro")
      ((quote unknown-kind) unknown-kind (car (quote ()))))))

(def render-arity
  (lambda (arity)
    (cond
      ((atom? arity) (structural-kind atom)
       (str+ "Arity::Exact(" (number->string arity) ")"))
      ((atom? arity) (structural-kind pair)
       (cond
         ((equal? (car arity) (quote at-least)) (structural-relation same)
          (str+ "Arity::AtLeast(" (number->string (second arity)) ")"))
         ((equal? (car arity) (quote between)) (structural-relation same)
          (str+ "Arity::Between { min: " (number->string (second arity))
                ", max: " (number->string (third arity)) " }"))
         ((quote unknown-arity) unknown-arity (car (quote ()))))))))

(def render-admitted
  (lambda (row)
    (cond
      ((equal? (field (quote surfaces) row) (quote admitted)) (structural-relation same) "true")
      ((equal? (field (quote surfaces) row) (quote admitted)) (structural-relation distinct) "false"))))

(def render-row
  (lambda (row)
    (str+
      "    FunctionSignature { semantic_id: 0b"
      (write-to-string (car row))
      ", kind: " (render-kind (field (quote kind) row))
      ", arity: " (render-arity (field (quote arity) row))
      ", admitted_surfaces: " (render-admitted row)
      ", signature: " (write-to-string (field (quote sig) row))
      ", documentation: " (write-to-string (field (quote doc) row))
      " },\n")))

(def render-rows
  (lambda (remaining)
    (cond
      ((atom? remaining) (structural-kind empty-list) "")
      ((atom? remaining) (structural-kind pair)
       (str+ (render-row (car remaining)) (render-rows (cdr remaining)))))))

(def header
  (str+
    "// GENERATED — DO NOT EDIT BY HAND.\n"
    "// Authority: lib/surface/function-signatures.lisp\n"
    "// Generator: scripts/generate-rust-function-signatures.lisp\n\n"
    "use crate::language_items::{Arity, LanguageItemKind};\n\n"
    "#[derive(Clone, Copy, Debug)]\n"
    "pub(crate) struct FunctionSignature {\n"
    "    pub(crate) semantic_id: u8,\n"
    "    pub(crate) kind: LanguageItemKind,\n"
    "    pub(crate) arity: Arity,\n"
    "    pub(crate) admitted_surfaces: bool,\n"
    "    pub(crate) signature: &'static str,\n"
    "    pub(crate) documentation: &'static str,\n"
    "}\n\n"
    "pub(crate) const FUNCTION_SIGNATURES: &[FunctionSignature] = &[\n"))

(def generated
  (str+ header (render-rows rows) "];\n"))

(cond
  ((atom? *argv*)
   (structural-kind empty-list)
   (second
     (list
       (write-file output-path generated)
       (print "Rust function signatures projection written"))))
  ((equal? (car *argv*) "--check")
   (structural-relation same)
   (cond
     ((equal? (read-file output-path) generated)
      (structural-relation same)
      (print "Rust function signatures projection is current"))
     ((equal? (read-file output-path) generated)
      (structural-relation distinct)
      (second
        (list
          (print "Rust function signatures projection is stale")
          (car (quote ())))))))
  ((quote write-projection)
   write-projection
   (second
     (list
       (write-file output-path generated)
       (print "Rust function signatures projection written")))))
