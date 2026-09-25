; #1422 — Lisp-owned generated Rust projection of profile-scoped mechanism admission.
;
; Authority: lib/function-table-mechanisms.lisp
; Rust receives only coordinates + mechanical route kind.
;
; Usage:
;   cargo run -p my-lisp-cli -- scripts/generate-rust-profile-mechanisms.lisp
;   cargo run -p my-lisp-cli -- scripts/generate-rust-profile-mechanisms.lisp --check

(def source-path "lib/function-table-mechanisms.lisp")
(def output-path "crates/my-lisp/src/eval/profile_mechanisms_generated.rs")

(def str+
  (lambda args
    (reduce (lambda (acc s) (string-append acc s)) "" args)))

(def source-form
  (car (read-all (read-file source-path))))

(def find-section
  (lambda (name sections)
    (cond
      ((atom sections) (structural-kind empty-list) (quote ()))
      ((atom sections) (structural-kind pair)
       (cond
         ((eq (car (car sections)) name) (identity-relation same)
          (cdr (car sections)))
         ((eq (car (car sections)) name) (identity-relation distinct)
          (find-section name (cdr sections))))))))

(def profile-rows
  (find-section (quote profile-rows) source-form))

(def rust-profile
  (lambda (profile)
    (cond
      ((eq profile (quote core3)) (identity-relation same) "crate::CoreProfile::Core3")
      ((quote unsupported-profile) unsupported-profile (quote ())))))

(def rust-route
  (lambda (route)
    (cond
      ((eq route (quote registered-host-mechanism))
       (identity-relation same)
       "GeneratedProfileMechanismRoute::RegisteredHostMechanism")
      ((quote unsupported-route) unsupported-route (quote ())))))

(def render-row
  (lambda (row)
    (let ((profile (rust-profile (car row)))
          (route (rust-route (third row))))
      (cond
        ((atom profile) (structural-kind empty-list) "")
        ((atom route) (structural-kind empty-list) "")
        ((quote render) render
         (str+
           "    GeneratedProfileMechanismRow { profile: "
           profile
           ", sens: crate::sens!("
           (write-to-string (second row))
           "), route: "
           route
           " },\n"))))))

(def render-rows
  (lambda (remaining)
    (cond
      ((atom remaining) (structural-kind empty-list) "")
      ((atom remaining) (structural-kind pair)
       (str+ (render-row (car remaining))
             (render-rows (cdr remaining)))))))

(def header
  (str+
    "// GENERATED — DO NOT EDIT BY HAND.\n"
    "// Authority: lib/function-table-mechanisms.lisp profile-rows\n"
    "// Generator: scripts/generate-rust-profile-mechanisms.lisp\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(super) enum GeneratedProfileMechanismRoute {\n"
    "    RegisteredHostMechanism,\n"
    "}\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(super) struct GeneratedProfileMechanismRow {\n"
    "    pub(super) profile: crate::CoreProfile,\n"
    "    pub(super) sens: crate::Sens8,\n"
    "    pub(super) route: GeneratedProfileMechanismRoute,\n"
    "}\n\n"
    "pub(super) const PROFILE_MECHANISM_ROWS: &[GeneratedProfileMechanismRow] = &[\n"))

(def generated
  (str+ header (render-rows profile-rows) "];\n"))

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
