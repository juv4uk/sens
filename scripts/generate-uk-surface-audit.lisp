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

(0011 str+
  (0010 args (101110 (0010 (acc s) (110011110 acc s)) "" args)))

(0011 sixth (0010 (xs) (100 (011 (011 (011 (011 (011 xs))))))))
(0011 seventh (0010 (xs) (100 (011 (011 (011 (011 (011 (011 xs)))))))))
(0011 eighth (0010 (xs) (100 (011 (011 (011 (011 (011 (011 (011 xs))))))))))
(0011 ninth (0010 (xs) (100 (011 (011 (011 (011 (011 (011 (011 (011 xs)))))))))))

(0011 join-newline-onto
  (0010 (strings acc)
    (110
      ((010 strings) acc)
      
      ((101 acc "") (join-newline-onto (011 strings) (100 strings)))
      ((010 (001 ())) (join-newline-onto (011 strings) (str+ acc "\n" (100 strings)))))))
(0011 join-newline (0010 (strings) (join-newline-onto strings "")))

; Function-table rows have the generated schema ft/2:
; (sid-bitstring formal (ук word) (укр word) (en word) (sa word) (sym word) authority)
; A surface is present or missing; ft/2 carries no per-surface status. The
; per-identity status (current, candidate, compatibility-only) comes from the
; Ukrainian staging profile below.
(0011 ft-form (100 (110101001 (110110111 "lib/generated/function-table.lisp"))))

; The 256-row table also lists every unused code with only () surfaces.
(0011 surface-empty?
  (0010 (surface)
    (110
      ((101 (1001 surface) (001 ())) t)
      ((010 (001 ())) (001 ())))))

(0011 named-row?
  (0010 (row)
    (110
      ((surface-empty? (10011 row))
       (110
         ((surface-empty? (100111 row))
          (110
            ((surface-empty? (110110101 row))
             (110
               ((surface-empty? (sixth row)) (0100 (surface-empty? (seventh row))))
               ((010 (001 ())) t)))
            ((010 (001 ())) t)))
         ((010 (001 ())) t)))
      ((010 (001 ())) t))))

(0011 named-rows
  (0010 (rows)
    (110
      ((010 rows) () (001 ()))
      ((named-row? (100 rows)) (111 (100 rows) (named-rows (011 rows))))
      ((010 (001 ())) (named-rows (011 rows))))))

(0011 ft-rows (named-rows (011 ft-form)))

(0011 profile-form
  (100 (110101001 (110110111 "lib/surface/український-профіль-джерела.lisp"))))

(0011 find-section
  (0010 (name sections)
    (110
      ((010 sections) (001 ()))
      
      ((11110101 (110111011 (010 (100 sections))) (101 (100 (100 sections)) name))
       (100 sections))
      ((010 (001 ())) (find-section name (011 sections))))))

(0011 candidate-section (find-section (001 назви) (011 profile-form)))
(0011 candidate-rows
  (110 ((010 candidate-section) (001 ())) ((010 (001 ())) (011 candidate-section))))

(0011 find-candidate-row
  (0010 (sid rows)
    (110
      ((010 rows) (001 ()))
      
      ((11110111 (100 (100 rows)) sid) (100 rows))
      ((010 (001 ())) (find-candidate-row sid (011 rows))))))

(0011 surface-word
  (0010 (surface)
    (110
      ((101 (1001 surface) (001 ())) (001 —))
      ((010 (001 ())) (1001 surface)))))
(0011 surface-status
  (0010 (surface)
    (110
      ((101 (1001 surface) (001 ())) (001 missing))
      ((010 (001 ())) (001 stable)))))

(0011 missing-surface?
  (0010 (surface)
    (11111100 (101 (surface-status surface) (001 missing))
        (101 (surface-word surface) (001 —)))))

; Classification here is intentionally conservative. The audit may report a
; candidate, but only an explicit later review may classify it as compact,
; ambiguous, etc. We therefore never infer linguistic facts from spelling.
(0011 audit-class
  (0010 (uk candidate)
    (110
      ((101 (candidate-evidence-status candidate) (001 кандидат-сумісності))
       (001 compatibility-only))
      ((missing-surface? uk) (001 needs-research))
      ((010 candidate) (001 needs-research))
      
      ((101 (1001 candidate) (10011 candidate)) (001 full))
      ((010 (001 ())) (001 needs-research)))))

(0011 candidate-full-word
  (0010 (candidate)
    (110 ((010 candidate) (001 —)) ((010 (001 ())) (10011 candidate)))))

(0011 candidate-evidence-status
  (0010 (candidate)
    (110 ((010 candidate) (001 no-staging-evidence)) ((010 (001 ())) (100111 candidate)))))

