; #1115 executable witness.
; The canonical registry API performs the semantic lookup.
; The witness then constructs only the data shape admitted at the backend
; boundary: exact SID, arguments, and portable contract.

(def early-sid-lowering-backend-request?
  (lambda (request)
    (cond
      ((atom request)
       (structural-kind empty-list)
       (quote no))
      ((quote always)
       (quote always)
       (cond
         ((equal? (car request) (quote surface))
          (structural-relation same)
          (quote no))
         ((quote always)
          (quote always)
          (let ((fields (cdr request)))
            (cond
              ((atom fields)
               (structural-kind empty-list)
               (quote no))
              ((quote always)
               (quote always)
               (let ((first-field (car fields)))
                 (cond
                   ((equal? (car first-field) (quote sid))
                    (structural-relation same)
                    (quote yes))
                   ((quote always)
                    (quote always)
                    (quote no)))))))))))

(def early-sid-lower
  (lambda (surface arguments contract)
    (let ((sid (semantic-registry-id surface)))
      (cond
        ((atom sid)
         (structural-kind empty-list)
         (quote rejected))
        ((quote always)
         (quote always)
         (list
           (cons (quote sid) sid)
           (cons (quote arguments) arguments)
           (cons (quote contract) contract)))))))

(def early-sid-lowering-peer-check
  (lambda (surface-a surface-b surface-c surface-d)
    (let ((a (semantic-registry-id surface-a))
          (b (semantic-registry-id surface-b))
          (c (semantic-registry-id surface-c))
          (d (semantic-registry-id surface-d)))
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
              ((quote always)
               (quote always)
               (quote distinct))))
           ((quote always)
            (quote always)
            (quote distinct))))
        ((quote always)
         (quote always)
         (quote distinct)))))

(def early-sid-lowering-witness
  (lambda ()
    (let ((atom-en (semantic-registry-id "atom"))
          (atom-uk (semantic-registry-id "атом?"))
          (atom-ukr (semantic-registry-id "атом?"))
          (atom-sa (semantic-registry-id "aṇu"))
          (atom-sym (semantic-registry-id ".?")))
      (list
        (early-sid-lowering-peer-check
          "atom" "атом?" "aṇu" ".?")
        (early-sid-lowering-backend-request?
          (early-sid-lower
            "atom"
            (quote (x))
            (quote (portable-result-domain structural-relation))))
        (early-sid-lowering-backend-request?
          (quote (surface atom?)))
        (equal? atom-en atom-uk)
        (equal? atom-en atom-ukr)
        (equal? atom-en atom-sa)
        (equal? atom-en atom-sym)
        (semantic-registry-id "not-admitted-by-language")))))