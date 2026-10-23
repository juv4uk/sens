; generate-meta-semantic-registry — українська проєкція шаблонів виводу
; Джерело влади: чинні lib/domains/d1.lisp ... lib/domains/d10.lisp.
; Це читання канонічних проєкцій, а не право виконання чи допуск T5M.
; Зовнішні назви my-semantic-* зберігаємо, бо вони мають споживачів;
; локальний вхід до стану готовності має українську назву.
; Статус not-verified є цитованими даними, а не підтвердженням виконання.

(завантажити-файл "lib/surface/semantic-registry-api.lisp")

(визначити my-semantic-surface-registry
  (функція ()
    (прочитати-семантичний-реєстр)))

(визначити my-semantic-id-for-surface
  (функція (назва-поверхні)
    (ідентичність-за-проєкцією
      назва-поверхні
      (my-semantic-surface-registry))))

(визначити готовність-породження-метасемантичного-реєстру
  (функція ()
    (як-є (generate-meta-semantic-registry (status not-verified) (projection ukr)))))
