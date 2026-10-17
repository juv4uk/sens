; Binary trees N=10 profile. Return checks in CLBG order; formatting is untimed.
(0011 make-tree
  (0010 (depth)
    (110
      ((101 depth #d24:000000000000000000000000) (001 leaf))
      (#d1:1
        (111
          (make-tree (01011 depth #d24:000000000000000000000001))
          (make-tree (01011 depth #d24:000000000000000000000001)))))))

(0011 tree-check
  (0010 (tree)
    (110
      ((010 tree) #d24:000000000000000000000001)
      (#d1:1
        (01010
          #d24:000000000000000000000001
          (01010
            (tree-check (100 tree))
            (tree-check (011 tree))))))))

(0011 churn
  (0010 (depth iterations total)
    (110
      ((101 iterations #d24:000000000000000000000000) total)
      (#d1:1
        (churn
          depth
          (01011 iterations #d24:000000000000000000000001)
          (01010 total (tree-check (make-tree depth))))))))
