; Acceptance witness for #3946.
; Each domain table is a separate Lisp file. The ordinary reader must eventually
; preserve the exact-width first key in every file without quoting it.

(0011 load-domain
  (0010 (path)
    (100
      (110101001
        (110110111 path)))))

(0011 table-rows
  (0010 (form)
    (011 form)))

(0011 first-key-text
  (0010 (form)
    (11110100
      (100
        (000100 0 (table-rows form))))))

(0011 d1 (load-domain "lib/domains/d1.lisp"))
(0011 d2 (load-domain "lib/domains/d2.lisp"))
(0011 d3 (load-domain "lib/domains/d3.lisp"))
(0011 d4 (load-domain "lib/domains/d4.lisp"))
(0011 d5 (load-domain "lib/domains/d5.lisp"))
(0011 d6 (load-domain "lib/domains/d6.lisp"))
(0011 d8 (load-domain "lib/domains/d8.lisp"))

(110
  ((101 (100 d1) (001 domain-table/1))
   (110
     ((101 (000000 (table-rows d1)) 2)
      (110
        ((101 (000000 (table-rows d2)) 4)
         (110
           ((101 (000000 (table-rows d3)) 8)
            (110
              ((101 (000000 (table-rows d4)) 16)
               (110
                 ((101 (000000 (table-rows d5)) 32)
                  (110
                    ((101 (000000 (table-rows d6)) 64)
                     (110
                       ((101 (000000 (table-rows d8)) 256)
                        (110
                       ((101 (first-key-text d1) "0")
                        (110
                          ((101 (first-key-text d2) "00")
                           (110
                             ((101 (first-key-text d3) "000")
                              (110
                                ((101 (first-key-text d4) "0000")
                                 (110
                                   ((101 (first-key-text d5) "00000")
                                    (110
                                      ((101 (first-key-text d6) "000000")
                                       (110
                                         ((101 (first-key-text d8) "00000000")
                                          (11011011 "DOMAIN-TABLE-READ: PASS files=7 rows=382 widths=1..6,8"))
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
