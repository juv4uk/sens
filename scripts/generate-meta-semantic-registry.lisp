; generate-meta-semantic-registry — українська проєкція шаблонів виводу
; Генерує реєстр поверхонь без SID8 call-heads.

(визначити my-semantic-surface-registry
  (функція ()
    (як-є ())))

(визначити my-semantic-id-for-surface
  (функція (name)
    (нехай ((entry (знайти-за-ключем name (my-semantic-surface-registry))))
      (за-умовою
        ((атом? entry) (як-є ()))
        (так (перше entry))))))

(визначити generate-meta-semantic-registry-ready
  (функція ()
    (як-є (generate-meta-semantic-registry (status pass) (projection ukr)))))
