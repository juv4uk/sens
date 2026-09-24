; #1255 — executable witness for the Core4 predicate-answer scale.
;
; The checker intentionally consumes the Lisp-owned contract as ordinary data.
; It does not manufacture predicate semantics in Rust or in this script.

(def pas-forms
  (read-all (read-file "contracts/core4-predicate-answer-scale.lisp")))

(def pas-contract (car pas-forms))
(def pas-schema (car pas-contract))
(def pas-sections (cdr pas-contract))

(def pas-field-from
  (lambda (name fields)
    (cond
      ((atom fields) (structural-kind empty-list) (quote missing))
      ((atom fields) (structural-kind pair)
       (let ((field (car fields)))
         (cond
           ((atom field) (structural-kind pair)
            (cond
              ((eq (car field) name) (identity-relation same) (cdr field))
              ((eq (car field) name) (identity-relation distinct)
               (pas-field-from name (cdr fields)))))
           ((quote pas-next) pas-next
            (pas-field-from name (cdr fields)))))))))

(def pas-field
  (lambda (section name)
    (pas-field-from name section)))

(def pas-check
  (lambda (label actual expected)
    (cond
      ((equal? actual expected) (structural-relation same) (quote ()))
      ((quote pas-fail) pas-fail
       (list (quote predicate-answer-scale-mismatch)
             label
             expected
             actual)))))

(def pas-first-failure
  (lambda (checks)
    (cond
      ((atom checks) (structural-kind empty-list) (quote ()))
      ((atom (car checks)) (structural-kind empty-list)
       (pas-first-failure (cdr checks)))
      ((quote pas-failure) pas-failure (car checks)))))

(def pas-meta (car pas-sections))
(def pas-no (second pas-sections))
(def pas-boundary (third pas-sections))
(def pas-yes (fourth pas-sections))
(def pas-algebra (fifth pas-sections))

(def pas-no-levels (pas-field pas-no (quote levels)))
(def pas-yes-levels (pas-field pas-yes (quote levels)))
(def pas-lower-sid (pas-field pas-boundary (quote no-sid-endpoint)))
(def pas-upper-sid (pas-field pas-boundary (quote yes-sid-endpoint)))

(def pas-verdict
  (lambda ()
    (let ((failure
            (pas-first-failure
              (list
                (pas-check (quote schema)
                           pas-schema
                           (quote core4-predicate-answer-scale/1))
                (pas-check (quote section-count)
                           (length pas-sections)
                           5)
                (pas-check (quote profile)
                           (pas-field pas-meta (quote profile))
                           (quote core4))
                (pas-check (quote semantic-form)
                           (pas-field pas-meta (quote semantic-form))
                           (quote homogeneous-bits))
                (pas-check (quote runtime-cutover)
                           (pas-field pas-meta (quote runtime-cutover))
                           (quote pending-1257))
                (pas-check (quote record-wrapper)
                           (pas-field pas-meta (quote record-wrapper))
                           (quote forbidden))
                (pas-check (quote no-direction)
                           (pas-field pas-no (quote direction))
                           (quote no))
                (pas-check (quote no-bit)
                           (pas-field pas-no (quote bit))
                           "0")
                (pas-check (quote no-levels)
                           pas-no-levels
                           (quote
                             (("0"       1 dṛḍha-niścaya)
                              ("00"      2 niścaya)
                              ("000"     3 nirṇaya)
                              ("0000"    4 saṃbhāvanā)
                              ("00000"   5 saṃśaya)
                              ("000000"  6 aniścaya)
                              ("0000000" 7 ajñāta-sīmā))))
                (pas-check (quote boundary)
                           (pas-field pas-boundary (quote boundary))
                           (quote directed-endpoints))
                (pas-check (quote undirected-answer)
                           (pas-field pas-boundary (quote undirected-answer))
                           (quote ()))
                (pas-check (quote boundary-sanskrit)
                           (pas-field pas-boundary (quote sanskrit))
                           (quote ajñāta))
                (pas-check (quote no-sid-endpoint)
                           pas-lower-sid
                           (quote 00000000))
                (pas-check (quote yes-sid-endpoint)
                           pas-upper-sid
                           (quote 11111111))
                (pas-check (quote sid-alias)
                           (pas-field pas-boundary (quote sid-alias))
                           (quote forbidden))
                (pas-check (quote empty-list-alias)
                           (pas-field pas-boundary (quote empty-list-alias))
                           (quote forbidden))
                (pas-check (quote sid-anchors-distinct)
                           (equal? pas-lower-sid pas-upper-sid)
                           (quote (structural-relation distinct)))
                (pas-check (quote yes-direction)
                           (pas-field pas-yes (quote direction))
                           (quote yes))
                (pas-check (quote yes-bit)
                           (pas-field pas-yes (quote bit))
                           "1")
                (pas-check (quote yes-levels)
                           pas-yes-levels
                           (quote
                             (("1"       1 dṛḍha-niścaya)
                              ("11"      2 niścaya)
                              ("111"     3 nirṇaya)
                              ("1111"    4 saṃbhāvanā)
                              ("11111"   5 saṃśaya)
                              ("111111"  6 aniścaya)
                              ("1111111" 7 ajñāta-sīmā))))
                (pas-check (quote answer-count)
                           (+ (length pas-no-levels) (length pas-yes-levels) 1)
                           15)
                (pas-check (quote not-law)
                           (pas-field pas-algebra (quote not-law))
                           (quote same-width-bit-inversion))
                (pas-check (quote weakening-law)
                           (pas-field pas-algebra (quote weakening-law))
                           (quote append-same-bit))
                (pas-check (quote boundary-law)
                           (pas-field pas-algebra (quote boundary-law))
                           (quote eighth-directed-step-reaches-function-sid-endpoint))))))
      (cond
        ((atom failure) (structural-kind empty-list)
         (quote (core4-predicate-answer-scale-ok)))
        ((quote pas-contract-failure) pas-contract-failure
         failure)))))

(pas-verdict)
