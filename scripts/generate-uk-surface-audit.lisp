; scripts/generate-uk-surface-audit.lisp — generated Ukrainian surface inventory
; for my-lisp#85. This is an AUDIT PROJECTION, never semantic authority.
;
; Authority path:
;   lib/surface/semantic-registry.lisp
;       -> direct Lisp query in this generator
;       -> lib/generated/uk-surface-audit.lisp
;
; Candidate evidence path:
;   lib/surface/український-профіль-джерела.lisp
;
; The generated function table is deliberately NOT an input here. It remains a
; review/presentation projection only; projections must not become source APIs.
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

(def join-newline-onto
  (lambda (strings acc)
    (cond
      ((atom strings) acc)
      ((eq acc "") (join-newline-onto (cdr strings) (car strings)))
      (t (join-newline-onto (cdr strings) (str+ acc "\n" (car strings)))))))
(def join-newline (lambda (strings) (join-newline-onto strings "")))

; Canonical registry:
; (
;   (binary 8)
;   (00000000 (en ()) (uk ()) (ukr ()) (sa ()) (sym ()))
;   (00000001 (en quote) ...)
;   ...)
;
; Canon 0 is a semantic ground value rather than a callable/function row, so
; the UK function-surface audit starts at SID 00000001 just as the historical
; function-table projection did.
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

(def candidate-row-id (lambda (row) (car row)))

(def candidate-id-count
  (lambda (sid rows acc)
    (cond
      ((atom rows) acc)
      ((equal? sid (candidate-row-id (car rows)))
       (candidate-id-count sid (cdr rows) (+ acc 1)))
      (t (candidate-id-count sid (cdr rows) acc)))))

(def registry-coverage-verdict
  (lambda (rows)
    (cond
      ((atom rows) (quote registry-coverage-ok))
      (t
       (let* ((sid (write-to-string (car (car rows))))
              (count (candidate-id-count sid candidate-rows 0)))
         (cond
           ((= count 1) 1 (registry-coverage-verdict (cdr rows)))
           ((= count 1) 0
            (list (quote registry-coverage-violation) sid count))))))))

(def fail-closed
  (lambda (verdict expected)
    (cond
      ((equal? verdict expected) (quote ok))
      (t
       (let ((shown (print verdict)))
         (car (quote ())))))))

(fail-closed
  (registry-coverage-verdict registry-rows)
  (quote registry-coverage-ok))

(cond
  ((= (length candidate-rows) (length registry-rows))
   1
   (quote staging-count-ok))
  ((= (length candidate-rows) (length registry-rows))
   0
   (let ((shown
           (print
             (list
               (quote staging-count-mismatch)
               (length candidate-rows)
               (length registry-rows)))))
     (car (quote ())))))

(def find-candidate-row
  (lambda (sid rows)
    (cond
      ((atom rows) (quote ()))
      ((equal? (car (car rows)) sid) (car rows))
      (t (find-candidate-row sid (cdr rows))))))

(def find-surface
  (lambda (namespace surfaces)
    (cond
      ((atom surfaces) (quote ()))
      ((eq (car (car surfaces)) namespace) (car surfaces))
      (t (find-surface namespace (cdr surfaces))))))

(def raw-surface-name
  (lambda (namespace row)
    (let ((surface (find-surface namespace (cdr row))))
      (cond
        ((atom surface) (quote ()))
        (t (second surface))))))

(def surface-word
  (lambda (namespace row)
    (let ((name (raw-surface-name namespace row)))
      (cond
        ((atom name)
         (cond
           ((eq name (quote ())) (quote —))
           (t name)))
        (t name)))))

(def surface-status
  (lambda (namespace row)
    (let ((name (raw-surface-name namespace row)))
      (cond
        ((atom name)
         (cond
           ((eq name (quote ())) (quote missing))
           (t (quote stable))))
        (t (quote stable))))))

(def candidate-full-word
  (lambda (candidate)
    (cond ((atom candidate) (quote —))
          (t (third candidate)))))

(def candidate-evidence-status
  (lambda (candidate)
    (cond ((atom candidate) (quote no-staging-evidence))
          (t (fourth candidate)))))

(def candidate-compact-word (lambda () (quote —)))

(def compatibility-candidate?
  (lambda (candidate)
    (cond
      ((atom candidate) (quote no))
      ((eq (fourth candidate) (quote кандидат-сумісності)) (quote yes))
      (t (quote no)))))

(def audit-class
  (lambda (row candidate)
    (cond
      ((eq (compatibility-candidate? candidate) (quote yes))
       (quote compatibility-only))
      ((eq (surface-status (quote uk) row) (quote missing))
       (quote needs-research))
      ((atom candidate) (quote needs-research))
      ((eq (second candidate) (third candidate)) (quote full))
      (t (quote needs-research)))))

(def ambiguity-status
  (lambda (candidate)
    (cond
      ((atom candidate) (quote needs-research))
      (t (quote not-yet-assessed)))))

(def primary-status
  (lambda (row candidate)
    (cond
      ((eq (compatibility-candidate? candidate) (quote yes)) (quote candidate))
      ((eq (surface-status (quote uk) row) (quote stable)) (quote stable))
      (t (quote missing)))))

(def render-surface
  (lambda (namespace row)
    (str+
      "(" (symbol->string namespace) " "
      (write-to-string (surface-word namespace row)) " "
      (write-to-string (surface-status namespace row)) ")")))

(def render-row
  (lambda (row)
    (let* ((sid (write-to-string (car row)))
           (candidate (find-candidate-row sid candidate-rows))
           (class (audit-class row candidate))
           (candidate-full (candidate-full-word candidate))
           (candidate-status (candidate-evidence-status candidate))
           (ambiguity (ambiguity-status candidate)))
      (str+
        "  (row " (write-to-string sid)
        " (current-uk " (write-to-string (surface-word (quote uk) row)) " "
                         (write-to-string (surface-status (quote uk) row)) ")"
        " (authoritative-full-uk " (write-to-string (surface-word (quote ukr) row)) " "
                                  (write-to-string (surface-status (quote ukr) row)) ")"
        " " (render-surface (quote en) row)
        " " (render-surface (quote sa) row)
        " " (render-surface (quote sym) row)
        " (primary-status " (write-to-string (primary-status row candidate)) ")"
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
       (let* ((sid (write-to-string (car (car rows))))
              (candidate (find-candidate-row sid candidate-rows))
              (class (audit-class (car rows) candidate)))
         (count-class wanted (cdr rows)
           (cond ((eq class wanted) (+ acc 1))
                 (t acc))))))))

(def count-candidates
  (lambda (rows acc)
    (cond
      ((atom rows) acc)
      (t
       (let ((sid (write-to-string (car (car rows)))))
         (count-candidates (cdr rows)
           (cond ((atom (find-candidate-row sid candidate-rows)) acc)
                 (t (+ acc 1)))))))))

(def total (length registry-rows))
(def full-count (count-class (quote full) registry-rows 0))
(def compatibility-count (count-class (quote compatibility-only) registry-rows 0))
(def needs-research-count (count-class (quote needs-research) registry-rows 0))
(def candidate-count (count-candidates registry-rows 0))

(def header
  (list
    "; GENERATED — DO NOT EDIT BY HAND"
    "; Semantic authority: lib/surface/semantic-registry.lisp"
    "; Candidate evidence only: lib/surface/український-профіль-джерела.lisp"
    "; Generator: scripts/generate-uk-surface-audit.lisp (my-lisp#85)"
    "; lib/generated/function-table.lisp is not an input"
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
