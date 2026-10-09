; #1115 executable witness.
; The canonical registry API performs the semantic lookup.
; The witness receives the canonical registry source as data from the test
; harness, parses it once in Lisp, and never re-enters host I/O.
;
; Backend boundary data is only: exact SID, arguments, portable contract.

(00001001 early-sid-lowering-backend-request?
  (00001000 (request)
    (00000111
      ((00000010 request)
       (00000001 no))
      ((not? (00000010 request))
       (10011100 ((first-field (00000101 request)))
         (00000111
           ((00000010 first-field)
            (00000001 no))
           ((not? (00000010 first-field))
            (00000111
              ((00100010 (00000101 first-field) (00000001 sid))
               (00000001 yes))
              ((not? (00100010 (00000101 first-field) (00000001 sid)))
               (00000001 no)))))))))

(00001001 early-sid-lower
  (00001000 (registry surface arguments contract)
    (10011100 ((sid (semantic-registry-id-in registry surface)))
      (00000111
        ((00100010 sid (00000001 ()))
         (00000001 rejected))
        ((not? (00100010 sid (00000001 ())))
         (00100111
           (00000100 (00000001 sid) sid)
           (00000100 (00000001 arguments) arguments)
           (00000100 (00000001 contract) contract)))))))

(00001001 early-sid-lowering-peer-check
  (00001000 (registry surface-a surface-b surface-c surface-d)
    (10011100 ((a (semantic-registry-id-in registry surface-a))
          (b (semantic-registry-id-in registry surface-b))
          (c (semantic-registry-id-in registry surface-c))
          (d (semantic-registry-id-in registry surface-d)))
      (00000111
        ((00100010 a b)
         (00000111
           ((00100010 b c)
            (00000111
              ((00100010 c d)
               (00100111 (00000001 same) a))
              ((not? (00100010 c d))
               (00000001 distinct))))
           ((not? (00100010 b c))
            (00000001 distinct))))
        ((not? (00100010 a b))
         (00000001 distinct))))))

(00001001 early-sid-lowering-witness
  (00001000 (registry-source)
    (10011100 ((registry (semantic-registry-read-source registry-source)))
      (10011100 ((atom-en (semantic-registry-id-in registry (00000001 atom?)))
            (atom-uk (semantic-registry-id-in registry (00000001 атом?)))
            (atom-ukr (semantic-registry-id-in registry (00000001 атом?)))
            (atom-sa (semantic-registry-id-in registry (00000001 aṇu)))
            (atom-sym (semantic-registry-id-in registry (00000001 .?))))
        (00100111
          (early-sid-lowering-peer-check
            registry
            (00000001 atom?) (00000001 атом?) (00000001 aṇu) (00000001 .?))
          (early-sid-lowering-backend-request?
            (early-sid-lower
              registry
              (00000001 atom?)
              (00000001 (x))
              (00000001 (portable-result-domain structural-relation))))
          (early-sid-lowering-backend-request?
            (00000001 (surface atom?)))
          (00100010 atom-en atom-uk)
          (00100010 atom-en atom-ukr)
          (00100010 atom-en atom-sa)
          (00100010 atom-en atom-sym)
          (semantic-registry-id-in registry (00000001 not-admitted-by-language)))))))