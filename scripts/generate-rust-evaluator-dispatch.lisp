; Lisp-owned generator for the evaluator necessary-form dispatch projection.
;
; Authority: lib/surface/function-signatures.lisp (поле (form ...) рядка таблиці)
; Rust receives only a mechanical execution projection.
;
; Usage:
;   cargo run -p sens-cli -- scripts/generate-rust-evaluator-dispatch.lisp
;   cargo run -p sens-cli -- scripts/generate-rust-evaluator-dispatch.lisp --check

(00001001 source-path "lib/surface/function-signatures.lisp")
(00001001 output-path "crates/sens/src/eval/necessary_forms_generated.rs")

(00001001 str+
  (00001000 args
    (00111001 (00001000 (acc s) (00111010 acc s)) "" args)))

;; Особливі форми — рядки таблиці з полем (form lambda|define).
(00001001 all-rows
  (00000101 (01001011 (10100110 source-path))))

(00001001 row-form
  (00001000 (row)
    (00101111 (00101101 (00000001 form) (00000110 row)))))

(00001001 form-rows
  (00001000 (remaining)
    (00000111
      ((00000010 remaining)
       ()
       (00000001 ()))
      ((00000010 remaining)
       (0)
       (00000111
         ((00000010 (00101101 (00000001 form) (00000110 (00000101 remaining))))
          ()
          (form-rows (00000110 remaining)))
         ((00000010 (00101101 (00000001 form) (00000110 (00000101 remaining))))
          (0)
          (00000100 (00000101 remaining) (form-rows (00000110 remaining)))))))))

(00001001 rows (form-rows all-rows))

(00001001 rust-mechanism
  (00001000 (name)
    (00000111
      ((00100010 name (00000001 lambda))
       (1)
       "NecessaryFormMechanism::Lambda")
      ((00100010 name (00000001 define))
       (1)
       "NecessaryFormMechanism::Define")
      ((00000001 no-known-mechanism)
       no-known-mechanism
       (00000101 (00000001 ()))))))

(00001001 render-row
  (00001000 (row)
    (10011100 ((mechanism (rust-mechanism (row-form row))))
      (00000111
        ((00000010 mechanism)
         ()
         (00000101 (00000001 ())))
        ((00000010 mechanism)
         (1)
         (str+
           "    NecessaryFormDispatchRow { legacy_registry_id: 0b"
           (01001100 (00000101 row))
           ", mechanism: "
           mechanism
           " },\n"))))))

(00001001 render-rows
  (00001000 (remaining)
    (00000111
      ((00000010 remaining)
       ()
       "")
      ((00000010 remaining)
       (0)
       (str+ (render-row (00000101 remaining))
             (render-rows (00000110 remaining)))))))

(00001001 header
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
    "    pub(super) legacy_registry_id: u8,\n"
    "    pub(super) mechanism: NecessaryFormMechanism,\n"
    "}\n\n"
    "pub(super) const NECESSARY_FORM_DISPATCH: &[NecessaryFormDispatchRow] = &[\n"))

(00001001 generated
  (str+ header (render-rows rows) "];\n"))

(00000111
  ((00000010 *argv*)
   ()
   (00101111
     (00100111
       (10100111 output-path generated)
       (01001000 "Rust evaluator dispatch projection written"))))
  ((00100010 (00000101 *argv*) "--check")
   (1)
   (10011100 ((current (10100110 output-path)))
     (00000111
       ((00100010 current generated)
        (1)
        (01001000 "Rust evaluator dispatch projection is current"))
       ((00100010 current generated)
        (0)
        (00101111
          (00100111
            (01001000 "Rust evaluator dispatch projection is stale")
            (00000101 (00000001 ()))))))))
  ((00000001 write-projection)
   write-projection
   (00101111
     (00100111
       (10100111 output-path generated)
       (01001000 "Rust evaluator dispatch projection written")))))
