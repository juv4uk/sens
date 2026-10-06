; Acceptance witness for #3946.
; Each domain table is a separate Lisp file. The ordinary reader must eventually
; preserve the exact-width first key in every file without quoting it.

(00001001 load-domain
  (00001000 (path)
    (00000101
      (01001011
        (10100110 path)))))

(00001001 table-rows
  (00001000 (form)
    (00000110 form)))

(00001001 first-key-text
  (00001000 (form)
    (01001100
      (00000101
        (00101011 0 (table-rows form))))))

(00001001 d1 (load-domain "lib/domains/d1.lisp"))
(00001001 d2 (load-domain "lib/domains/d2.lisp"))
(00001001 d3 (load-domain "lib/domains/d3.lisp"))
(00001001 d4 (load-domain "lib/domains/d4.lisp"))
(00001001 d5 (load-domain "lib/domains/d5.lisp"))
(00001001 d6 (load-domain "lib/domains/d6.lisp"))
(00001001 d8 (load-domain "lib/domains/d8.lisp"))

(00000111
  ((00000011 (00000101 d1) (00000001 domain-table/1))
   (00000111
     ((00000011 (00101000 (table-rows d1)) 2)
      (00000111
        ((00000011 (00101000 (table-rows d2)) 4)
         (00000111
           ((00000011 (00101000 (table-rows d3)) 8)
            (00000111
              ((00000011 (00101000 (table-rows d4)) 16)
               (00000111
                 ((00000011 (00101000 (table-rows d5)) 32)
                  (00000111
                    ((00000011 (00101000 (table-rows d6)) 64)
                     (00000111
                       ((00000011 (00101000 (table-rows d8)) 256)
                        (00000111
                       ((00000011 (first-key-text d1) "0")
                        (00000111
                          ((00000011 (first-key-text d2) "00")
                           (00000111
                             ((00000011 (first-key-text d3) "000")
                              (00000111
                                ((00000011 (first-key-text d4) "0000")
                                 (00000111
                                   ((00000011 (first-key-text d5) "00000")
                                    (00000111
                                      ((00000011 (first-key-text d6) "000000")
                                       (00000111
                                         ((00000011 (first-key-text d8) "00000000")
                                          (01001000 "DOMAIN-TABLE-READ: PASS files=7 rows=382 widths=1..6,8"))
                                         (t (domain-table-width-loss-d8))))
                                      (t (domain-table-width-loss-d6))))
                                   (t (domain-table-width-loss-d5))))
                                (t (domain-table-width-loss-d4))))
                             (t (domain-table-width-loss-d3))))
                          (t (domain-table-width-loss-d2))))
                       (t (domain-table-width-loss-d1))))
                          (t (domain-table-d8-count-failure))))
                    (t (domain-table-d6-count-failure))))
                 (t (domain-table-d5-count-failure))))
              (t (domain-table-d4-count-failure))))
           (t (domain-table-d3-count-failure))))
        (t (domain-table-d2-count-failure))))
     (t (domain-table-d1-count-failure))))
  (t (domain-table-schema-failure)))
