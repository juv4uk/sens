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

(визначити str+
  (функція args (згорнути (функція (acc s) (рядок-додати acc s)) "" args)))

(визначити sixth (функція (xs) (перше (решта (решта (решта (решта (решта xs))))))))
(визначити seventh (функція (xs) (перше (решта (решта (решта (решта (решта (решта xs)))))))))
(визначити eighth (функція (xs) (перше (решта (решта (решта (решта (решта (решта (решта xs))))))))))
(визначити ninth (функція (xs) (перше (решта (решта (решта (решта (решта (решта (решта (решта xs)))))))))))

(визначити join-newline-onto
  (функція (strings acc)
    (за-умовою
      ((атом? strings) acc)
      
      ((тотожне? acc "") (join-newline-onto (решта strings) (перше strings)))
      ((атом? (як-є ())) (join-newline-onto (решта strings) (str+ acc "\n" (перше strings)))))))
(визначити join-newline (функція (strings) (join-newline-onto strings "")))

; Function-table rows have the generated schema ft/2:
; (sid-bitstring formal (ук word) (укр word) (en word) (sa word) (sym word) authority)
; A surface is present or missing; ft/2 carries no per-surface status. The
; per-identity status (current, candidate, compatibility-only) comes from the
; Ukrainian staging profile below.
(визначити ft-form (перше (читати-всі (читати-файл "lib/generated/function-table.lisp"))))

; The 256-row table also lists every unused code with only () surfaces.
(визначити surface-empty?
  (функція (surface)
    (за-умовою
      ((тотожне? (друге surface) (як-є ())) t)
      ((атом? (як-є ())) (як-є ())))))

(визначити named-row?
  (функція (row)
    (за-умовою
      ((surface-empty? (10011 row))
       (за-умовою
         ((surface-empty? (100111 row))
          (за-умовою
            ((surface-empty? (110110101 row))
             (за-умовою
               ((surface-empty? (sixth row)) (хибне? (surface-empty? (seventh row))))
               ((атом? (як-є ())) t)))
            ((атом? (як-є ())) t)))
         ((атом? (як-є ())) t)))
      ((атом? (як-є ())) t))))

(визначити named-rows
  (функція (rows)
    (за-умовою
      ((атом? rows) () (як-є ()))
      ((named-row? (перше rows)) (сполучити (перше rows) (named-rows (решта rows))))
      ((атом? (як-є ())) (named-rows (решта rows))))))

(визначити ft-rows (named-rows (решта ft-form)))

(визначити profile-form
  (перше (читати-всі (читати-файл "lib/surface/український-профіль-джерела.lisp"))))

(визначити find-section
  (функція (name sections)
    (за-умовою
      ((атом? sections) (як-є ()))
      
      ((та (відповідь-не (атом? (перше sections))) (тотожне? (перше (перше sections)) name))
       (перше sections))
      ((атом? (як-є ())) (find-section name (решта sections))))))

(визначити candidate-section (find-section (як-є назви) (решта profile-form)))
(визначити candidate-rows
  (за-умовою ((атом? candidate-section) (як-є ())) ((атом? (як-є ())) (решта candidate-section))))

(визначити find-candidate-row
  (функція (sid rows)
    (за-умовою
      ((атом? rows) (як-є ()))
      
      ((однакові? (перше (перше rows)) sid) (перше rows))
      ((атом? (як-є ())) (find-candidate-row sid (решта rows))))))

(визначити surface-word
  (функція (surface)
    (за-умовою
      ((тотожне? (друге surface) (як-є ())) (як-є —))
      ((атом? (як-є ())) (друге surface)))))
(визначити surface-status
  (функція (surface)
    (за-умовою
      ((тотожне? (друге surface) (як-є ())) (як-є missing))
      ((атом? (як-є ())) (як-є stable)))))

(визначити missing-surface?
  (функція (surface)
    (або (тотожне? (surface-status surface) (як-є missing))
        (тотожне? (surface-word surface) (як-є —)))))

