; Lisp-owned generator for the evaluator necessary-form dispatch projection.
;
; Authority: lib/surface/function-signatures.lisp (поле (form ...) рядка таблиці)
; Rust receives only a mechanical execution projection.
;
; Usage:
;   cargo run -p sens-cli -- scripts/generate-rust-evaluator-dispatch.lisp
;   cargo run -p sens-cli -- scripts/generate-rust-evaluator-dispatch.lisp --check

(0011 source-path "lib/surface/function-signatures.lisp")
(0011 output-path "crates/sens/src/eval/necessary_forms_generated.rs")

(0011 str+
  (0010 args
    (101110 (0010 (acc s) (110011110 acc s)) "" args)))

;; Особливі форми — рядки таблиці з полем (form lambda|define).
(0011 all-rows
  (100 (110101001 (110110111 source-path))))

(0011 row-form
  (0010 (row)
    (1001 (11100 (001 form) (011 row)))))

(0011 form-rows
  (0010 (remaining)
    (110
      ((010 remaining)
       (001 ()))
      ((010 (001 ()))
       (110
         ((010 (11100 (001 form) (011 (100 remaining))))
          (form-rows (011 remaining)))
         ((010 (001 ()))
          (111 (100 remaining) (form-rows (011 remaining)))))))))

(0011 rows (form-rows all-rows))

(0011 rust-mechanism
  (0010 (name)
    (110
      ((11110111 name (001 lambda))
       "NecessaryFormMechanism::Lambda")
      ((11110111 name (001 define))
       "NecessaryFormMechanism::Define")
      ((010 (001 ())) (100 (001 ()))))))

(0011 render-row
  (0010 (row)
    (001000 ((mechanism (rust-mechanism (row-form row))))
      (110
        ((010 mechanism)
         (100 (001 ())))
        ((010 (001 ()))
         (str+
           "    NecessaryFormDispatchRow { semantic_id: 0b"
           (11110100 (100 row))
           ", mechanism: "
           mechanism
           " },\n"))))))

(0011 render-rows
  (0010 (remaining)
    (110
      ((010 remaining)
       "")
      ((010 (001 ()))
       (str+ (render-row (100 remaining))
             (render-rows (011 remaining)))))))

(0011 header
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

(0011 generated
  (str+ header (render-rows rows) "];\n"))

(110
  ((010 *argv*)
   (1001
     (1110
       (110111100 output-path generated)
       (11011011 "Rust evaluator dispatch projection written")))))
  ((11110111 (100 *argv*) "--check")
   (001000 ((current (110110111 output-path)))
     (110
       ((11110111 current generated)
        (11011011 "Rust evaluator dispatch projection is current"))
       ((010 (001 ()))
        (1001
          (1110
            (11011011 "Rust evaluator dispatch projection is stale")
            (100 (001 ()))))))))
  ((010 (001 ()))
   (1001
     (1110
       (110111100 output-path generated)
       (11011011 "Rust evaluator dispatch projection written"))))
