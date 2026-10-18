; Binary trees N=10 profile. Return checks in CLBG order; formatting is untimed.
(визначити make-tree
  (функція (depth)
    (за-умовою
      ((тотожне? depth #d24:000000000000000000000000) (як-є leaf))
      (#d1:1
        (сполучити
          (make-tree (01011 depth #d24:000000000000000000000001))
          (make-tree (01011 depth #d24:000000000000000000000001)))))))

(визначити tree-check
  (функція (tree)
    (за-умовою
      ((атом? tree) #d24:000000000000000000000001)
      (#d1:1
        (01010
          #d24:000000000000000000000001
          (01010
            (tree-check (перше tree))
            (tree-check (решта tree))))))))

(визначити churn
  (функція (depth iterations total)
    (за-умовою
      ((тотожне? iterations #d24:000000000000000000000000) total)
      (#d1:1
        (churn
          depth
          (01011 iterations #d24:000000000000000000000001)
          (01010 total (tree-check (make-tree depth))))))))
