; generate-meta-semantic-registry — українська проєкція шаблонів виводу
; Генерує реєстр поверхонь без старих викличних кодів.
; Зовнішні назви my-semantic-* зберігаємо, бо вони мають споживачів;
; локальні зв'язування відтепер мають українські імена.

(визначити my-semantic-surface-registry
  (функція ()
    (як-є ())))

(визначити my-semantic-id-for-surface
  (функція (назва-поверхні)
    (нехай ((запис-поверхні (знайти-за-ключем назва-поверхні (my-semantic-surface-registry))))
      (за-умовою
        ((атом? запис-поверхні) (як-є ()))
        (так (перше запис-поверхні))))))

(визначити generate-meta-semantic-registry-ready
  (функція ()
    (як-є (generate-meta-semantic-registry (status pass) (projection ukr)))))
