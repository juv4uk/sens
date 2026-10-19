; Acceptance witness for #3946.
; Each domain table is a separate Lisp file. The ordinary reader must eventually
; preserve the exact-width first key in every file without quoting it.

(визначити load-domain
  (функція (path)
    (перше
      (читати-всі
        (читати-файл path)))))

(визначити table-rows
  (функція (form)
    (решта form)))

(визначити first-key-text
  (функція (form)
    (значення-у-текст
      (перше
        (елемент-списку-за-індексом 0 (table-rows form))))))

(визначити d1 (load-domain "lib/domains/d1.lisp"))
(визначити d2 (load-domain "lib/domains/d2.lisp"))
(визначити d3 (load-domain "lib/domains/d3.lisp"))
(визначити d4 (load-domain "lib/domains/d4.lisp"))
(визначити d5 (load-domain "lib/domains/d5.lisp"))
(визначити d6 (load-domain "lib/domains/d6.lisp"))
(визначити d8 (load-domain "lib/domains/d8.lisp"))

(за-умовою
  ((тотожне? (перше d1) (як-є domain-table/1))
   (за-умовою
     ((тотожне? (довжина (table-rows d1)) 2)
      (за-умовою
        ((тотожне? (довжина (table-rows d2)) 4)
         (за-умовою
           ((тотожне? (довжина (table-rows d3)) 8)
            (за-умовою
              ((тотожне? (довжина (table-rows d4)) 16)
               (за-умовою
                 ((тотожне? (довжина (table-rows d5)) 32)
                  (за-умовою
                    ((тотожне? (довжина (table-rows d6)) 64)
                     (за-умовою
                       ((тотожне? (довжина (table-rows d8)) 256)
                        (за-умовою
                       ((тотожне? (first-key-text d1) "0")
                        (за-умовою
                          ((тотожне? (first-key-text d2) "00")
                           (за-умовою
                             ((тотожне? (first-key-text d3) "000")
                              (за-умовою
                                ((тотожне? (first-key-text d4) "0000")
                                 (за-умовою
                                   ((тотожне? (first-key-text d5) "00000")
                                    (за-умовою
                                      ((тотожне? (first-key-text d6) "000000")
                                       (за-умовою
                                         ((тотожне? (first-key-text d8) "00000000")
                                          (друкувати "DOMAIN-TABLE-READ: PASS files=7 rows=382 widths=1..6,8"))
                                         (так (domain-table-width-loss-d8))))
                                      (так (domain-table-width-loss-d6))))
                                   (так (domain-table-width-loss-d5))))
                                (так (domain-table-width-loss-d4))))
                             (так (domain-table-width-loss-d3))))
                          (так (domain-table-width-loss-d2))))
                       (так (domain-table-width-loss-d1))))
                          (так (domain-table-d8-count-failure))))
                    (так (domain-table-d6-count-failure))))
                 (так (domain-table-d5-count-failure))))
              (так (domain-table-d4-count-failure))))
           (так (domain-table-d3-count-failure))))
        (так (domain-table-d2-count-failure))))
     (так (domain-table-d1-count-failure))))
  (так (domain-table-schema-failure)))
