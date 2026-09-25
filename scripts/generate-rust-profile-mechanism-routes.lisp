; #1422 — generate the mechanical Core×SENS mechanism-admission projection.
;
; Authority: lib/function-table-mechanisms.lisp (profile-routes section).
; Rust receives only coordinates + route kind. No law, surface, kernel syntax,
; result semantics, or independent admission data may be authored in Rust.
;
; Usage:
;   cargo run -p my-lisp-cli -- scripts/generate-rust-profile-mechanism-routes.lisp
;   cargo run -p my-lisp-cli -- scripts/generate-rust-profile-mechanism-routes.lisp --check

(def source-path "lib/function-table-mechanisms.lisp")
(def output-path "crates/my-lisp/src/eval/profile_mechanisms_generated.rs")

(def str+
  (lambda args
    (reduce (lambda (acc s) (string-append acc s)) "" args)))

(def metadata
  (car (read-all (read-file source-path))))

(def find-section
  (lambda (name sections)
    (cond
      ((atom sections) (structural-kind empty-list) (quote ()))
      ((atom sections) (structural-kind pair)
       (cond
         ((eq (car (car sections)) name) (identity-relation same)
          (car sections))
         ((eq (car (car sections)) name) (identity-relation distinct)
          (find-section name (cdr sections))))))))

(def profile-rows
  (cdr (find-section (quote profile-routes) metadata)))

(def rust-profile
  (lambda (profile)
    (cond
      ((eq profile (quote core3)) (identity-relation same) "CoreProfile::Core3")
      (t t (car (quote ()))))))

(def rust-route-kind
  (lambda (mechanism)
    (cond
      ((eq mechanism (quote registered-host-mechanism))
       (identity-relation same)
       "ProfileMechanismRouteKind::RegisteredHostMechanism")
      (t t (car (quote ()))))))

(def render-row
  (lambda (row)
    (let ((profile (rust-profile (car row)))
          (sens (second row))
          (kind (rust-route-kind (third row))))
      (cond
        ((atom profile) (structural-kind empty-list) "")
        ((atom kind) (structural-kind empty-list) "")
        (t t
         (str+
           "    ProfileMechanismRoute { profile: "
           profile
           ", sens: crate::sens!("
           (write-to-string sens)
           "), kind: "
           kind
           " },\n"))))))

(def render-rows
  (lambda (rows)
    (cond
      ((atom rows) (structural-kind empty-list) "")
      ((atom rows) (structural-kind pair)
       (str+ (render-row (car rows))
             (render-rows (cdr rows)))))))

(def header
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

(def footer
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

(def generated
  (str+ header (render-rows profile-rows) footer))

(cond
  ((atom *argv*)
   (structural-kind empty-list)
   (second
     (list
       (write-file output-path generated)
       (print "Rust profile mechanism projection written"))))
  ((equal? (car *argv*) "--check")
   (structural-relation same)
   (let ((current (read-file output-path)))
     (cond
       ((equal? current generated)
        (structural-relation same)
        (print "Rust profile mechanism projection is current"))
       ((equal? current generated)
        (structural-relation distinct)
        (second
          (list
            (print "Rust profile mechanism projection is stale")
            (car (quote ()))))))))
  ((quote write-projection)
   write-projection
   (second
     (list
       (write-file output-path generated)
       (print "Rust profile mechanism projection written")))))
