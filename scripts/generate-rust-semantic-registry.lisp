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

(0011 source-path "lib/surface/semantic-registry.lisp")
(0011 output-path "crates/sens/src/semantic_registry_generated.rs")

(0011 str+
  (0010 args
    (101110 (0010 (acc s) (110011110 acc s)) "" args)))

(0011 registry-form
  (100 (110101001 (110110111 source-path))))

(0011 rows registry-form)

(0011 rust-string
  (0010 (value)
    (110
      ((string-membership-helper value)
       (class-membership string member)
       (11110100 value))
      ((string-membership-helper value)
       (class-membership string nonmember)
       (11110100 (11101110 value))))))


(0011 render-surface
  (0010 (entry)
    (001000 ((name (1001 entry)))
      (110
        ((11110111 name (001 ()))
         (1)
         "")
        ((11110111 name (001 ()))
         (0)
         (str+
           "SemanticSurface { namespace: "
           (rust-string (100 entry))
           ", name: "
           (rust-string name)
           " }, "))))))

(0011 render-surfaces
  (0010 (surfaces)
    (110
      ((010 surfaces)
       ()
       "")
      ((010 surfaces)
       (0)
       (str+
         (render-surface (100 surfaces))
         (render-surfaces (011 surfaces)))))))

(0011 render-row
  (0010 (row)
    (str+
      "    SemanticRow { semantic_id: 0b"
      (11110100 (100 row))
      ", surfaces: &["
      (render-surfaces (011 row))
      "] },\n")))

(0011 render-rows
  (0010 (remaining)
    (110
      ((010 remaining)
       ()
       "")
      ((010 remaining)
       (0)
       (str+
         (render-row (100 remaining))
         (render-rows (011 remaining)))))))

(0011 header
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

(0011 generated
  (str+ header (render-rows rows) "];\n"))

(110
  ((010 *argv*)
   ()
   (1001
     (1110
       (110111100 output-path generated)
       (11011011 "Rust semantic registry projection written"))))
  ((11110111 (100 *argv*) "--check")
   (1)
   (001000 ((current (110110111 output-path)))
     (110
       ((11110111 current generated)
        (1)
        (11011011 "Rust semantic registry projection is current"))
       ((11110111 current generated)
        (0)
        (1001
          (1110
            (11011011 "Rust semantic registry projection is stale")
            (100 (001 ()))))))))
  ((001 write-projection)
   write-projection
   (1001
     (1110
       (110111100 output-path generated)
       (11011011 "Rust semantic registry projection written")))))
