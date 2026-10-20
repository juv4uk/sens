;; Knowledge D3 — українська проєкція (candidate).
;; Журнал знань і пакетні операції без SID8 call-heads.

(визначити knowledge-package
  (функція (name clauses metadata)
    (список (як-є knowledge-package) name clauses metadata)))

(визначити knowledge-package?
  (функція (value)
    (за-умовою
      ((атом? value) ні)
      ((тотожне? (перше value) (як-є knowledge-package)) так)
      (так ні))))

(визначити knowledge-name (функція (pkg) (друге pkg)))
(визначити knowledge-clauses (функція (pkg) (третє pkg)))
(визначити knowledge-metadata (функція (pkg) (четверте pkg)))

(визначити knowledge-tell
  (функція (pkg clause)
    (knowledge-package
      (knowledge-name pkg)
      (сполучити clause (knowledge-clauses pkg))
      (knowledge-metadata pkg))))

(визначити knowledge-retract
  (функція (pkg clause)
    (knowledge-package
      (knowledge-name pkg)
      (вилучити clause (knowledge-clauses pkg))
      (knowledge-metadata pkg))))

(визначити knowledge-member?
  (функція (clause clauses)
    (за-умовою
      ((атом? clauses) ні)
      ((однакові? clause (перше clauses)) так)
      (так (knowledge-member? clause (решта clauses))))))

(визначити knowledge-union
  (функція (left right)
    (за-умовою
      ((атом? right) left)
      ((knowledge-member? (перше right) left)
       (knowledge-union left (решта right)))
      (так (knowledge-union (сполучити (перше right) left) (решта right))))))

(визначити knowledge-d3-candidate-witness
  (функція ()
    (нехай ((pkg0 (knowledge-package (як-є demo) (як-є ()) (як-є ())))
          (pkg1 (knowledge-tell pkg0 (як-є (fact a))))
          (pkg2 (knowledge-tell pkg1 (як-є (fact b)))))
      (за-умовою
        ((knowledge-package? pkg2)
         (за-умовою
           ((knowledge-member? (як-є (fact a)) (knowledge-clauses pkg2))
            (як-є (knowledge-d3-candidate-witness (status pass))))
           (так (як-є (knowledge-d3-candidate-witness (status fail member))))))
        (так (як-є (knowledge-d3-candidate-witness (status fail not-package))))))))

(knowledge-d3-candidate-witness)
