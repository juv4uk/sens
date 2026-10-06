; Prove that the SENS Lisp runtime can read the canonical D1-D6 table as data.
; No Python parser is involved in this witness.

(00001001 domain-form
  (00000101
    (01001011
      (10100110 "lib/generated/domain-table-d1-d6.lisp"))))

(00001001 domain-tag (00000101 domain-form))
(00001001 domain-rows (00000110 domain-form))

(00000111
  ((00000011 domain-tag (00000001 domain-ft/1))
   (00000111
     ((00000011 (00101000 domain-rows) 126)
      (01001000 "DOMAIN-TABLE-READ: PASS rows=126"))
     (t
      (00000101 ()))))
  (t
   (00000101 ())))
