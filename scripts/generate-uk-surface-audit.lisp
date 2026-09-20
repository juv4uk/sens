; scripts/generate-uk-surface-audit.lisp — generated Ukrainian surface inventory
; for my-lisp#85. This is an AUDIT PROJECTION, never semantic authority.
;
; Authority path:
;   lib/surface/semantic-registry.lisp
;       -> this audit projection
;
; Candidate evidence path:
;   lib/surface/український-профіль-джерела.lisp
; Candidate spellings remain proposals. The generated function-table is only
; a review projection and is deliberately NOT read by this generator.
; This generator MUST NOT promote staging candidates into Canon authority.
;
; Output:
;   lib/generated/uk-surface-audit.lisp
;
; Usage from repo root:
;   cargo run -p my-lisp-cli --bin my-lisp -- scripts/generate-uk-surface-audit.lisp

(def str+
  (lambda args (reduce (lambda (acc s) (string-append acc s)) "" args)))

(def second (lambda (xs) (car (cdr xs))))
(def third (lambda (xs) (car (cdr (cdr xs)))))
(def fourth (lambda (xs) (car (cdr (cdr (cdr xs))))))
(def fifth (lambda (xs) (car (cdr (cdr (cdr (cdr xs)))))))
(def sixth (lambda (xs) (car (cdr (cdr (cdr (cdr (cdr xs))))))))
(def seventh (lambda (xs) (car (cdr (cdr (cdr (cdr (cdr (cdr xs)))))))))
(def eighth (lambda (xs) (car (cdr (cdr (cdr (cdr (cdr (cdr (cdr xs))))))))))
(def ninth (lambda (xs) (car (cdr (cdr (cdr (cdr (cdr (cdr (cdr (cdr xs)))))))))))

(def join-newline-onto
  (lambda (strings acc)
    (cond
      ((atom strings) acc)
      ((eq acc "") (join-newline-onto (cdr strings) (car strings)))
      (t (join-newline-onto (cdr strings) (str+ acc "\n" (car strings)))))))
(def join-newline (lambda (strings) (join-newline-onto strings "")))

; Canon/function-table authority rows come directly from semantic-registry.lisp:
; (sid-bitstring (en word-or-()) (uk word-or-()) (ukr word-or-())
;     (sa word-or-()) (sym word-or-()))
; SID 00000000 is structural (), not a callable surface row, so the audit skips it.
(def registry-form
  (car (read-all (read-file "lib/surface/semantic-registry.lisp"))))
(def registry-rows (cdr (cdr registry-form)))

(def profile-form
  (car (read-all (read-file "lib/surface/український-профіль-джерела.lisp"))))

(def find-section
  (lambda (name sections)
    (cond
      ((atom sections) (quote ()))
      ((and (not (atom (car sections))) (eq (car (car sections)) name))
       (car sections))
      (t (find-section name (cdr sections))))))

(def candidate-section (find-section (quote назви) (cdr profile-form)))
(def candidate-rows
  (cond
    ((atom candidate-section) (quote ()))
    (t (cdr candidate-section))))

(def find-candidate-row
  (lambda (sid rows)
    (cond
      ((atom rows) (quote ()))
      ((equal? (car (car rows)) sid) (car rows))
      (t (find-candidate-row sid (cdr rows))))))

(def find-surface
  (lambda (name surfaces)
    (cond
      ((atom surfaces) (quote ()))
      ((eq (car (car surfaces)) name) (car surfaces))
      (t (find-surface name (cdr surfaces))))))

(def surface-word
  (lambda (surface)
    (cond
      ((atom surface) (quote ()))
      (t (second surface)))))

(def registry-surface-word
  (lambda (name row)
    (surface-word (find-surface name (cdr row)))))

(def surface-status
  (lambda (word)
    (cond
      ((equal? word (quote ())) (quote missing))
      (t (quote stable)))))

(def display-surface-word
  (lambda (word)
    (cond
      ((equal? word (quote ())) (quote —))
      (t word))))

(def missing-surface?
  (lambda (word)
    (equal? word (quote ()))))

; Classification here is intentionally conservative. The audit may report a
; candidate, but only an explicit later review may classify it as compact,
; ambiguous, etc. We therefore never infer linguistic facts from spelling.
(def audit-class
  (lambda (uk candidate)
    (cond
      ((and (not (atom candidate))
            (eq (fourth candidate) (quote кандидат-сумісності)))
       (quote compatibility-only))
      ((missing-surface? uk) (quote needs-research))
      ((atom candidate) (quote needs-research))
      ((eq (second candidate) (third candidate)) (quote full))
      (t (quote needs-research)))))

