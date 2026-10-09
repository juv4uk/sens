; #1422/#2375 — generate the explicit mechanism-lab admission projection.
;
; Authority: lib/function-table-mechanisms.lisp (lab-routes section).
; Rust receives only coordinates + route kind. No law, surface, kernel syntax,
; result semantics, or independently editable admission data may live there.
;
; Usage:
;   cargo run -p sens-cli -- scripts/generate-rust-profile-mechanism-routes.lisp
;   cargo run -p sens-cli -- scripts/generate-rust-profile-mechanism-routes.lisp --check

(00001001 source-path "lib/function-table-mechanisms.lisp")
(00001001 output-path "crates/sens/src/eval/profile_mechanisms_generated.rs")

(00001001 str+
  (00001000 args
    (00111001 (00001000 (acc s) (00111010 acc s)) "" args)))

(00001001 metadata
  (00000101 (01001011 (10100110 source-path))))

(00001001 find-section
  (00001000 (name sections)
    (00000111
      ((00000010 sections) () (00000001 ()))
      ((00000010 sections) (#b0)
       (00000111
         ((00000011 (00000101 (00000101 sections)) name) (#b1)
          (00000101 sections))
         ((00000011 (00000101 (00000101 sections)) name) (#b0)
          (find-section name (00000110 sections))))))))

(00001001 lab-rows
  (00000110 (find-section (00000001 lab-routes) metadata)))

(00001001 rust-route-kind
  (00001000 (mechanism)
    (00000111
      ((00000011 mechanism (00000001 registered-host-mechanism))
       (#b1)
       "ProfileMechanismRouteKind::RegisteredHostMechanism")
      (t (00000101 (00000001 ()))))))

(00001001 render-row
  (00001000 (row)
    (10011101 ((sid (00000101 row))
           (kind (rust-route-kind (00101111 row))))
      (00000111
        ((00000010 kind) () "")
        (t
         (str+
           "    MechanismLabRoute { sens: crate::sens!("
           (01001100 sid)
           "), kind: "
           kind
           " },\n"))))))

(00001001 render-rows
  (00001000 (rows)
    (00000111
      ((00000010 rows) () "")
      ((00000010 rows) (#b0)
       (str+ (render-row (00000101 rows))
             (render-rows (00000110 rows)))))))

(00001001 header
  (str+
    "// GENERATED — DO NOT EDIT BY HAND.\n"
    "// Authority: lib/function-table-mechanisms.lisp (lab-routes)\n"
    "// Generator: scripts/generate-rust-profile-mechanism-routes.lisp\n\n"
    "use crate::Sens8;\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(crate) enum MechanismLabRouteKind {\n"
    "    RegisteredHostMechanism,\n"
    "}\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "struct MechanismLabRoute {\n"
    "    sens: Sens8,\n"
    "    kind: MechanismLabRouteKind,\n"
    "}\n\n"
    "const MECHANISM_LAB_ROUTES: &[MechanismLabRoute] = &[\n"))

(00001001 footer
  (str+
    "];\n\n"
    "pub(crate) fn mechanism_lab_route(\n"
    "    sens: Sens8,\n"
    ") -> Option<MechanismLabRouteKind> {\n"
    "    MECHANISM_LAB_ROUTES\n"
    "        .iter()\n"
    "        .find(|row| row.sens == sens)\n"
    "        .map(|row| row.kind)\n"
    "}\n"))

(00001001 generated
  (str+ header (render-rows lab-rows) footer))

(00000111
  ((00000010 *argv*)
   ()
   (00101111
     (00100111
       (10100111 output-path generated)
       (01001000 "Rust mechanism-lab projection written"))))
  ((00100010 (00000101 *argv*) "--check")
   (#b1)
   (10011100 ((current (10100110 output-path)))
     (00000111
       ((00100010 current generated)
        (#b1)
        (01001000 "Rust mechanism-lab projection is current"))
       ((00100010 current generated)
        (#b0)
        (00101111
          (00100111
            (01001000 "Rust mechanism-lab projection is stale")
            (00000101 (00000001 ()))))))))
  ((00000001 write-projection)
   write-projection
   (00101111
     (00100111
       (10100111 output-path generated)
       (01001000 "Rust mechanism-lab projection written")))))