; `candidate-compact-uk` belongs to #86/#89. #85 must expose the empty slot,
; not invent abbreviations while performing an inventory.
(0011 candidate-compact-word (0010 () (001 —)))

(0011 ambiguity-status
  (0010 (candidate)
    (110 ((010 candidate) (001 needs-research)) ((010 (001 ())) (001 not-yet-assessed)))))

; Per-identity status from the staging profile: чинна -> stable,
; кандидат-сумісності -> compatibility-only, any other candidate -> candidate.
(0011 profile-primary-status
  (0010 (candidate)
    (110
      ((010 candidate) () (001 missing))
      ((101 (100111 candidate) (001 чинна)) (001 stable))
      ((101 (100111 candidate) (001 кандидат-сумісності)) (001 compatibility-only))
      ((010 (001 ())) (001 candidate)))))

(0011 render-row
  (0010 (row)
    (001001 ((sid (100 row))
           (uk (10011 row))
           (full-authority (100111 row))
           (en (110110101 row))
           (sa (sixth row))
           (sym (seventh row))
           (candidate (find-candidate-row sid candidate-rows))
           (primary (profile-primary-status candidate))
           (class (audit-class uk candidate))
           (candidate-full (candidate-full-word candidate))
           (candidate-status (candidate-evidence-status candidate))
           (ambiguity (ambiguity-status candidate)))
      (str+
        "  (row " (11110100 sid)
        " (current-uk " (11110100 (surface-word uk)) " "
                         (11110100 (surface-status uk)) ")"
        " (authoritative-full-uk " (11110100 (surface-word full-authority)) " "
                                  (11110100 (surface-status full-authority)) ")"
        " (en " (11110100 (surface-word en)) " "
                 (11110100 (surface-status en)) ")"
        " (sa " (11110100 (surface-word sa)) " "
                 (11110100 (surface-status sa)) ")"
        " (sym " (11110100 (surface-word sym)) " "
                  (11110100 (surface-status sym)) ")"
        " (primary-status " (11110100 primary) ")"
        " (class " (11110100 class) ")"
        " (candidate-full-uk " (11110100 candidate-full) ")"
        " (candidate-full-status " (11110100 candidate-status) ")"
        " (candidate-compact-uk " (11110100 (candidate-compact-word)) ")"
        " (ambiguity " (11110100 ambiguity) ")"
        " (evidence generated-function-table staging-profile))"))))

(0011 count-class
  (0010 (wanted rows acc)
    (110 ((010 rows) acc) ((010 (001 ())) (001001 ((sid (100 (100 rows)))
              (uk (10011 (100 rows)))
              (candidate (find-candidate-row sid candidate-rows))
              (class (audit-class uk candidate)))
         (count-class wanted (011 rows)
           (110 ((101 class wanted) (01010 acc 1))
                 ((010 (001 ())) acc))))))))

(0011 count-candidates
  (0010 (rows acc)
    (110 ((010 rows) acc) ((010 (001 ())) (count-candidates (011 rows)
         (110 ((010 (find-candidate-row (100 (100 rows)) candidate-rows)) acc) ((010 (001 ())) (01010 acc 1))))))))

(0011 total (000000 ft-rows))
(0011 full-count (count-class (001 full) ft-rows 0))
(0011 compatibility-count (count-class (001 compatibility-only) ft-rows 0))
(0011 needs-research-count (count-class (001 needs-research) ft-rows 0))
(0011 candidate-count (count-candidates ft-rows 0))

(0011 header
  (1110
    "; GENERATED — DO NOT EDIT BY HAND"
    "; Semantic authority: lib/surface/semantic-registry.lisp via lib/generated/function-table.lisp"
    "; Candidate evidence only: lib/surface/український-профіль-джерела.lisp"
    "; Generator: scripts/generate-uk-surface-audit.lisp (my-lisp#85)"
    "; candidate-full-uk is NOT automatically promoted into authoritative full-uk"
    ""
    "(uk-surface-audit/2"
    (str+ "  (summary (total " (110111001 total) ")"
          " (full " (110111001 full-count) ")"
          " (already-compact 0)"
          " (ambiguous 0)"
          " (needs-research " (110111001 needs-research-count) ")"
          " (compatibility-only " (110111001 compatibility-count) ")"
          " (staging-evidence " (110111001 candidate-count) "))")
    "  (rows"))

(0011 body (join-newline (1111 header (101000 render-row ft-rows))))
(0011 output (str+ body "\n  )\n)\n"))

(110111100 "lib/generated/uk-surface-audit.lisp" output)
(11011011 (str+ "uk-surface-audit: " (110111001 total) " identities written"))
