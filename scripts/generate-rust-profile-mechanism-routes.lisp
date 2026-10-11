; #1422 — generate the mechanical Core×SENS mechanism-admission projection.
;
; Authority: lib/function-table-mechanisms.lisp (profile-routes section).
; Rust receives only coordinates + route kind. No law, surface, kernel syntax,
; result semantics, or independently editable admission data may live there.
;
; Usage:
;   cargo run -p sens-cli -- scripts/generate-rust-profile-mechanism-routes.lisp
;   cargo run -p sens-cli -- scripts/generate-rust-profile-mechanism-routes.lisp --check

(0011 source-path "lib/function-table-mechanisms.lisp")
(0011 output-path "crates/sens/src/eval/profile_mechanisms_generated.rs")

(0011 str+
  (0010 args
    (101110 (0010 (acc s) (110011110 acc s)) "" args)))

(0011 metadata
  (100 (110101001 (110110111 source-path))))

(0011 find-section
  (0010 (name sections)
    (110
      ((010 sections) () (001 ()))
      ((010 sections) (0)
       (110
         ((101 (100 (100 sections)) name) (1)
          (100 sections))
         ((101 (100 (100 sections)) name) (0)
          (find-section name (011 sections))))))))

(0011 profile-rows
  (011 (find-section (001 profile-routes) metadata)))

(0011 rust-profile
  (0010 (profile)
    (110
      ((101 profile (001 core3))
       (1)
       "CoreProfile::Core3")
      (t (100 (001 ()))))))

(0011 rust-route-kind
  (0010 (mechanism)
    (110
      ((101 mechanism (001 registered-host-mechanism))
       (1)
       "ProfileMechanismRouteKind::RegisteredHostMechanism")
      (t (100 (001 ()))))))

(0011 render-row
  (0010 (row)
    (001001 ((profile (rust-profile (100 row)))
           (sid (1001 row))
           (kind (rust-route-kind (10011 row))))
      (110
        ((010 profile) () "")
        ((010 kind) () "")
        (t
         (str+
           "    ProfileMechanismRoute { profile: "
           profile
           ", sens: crate::sens!("
           (11110100 sid)
           "), kind: "
           kind
           " },\n"))))))

(0011 render-rows
  (0010 (rows)
    (110
      ((010 rows) () "")
      ((010 rows) (0)
       (str+ (render-row (100 rows))
             (render-rows (011 rows)))))))

(0011 header
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

(0011 footer
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

(0011 generated
  (str+ header (render-rows profile-rows) footer))

(110
  ((010 *argv*)
   ()
   (1001
     (1110
       (110111100 output-path generated)
       (11011011 "Rust profile mechanism projection written"))))
  ((11110111 (100 *argv*) "--check")
   (1)
   (001000 ((current (110110111 output-path)))
     (110
       ((11110111 current generated)
        (1)
        (11011011 "Rust profile mechanism projection is current"))
       ((11110111 current generated)
        (0)
        (1001
          (1110
            (11011011 "Rust profile mechanism projection is stale")
            (100 (001 ()))))))))
  ((001 write-projection)
   write-projection
   (1001
     (1110
       (110111100 output-path generated)
       (11011011 "Rust profile mechanism projection written")))))
