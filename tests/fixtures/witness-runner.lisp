; tests/fixtures/witness-runner.lisp — протокол вердиктів семантичних свідчень, яким володіє Lisp.
; Ukrainian projection only.

(визначити witness-d1-no
  (функція ()
    (тотожне? (як-є witness-no-left) (як-є witness-no-right))))

(визначити witness-d1-no?
  (функція (value)
    (тотожне? value (witness-d1-no))))

(визначити witness-find-entry
  (функція (key alist)
    (за-умовою
      ((атом? alist)
       (як-є ()))
      ((тотожне? (перше (перше alist)) key)
       (перше alist))
      (так (witness-find-entry key (решта alist))))))

(визначити witness-field
  (функція (key alist)
    (нехай ((entry (witness-find-entry key alist)))
      (за-умовою
        ((атом? entry) (як-є ()))
        (так (решта entry))))))

(визначити witness-has-field?
  (функція (key alist)
    (нехай ((entry (witness-find-entry key alist)))
      (за-умовою
        ((атом? entry) (witness-d1-no))
        (так (як-є (1)))))))

(визначити witness-check-row
  (функція (row)
    (нехай ((actual (witness-field (як-є actual) row))
          (expected (witness-field (як-є expected) row)))
      (за-умовою
        ((однакові? actual expected) (як-є (status pass)))
        (так (список (як-є status) (як-є fail) (як-є actual) actual (як-є expected) expected))))))

(визначити witness-check-rows
  (функція (rows)
    (за-умовою
      ((атом? rows)
       (як-є (witness-runner (status pass))))
      (так
       (нехай ((result (witness-check-row (перше rows))))
         (за-умовою
           ((тотожне? (перше result) (як-є status))
            (за-умовою
              ((тотожне? (друге result) (як-є pass))
               (witness-check-rows (решта rows)))
              (так result)))
           (так result)))))))
