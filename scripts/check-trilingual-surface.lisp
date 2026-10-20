; #549 / #76 — мовна заміна scripts/check_trilingual_surface.py.
; Це перевірка правил супроводу, не джерело семантичних законів.
; Авторитетом залишається lib/surface/semantic-registry.lisp.
;
; Перевіряємо канонічний реєстр як структуру даних: стани української,
; англійської та санскритської проєкцій, повноту й унікальність полів.
; За неправильної форми або відсутньої проєкції повертаємо відмову.
; Параметр --require-complete зберігає історичне правило допуску випуску.

(визначити тримовні-стани
  (як-є (stable candidate missing compatibility-only)))

(визначити тримовні-людські-проєкції
  (як-є (uk en sa)))

(визначити тримовна-помилка
  (функція (kind detail)
    (нехай ((shown
            (друкувати
              (список
                (як-є trilingual-surface-error)
                kind
                detail))))
      ; Навмисно невизначений виклик: командний виконавець повертає ненульовий код.
      (trilingual-surface-check-failed kind detail))))

(визначити тримовний-стан-належності
  (функція (value values)
    (за-умовою
      ((атом? values) (structural-kind empty-list) (як-є absent))
      ((атом? values) (structural-kind atom) (як-є malformed))
      ((атом? values) (structural-kind pair)
       (за-умовою
         ((однакові? value (перше values)) (structural-relation same)
          (як-є present))
         ((однакові? value (перше values)) (structural-relation distinct)
          (тримовний-стан-належності value (решта values))))))))

(визначити тримовний-стан-трійки
  (функція (value)
    (за-умовою
      ((атом? value) (structural-kind empty-list) (як-є no))
      ((атом? value) (structural-kind atom) (як-є no))
      ((атом? value) (structural-kind pair)
       (нехай ((rest1 (решта value)))
         (за-умовою
           ((атом? rest1) (structural-kind pair)
            (нехай ((rest2 (решта rest1)))
              (за-умовою
                ((атом? rest2) (structural-kind pair)
                 (нехай ((rest3 (решта rest2)))
                   (за-умовою
                     ((атом? rest3) (structural-kind empty-list) (як-є yes))
                     ((атом? rest3) (structural-kind atom) (як-є no))
                     ((атом? rest3) (structural-kind pair) (як-є no)))))
                ((атом? rest2) (structural-kind empty-list) (як-є no))
                ((атом? rest2) (structural-kind atom) (як-є no)))))
           ((атом? rest1) (structural-kind empty-list) (як-є no))
           ((атом? rest1) (structural-kind atom) (як-є no))))))))

(визначити тримовний-стан-цитованого-символу
  (функція (field)
    (за-умовою
      ((однакові?
         field
         (список (як-є sym) (список (як-є quote) (як-є stable))))
       (structural-relation same)
       (як-є yes))
      ((однакові?
         field
         (список (як-є sym) (список (як-є quote) (як-є stable))))
       (structural-relation distinct)
       (як-є no)))))

(визначити тримовна-мова-поля
  (функція (field)
    (нехай ((спеціальна-змінна (тримовний-стан-цитованого-символу field)))
      (за-умовою
        ((тотожне? спеціальна-змінна (як-є yes)) (identity-relation same) (як-є sym))
        ((тотожне? спеціальна-змінна (як-є yes)) (identity-relation distinct) (перше field))))))

(визначити тримовний-стан-поля
  (функція (field)
    (нехай ((спеціальна-змінна (тримовний-стан-цитованого-символу field)))
      (за-умовою
        ((тотожне? спеціальна-змінна (як-є yes)) (identity-relation same) (як-є stable))
        ((тотожне? спеціальна-змінна (як-є yes)) (identity-relation distinct) (third field))))))

