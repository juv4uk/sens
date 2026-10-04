; #1422 — generate the mechanical Core×SENS mechanism-admission projection.
;
; Authority: lib/function-table-mechanisms.lisp (profile-routes section).
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
      ((00000010 sections) (0)
       (00000111
         ((00000011 (00000101 (00000101 sections)) name) (1)
          (00000101 sections))
         ((00000011 (00000101 (00000101 sections)) name) (0)
          (find-section name (00000110 sections))))))))

(00001001 profile-rows
  (00000110 (find-section (00000001 profile-routes) metadata)))

(00001001 rust-profile
  (00001000 (profile)
    (00000111
      ((00000011 profile (00000001 core3))
       (1)
       "CoreProfile::Core3")
      (t (00000101 (00000001 ()))))))

(00001001 rust-route-kind
  (00001000 (mechanism)
    (00000111
      ((00000011 mechanism (00000001 registered-host-mechanism))
       (1)
       "ProfileMechanismRouteKind::RegisteredHostMechanism")
      (t (00000101 (00000001 ()))))))

(00001001 render-row
  (00001000 (row)
    (10011101 ((profile (rust-profile (00000101 row)))
           (sid (00101111 row))
           (kind (rust-route-kind (00110000 row))))
      (00000111
        ((00000010 profile) () "")
        ((00000010 kind) () "")
        (t
         (str+
           "    ProfileMechanismRoute { profile: "
           profile
           ", sens: crate::sens!("
           (01001100 sid)
           "), kind: "
           kind
           " },\n"))))))

(00001001 render-rows
  (00001000 (rows)
    (00000111
      ((00000010 rows) () "")
      ((00000010 rows) (0)
       (str+ (render-row (00000101 rows))
             (render-rows (00000110 rows)))))))

(00001001 header
  (str+
    "// GENERATED — DO NOT EDIT BY HAND.\n"
    "// Authority: lib/function-table-mechanisms.lisp (profile-routes)\n"
    "// Generator: scripts/generate-rust-profile-mechanism-routes.lisp\n\n"
    "use crate::{CoreProfile, Sens8};\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(crate) enum ProfileMechanismRouteKind {\n"
    "    RegisteredHostMechanism,\n"
    "}\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "struct ProfileMechanismRoute {\n"
    "    profile: CoreProfile,\n"
    "    sens: Sens8,\n"
    "    kind: ProfileMechanismRouteKind,\n"
    "}\n\n"
    "const PROFILE_MECHANISM_ROUTES: &[ProfileMechanismRoute] = &[\n"))

(00001001 footer
  (str+
    "];\n\n"
    "pub(crate) fn profile_mechanism_route(\n"
    "    profile: CoreProfile,\n"
    "    sens: Sens8,\n"
    ") -> Option<ProfileMechanismRouteKind> {\n"
    "    PROFILE_MECHANISM_ROUTES\n"
    "        .iter()\n"
    "        .find(|row| row.profile == profile && row.sens == sens)\n"
    "        .map(|row| row.kind)\n"
    "}\n"))

(00001001 generated
  (str+ header (render-rows profile-rows) footer))

(00000111
  ((00000010 *argv*)
   ()
   (00101111
     (00100111
       (10100111 output-path generated)
       (01001000 "Rust profile mechanism projection written"))))
  ((00100010 (00000101 *argv*) "--check")
   (1)
   (10011100 ((current (10100110 output-path)))
     (00000111
       ((00100010 current generated)
        (1)
        (01001000 "Rust profile mechanism projection is current"))
       ((00100010 current generated)
        (0)
        (00101111
          (00100111
            (01001000 "Rust profile mechanism projection is stale")
            (00000101 (00000001 ()))))))))
  ((00000001 write-projection)
   write-projection
   (00101111
     (00100111
       (10100111 output-path generated)
       (01001000 "Rust profile mechanism projection written")))))
