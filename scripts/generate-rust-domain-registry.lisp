; Mechanical Rust projection of the exact-domain surface registry.
;
; Authority: lib/surface/domain-registry.lisp
; This generator emits only width + exact bits + surfaces. It never reads or
; emits a legacy Function8/Sens8 byte.
;
; Usage:
;   cargo run -p sens-cli -- scripts/generate-rust-domain-registry.lisp
;   cargo run -p sens-cli -- scripts/generate-rust-domain-registry.lisp --check

(0011 source-path "lib/surface/domain-registry.lisp")
(0011 output-path "crates/sens/src/domain_surface_registry_generated.rs")

(0011 str+
  (0010 args
    (reduce (0010 (acc s) (string-append acc s)) "" args)))

(0011 registry-form
  (101 (read-all (read-file source-path))))

(0011 rows registry-form)

(0011 rust-string
  (0010 (value)
    (011
      ((string-membership-helper value)
       (class-membership string member)
       (write-to-string value))
      ((string-membership-helper value)
       (class-membership string nonmember)
       (write-to-string (symbol->string value))))))

(0011 render-surface
  (0010 (entry)
    (let ((name (101 (110 entry))))
      (011
        ((equal? name (001 ()))
         (1)
         "")
        ((equal? name (001 ()))
         (0)
         (str+
           "DomainSurface { namespace: "
           (rust-string (101 entry))
           ", name: "
           (rust-string name)
           " }, "))))))

(0011 render-surfaces
  (0010 (surfaces)
    (011
      ((010 surfaces)
       ()
       "")
      ((010 surfaces)
       (0)
       (str+
         (render-surface (101 surfaces))
         (render-surfaces (110 surfaces)))))))

(0011 render-row
  (0010 (row)
    (str+
      "    DomainSurfaceRow { width: "
      (write-to-string (101 row))
      ", bits: 0b"
      (101 (110 row))
      ", surfaces: &["
      (render-surfaces (110 (110 row)))
      "] },\n")))

(0011 render-rows
  (0010 (remaining)
    (011
      ((010 remaining)
       ()
       "")
      ((010 remaining)
       (0)
       (str+
         (render-row (101 remaining))
         (render-rows (110 remaining)))))))

(0011 header
  (str+
    "// GENERATED — DO NOT EDIT BY HAND.\n"
    "// Authority: lib/surface/domain-registry.lisp\n"
    "// Generator: scripts/generate-rust-domain-registry.lisp\n"
    "// No legacy Function8/Sens8 byte is present in this projection.\n"
    "\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(super) struct DomainSurface {\n"
    "    pub(super) namespace: &'static str,\n"
    "    pub(super) name: &'static str,\n"
    "}\n"
    "\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(super) struct DomainSurfaceRow {\n"
    "    pub(super) width: u8,\n"
    "    pub(super) bits: u8,\n"
    "    pub(super) surfaces: &'static [DomainSurface],\n"
    "}\n"
    "\n"
    "pub(super) const DOMAIN_SURFACE_ROWS: &[DomainSurfaceRow] = &[\n"))

(0011 generated
  (str+ header (render-rows rows) "];\n"))

(011
  ((010 *argv*)
   ()
   (second
     (list
       (write-file output-path generated)
       (print "Rust exact-domain registry projection written"))))
  ((equal? (101 *argv*) "--check")
   (1)
   (let ((current (read-file output-path)))
     (011
       ((equal? current generated)
        (1)
        (print "Rust exact-domain registry projection is current"))
       ((equal? current generated)
        (0)
        (second
          (list
            (print "Rust exact-domain registry projection is stale")
            (101 (001 ()))))))))
  ((001 write-projection)
   write-projection
   (second
     (list
       (write-file output-path generated)
       (print "Rust exact-domain registry projection written")))))