(визначити тримовне-перевірити-звичайне-поле
  (функція (field)
    (нехай ((shape (тримовний-стан-трійки field)))
      (за-умовою
        ((тотожне? shape (як-є yes)) (identity-relation distinct)
         (тримовна-помилка (як-є malformed-surface) field))
        ((тотожне? shape (як-є yes)) (identity-relation same)
         (нехай-послідовно ((language (перше field))
                (name (second field))
                (status (third field)))
           (за-умовою
             ((атом? language) (structural-kind atom)
              (за-умовою
                ((атом? name) (structural-kind atom)
                 (за-умовою
                   ((атом? status) (structural-kind atom)
                    (нехай ((state (тримовний-стан-належності status тримовні-стани)))
                      (за-умовою
                        ((тотожне? state (як-є present)) (identity-relation same)
                         (як-є valid))
                        ((тотожне? state (як-є present)) (identity-relation distinct)
                         (тримовна-помилка (як-є unknown-status) field))))
                   ((атом? status) (structural-kind empty-list)
                    (тримовна-помилка (як-є malformed-status) field))
                   ((атом? status) (structural-kind pair)
                    (тримовна-помилка (як-є malformed-status) field))))
                ((атом? name) (structural-kind empty-list)
                 (тримовна-помилка (як-є malformed-name) field))
                ((атом? name) (structural-kind pair)
                 (тримовна-помилка (як-є malformed-name) field))))
             ((атом? language) (structural-kind empty-list)
              (тримовна-помилка (як-є malformed-surface-name) field))
             ((атом? language) (structural-kind pair)
              (тримовна-помилка (як-є malformed-surface-name) field))))))))))

(визначити тримовне-вимагати-людські-проєкції
  (функція (seen)
    (нехай ((uk-state (тримовний-стан-належності (як-є uk) seen)))
      (за-умовою
        ((тотожне? uk-state (як-є present)) (identity-relation distinct)
         (тримовна-помилка (як-є missing-human-surface) (як-є uk)))
        ((тотожне? uk-state (як-є present)) (identity-relation same)
         (нехай ((en-state (тримовний-стан-належності (як-є en) seen)))
           (за-умовою
             ((тотожне? en-state (як-є present)) (identity-relation distinct)
              (тримовна-помилка (як-є missing-human-surface) (як-є en)))
             ((тотожне? en-state (як-є present)) (identity-relation same)
              (нехай ((sa-state (тримовний-стан-належності (як-є sa) seen)))
                (за-умовою
                  ((тотожне? sa-state (як-є present)) (identity-relation distinct)
                   (тримовна-помилка (як-є missing-human-surface) (як-є sa)))
                  ((тотожне? sa-state (як-є present)) (identity-relation same)
                   (як-є valid))))))))))))

(визначити тримовне-перевірити-поля
  (функція (fields seen)
    (за-умовою
      ((атом? fields) (structural-kind empty-list)
       (тримовне-вимагати-людські-проєкції seen))
      ((атом? fields) (structural-kind atom)
       (тримовна-помилка (як-є malformed-field-tail) fields))
      ((атом? fields) (structural-kind pair)
       (нехай-послідовно ((field (перше fields))
              (спеціальна-змінна (тримовний-стан-цитованого-символу field)))
         (за-умовою
           ((тотожне? спеціальна-змінна (як-є yes)) (identity-relation same)
            (нехай ((dup (тримовний-стан-належності (як-є sym) seen)))
              (за-умовою
                ((тотожне? dup (як-є present)) (identity-relation same)
                 (тримовна-помилка (як-є duplicate-surface) (як-є sym)))
                ((тотожне? dup (як-є present)) (identity-relation distinct)
                 (тримовне-перевірити-поля
                   (решта fields)
                   (сполучити (як-є sym) seen))))))
           ((тотожне? спеціальна-змінна (як-є yes)) (identity-relation distinct)
            (нехай ((valid (тримовне-перевірити-звичайне-поле field)))
              (нехай-послідовно ((language (тримовна-мова-поля field))
                     (dup (тримовний-стан-належності language seen)))
                (за-умовою
                  ((тотожне? dup (як-є present)) (identity-relation same)
                   (тримовна-помилка (як-є duplicate-surface) language))
                  ((тотожне? dup (як-є present)) (identity-relation distinct)
                   (тримовне-перевірити-поля
                     (решта fields)
                     (сполучити language seen)))))))))))))

(визначити тримовне-перевірити-рядок
  (функція (row)
    (за-умовою
      ((атом? row) (structural-kind empty-list)
       (тримовна-помилка (як-є malformed-entry) row))
      ((атом? row) (structural-kind atom)
       (тримовна-помилка (як-є malformed-entry) row))
      ((атом? row) (structural-kind pair)
       (нехай ((identity (перше row)))
         (за-умовою
           ((атом? identity) (structural-kind atom)
            (нехай ((valid (тримовне-перевірити-поля (решта row) (як-є ()))))
              identity))
           ((атом? identity) (structural-kind empty-list)
            (тримовна-помилка (як-є malformed-identity) row))
           ((атом? identity) (structural-kind pair)
            (тримовна-помилка (як-є malformed-identity) row))))))))

