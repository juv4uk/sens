; Свідок топології співвідповідників порівняння #536 мовою СЕНС.
; Перевіряємо тотожності й незалежне лексичне затінення проєкцій.
; Спостереження не визначають математичної істини точного Q.
; Її встановлюють contracts/exact-q-binary-contract.lisp та відповідні свідки.
; Порівняння між українською, санскритською та символьною проєкціями
; навмисно лишається багатомовним: це предмет самої перевірки.
; Назви протокольних результатів у цитованих даних незмінні.

(визначити спостереження-топології-співвідповідників-порівняння
  (список
    ; Initial stable peer identities.
    (тотожне? менше? hīna?)
    (тотожне? hīna? <)
    (тотожне? більше? adhika?)
    (тотожне? adhika? >)
    (тотожне? рівне? sama?)
    (тотожне? sama? =)

    ; 1014: shadow each spelling independently. The shadow becomes distinct,
    ; while the two untouched peers remain one callable identity.
    (нехай ((менше? (функція (ліве праве) (як-є shadowed))))
      (список (тотожне? менше? hīna?) (тотожне? hīna? <)))
    (нехай ((hīna? (функція (ліве праве) (як-є shadowed))))
      (список (тотожне? hīna? менше?) (тотожне? менше? <)))
    (нехай ((< (функція (ліве праве) (як-є shadowed))))
      (список (тотожне? < менше?) (тотожне? менше? hīna?)))

    ; 1015.
    (нехай ((більше? (функція (ліве праве) (як-є shadowed))))
      (список (тотожне? більше? adhika?) (тотожне? adhika? >)))
    (нехай ((adhika? (функція (ліве праве) (як-є shadowed))))
      (список (тотожне? adhika? більше?) (тотожне? більше? >)))
    (нехай ((> (функція (ліве праве) (як-є shadowed))))
      (список (тотожне? > більше?) (тотожне? більше? adhika?)))

    ; 1016.
    (нехай ((рівне? (функція (ліве праве) (як-є shadowed))))
      (список (тотожне? рівне? sama?) (тотожне? sama? =)))
    (нехай ((sama? (функція (ліве праве) (як-є shadowed))))
      (список (тотожне? sama? рівне?) (тотожне? рівне? =)))
    (нехай ((= (функція (ліве праве) (як-є shadowed))))
      (список (тотожне? = рівне?) (тотожне? рівне? sama?)))))

(визначити очікування-топології-співвідповідників-порівняння
  (як-є
    (
      (identity-relation same)
      (identity-relation same)
      (identity-relation same)
      (identity-relation same)
      (identity-relation same)
      (identity-relation same)

      ((identity-relation distinct) (identity-relation same))
      ((identity-relation distinct) (identity-relation same))
      ((identity-relation distinct) (identity-relation same))

      ((identity-relation distinct) (identity-relation same))
      ((identity-relation distinct) (identity-relation same))
      ((identity-relation distinct) (identity-relation same))

      ((identity-relation distinct) (identity-relation same))
      ((identity-relation distinct) (identity-relation same))
      ((identity-relation distinct) (identity-relation same))
    )))

; Колишні назви — сумісні зв'язування тих самих двох значень.
(визначити runtime-peer-comparison-topology-observations спостереження-топології-співвідповідників-порівняння)
(визначити runtime-peer-comparison-topology-expected очікування-топології-співвідповідників-порівняння)


(за-умовою
  ((однакові?
     спостереження-топології-співвідповідників-порівняння
     очікування-топології-співвідповідників-порівняння)
   (structural-relation same)
   (як-є (runtime-peer-comparison-topology-witness (status pass))))
  ((однакові?
     спостереження-топології-співвідповідників-порівняння
     очікування-топології-співвідповідників-порівняння)
   (structural-relation distinct)
   (список
     (як-є runtime-peer-comparison-topology-witness)
     (як-є (status fail))
     (список
       (як-є actual)
       спостереження-топології-співвідповідників-порівняння)
     (список
       (як-є expected)
       очікування-топології-співвідповідників-порівняння))))
