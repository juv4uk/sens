; Lisp-owned Rust projection of the canonical semantic registry.
;
; Authority: lib/surface/semantic-registry.lisp
;
; This generator reads the registry as ordinary Lisp data. It emits only a
; mechanical Rust runtime projection. Rust never parses the canonical Lisp
; source text at runtime.
;
; Usage:
;   cargo run -p my-lisp-cli -- scripts/generate-rust-semantic-registry.lisp
;   cargo run -p my-lisp-cli -- scripts/generate-rust-semantic-registry.lisp --check

(визначити source-path "lib/surface/semantic-registry.lisp")
(визначити output-path "crates/sens/src/semantic_registry_generated.rs")

(визначити str+
  (функція args
    (101110 (0010 (acc s) (110011110 acc s)) "" args)))

(визначити registry-form
  (100 (110101001 (110110111 source-path))))

(визначити rows registry-form)

(визначити rust-string
  (функція (value)
    (за-умовою
      ((string-membership-helper value)
       (class-membership string member)
       (11110100 value))
      ((string-membership-helper value)
       (class-membership string nonmember)
       (11110100 (11101110 value))))))


(визначити render-surface
  (функція (entry)
    (001000 ((name (1001 entry)))
      (за-умовою
        ((11110111 name (001 ()))
         (1)
         "")
        ((11110111 name (001 ()))
         (0)
         (str+
           "SemanticSurface { namespace: "
           (rust-string (перше entry))
           ", name: "
           (rust-string name)
           " }, "))))))

(визначити render-surfaces
  (функція (surfaces)
    (за-умовою
      ((атом? surfaces)
       ()
       "")
      ((атом? surfaces)
       (0)
       (str+
         (render-surface (перше surfaces))
         (render-surfaces (решта surfaces)))))))

(визначити render-row
  (функція (row)
    (str+
      "    SemanticRow { semantic_id: 0b"
      (11110100 (100 row))
      ", surfaces: &["
      (render-surfaces (решта row))
      "] },\n")))

(визначити render-rows
  (функція (remaining)
    (за-умовою
      ((атом? remaining)
       ()
       "")
      ((атом? remaining)
       (0)
       (str+
         (render-row (перше remaining))
         (render-rows (решта remaining)))))))

(визначити header
  (str+
    "// GENERATED — DO NOT EDIT BY HAND.\n"
    "// Authority: lib/surface/semantic-registry.lisp\n"
    "// Generator: scripts/generate-rust-semantic-registry.lisp\n"
    "//\n"
    "// Binary identities below are an implementation projection only.\n"
    "// Canonical semantic identity remains the bare binary token in the Lisp registry.\n"
    "\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(super) struct SemanticSurface {\n"
    "    pub(super) namespace: &'static str,\n"
    "    pub(super) name: &'static str,\n"
    "}\n"
    "\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(super) struct SemanticRow {\n"
    "    pub(super) semantic_id: u8,\n"
    "    pub(super) surfaces: &'static [SemanticSurface],\n"
    "}\n"
    "\n"
    "pub(super) const SEMANTIC_ROWS: &[SemanticRow] = &[\n"))

(визначити generated
  (str+ header (render-rows rows) "];\n"))

(за-умовою
  ((атом? *argv*)
   ()
   (друге
     (список
       (110111100 output-path generated)
       (11011011 "Rust semantic registry projection written"))))
  ((11110111 (100 *argv*) "--check")
   (1)
   (001000 ((current (110110111 output-path)))
     (за-умовою
       ((11110111 current generated)
        (1)
        (11011011 "Rust semantic registry projection is current"))
       ((11110111 current generated)
        (0)
        (друге
          (список
            (11011011 "Rust semantic registry projection is stale")
            (перше (як-є ()))))))))
  ((як-є write-projection)
   write-projection
   (друге
     (список
       (110111100 output-path generated)
       (11011011 "Rust semantic registry projection written")))))
