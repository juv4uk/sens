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
    (згорнути (функція (acc s) (рядок-додати acc s)) "" args)))

(визначити registry-form
  (перше (читати-всі (читати-файл source-path))))

(визначити rows registry-form)

(визначити rust-string
  (функція (value)
    (за-умовою
      ((класифікувати-рядкове-значення value)
       (class-membership string member)
       (значення-у-текст value))
      ((класифікувати-рядкове-значення value)
       (class-membership string nonmember)
       (значення-у-текст (символ-у-текст value))))))


(визначити render-surface
  (функція (entry)
    (нехай ((name (друге entry)))
      (за-умовою
        ((однакові? name (як-є ()))
         (1)
         "")
        ((однакові? name (як-є ()))
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
      (значення-у-текст (перше row))
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
       (записати-файл output-path generated)
       (друкувати "Rust semantic registry projection written"))))
  ((однакові? (перше *argv*) "--check")
   (1)
   (нехай ((current (читати-файл output-path)))
     (за-умовою
       ((однакові? current generated)
        (1)
        (друкувати "Rust semantic registry projection is current"))
       ((однакові? current generated)
        (0)
        (друге
          (список
            (друкувати "Rust semantic registry projection is stale")
            (перше (як-є ()))))))))
  ((як-є write-projection)
   write-projection
   (друге
     (список
       (записати-файл output-path generated)
       (друкувати "Rust semantic registry projection written")))))