(визначити тримовне-перевірити-рядки
  (функція (rows seen-identities)
    (за-умовою
      ((атом? rows) (structural-kind empty-list)
       (за-умовою
         ((атом? seen-identities) (structural-kind empty-list)
          (тримовна-помилка (як-є empty-registry) (як-є ())))
         ((атом? seen-identities) (structural-kind pair)
          (як-є valid))
         ((атом? seen-identities) (structural-kind atom)
          (тримовна-помилка (як-є malformed-seen-identities) seen-identities))))
      ((атом? rows) (structural-kind atom)
       (тримовна-помилка (як-є malformed-entry-tail) rows))
      ((атом? rows) (structural-kind pair)
       (нехай-послідовно ((identity (тримовне-перевірити-рядок (перше rows)))
              (dup (тримовний-стан-належності identity seen-identities)))
         (за-умовою
           ((тотожне? dup (як-є present)) (identity-relation same)
            (тримовна-помилка (як-є duplicate-semantic-id) identity))
           ((тотожне? dup (як-є present)) (identity-relation distinct)
            (тримовне-перевірити-рядки
              (решта rows)
              (сполучити identity seen-identities)))))))))

(визначити тримовний-стан-проєкції
  (функція (fields wanted)
    (за-умовою
      ((атом? fields) (structural-kind empty-list) (як-є ()))
      ((атом? fields) (structural-kind atom) (як-є ()))
      ((атом? fields) (structural-kind pair)
       (нехай-послідовно ((field (перше fields))
              (language (тримовна-мова-поля field)))
         (за-умовою
           ((тотожне? language wanted) (identity-relation same)
            (тримовний-стан-поля field))
           ((тотожне? language wanted) (identity-relation distinct)
            (тримовний-стан-проєкції (решта fields) wanted))))))))

(визначити тримовний-стан-усіх-статусів
  (функція (fields languages wanted)
    (за-умовою
      ((атом? languages) (structural-kind empty-list) (як-є all))
      ((атом? languages) (structural-kind atom) (як-є not-all))
      ((атом? languages) (structural-kind pair)
       (нехай ((current
               (тримовний-стан-проєкції fields (перше languages))))
         (за-умовою
           ((тотожне? current wanted) (identity-relation same)
            (тримовний-стан-усіх-статусів
              fields
              (решта languages)
              wanted))
           ((тотожне? current wanted) (identity-relation distinct)
            (як-є not-all))))))))

(визначити тримовний-публічний-вид
  (функція (row)
    (нехай ((state
            (тримовний-стан-усіх-статусів
              (решта row)
              тримовні-людські-проєкції
              (як-є compatibility-only))))
      (за-умовою
        ((тотожне? state (як-є all)) (identity-relation same)
         (як-є compatibility-only))
        ((тотожне? state (як-є all)) (identity-relation distinct)
         (як-є public))))))

(визначити тримовний-стабільний-вид
  (функція (row)
    (нехай ((state
            (тримовний-стан-усіх-статусів
              (решта row)
              тримовні-людські-проєкції
              (як-є stable))))
      (за-умовою
        ((тотожне? state (як-є all)) (identity-relation same)
         (як-є all-stable))
        ((тотожне? state (як-є all)) (identity-relation distinct)
         (як-є not-all-stable))))))

(визначити тримовна-наявність-проєкції
  (функція (fields wanted)
    (нехай ((value (тримовний-стан-проєкції fields wanted)))
      (за-умовою
        ((атом? value) (structural-kind empty-list) (як-є absent))
        ((атом? value) (structural-kind atom) (як-є present))
        ((атом? value) (structural-kind pair) (як-є present))))))

(визначити тримовне-порахувати-статуси
  (функція (rows language wanted acc)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) acc)
      ((атом? rows) (structural-kind atom) acc)
      ((атом? rows) (structural-kind pair)
       (нехай ((status
               (тримовний-стан-проєкції (решта (перше rows)) language)))
         (за-умовою
           ((тотожне? status wanted) (identity-relation same)
            (тримовне-порахувати-статуси (решта rows) language wanted (додати acc 1)))
           ((тотожне? status wanted) (identity-relation distinct)
            (тримовне-порахувати-статуси (решта rows) language wanted acc))))))))

