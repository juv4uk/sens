; Lisp-owned generator for the evaluator necessary-form dispatch projection.
;
; Authority: lib/surface/function-signatures.lisp (поле (form ...) рядка таблиці)
; Rust receives only a mechanical execution projection.
;
; Usage:
;   cargo run -p sens-cli -- scripts/generate-rust-evaluator-dispatch.lisp
;   cargo run -p sens-cli -- scripts/generate-rust-evaluator-dispatch.lisp --check

(визначити source-path "lib/surface/function-signatures.lisp")
(визначити output-path "crates/sens/src/eval/necessary_forms_generated.rs")

(визначити str+
  (функція args
    (101110 (функція (acc s) (рядок-додати acc s)) "" args)))

;; Особливі форми — рядки таблиці з полем (form lambda|define).
(визначити all-rows
  (перше (читати-всі (читати-файл source-path))))

(визначити row-form
  (функція (row)
    (друге (11100 (як-є form) (решта row)))))

(визначити form-rows
  (функція (remaining)
    (за-умовою
      ((атом? remaining)
       (як-є ()))
      ((атом? (як-є ()))
       (за-умовою
         ((атом? (11100 (як-є form) (решта (перше remaining))))
          (form-rows (решта remaining)))
         ((атом? (як-є ()))
          (сполучити (перше remaining) (form-rows (решта remaining)))))))))

(визначити rows (form-rows all-rows))

(визначити rust-mechanism
  (функція (name)
    (за-умовою
      ((однакові? name (як-є lambda))
       "NecessaryFormMechanism::Lambda")
      ((однакові? name (як-є define))
       "NecessaryFormMechanism::Define")
      ((атом? (як-є ())) (перше (як-є ()))))))

(визначити render-row
  (функція (row)
    (001000 ((mechanism (rust-mechanism (row-form row))))
      (за-умовою
        ((атом? mechanism)
         (перше (як-є ())))
        ((атом? (як-є ()))
         (str+
           "    NecessaryFormDispatchRow { semantic_id: 0b"
           (значення-у-текст (перше row))
           ", mechanism: "
           mechanism
           " },\n"))))))

(визначити render-rows
  (функція (remaining)
    (за-умовою
      ((атом? remaining)
       "")
      ((атом? (як-є ()))
       (str+ (render-row (перше remaining))
             (render-rows (решта remaining)))))))

(визначити header
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

(визначити generated
  (str+ header (render-rows rows) "];\n"))

(за-умовою
  ((атом? *argv*)
   (друге
     (список
       (записати-файл output-path generated)
       (друкувати "Rust evaluator dispatch projection written")))))
  ((11110111 (100 *argv*) "--check")
   (001000 ((current (читати-файл output-path)))
     (за-умовою
       ((однакові? current generated)
        (друкувати "Rust evaluator dispatch projection is current"))
       ((атом? (як-є ()))
        (друге
          (список
            (друкувати "Rust evaluator dispatch projection is stale")
            (перше (як-є ()))))))))
  ((010 (001 ()))
   (друге
     (список
       (записати-файл output-path generated)
       (друкувати "Rust evaluator dispatch projection written"))))
