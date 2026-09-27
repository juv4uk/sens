; scripts/generate-uk-surface-audit.lisp — generated Ukrainian surface inventory
; for my-lisp#85. This is an AUDIT PROJECTION, never semantic authority.
;
; Authority path:
;   semantic-registry.lisp
;       -> scripts/generate-function-table.lisp
;       -> lib/generated/function-table.lisp
;       -> this audit projection
;
; Candidate evidence path:
;   lib/surface/український-профіль-джерела.lisp
; Candidate spellings remain proposals. `lib/generated/function-table.lisp`
; is a checked projection, not a second semantic authority. This generator
; MUST NOT promote staging candidates into that current `full-uk` projection.
;
; Output:
;   lib/generated/uk-surface-audit.lisp
;
; Usage from repo root:
;   cargo run -p my-lisp-cli --bin my-lisp -- scripts/generate-uk-surface-audit.lisp

(00001001 str+
  (00001000 args (00111001 (00001000 (acc s) (00111010 acc s)) "" args)))

(00001001 sixth (00001000 (xs) (00000101 (00000110 (00000110 (00000110 (00000110 (00000110 xs))))))))
(00001001 seventh (00001000 (xs) (00000101 (00000110 (00000110 (00000110 (00000110 (00000110 (00000110 xs)))))))))
(00001001 eighth (00001000 (xs) (00000101 (00000110 (00000110 (00000110 (00000110 (00000110 (00000110 (00000110 xs))))))))))
(00001001 ninth (00001000 (xs) (00000101 (00000110 (00000110 (00000110 (00000110 (00000110 (00000110 (00000110 (00000110 xs)))))))))))

(00001001 join-newline-onto
  (00001000 (strings acc)
    (00000111
      ((00000010 strings) () acc)
      ((00000010 strings) (1) acc)
      ((00000011 acc "") (join-newline-onto (00000110 strings) (00000101 strings)))
      (t (join-newline-onto (00000110 strings) (str+ acc "\n" (00000101 strings)))))))
(00001001 join-newline (00001000 (strings) (join-newline-onto strings "")))

; Function-table rows have the generated schema ft/2:
; (sid-bitstring formal (ук word) (укр word) (en word) (sa word) (sym word) authority)
; A surface is present or missing; ft/2 carries no per-surface status. The
; per-identity status (current, candidate, compatibility-only) comes from the
; Ukrainian staging profile below.
(00001001 ft-form (00000101 (01001011 (10100110 "lib/generated/function-table.lisp"))))

; The 256-row table also lists every unused code with only () surfaces.
(00001001 surface-empty?
  (00001000 (surface)
    (00000111
      ((00000011 (00101111 surface) (00000001 ())) t)
      (t (00000001 ())))))

(00001001 named-row?
  (00001000 (row)
    (00000111
      ((surface-empty? (00110000 row))
       (00000111
         ((surface-empty? (00110001 row))
          (00000111
            ((surface-empty? (00110010 row))
             (00000111
               ((surface-empty? (sixth row)) (00100001 (surface-empty? (seventh row))))
               (t t)))
            (t t)))
         (t t)))
      (t t))))

(00001001 named-rows
  (00001000 (rows)
    (00000111
      ((00000010 rows) () (00000001 ()))
      ((named-row? (00000101 rows)) (00000100 (00000101 rows) (named-rows (00000110 rows))))
      (t (named-rows (00000110 rows))))))

(00001001 ft-rows (named-rows (00000110 ft-form)))

(00001001 profile-form
  (00000101 (01001011 (10100110 "lib/surface/український-профіль-джерела.lisp"))))

(00001001 find-section
  (00001000 (name sections)
    (00000111
      ((00000010 sections) () (00000001 ()))
      ((00000010 sections) (1) (00000001 ()))
      ((10011010 (10110001 (00000010 (00000101 sections))) (00000011 (00000101 (00000101 sections)) name))
       (00000101 sections))
      (t (find-section name (00000110 sections))))))

(00001001 candidate-section (find-section (00000001 назви) (00000110 profile-form)))
(00001001 candidate-rows
  (00000111
    ((00000010 candidate-section) () (00000001 ()))
    ((00000010 candidate-section) (1) (00000001 ()))
    (t (00000110 candidate-section))))

(00001001 find-candidate-row
  (00001000 (sid rows)
    (00000111
      ((00000010 rows) () (00000001 ()))
      ((00000010 rows) (1) (00000001 ()))
      ((00100010 (00000101 (00000101 rows)) sid) (00000101 rows))
      (t (find-candidate-row sid (00000110 rows))))))

(00001001 surface-word
  (00001000 (surface)
    (00000111
      ((00000011 (00101111 surface) (00000001 ())) (00000001 —))
      (t (00101111 surface)))))
(00001001 surface-status
  (00001000 (surface)
    (00000111
      ((00000011 (00101111 surface) (00000001 ())) (00000001 missing))
      (t (00000001 stable)))))

(00001001 missing-surface?
  (00001000 (surface)
    (10011011 (00000011 (surface-status surface) (00000001 missing))
        (00000011 (surface-word surface) (00000001 —)))))

; Classification here is intentionally conservative. The audit may report a
; candidate, but only an explicit later review may classify it as compact,
; ambiguous, etc. We therefore never infer linguistic facts from spelling.
(00001001 audit-class
  (00001000 (uk candidate)
    (00000111
      ((00000011 (candidate-evidence-status candidate) (00000001 кандидат-сумісності))
       (00000001 compatibility-only))
      ((missing-surface? uk) (00000001 needs-research))
      ((00000010 candidate) () (00000001 needs-research))
      ((00000010 candidate) (1) (00000001 needs-research))
      ((00000011 (00101111 candidate) (00110000 candidate)) (00000001 full))
      (t (00000001 needs-research)))))