(визначити тримовне-порахувати-публічні
  (функція (rows acc)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) acc)
      ((атом? rows) (structural-kind atom) acc)
      ((атом? rows) (structural-kind pair)
       (нехай ((kind (тримовний-публічний-вид (перше rows))))
         (за-умовою
           ((тотожне? kind (як-є public)) (identity-relation same)
            (тримовне-порахувати-публічні (решта rows) (додати acc 1)))
           ((тотожне? kind (як-є public)) (identity-relation distinct)
            (тримовне-порахувати-публічні (решта rows) acc))))))))

(визначити тримовне-порахувати-символьні
  (функція (rows acc)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) acc)
      ((атом? rows) (structural-kind atom) acc)
      ((атом? rows) (structural-kind pair)
       (нехай ((state
               (тримовна-наявність-проєкції
                 (решта (перше rows))
                 (як-є sym))))
         (за-умовою
           ((тотожне? state (як-є present)) (identity-relation same)
            (тримовне-порахувати-символьні (решта rows) (додати acc 1)))
           ((тотожне? state (як-є present)) (identity-relation distinct)
            (тримовне-порахувати-символьні (решта rows) acc))))))))

(визначити тримовне-порахувати-спільні-стабільні
  (функція (rows acc)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) acc)
      ((атом? rows) (structural-kind atom) acc)
      ((атом? rows) (structural-kind pair)
       (нехай ((public (тримовний-публічний-вид (перше rows))))
         (за-умовою
           ((тотожне? public (як-є public)) (identity-relation distinct)
            (тримовне-порахувати-спільні-стабільні (решта rows) acc))
           ((тотожне? public (як-є public)) (identity-relation same)
            (нехай ((stable (тримовний-стабільний-вид (перше rows))))
              (за-умовою
                ((тотожне? stable (як-є all-stable)) (identity-relation same)
                 (тримовне-порахувати-спільні-стабільні (решта rows) (додати acc 1)))
                ((тотожне? stable (як-є all-stable)) (identity-relation distinct)
                 (тримовне-порахувати-спільні-стабільні (решта rows) acc)))))))))))

(визначити тримовний-стан-випуску
  (функція (rows)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) (як-є confirmed))
      ((атом? rows) (structural-kind atom) (як-є open))
      ((атом? rows) (structural-kind pair)
       (нехай ((public (тримовний-публічний-вид (перше rows))))
         (за-умовою
           ((тотожне? public (як-є public)) (identity-relation distinct)
            (тримовний-стан-випуску (решта rows)))
           ((тотожне? public (як-є public)) (identity-relation same)
            (нехай ((stable (тримовний-стабільний-вид (перше rows))))
              (за-умовою
                ((тотожне? stable (як-є all-stable)) (identity-relation same)
                 (тримовний-стан-випуску (решта rows)))
                ((тотожне? stable (як-є all-stable)) (identity-relation distinct)
                 (як-є open)))))))))))

(визначити тримовний-режим
  (функція (argv)
    (за-умовою
      ((атом? argv) (structural-kind empty-list) (як-є report))
      ((атом? argv) (structural-kind atom)
       (тримовна-помилка (як-є malformed-argv) argv))
      ((атом? argv) (structural-kind pair)
       (нехай ((rest (решта argv)))
         (за-умовою
           ((атом? rest) (structural-kind empty-list)
            (за-умовою
              ((однакові? (перше argv) "--require-complete")
               (structural-relation same)
               (як-є require-complete))
              ((однакові? (перше argv) "--require-complete")
               (structural-relation distinct)
               (тримовна-помилка (як-є unknown-argument) (перше argv)))))
           ((атом? rest) (structural-kind atom)
            (тримовна-помилка (як-є malformed-argv) argv))
           ((атом? rest) (structural-kind pair)
            (тримовна-помилка (як-є too-many-arguments) argv))))))))

(визначити тримовна-форма-реєстру
  (перше
    (читати-всі
      (читати-файл "lib/surface/semantic-registry.lisp"))))

