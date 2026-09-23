; #1115 executable witness.
; The canonical registry API performs the semantic lookup.
; The witness receives the canonical registry source as data from the test
; harness, parses it once in Lisp, and never re-enters host I/O.
;
; Backend boundary data is only: exact SID, arguments, portable contract.

(def early-sid-lowering-backend-request?
  (lambda (request)
    (cond
      ((atom request)
       (structural-kind empty-list)
       (quote no))
      ((atom request)
       (structural-kind pair)
       (cond
         ((equal? (car request) (quote surface))
          (structural-relation same)
          (quote no))
         ((equal? (car request) (quote surface))
          (structural-relation distinct)
          (let ((fields (cdr request)))
            (cond
              ((atom fields)
               (structural-kind empty-list)
               (quote no))
              ((atom fields)
               (structural-kind pair)
               (let ((first-field (car fields)))
                 (cond
                   ((equal? (car first-field) (quote sid))
                    (structural-relation same)
                    (quote yes))
                   ((equal? (car first-field) (quote sid))
                    (structural-relation distinct)
                    (quote no)))))))))))))

(def early-sid-lower
  (lambda (registry surface arguments contract)
    (let ((sid (semantic-registry-id-in registry surface)))
      (cond
        ((atom sid)
         (structural-kind empty-list)
         (quote rejected))
        ((atom sid)
         (structural-kind atom)
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
         (structural-relation same)
         (cond
           ((equal? b c)
            (structural-relation same)
            (cond
              ((equal? c d)
               (structural-relation same)
               (list (quote same) a))
              ((equal? c d)
               (structural-relation distinct)
               (quote distinct))))
           ((equal? b c)
            (structural-relation distinct)
            (quote distinct))))
        ((equal? a b)
         (structural-relation distinct)
         (quote distinct))))))

(def early-sid-lowering-witness
  (lambda (registry-source)
    (let ((registry (semantic-registry-read-source registry-source)))
      (let ((atom-en (semantic-registry-id-in registry "atom"))
            (atom-uk (semantic-registry-id-in registry "атом?"))
            (atom-ukr (semantic-registry-id-in registry "атом?"))
            (atom-sa (semantic-registry-id-in registry "aṇu"))
            (atom-sym (semantic-registry-id-in registry ".?")))
        (list
          (early-sid-lowering-peer-check
            registry
            "atom" "атом?" "aṇu" ".?")
          (early-sid-lowering-backend-request?
            (early-sid-lower
              registry
              "atom"
              (quote (x))
              (quote (portable-result-domain structural-relation))))
          (early-sid-lowering-backend-request?
            (quote (surface atom?)))
          (equal? atom-en atom-uk)
          (equal? atom-en atom-ukr)
          (equal? atom-en atom-sa)
          (equal? atom-en atom-sym)
          (semantic-registry-id-in registry "not-admitted-by-language"))))))