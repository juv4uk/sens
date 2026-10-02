; Генерує Rust-проєкцію метаданих функцій таблиці за кодом СЕНС.
; Authority: lib/surface/function-signatures.lisp
; Output: crates/sens/src/function_signatures_generated.rs
; Usage:
;   sens scripts/generate-rust-function-signatures.lisp
;   sens scripts/generate-rust-function-signatures.lisp --check

(00001001 source-path "lib/surface/function-signatures.lisp")
(00001001 output-path "crates/sens/src/function_signatures_generated.rs")

(00001001 str+
  (00001000 args
    (00111001 (00001000 (acc s) (00111010 acc s)) "" args)))

; Local exact D1 control helpers for generator-only structure tests.
(00001001 sig-predicate-yes
  (00001000 ()
    (00000010 (00000001 ()))))

(00001001 sig-predicate-no
  (00001000 ()
    (00000010 (00000001 (00000000)))))

(00001001 sig-predicate-no?
  (00001000 (value)
    (00000011 value (sig-predicate-no))))

(00001001 sig-empty-list?
  (00001000 (value)
    (00100010 value (00000001 ()))))

(00001001 sig-nonempty-atom?
  (00001000 (value)
    (00000111
      ((sig-empty-list? value) (sig-predicate-no))
      ((00000010 value) (sig-predicate-yes))
      ((sig-predicate-yes) (sig-predicate-no)))))

(00001001 sig-pair?
  (00001000 (value)
    (00000111
      ((00000010 value) (sig-predicate-no))
      ((sig-predicate-yes) (sig-predicate-yes)))))

; Rust arity fields are machine projection, not human number presentation.
; number->string deliberately returns the canonical #q2:<bits>/1 wire.
; Arity metadata is non-negative integer data, so consume its binary numerator
; and emit an equivalent Rust binary integer literal.
(00001001 wire-integer-bits-onto
  (00001000 (remaining acc)
    (00000111
      ((00100010 (00111111 remaining) "/") acc)
      ((sig-predicate-yes)
       (wire-integer-bits-onto
         (01000000 remaining)
         (00111010 acc (00111111 remaining)))))))

(00001001 render-rust-nat
  (00001000 (n)
    (10011100 ((wire (01000110 n)))
      (00000111
        ((00111101 "#q2:" wire)
         (str+
           "0b"
           (wire-integer-bits-onto
             (01000000 (01000000 (01000000 (01000000 wire))))
             "")))
        ((sig-predicate-yes)
         (00000101 (00000001 ())))))))

(00001001 rows (00000101 (01001011 (10100110 source-path))))

(00001001 field
  (00001000 (key row)
    (00101111 (00101101 key (00000110 row)))))

(00001001 has-field?
  (00001000 (key row)
    (sig-pair? (00101101 key (00000110 row)))))

(00001001 render-kind
  (00001000 (kind)
    (00000111
      ((00100010 kind (00000001 builtin)) "LanguageItemKind::Builtin")
      ((00100010 kind (00000001 syntax)) "LanguageItemKind::SyntaxForm")
      ((00100010 kind (00000001 macro)) "LanguageItemKind::Macro")
      ((sig-predicate-yes) (00000101 (00000001 ()))))))

(00001001 render-arity
  (00001000 (arity)
    (00000111
      ((sig-nonempty-atom? arity)
       (str+ "Arity::Exact(" (render-rust-nat arity) ")"))
      ((sig-pair? arity)
       (00000111
         ((00100010 (00000101 arity) (00000001 at-least))
          (str+ "Arity::AtLeast(" (render-rust-nat (00101111 arity)) ")"))
         ((00100010 (00000101 arity) (00000001 between))
          (str+ "Arity::Between { min: " (render-rust-nat (00101111 arity))
                ", max: " (render-rust-nat (00110000 arity)) " }"))
         ((sig-predicate-yes) (00000101 (00000001 ()))))))))

(00001001 render-admitted
  (00001000 (row)
    (00000111
      ((00100010 (field (00000001 surfaces) row) (00000001 admitted)) "true")
      ((sig-predicate-yes) "false"))))

(00001001 render-row
  (00001000 (row)
    (str+
      "    FunctionSignature { semantic_id: 0b"
      (01001100 (00000101 row))
      ", kind: " (render-kind (field (00000001 kind) row))
      ", arity: " (render-arity (field (00000001 arity) row))
      ", admitted_surfaces: " (render-admitted row)
      ", signature: " (01001100 (field (00000001 sig) row))
      ", documentation: " (01001100 (field (00000001 doc) row))
      " },\n")))

(00001001 render-rows
  (00001000 (remaining)
    (00000111
      ((sig-empty-list? remaining) "")
      ((sig-pair? remaining)
       (str+ (render-row (00000101 remaining)) (render-rows (00000110 remaining)))))))

(00001001 header
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

(00001001 generated
  (str+ header (render-rows rows) "];\n"))

(00000111
  ((sig-empty-list? *argv*)
   (00101111
     (00100111
       (10100111 output-path generated)
       (01001000 "Rust function signatures projection written"))))
  ((00100010 (00000101 *argv*) "--check")
   (00000111
     ((00100010 (10100110 output-path) generated)
      (01001000 "Rust function signatures projection is current"))
     ((sig-predicate-yes)
      (00101111
        (00100111
          (01001000 "Rust function signatures projection is stale")
          (00000101 (00000001 ())))))))
  ((sig-predicate-yes)
   (00101111
     (00100111
       (10100111 output-path generated)
       (01001000 "Rust function signatures projection written")))))
