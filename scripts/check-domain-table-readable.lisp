; Prove that SENS itself reads the self-describing exact-width domain table.
; Critical property: equal payloads at different widths must stay distinct
; after read-file -> read-all: 0 != 00 != 000 != 0000 != 00000 != 000000.

(00001001 domain-form
  (00000101
    (01001011
      (10100110 "lib/generated/domain-table-d1-d6.lisp"))))

(00001001 domain-tag (00000101 domain-form))
(00001001 domain-rows (00000110 domain-form))

(00001001 key-text
  (00001000 (row)
    (01001100 (00000101 row))))

; Row offsets are cumulative domain capacities:
; D1 starts 0, D2 starts 2, D3 starts 6, D4 starts 14, D5 starts 30, D6 starts 62.
(00001001 k1 (key-text (00101011 0 domain-rows)))
(00001001 k2 (key-text (00101011 2 domain-rows)))
(00001001 k3 (key-text (00101011 6 domain-rows)))
(00001001 k4 (key-text (00101011 14 domain-rows)))
(00001001 k5 (key-text (00101011 30 domain-rows)))
(00001001 k6 (key-text (00101011 62 domain-rows)))

(00000111
  ((00000011 domain-tag (00000001 domains/1))
   (00000111
     ((00000011 (00101000 domain-rows) 126)
      (00000111
        ((00000011 k1 "0")
         (00000111
           ((00000011 k2 "00")
            (00000111
              ((00000011 k3 "000")
               (00000111
                 ((00000011 k4 "0000")
                  (00000111
                    ((00000011 k5 "00000")
                     (00000111
                       ((00000011 k6 "000000")
                        (01001000 "DOMAIN-TABLE-READ: PASS rows=126 widths=1..6"))
                       (t (domain-table-width-loss-d6))))
                    (t (domain-table-width-loss-d5))))
                 (t (domain-table-width-loss-d4))))
              (t (domain-table-width-loss-d3))))
           (t (domain-table-width-loss-d2))))
        (t (domain-table-width-loss-d1))))
     (t (domain-table-row-count-failure))))
  (t (domain-table-schema-failure)))
