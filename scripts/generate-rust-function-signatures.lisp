; Генерує Rust-проєкцію метаданих функцій таблиці за кодом СЕНС.
; Authority: lib/surface/function-signatures.lisp
; Output: crates/sens/src/function_signatures_generated.rs
; Usage:
;   sens scripts/generate-rust-function-signatures.lisp
;   sens scripts/generate-rust-function-signatures.lisp --check

(0011 source-path "lib/surface/function-signatures.lisp")
(0011 output-path "crates/sens/src/function_signatures_generated.rs")

(0011 str+
  (0010 args
    (101110 (0010 (acc s) (110011110 acc s)) "" args)))

; Rust arity fields are machine projection, not human number presentation.
; number->string deliberately returns the canonical #q2:<bits>/1 wire.
; Arity metadata is non-negative integer data, so consume its binary numerator
; and emit an equivalent Rust binary integer literal.
(0011 wire-integer-bits-onto
  (0010 (remaining acc)
    (110
      ((11110111 (110101011 remaining) "/") acc)
      ((010 (001 ()))
       (wire-integer-bits-onto
         (110011101 remaining)
         (110011110 acc (110101011 remaining)))))))

(0011 render-rust-nat
  (0010 (n)
    (001000 ((wire (110111001 n)))
      (110
        ((110101010 "#q2:" wire)
         (str+
           "0b"
           (wire-integer-bits-onto
             (110011101 (110011101 (110011101 (110011101 wire))))
             "")))
        ((010 (001 ())) (100 (001 ())))))))

(0011 rows (100 (110101001 (110110111 source-path))))

(0011 field
  (0010 (key row)
    (1001 (11100 key (011 row)))))

(0011 has-field?
  (0010 (key row)
    (110
      ((010 (11100 key (011 row))) (001 ()))
      ((010 (001 ())) t))))

(0011 render-kind
  (0010 (kind)
    (110
      ((101 kind (001 builtin)) "LanguageItemKind::Builtin")
      ((101 kind (001 syntax)) "LanguageItemKind::SyntaxForm")
      ((101 kind (001 macro)) "LanguageItemKind::Macro")
      ((010 (001 ())) (100 (001 ()))))))

(0011 render-arity
  (0010 (arity)
    (110
      ((010 arity)
       (str+ "Arity::Exact(" (render-rust-nat arity) ")"))
      ((010 (001 ()))
       (110
         ((11110111 (100 arity) (001 at-least))
          (str+ "Arity::AtLeast(" (render-rust-nat (1001 arity)) ")"))
         ((11110111 (100 arity) (001 between))
          (str+ "Arity::Between { min: " (render-rust-nat (1001 arity))
                ", max: " (render-rust-nat (10011 arity)) " }"))
         ((010 (001 ())) (100 (001 ()))))))))

(0011 render-admitted
  (0010 (row)
    (110
      ((101 (field (001 surfaces) row) (001 admitted)) "true")
      ((010 (001 ())) "false"))))

(0011 render-row
  (0010 (row)
    (str+
      "    FunctionSignature { semantic_id: 0b"
      (11110100 (100 row))
      ", kind: " (render-kind (field (001 kind) row))
      ", arity: " (render-arity (field (001 arity) row))
      ", admitted_surfaces: " (render-admitted row)
      ", signature: " (11110100 (field (001 sig) row))
      ", documentation: " (11110100 (field (001 doc) row))
      " },\n")))

(0011 render-rows
  (0010 (remaining)
    (110
      ((010 remaining) "")
      ((010 (001 ()))
       (str+ (render-row (100 remaining)) (render-rows (011 remaining)))))))

(0011 header
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

(0011 generated
  (str+ header (render-rows rows) "];\n"))

(110
  ((010 *argv*)
   ()
   (1001
     (1110
       (110111100 output-path generated)
       (11011011 "Rust function signatures projection written"))))
  ((11110111 (100 *argv*) "--check")
   (1)
   (110
     ((11110111 (110110111 output-path) generated)
      (1)
      (11011011 "Rust function signatures projection is current"))
     ((11110111 (110110111 output-path) generated)
      (0)
      (1001
        (1110
          (11011011 "Rust function signatures projection is stale")
          (100 (001 ())))))))
  ((001 write-projection)
   write-projection
   (1001
     (1110
       (110111100 output-path generated)
       (11011011 "Rust function signatures projection written")))))
