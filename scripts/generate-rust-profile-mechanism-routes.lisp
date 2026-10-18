; #1422 — generate the mechanical Core×SENS mechanism-admission projection.
;
; Authority: lib/function-table-mechanisms.lisp (profile-routes section).
; Rust receives only coordinates + route kind. No law, surface, kernel syntax,
; result semantics, or independently editable admission data may live there.
;
; Usage:
;   cargo run -p sens-cli -- scripts/generate-rust-profile-mechanism-routes.lisp
;   cargo run -p sens-cli -- scripts/generate-rust-profile-mechanism-routes.lisp --check

(визначити source-path "lib/function-table-mechanisms.lisp")
(визначити output-path "crates/sens/src/eval/profile_mechanisms_generated.rs")

(визначити str+
  (функція args
    (101110 (0010 (acc s) (110011110 acc s)) "" args)))

(визначити metadata
  (100 (110101001 (110110111 source-path))))

(визначити find-section
  (функція (name sections)
    (за-умовою
      ((атом? sections) () (як-є ()))
      ((атом? sections) (0)
       (за-умовою
         ((тотожне? (перше (перше sections)) name) (1)
          (перше sections))
         ((тотожне? (перше (перше sections)) name) (0)
          (find-section name (решта sections))))))))

(визначити profile-rows
  (решта (find-section (як-є profile-routes) metadata)))

(визначити rust-profile
  (функція (profile)
    (за-умовою
      ((тотожне? profile (як-є core3))
       (1)
       "CoreProfile::Core3")
      (t (перше (як-є ()))))))

(визначити rust-route-kind
  (функція (mechanism)
    (за-умовою
      ((тотожне? mechanism (як-є registered-host-mechanism))
       (1)
       "ProfileMechanismRouteKind::RegisteredHostMechanism")
      (t (перше (як-є ()))))))

(визначити render-row
  (функція (row)
    (001001 ((profile (rust-profile (100 row)))
           (sid (друге row))
           (kind (rust-route-kind (10011 row))))
      (за-умовою
        ((атом? profile) () "")
        ((атом? kind) () "")
        (t
         (str+
           "    ProfileMechanismRoute { profile: "
           profile
           ", sens: crate::sens!("
           (11110100 sid)
           "), kind: "
           kind
           " },\n"))))))

(визначити render-rows
  (функція (rows)
    (за-умовою
      ((атом? rows) () "")
      ((атом? rows) (0)
       (str+ (render-row (перше rows))
             (render-rows (решта rows)))))))

(визначити header
  (str+
    "// GENERATED — DO NOT EDIT BY HAND.\n"
    "// Authority: lib/function-table-mechanisms.lisp (profile-routes)\n"
    "// Generator: scripts/generate-rust-profile-mechanism-routes.lisp\n\n"
    "use crate::{CoreProfile, CoreDomainIdentity};\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "#[allow(dead_code)]\n"
    "pub(crate) enum ProfileMechanismRouteKind {\n"
    "    RegisteredHostMechanism,\n"
    "}\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "struct ProfileMechanismRoute {\n"
    "    profile: CoreProfile,\n"
    "    sens: CoreDomainIdentity,\n"
    "    kind: ProfileMechanismRouteKind,\n"
    "}\n\n"
    "const PROFILE_MECHANISM_ROUTES: &[ProfileMechanismRoute] = &[\n"))

(визначити footer
  (str+
    "];\n\n"
    "pub(crate) fn profile_mechanism_route(\n"
    "    profile: CoreProfile,\n"
    "    sens: CoreDomainIdentity,\n"
    ") -> Option<ProfileMechanismRouteKind> {\n"
    "    PROFILE_MECHANISM_ROUTES\n"
    "        .iter()\n"
    "        .find(|row| row.profile == profile && row.sens == sens)\n"
    "        .map(|row| row.kind)\n"
    "}\n"))

(визначити generated
  (str+ header (render-rows profile-rows) footer))

(за-умовою
  ((атом? *argv*)
   ()
   (друге
     (список
       (110111100 output-path generated)
       (11011011 "Rust profile mechanism projection written"))))
  ((11110111 (100 *argv*) "--check")
   (1)
   (001000 ((current (110110111 output-path)))
     (за-умовою
       ((11110111 current generated)
        (1)
        (11011011 "Rust profile mechanism projection is current"))
       ((11110111 current generated)
        (0)
        (друге
          (список
            (11011011 "Rust profile mechanism projection is stale")
            (перше (як-є ()))))))))
  ((як-є write-projection)
   write-projection
   (друге
     (список
       (110111100 output-path generated)
       (11011011 "Rust profile mechanism projection written")))))
