; Mechanical Rust projection of the exact-domain surface registry.
;
; Authority: knowledge/domain-surface-registry.lisp
; This generator emits only width + exact bits + surfaces. It never reads or
; emits a legacy Function8/Sens8 byte.
;
; Usage:
;   cargo run -p sens-cli -- scripts/generate-rust-domain-registry.lisp
;   cargo run -p sens-cli -- scripts/generate-rust-domain-registry.lisp --check

(00001001 source-path "knowledge/domain-surface-registry.lisp")
(00001001 output-path "crates/sens/src/domain_surface_registry_generated.rs")

(00001001 str+
  (00001000 args
    (00111001 (00001000 (acc s) (00111010 acc s)) "" args)))

(00001001 registry-form
  (00000101 (01001011 (10100110 source-path))))

(00001001 rows registry-form)

(00001001 rust-string
  (00001000 (value)
    (00000111
      ((string-membership-helper value)
       (class-membership string member)
       (01001100 value))
      ((string-membership-helper value)
       (class-membership string nonmember)
       (01001100 (01000010 value))))))

(00001001 render-surface
  (00001000 (entry)
    (10011100 ((name (00000101 (00000110 entry))))
      (00000111
        ((00100010 name (00000001 ()))
         (1)
         "")
        ((00100010 name (00000001 ()))
         (0)
         (str+
           "DomainSurface { namespace: "
           (rust-string (00000101 entry))
           ", name: "
           (rust-string name)
           " }, "))))))

(00001001 render-surfaces
  (00001000 (surfaces)
    (00000111
      ((00000010 surfaces)
       ()
       "")
      ((00000010 surfaces)
       (0)
       (str+
         (render-surface (00000101 surfaces))
         (render-surfaces (00000110 surfaces)))))))

(00001001 render-row
  (00001000 (row)
    (10011100
      ((width (00000101 row))
       (bits (00000101 (00000110 row)))
       (surfaces (00000110 (00000110 row))))
      (str+
        "    DomainSurfaceRow { width: "
        (01001100 width)
        ", bits: 0b"
        bits
        ", surfaces: &["
        (render-surfaces surfaces)
        "] },\n"))))

(00001001 render-rows
  (00001000 (remaining)
    (00000111
      ((00000010 remaining)
       ()
       "")
      ((00000010 remaining)
       (0)
       (str+
         (render-row (00000101 remaining))
         (render-rows (00000110 remaining)))))))

(00001001 header
  (str+
    "// GENERATED — DO NOT EDIT BY HAND.\n"
    "// Authority: knowledge/domain-surface-registry.lisp\n"
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

(00001001 generated
  (str+ header (render-rows rows) "];\n"))

(00000111
  ((00100010 *argv* (00000001 ()))
   (1)
   (00101111
     (00100111
       (10100111 output-path generated)
       (01001000 "Rust exact-domain registry projection written"))))
  ((00100010 (00000101 *argv*) "--check")
   (1)
   (10011100 ((current (10100110 output-path)))
     (00000111
       ((00100010 current generated)
        (1)
        (01001000 "Rust exact-domain registry projection is current"))
       ((00100010 current generated)
        (0)
        (00101111
          (00100111
            (01001000 "Rust exact-domain registry projection is stale")
            (00000101 (00000001 ()))))))))
  ((00000001 write-projection)
   write-projection
   (00101111
     (00100111
       (10100111 output-path generated)
       (01001000 "Rust exact-domain registry projection written")))))