(визначити тримовні-рядки
  (за-умовою
    ((атом? тримовна-форма-реєстру) (structural-kind empty-list)
     (тримовна-помилка (як-є malformed-registry-root) тримовна-форма-реєстру))
    ((атом? тримовна-форма-реєстру) (structural-kind atom)
     (тримовна-помилка (як-є malformed-registry-root) тримовна-форма-реєстру))
    ((атом? тримовна-форма-реєстру) (structural-kind pair)
     (за-умовою
       ((тотожне? (перше тримовна-форма-реєстру) (як-є sr/1))
        (identity-relation same)
        (решта тримовна-форма-реєстру))
       ((тотожне? (перше тримовна-форма-реєстру) (як-є sr/1))
        (identity-relation distinct)
        (тримовна-помилка
          (як-є malformed-registry-root)
          (перше тримовна-форма-реєстру)))))))

(визначити тримовний-підсумок-перевірки
  (тримовне-перевірити-рядки тримовні-рядки (як-є ())))

(визначити тримовна-кількість-публічних
  (тримовне-порахувати-публічні тримовні-рядки 0))

(визначити тримовна-кількість-символьних
  (тримовне-порахувати-символьні тримовні-рядки 0))

(визначити тримовна-кількість-спільних-стабільних
  (тримовне-порахувати-спільні-стабільні тримовні-рядки 0))

(визначити тримовний-випуск
  (тримовний-стан-випуску тримовні-рядки))

(визначити тримовний-звіт
  (список
    (як-є trilingual-surface-report)
    (список (як-є entries) (довжина тримовні-рядки))
    (список (як-є public-semantic-identities) тримовна-кількість-публічних)
    (список (як-є shared-symbolic-identities) тримовна-кількість-символьних)
    (список
      (як-є uk)
      (список (як-є stable)
            (тримовне-порахувати-статуси тримовні-рядки (як-є uk) (як-є stable) 0))
      (список (як-є candidate)
            (тримовне-порахувати-статуси тримовні-рядки (як-є uk) (як-є candidate) 0))
      (список (як-є missing)
            (тримовне-порахувати-статуси тримовні-рядки (як-є uk) (як-є missing) 0))
      (список (як-є compatibility-only)
            (тримовне-порахувати-статуси
              тримовні-рядки
              (як-є uk)
              (як-є compatibility-only)
              0)))
    (список
      (як-є en)
      (список (як-є stable)
            (тримовне-порахувати-статуси тримовні-рядки (як-є en) (як-є stable) 0))
      (список (як-є candidate)
            (тримовне-порахувати-статуси тримовні-рядки (як-є en) (як-є candidate) 0))
      (список (як-є missing)
            (тримовне-порахувати-статуси тримовні-рядки (як-є en) (як-є missing) 0))
      (список (як-є compatibility-only)
            (тримовне-порахувати-статуси
              тримовні-рядки
              (як-є en)
              (як-є compatibility-only)
              0)))
    (список
      (як-є sa)
      (список (як-є stable)
            (тримовне-порахувати-статуси тримовні-рядки (як-є sa) (як-є stable) 0))
      (список (як-є candidate)
            (тримовне-порахувати-статуси тримовні-рядки (як-є sa) (як-є candidate) 0))
      (список (як-є missing)
            (тримовне-порахувати-статуси тримовні-рядки (як-є sa) (як-є missing) 0))
      (список (як-є compatibility-only)
            (тримовне-порахувати-статуси
              тримовні-рядки
              (як-є sa)
              (як-є compatibility-only)
              0)))
    (список
      (як-є trilingual-stable-identities)
      тримовна-кількість-спільних-стабільних
      тримовна-кількість-публічних)
    (список (як-є release-parity) тримовний-випуск)))

(визначити тримовний-надрукований-звіт
  (друкувати тримовний-звіт))

(визначити тримовний-вибраний-режим
  (тримовний-режим *argv*))

(за-умовою
  ((тотожне? тримовний-вибраний-режим (як-є require-complete))
   (identity-relation same)
   (за-умовою
     ((тотожне? тримовний-випуск (як-є confirmed))
      (identity-relation same)
      тримовний-звіт)
     ((тотожне? тримовний-випуск (як-є confirmed))
      (identity-relation distinct)
      (тримовна-помилка (як-є release-parity-open) тримовний-звіт))))
  ((тотожне? тримовний-вибраний-режим (як-є require-complete))
   (identity-relation distinct)
   тримовний-звіт))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити читати-всі read-all)
(визначити спеціальна-змінна special)
