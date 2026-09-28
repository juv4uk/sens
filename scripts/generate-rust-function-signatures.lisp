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

; Rust arity fields are machine projection, not human number presentation.
; number->string deliberately returns the canonical #q2:<bits>/1 wire.
; Arity metadata is non-negative integer data, so consume its binary numerator
; and emit an equivalent Rust binary integer literal.
(00001001 wire-integer-bits-onto
  (00001000 (remaining acc)
    (00000111
      ((00100010 (00111111 remaining) "/") (1) acc)
      ((00100010 (00111111 remaining) "/") (0)
       (wire-integer-bits-onto
         (01000000 remaining)
         (00111010 acc (00111111 remaining)))))))

(00001001 render-rust-nat
  (00001000 (n)
    (10011100 ((wire (01000110 n)))
      (00000111
        ((00111101 "#q2:" wire)
         (1)
         (str+
           "0b"
           (wire-integer-bits-onto
             (01000000 (01000000 (01000000 (01000000 wire))))
             "")))
        ((00111101 "#q2:" wire)
         (0)
         (00000101 (00000001 ())))))))

(00001001 rows (00000101 (01001011 (10100110 source-path))))

(00001001 field
  (00001000 (key row)
    (00101111 (00101101 key (00000110 row)))))

(00001001 has-field?
  (00001000 (key row)
    (00000111
      ((00000010 (00101101 key (00000110 row))) () (00000001 ()))
      ((00000010 (00101101 key (00000110 row))) (0) t))))

(00001001 render-kind
  (00001000 (kind)
    (00000111
      ((00100010 kind (00000001 builtin)) (1) "LanguageItemKind::Builtin")
      ((00100010 kind (00000001 syntax)) (1) "LanguageItemKind::SyntaxForm")
      ((00100010 kind (00000001 macro)) (1) "LanguageItemKind::Macro")
      ((00000001 unknown-kind) unknown-kind (00000101 (00000001 ()))))))

(00001001 render-arity
  (00001000 (arity)
    (00000111
      ((00000010 arity) (1)
       (str+ "Arity::Exact(" (render-rust-nat arity) ")"))
      ((00000010 arity) (0)
       (00000111
         ((00100010 (00000101 arity) (00000001 at-least)) (1)
          (str+ "Arity::AtLeast(" (render-rust-nat (00101111 arity)) ")"))
         ((00100010 (00000101 arity) (00000001 between)) (1)
          (str+ "Arity::Between { min: " (render-rust-nat (00101111 arity))
                ", max: " (render-rust-nat (00110000 arity)) " }"))
         ((00000001 unknown-arity) unknown-arity (00000101 (00000001 ()))))))))

(00001001 render-admitted
  (00001000 (row)
    (00000111
      ((00100010 (field (00000001 surfaces) row) (00000001 admitted)) (1) "true")
      ((00100010 (field (00000001 surfaces) row) (00000001 admitted)) (0) "false"))))

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
      ((00000010 remaining) () "")
      ((00000010 remaining) (0)
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
  ((00000010 *argv*)
   ()
   (00101111
     (00100111
       (10100111 output-path generated)
       (01001000 "Rust function signatures projection written"))))
  ((00100010 (00000101 *argv*) "--check")
   (1)
   (00000111
     ((00100010 (10100110 output-path) generated)
      (1)
      (01001000 "Rust function signatures projection is current"))
     ((00100010 (10100110 output-path) generated)
      (0)
      (00101111
        (00100111
          (01001000 "Rust function signatures projection is stale")
          (00000101 (00000001 ())))))))
  ((00000001 write-projection)
   write-projection
   (00101111
     (00100111
       (10100111 output-path generated)
       (01001000 "Rust function signatures projection written")))))