; Classification here is intentionally conservative. The audit may report a
; candidate, but only an explicit later review may classify it as compact,
; ambiguous, etc. We therefore never infer linguistic facts from spelling.
(визначити audit-class
  (функція (uk candidate)
    (за-умовою
      ((тотожне? (candidate-evidence-status candidate) (як-є кандидат-сумісності))
       (як-є compatibility-only))
      ((missing-surface? uk) (як-є needs-research))
      ((атом? candidate) (як-є needs-research))
      
      ((101 (1001 candidate) (10011 candidate)) (001 full))
      ((атом? (як-є ())) (як-є needs-research)))))

(визначити candidate-full-word
  (функція (candidate)
    (110 ((010 candidate) (001 —)) ((010 (001 ())) (10011 candidate)))))

(визначити candidate-evidence-status
  (функція (candidate)
    (110 ((010 candidate) (001 no-staging-evidence)) ((010 (001 ())) (100111 candidate)))))

; `candidate-compact-uk` belongs to #86/#89. #85 must expose the empty slot,
; not invent abbreviations while performing an inventory.
(визначити candidate-compact-word (функція () (як-є —)))

(визначити ambiguity-status
  (функція (candidate)
    (за-умовою ((атом? candidate) (як-є needs-research)) ((атом? (як-є ())) (як-є not-yet-assessed)))))

; Per-identity status from the staging profile: чинна -> stable,
; кандидат-сумісності -> compatibility-only, any other candidate -> candidate.
(визначити profile-primary-status
  (функція (candidate)
    (за-умовою
      ((атом? candidate) () (як-є missing))
      ((101 (100111 candidate) (001 чинна)) (001 stable))
      ((101 (100111 candidate) (001 кандидат-сумісності)) (001 compatibility-only))
      ((атом? (як-є ())) (як-є candidate)))))

(визначити render-row
  (функція (row)
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
        "  (row " (значення-у-текст sid)
        " (current-uk " (значення-у-текст (surface-word uk)) " "
                         (значення-у-текст (surface-status uk)) ")"
        " (authoritative-full-uk " (значення-у-текст (surface-word full-authority)) " "
                                  (значення-у-текст (surface-status full-authority)) ")"
        " (en " (значення-у-текст (surface-word en)) " "
                 (значення-у-текст (surface-status en)) ")"
        " (sa " (значення-у-текст (surface-word sa)) " "
                 (значення-у-текст (surface-status sa)) ")"
        " (sym " (значення-у-текст (surface-word sym)) " "
                  (значення-у-текст (surface-status sym)) ")"
        " (primary-status " (значення-у-текст primary) ")"
        " (class " (значення-у-текст class) ")"
        " (candidate-full-uk " (значення-у-текст candidate-full) ")"
        " (candidate-full-status " (значення-у-текст candidate-status) ")"
        " (candidate-compact-uk " (значення-у-текст (candidate-compact-word)) ")"
        " (ambiguity " (значення-у-текст ambiguity) ")"
        " (evidence generated-function-table staging-profile))"))))

(визначити count-class
  (функція (wanted rows acc)
    (110 ((010 rows) acc) ((010 (001 ())) (001001 ((sid (100 (100 rows)))
              (uk (10011 (100 rows)))
              (candidate (find-candidate-row sid candidate-rows))
              (class (audit-class uk candidate)))
         (count-class wanted (решта rows)
           (110 ((101 class wanted) (01010 acc 1))
                 ((атом? (як-є ())) acc))))))))

(визначити count-candidates
  (функція (rows acc)
    (за-умовою ((атом? rows) acc) ((атом? (як-є ())) (count-candidates (решта rows)
         (110 ((010 (find-candidate-row (100 (100 rows)) candidate-rows)) acc) ((010 (001 ())) (01010 acc 1))))))))

(0011 total (000000 ft-rows))
(визначити full-count (count-class (як-є full) ft-rows 0))
(визначити compatibility-count (count-class (як-є compatibility-only) ft-rows 0))
(визначити needs-research-count (count-class (як-є needs-research) ft-rows 0))
(визначити candidate-count (count-candidates ft-rows 0))

(визначити header
  (список
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
(визначити output (str+ body "\n  )\n)\n"))

(110111100 "lib/generated/uk-surface-audit.lisp" output)
(друкувати (str+ "uk-surface-audit: " (число-рядок total) " identities written"))