(00001001 candidate-full-word
  (00001000 (candidate)
    (00000111 ((00000010 candidate) () (00000001 —))
          ((00000010 candidate) (1) (00000001 —))
          (t (00110000 candidate)))))

(00001001 candidate-evidence-status
  (00001000 (candidate)
    (00000111 ((00000010 candidate) () (00000001 no-staging-evidence))
          ((00000010 candidate) (1) (00000001 no-staging-evidence))
          (t (00110001 candidate)))))

; `candidate-compact-uk` belongs to #86/#89. #85 must expose the empty slot,
; not invent abbreviations while performing an inventory.
(00001001 candidate-compact-word (00001000 () (00000001 —)))

(00001001 ambiguity-status
  (00001000 (candidate)
    (00000111
      ((00000010 candidate) () (00000001 needs-research))
      ((00000010 candidate) (1) (00000001 needs-research))
      (t (00000001 not-yet-assessed)))))

; Per-identity status from the staging profile: чинна -> stable,
; кандидат-сумісності -> compatibility-only, any other candidate -> candidate.
(00001001 profile-primary-status
  (00001000 (candidate)
    (00000111
      ((00000010 candidate) () (00000001 missing))
      ((00000011 (00110001 candidate) (00000001 чинна)) (00000001 stable))
      ((00000011 (00110001 candidate) (00000001 кандидат-сумісності)) (00000001 compatibility-only))
      (t (00000001 candidate)))))

(00001001 render-row
  (00001000 (row)
    (10011101 ((sid (00000101 row))
           (uk (00110000 row))
           (full-authority (00110001 row))
           (en (00110010 row))
           (sa (sixth row))
           (sym (seventh row))
           (candidate (find-candidate-row sid candidate-rows))
           (primary (profile-primary-status candidate))
           (class (audit-class uk candidate))
           (candidate-full (candidate-full-word candidate))
           (candidate-status (candidate-evidence-status candidate))
           (ambiguity (ambiguity-status candidate)))
      (str+
        "  (row " (01001100 sid)
        " (current-uk " (01001100 (surface-word uk)) " "
                         (01001100 (surface-status uk)) ")"
        " (authoritative-full-uk " (01001100 (surface-word full-authority)) " "
                                  (01001100 (surface-status full-authority)) ")"
        " (en " (01001100 (surface-word en)) " "
                 (01001100 (surface-status en)) ")"
        " (sa " (01001100 (surface-word sa)) " "
                 (01001100 (surface-status sa)) ")"
        " (sym " (01001100 (surface-word sym)) " "
                  (01001100 (surface-status sym)) ")"
        " (primary-status " (01001100 primary) ")"
        " (class " (01001100 class) ")"
        " (candidate-full-uk " (01001100 candidate-full) ")"
        " (candidate-full-status " (01001100 candidate-status) ")"
        " (candidate-compact-uk " (01001100 (candidate-compact-word)) ")"
        " (ambiguity " (01001100 ambiguity) ")"
        " (evidence generated-function-table staging-profile))"))))

(00001001 count-class
  (00001000 (wanted rows acc)
    (00000111
      ((00000010 rows) () acc)
      ((00000010 rows) (1) acc)
      (t
       (10011101 ((sid (00000101 (00000101 rows)))
              (uk (00110000 (00000101 rows)))
              (candidate (find-candidate-row sid candidate-rows))
              (class (audit-class uk candidate)))
         (count-class wanted (00000110 rows)
           (00000111 ((00000011 class wanted) (00001100 acc 1))
                 (t acc))))))))

(00001001 count-candidates
  (00001000 (rows acc)
    (00000111
      ((00000010 rows) () acc)
      ((00000010 rows) (1) acc)
      (t
       (count-candidates (00000110 rows)
         (00000111 ((00000010 (find-candidate-row (00000101 (00000101 rows)) candidate-rows)) () acc)
               ((00000010 (find-candidate-row (00000101 (00000101 rows)) candidate-rows)) (1) acc)
               (t (00001100 acc 1))))))))

(00001001 total (00101000 ft-rows))
(00001001 full-count (count-class (00000001 full) ft-rows 0))
(00001001 compatibility-count (count-class (00000001 compatibility-only) ft-rows 0))
(00001001 needs-research-count (count-class (00000001 needs-research) ft-rows 0))
(00001001 candidate-count (count-candidates ft-rows 0))

(00001001 header
  (00100111
    "; GENERATED — DO NOT EDIT BY HAND"
    "; Semantic authority: lib/surface/semantic-registry.lisp via lib/generated/function-table.lisp"
    "; Candidate evidence only: lib/surface/український-профіль-джерела.lisp"
    "; Generator: scripts/generate-uk-surface-audit.lisp (my-lisp#85)"
    "; candidate-full-uk is NOT automatically promoted into authoritative full-uk"
    ""
    "(uk-surface-audit/2"
    (str+ "  (summary (total " (01000110 total) ")"
          " (full " (01000110 full-count) ")"
          " (already-compact 0)"
          " (ambiguous 0)"
          " (needs-research " (01000110 needs-research-count) ")"
          " (compatibility-only " (01000110 compatibility-count) ")"
          " (staging-evidence " (01000110 candidate-count) "))")
    "  (rows"))

(00001001 body (join-newline (00101001 header (00110111 render-row ft-rows))))
(00001001 output (str+ body "\n  )\n)\n"))

(10100111 "lib/generated/uk-surface-audit.lisp" output)
(01001000 (str+ "uk-surface-audit: " (01000110 total) " identities written"))
