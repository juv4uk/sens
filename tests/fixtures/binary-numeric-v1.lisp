; #954 stacked on #1096 — BINARY is the explicit numeric interpretation
; boundary for reserved bare SID spellings.
;
; Bare eight bits remain semantic identity. Only an explicit call to BINARY
; asks for the exact integer represented by those bits.

(def binary-zero (binary 00000000))
(def binary-twelve (binary 00001100))
(def binary-max (binary 11111111))
(def binary-invalid (binary 12))

(cond
  ((= binary-zero 0) 1
   (cond
     ((= binary-twelve 12) 1
      (cond
        ((= binary-max 255) 1
         (cond
           ((atom binary-invalid) (structural-kind empty-list)
            (quote (binary-numeric-witness (status pass))))
           (t t
            (quote (binary-numeric-witness
                     (status fail)
                     (reason invalid-input-must-be-no-answer))))))
        (t t
         (quote (binary-numeric-witness
                  (status fail)
                  (reason max-boundary))))))
     (t t
      (quote (binary-numeric-witness
               (status fail)
               (reason sid-00001100-must-mean-12-when-explicit))))))
  (t t
   (quote (binary-numeric-witness
            (status fail)
            (reason zero-boundary)))))
