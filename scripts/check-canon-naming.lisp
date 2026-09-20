; scripts/check-canon-naming.lisp
; Focused terminology guard for current human-facing documents (#1011).
; Historical/archive material and machine identifiers are intentionally out of scope.

(def current-facing-canon-files
  (quote
    ("README.md"
     "CURRENT.md"
     "docs/language-core.md"
     "docs/semantic-authority-map.md"
     "docs/semantic-authority-map.uk.md"
     "docs/ukrainian-api.md"
     "language-contract.lisp"
     "scripts/generate-ukrainian-api.py")))

(def forbidden-canon-phrases
  (quote
    ("Canon 0+7"
     "Canon 0 +"
     "Canon 0"
     "CANON 0"
     "Canon zero"
     "Canon-zero"
     "Канон 0+7"
     "Канон 0 +"
     "Канон 0")))

(def first-forbidden-phrase
  (lambda (text phrases)
    (cond
      ((atom phrases) (quote ()))
      ((string-contains? (car phrases) text) (car phrases))
      (t (first-forbidden-phrase text (cdr phrases))))))

(def check-current-facing-canon-files
  (lambda (paths)
    (cond
      ((atom paths) (quote canon-naming-ok))
      (t
       (let* ((path (car paths))
              (text (read-file path))
              (forbidden (first-forbidden-phrase text forbidden-canon-phrases)))
         (cond
           ((atom forbidden)
            (check-current-facing-canon-files (cdr paths)))
           (t
            (list (quote canon-naming-violation) path forbidden))))))))

(def verdict (check-current-facing-canon-files current-facing-canon-files))

(cond
  ((equal? verdict (quote canon-naming-ok))
   (print "canon-naming: current-facing terminology is canon()"))
  (t
   (let ((shown (print verdict)))
     (car (quote ())))))
