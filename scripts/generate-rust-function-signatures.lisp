; Генерує Rust-проєкцію метаданих функцій таблиці за кодом СЕНС.
; Authority: lib/surface/function-signatures.lisp
; Output: crates/sens/src/function_signatures_generated.rs
; Usage:
;   sens scripts/generate-rust-function-signatures.lisp
;   sens scripts/generate-rust-function-signatures.lisp --check

(визначити source-path "lib/surface/function-signatures.lisp")
(визначити output-path "crates/sens/src/function_signatures_generated.rs")

(визначити str+
  (функція args
    (згорнути (функція (acc s) (рядок-додати acc s)) "" args)))

; Rust arity fields are machine projection, not human number presentation.
; number->string deliberately returns the canonical #q2:<bits>/1 wire.
; Arity metadata is non-negative integer data, so consume its binary numerator
; and emit an equivalent Rust binary integer literal.
(визначити wire-integer-bits-onto
  (функція (remaining acc)
    (за-умовою
      ((однакові? (рядок-перший remaining) "/") acc)
      ((атом? (як-є ()))
       (wire-integer-bits-onto
         (рядок-решта remaining)
         (рядок-додати acc (рядок-перший remaining)))))))

(визначити render-rust-nat
  (функція (n)
    (нехай ((wire (число-рядок n)))
      (за-умовою
        ((рядок-префікс? "#q2:" wire)
         (str+
           "0b"
           (wire-integer-bits-onto
             (рядок-решта (рядок-решта (рядок-решта (рядок-решта wire))))
             "")))
        ((атом? (як-є ())) (перше (як-є ())))))))

(визначити rows (перше (читати-всі (читати-файл source-path))))

(визначити field
  (функція (key row)
    (друге (знайти-за-ключем key (решта row)))))

(визначити has-field?
  (функція (key row)
    (за-умовою
      ((атом? (знайти-за-ключем key (решта row))) (як-є ()))
      ((атом? (як-є ())) t))))

(визначити render-kind
  (функція (kind)
    (за-умовою
      ((тотожне? kind (як-є builtin)) "LanguageItemKind::Builtin")
      ((тотожне? kind (як-є syntax)) "LanguageItemKind::SyntaxForm")
      ((тотожне? kind (як-є macro)) "LanguageItemKind::Macro")
      ((атом? (як-є ())) (перше (як-є ()))))))

(визначити render-arity
  (функція (arity)
    (за-умовою
      ((атом? arity)
       (str+ "Arity::Exact(" (render-rust-nat arity) ")"))
      ((атом? (як-є ()))
       (за-умовою
         ((однакові? (перше arity) (як-є at-least))
          (str+ "Arity::AtLeast(" (render-rust-nat (друге arity)) ")"))
         ((однакові? (перше arity) (як-є between))
          (str+ "Arity::Between { min: " (render-rust-nat (друге arity))
                ", max: " (render-rust-nat (третє arity)) " }"))
         ((атом? (як-є ())) (перше (як-є ()))))))))

(визначити render-admitted
  (функція (row)
    (за-умовою
      ((тотожне? (field (як-є surfaces) row) (як-є admitted)) "true")
      ((атом? (як-є ())) "false"))))

(визначити render-row
  (функція (row)
    (str+
      "    FunctionSignature { semantic_id: 0b"
      (значення-у-текст (перше row))
      ", kind: " (render-kind (field (як-є kind) row))
      ", arity: " (render-arity (field (як-є arity) row))
      ", admitted_surfaces: " (render-admitted row)
      ", signature: " (значення-у-текст (field (як-є sig) row))
      ", documentation: " (значення-у-текст (field (як-є doc) row))
      " },\n")))

(визначити render-rows
  (функція (remaining)
    (за-умовою
      ((атом? remaining) "")
      ((атом? (як-є ()))
       (str+ (render-row (перше remaining)) (render-rows (решта remaining)))))))

(визначити header
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

(визначити generated
  (str+ header (render-rows rows) "];\n"))

(за-умовою
  ((атом? *argv*)
   ()
   (друге
     (список
       (записати-файл output-path generated)
       (друкувати "Rust function signatures projection written"))))
  ((однакові? (перше *argv*) "--check")
   (1)
   (за-умовою
     ((однакові? (читати-файл output-path) generated)
      (1)
      (друкувати "Rust function signatures projection is current"))
     ((однакові? (читати-файл output-path) generated)
      (0)
      (друге
        (список
          (друкувати "Rust function signatures projection is stale")
          (перше (як-є ())))))))
  ((як-є write-projection)
   write-projection
   (друге
     (список
       (записати-файл output-path generated)
       (друкувати "Rust function signatures projection written")))))
