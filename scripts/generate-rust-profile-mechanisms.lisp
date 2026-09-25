; #1422 — generate the Rust projection of SENS-owned profile-scoped
; mechanism admission.
;
; Authority: lib/function-table-mechanisms.lisp (profile-rows only).
; Rust receives only mechanical coordinates + route kind.
;
; Usage:
;   cargo run -p my-lisp-cli -- scripts/generate-rust-profile-mechanisms.lisp
;   cargo run -p my-lisp-cli -- scripts/generate-rust-profile-mechanisms.lisp --check

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
  (cdr (find-section (quote profile-rows) metadata)))

(def rust-profile
  (lambda (profile)
    (cond
      ((eq profile (quote core1)) (identity-relation same) "CoreProfile::Core1")
      ((eq profile (quote core2)) (identity-relation same) "CoreProfile::Core2")
      ((eq profile (quote core3)) (identity-relation same) "CoreProfile::Core3")
      ((eq profile (quote core4)) (identity-relation same) "CoreProfile::Core4")
      ((quote unsupported-profile) unsupported-profile (car (quote ()))))))

(def rust-route
  (lambda (mechanism)
    (cond
      ((eq mechanism (quote registered-host-mechanism))
       (identity-relation same)
       "ProfileMechanismRoute::RegisteredHostMechanism")
      ((quote unsupported-profile-mechanism)
       unsupported-profile-mechanism
       (car (quote ()))))))

(def render-row
  (lambda (row)
    (str+
      "    ProfileMechanismRow { profile: "
      (rust-profile (car row))
      ", function: crate::sens!("
      (write-to-string (second row))
      "), route: "
      (rust-route (third row))
      " },\n")))

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
    "// Authority: lib/function-table-mechanisms.lisp profile-rows\n"
    "// Generator: scripts/generate-rust-profile-mechanisms.lisp\n\n"
    "use crate::{CoreProfile, Sens8};\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(crate) enum ProfileMechanismRoute {\n"
    "    RegisteredHostMechanism,\n"
    "}\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(crate) struct ProfileMechanismRow {\n"
    "    pub(crate) profile: CoreProfile,\n"
    "    pub(crate) function: Sens8,\n"
    "    pub(crate) route: ProfileMechanismRoute,\n"
    "}\n\n"
    "pub(crate) const PROFILE_MECHANISM_ROUTES: &[ProfileMechanismRow] = &[\n"))

(def footer
  (str+
    "];\n\n"
    "pub(crate) fn profile_mechanism_route(\n"
    "    profile: Option<CoreProfile>,\n"
    "    function: Sens8,\n"
    ") -> Option<ProfileMechanismRoute> {\n"
    "    let profile = profile?;\n"
    "    PROFILE_MECHANISM_ROUTES\n"
    "        .iter()\n"
    "        .find(|row| row.profile == profile && row.function == function)\n"
    "        .map(|row| row.route)\n"
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
