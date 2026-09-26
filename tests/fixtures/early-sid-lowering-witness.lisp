; #1115 executable witness.
; The canonical registry API performs the semantic lookup.
; The witness receives the canonical registry source as data from the test
; harness, parses it once in Lisp, and never re-enters host I/O.
;
; Backend boundary data is only: exact SID, arguments, portable contract.

(def early-sid-lowering-backend-request?
  (lambda (request)
    (cond
      ((atom? request)
       ()
       (quote no))
      ((atom? request)
       (0)
       (let ((first-field (car request)))
         (cond
           ((atom? first-field)
            (0)
            (cond
              ((equal? (car first-field) (quote sid))
               (1)
               (quote yes))
              ((equal? (car first-field) (quote sid))
               (0)
               (quote no))))
           ((atom? first-field)
            (1)
            (quote no))
           ((atom? first-field)
            ()
            (quote no))))))))

(def early-sid-lower
  (lambda (registry surface arguments contract)
    (let ((sid (semantic-registry-id-in registry surface)))
      (cond
        ((atom? sid)
         ()
         (quote rejected))
        ((atom? sid)
         (1)
         (list
           (cons (quote sid) sid)
           (cons (quote arguments) arguments)
           (cons (quote contract) contract)))))))

(def early-sid-lowering-peer-check
  (lambda (registry surface-a surface-b surface-c surface-d)
    (let ((a (semantic-registry-id-in registry surface-a))
          (b (semantic-registry-id-in registry surface-b))
          (c (semantic-registry-id-in registry surface-c))
          (d (semantic-registry-id-in registry surface-d)))
      (cond
        ((equal? a b)
         (1)
         (cond
           ((equal? b c)
            (1)
            (cond
              ((equal? c d)
               (1)
               (list (quote same) a))
              ((equal? c d)
               (0)
               (quote distinct))))
           ((equal? b c)
            (0)
            (quote distinct))))
        ((equal? a b)
         (0)
         (quote distinct))))))

(def early-sid-lowering-witness
  (lambda (registry-source)
    (let ((registry (semantic-registry-read-source registry-source)))
      (let ((atom-en (semantic-registry-id-in registry (quote atom?)))
            (atom-uk (semantic-registry-id-in registry (quote атом?)))
            (atom-ukr (semantic-registry-id-in registry (quote атом?)))
            (atom-sa (semantic-registry-id-in registry (quote aṇu)))
            (atom-sym (semantic-registry-id-in registry (quote .?))))
        (list
          (early-sid-lowering-peer-check
            registry
            (quote atom?) (quote атом?) (quote aṇu) (quote .?))
          (early-sid-lowering-backend-request?
            (early-sid-lower
              registry
              (quote atom?)
              (quote (x))
              (quote (portable-result-domain structural-relation))))
          (early-sid-lowering-backend-request?
            (quote (surface atom?)))
          (equal? atom-en atom-uk)
          (equal? atom-en atom-ukr)
          (equal? atom-en atom-sa)
          (equal? atom-en atom-sym)
          (semantic-registry-id-in registry (quote not-admitted-by-language)))))))