(def candidate-full-word
  (lambda (candidate)
    (cond ((atom candidate) (quote —))
          (t (third candidate)))))

(def candidate-evidence-status
  (lambda (candidate)
    (cond ((atom candidate) (quote no-staging-evidence))
          (t (fourth candidate)))))

; `candidate-compact-uk` belongs to #86/#89. #85 must expose the empty slot,
; not invent abbreviations while performing an inventory.
(def candidate-compact-word (lambda () (quote —)))

(def ambiguity-status
  (lambda (candidate)
    (cond
      ((atom candidate) (quote needs-research))
      (t (quote not-yet-assessed)))))

(def render-row
  (lambda (row)
    (let* ((sid (car row))
           (uk (registry-surface-word (quote uk) row))
           (full-authority (registry-surface-word (quote ukr) row))
           (en (registry-surface-word (quote en) row))
           (sa (registry-surface-word (quote sa) row))
           (sym (registry-surface-word (quote sym) row))
           (candidate (find-candidate-row sid candidate-rows))
           (class (audit-class uk candidate))
           (candidate-full (candidate-full-word candidate))
           (candidate-status (candidate-evidence-status candidate))
           (ambiguity (ambiguity-status candidate)))
      (str+
        "  (row " (write-to-string sid)
        " (current-uk " (write-to-string (display-surface-word uk)) " "
                         (write-to-string (surface-status uk)) ")"
        " (authoritative-full-uk " (write-to-string (display-surface-word full-authority)) " "
                                  (write-to-string (surface-status full-authority)) ")"
        " (en " (write-to-string (display-surface-word en)) " "
                 (write-to-string (surface-status en)) ")"
        " (sa " (write-to-string (display-surface-word sa)) " "
                 (write-to-string (surface-status sa)) ")"
        " (sym " (write-to-string (display-surface-word sym)) " "
                  (write-to-string (surface-status sym)) ")"
        " (primary-status stable)"
        " (class " (write-to-string class) ")"
        " (candidate-full-uk " (write-to-string candidate-full) ")"
        " (candidate-full-status " (write-to-string candidate-status) ")"
        " (candidate-compact-uk " (write-to-string (candidate-compact-word)) ")"
        " (ambiguity " (write-to-string ambiguity) ")"
        " (evidence semantic-registry staging-profile))"))))

(def count-class
  (lambda (wanted rows acc)
    (cond
      ((atom rows) acc)
      (t
       (let* ((sid (car (car rows)))
              (uk (registry-surface-word (quote uk) (car rows)))
              (candidate (find-candidate-row sid candidate-rows))
              (class (audit-class uk candidate)))
         (count-class wanted (cdr rows)
           (cond ((eq class wanted) (+ acc 1))
                 (t acc))))))))

(def count-candidates
  (lambda (rows acc)
    (cond
      ((atom rows) acc)
      (t
       (count-candidates (cdr rows)
         (cond ((atom (find-candidate-row (car (car rows)) candidate-rows)) acc)
               (t (+ acc 1))))))))

(def total (length registry-rows))
(def full-count (count-class (quote full) registry-rows 0))
(def compatibility-count (count-class (quote compatibility-only) registry-rows 0))
(def needs-research-count (count-class (quote needs-research) registry-rows 0))
(def candidate-count (count-candidates registry-rows 0))

(def header
  (list
    "; GENERATED — DO NOT EDIT BY HAND"
    "; Semantic authority: lib/surface/semantic-registry.lisp (direct input)"
    "; Candidate evidence only: lib/surface/український-профіль-джерела.lisp"
    "; Generator: scripts/generate-uk-surface-audit.lisp (my-lisp#85)"
    "; candidate-full-uk is NOT automatically promoted into authoritative full-uk"
    ""
    "(uk-surface-audit/2"
    (str+ "  (summary (total " (number->string total) ")"
          " (full " (number->string full-count) ")"
          " (already-compact 0)"
          " (ambiguous 0)"
          " (needs-research " (number->string needs-research-count) ")"
          " (compatibility-only " (number->string compatibility-count) ")"
          " (staging-evidence " (number->string candidate-count) "))")
    "  (rows"))

(def body (join-newline (append header (map render-row registry-rows))))
(def output (str+ body "\n  )\n)\n"))

(write-file "lib/generated/uk-surface-audit.lisp" output)
(print (str+ "uk-surface-audit: " (number->string total) " identities written"))
