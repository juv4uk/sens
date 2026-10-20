; #305 — semantic-registry meaning is Lisp-owned before the stale Rust oracle
; is retired. Ukrainian projection only.
; Expected values and the comparison logic stay here in Lisp.

(load "lib/generated/meta-semantic-registry.lisp")
(load "lib/meta-eval.lisp")

(визначити registry-native-value
  (функція (source)
    (прочитати-вираз source)))

(визначити registry-meta-value
  (функція (source)
    (обчислити-мета-вираз (прочитати-вираз source) (як-є ()))))

(визначити registry-meta-program-result
  (функція (source)
    (решта (обчислити-послідовність-форм (прочитати-форми source) (як-є ())))))

(визначити registry-witness-failure
  (функція (case actual expected)
    (список
      (як-є meta-semantic-registry-witness)
      (як-є (status fail))
      (список (як-є case) case)
      (список (як-є actual) actual)
      (список (як-є expected) expected))))

(визначити registry-check-rows
  (функція (rows)
    (за-умовою
      ((атом? rows)
       (як-є (meta-semantic-registry-witness (status pass))))
      (так
       (нехай ((row (перше rows)))
         (за-умовою
           ((однакові? (друге row) (третє row))
            (registry-check-rows (решта rows)))
           (так
            (registry-witness-failure
              (перше row)
              (друге row)
              (третє row)))))))))

(визначити registry-witness-rows
  (функція ()
    (список
      (список (як-є quote-id-en)
            (my-semantic-id-for-surface (як-є quote))
            1)
      (список (як-є quote-id-uk)
            (my-semantic-id-for-surface (як-є як-є))
            1)
      (список (як-є lambda-id-en)
            (my-semantic-id-for-surface (як-є lambda))
            8)
      (список (як-є lambda-id-uk)
            (my-semantic-id-for-surface (як-є функція))
            8)
      (список (як-є define-id-en)
            (my-semantic-id-for-surface (як-є define))
            9)
      (список (як-є define-id-uk)
            (my-semantic-id-for-surface (як-є визначити))
            9)
      (список (як-є unadmitted-closed)
            (my-semantic-id-for-surface (як-є not-a-surface))
            (як-є ()))
      (список (як-є atom-native-legacy-byte)
            (registry-native-value "(атом? (як-є x))")
            (як-є (1)))
      (список (як-є atom-meta-en)
            (registry-meta-value "(атом? (як-є x))")
            (як-є (1)))
      (список (як-є atom-meta-uk)
            (registry-meta-value "(атом? (як-є x))")
            (як-є (1)))
      (список (як-є atom-meta-sa)
            (registry-meta-value "(aṇu (svarūpa x))")
            (як-є (1)))
      (список (як-є atom-meta-symbolic)
            (registry-meta-value "(.? (як-є x))")
            (як-є (1)))
      (список (як-є lambda-native-en)
            (registry-native-value "((функція (x) x) 42)")
            42)
      (список (як-є lambda-native-uk)
            (registry-native-value "((функція (x) x) 42)")
            42)
      (список (як-є define-native-en)
            (registry-native-value "(визначити registry-native-en-answer 42)")
            42)
      (список (як-є define-native-uk)
            (registry-native-value "(визначити registry-native-uk-answer 42)")
            42)
      (список (як-є def-native-compat)
            (registry-native-value "(визначити registry-native-def-answer 42)")
            42)
      (список (як-є lambda-meta-en)
            (registry-meta-value "((функція (x) x) 42)")
            42)
      (список (як-є lambda-meta-uk)
            (registry-meta-value "((функція (x) x) 42)")
            42)
      (список (як-є define-meta-en)
            (registry-meta-program-result "(визначити registry-meta-en-answer 42)")
            42)
      (список (як-є define-meta-uk)
            (registry-meta-program-result "(визначити registry-meta-uk-answer 42)")
            42)
      (список (як-є def-meta-compat)
            (registry-meta-program-result "(визначити registry-meta-def-answer 42)")
            42))))

(registry-check-rows (registry-witness-rows))
