; Машинна вісь точних доменів SENS — лише опис допущених реалізацій.
; Перший компонент ключа є шириною домену, другий — його пакованими бітами.
; Обидва передаються як десяткові дані; збіг другого компонента не означає
; тотожності між доменами. Семантичний закон живе тільки в ратифікованій
; драбині, а свідки ISA не перетворюються на функції SENS.
;
; Каталоги нижче збережено без змін: машина не визначає семантику мови.

(визначити вісь-спроможностей-машини-v3
  (як-є
    ((5 8
       ((integer-zero-test bounded-nonnegative-u64 internal-bit-d1-boundary)))
     (5 10
       ((integer-add bounded-u32-inputs u64-result)))
     (5 11
       ((integer-subtract bounded-u64 no-underflow)))
     (5 22
       ((integer-multiply bounded-u32-inputs u64-result)))
     (5 23
       ((integer-quotient bounded-positive-i64 equal-operands-only)))
     (5 26
       ((integer-order-less bounded-nonnegative-i63 internal-bit-d1-boundary)))
     (5 27
       ((integer-order-greater bounded-nonnegative-i63 internal-bit-d1-boundary)))
     (6 14
       ((integer-increment bounded-u64 no-overflow)))
     (6 15
       ((integer-decrement bounded-u64 no-underflow)))
     (3 5
       ((identity-compare bounded-u64)))
     (3 6
       ((conditional-branch bounded-u64)))
     (3 7
       ((pair-field-store head bounded-u64)
        (pair-field-store tail bounded-u64)))
     (3 4
       ((pair-field-load head bounded-u64)))
     (3 3
       ((pair-field-load tail bounded-u64))))))

(визначити свідки-цілей-спроможності-машини-v2
  (як-є
    ((x86-64
       (integer-zero-test bounded-nonnegative-u64 internal-bit-d1-boundary
         (admitted-form cmp-r64-r64)
         (admitted-form sete-r8)
         (admitted-form movzx-r64-r8)
         (lowering x86-lower-zerop-u64-forms))
       (integer-add bounded-u32-inputs u64-result
         (admitted-form add-r64-r64)
         (lowering x86-lower-add-u64-forms))
       (integer-subtract bounded-u64 no-underflow
         (admitted-form sub-r64-r64)
         (lowering x86-lower-difference-u64-forms))
       (integer-multiply bounded-u32-inputs u64-result
         (admitted-form imul-r64-r64)
         (lowering x86-lower-times-u64-forms))
       (integer-quotient bounded-positive-i64 equal-operands-only
         (admitted-form cqo)
         (admitted-form idiv-r64)
         (lowering x86-lower-quotient-i64-equal-forms))
       (integer-order-less bounded-nonnegative-i63 internal-bit-d1-boundary
         (admitted-form cmp-r64-r64)
         (admitted-form setl-r8)
         (admitted-form movzx-r64-r8)
         (lowering x86-lower-order-i64-forms))
       (integer-order-greater bounded-nonnegative-i63 internal-bit-d1-boundary
         (admitted-form cmp-r64-r64)
         (admitted-form setg-r8)
         (admitted-form movzx-r64-r8)
         (lowering x86-lower-order-i64-forms))
       (integer-increment bounded-u64 no-overflow
         (admitted-form add-r64-r64)
         (lowering x86-lower-add-u64-forms))
       (integer-decrement bounded-u64 no-underflow
         (admitted-form sub-r64-r64)
         (lowering x86-lower-difference-u64-forms))
       (identity-compare bounded-u64
         (admitted-form cmp-r64-r64)
         (lowering x86-lower-eq-cond-u64-forms))
       (conditional-branch bounded-u64
         (admitted-form jnz-rel8)
         (lowering x86-lower-eq-cond-u64-forms))
       (pair-field-store head bounded-u64
         (admitted-form mov-mem-disp8-r64)
         (lowering x86-lower-bounded-pair-store-u64-forms))
       (pair-field-store tail bounded-u64
         (admitted-form mov-mem-disp8-r64)
         (lowering x86-lower-bounded-pair-store-u64-forms))
       (pair-field-load head bounded-u64
         (admitted-form mov-r64-mem-disp8)
         (lowering x86-lower-cons-car-u64-forms))
       (pair-field-load tail bounded-u64
         (admitted-form mov-r64-mem-disp8)
         (lowering x86-lower-cons-cdr-u64-forms))))))

(визначити статуси-свідків-цілей-машини-v1
  (як-є
    ((x86-64 witnessed)
     (arm64 absent)
     (risc-v absent)
     (fpga absent))))

; Пошук точного ключа (ширина, біти) через D3 CAR/CDR і EQ на атомах.
; D3 EQ не застосовується до цілих списків: порожнечу перевіряє ATOM.
; Для кожного непорожнього рядка перевіряємо ОБИДВІ координати.
(визначити можливість-знайти-рядок-домену
  (функція (ширина-домену біти-домену рядки-доменів)
    (за-умовою
      ((атом? рядки-доменів) (як-є ()))
      (так
        ((функція (поточний-рядок)
          (за-умовою
            ((тотожне? ширина-домену (перше поточний-рядок))
              (за-умовою
                ((тотожне? біти-домену (друге поточний-рядок))
                  поточний-рядок)
                (так
                  (можливість-знайти-рядок-домену
                    ширина-домену біти-домену (решта рядки-доменів)))))
            (так
              (можливість-знайти-рядок-домену
                ширина-домену біти-домену (решта рядки-доменів)))))
         (перше рядки-доменів))))))

; Витягуємо третє поле лише після того, як знайдено непорожній рядок.
; Невідома адреса повертає порожній список і не успадковує чужий домен.
(визначити спроможності-для-домену
  (функція (ширина-домену біти-домену)
    ((функція (знайдений-рядок)
       (за-умовою
         ((атом? знайдений-рядок) (як-є ()))
         (так (перше (решта (решта знайдений-рядок))))))
     (можливість-знайти-рядок-домену
       ширина-домену біти-домену вісь-спроможностей-машини-v3))))

; Аналогічний пошук за атомарною назвою цільової платформи.
; Доменні ключі сюди не потрапляють, і цей каталог нічого не виконує.
(визначити можливість-знайти-рядок
  (функція (ключ-можливості рядки-можливостей)
    (за-умовою
      ((атом? рядки-можливостей) (як-є ()))
      (так
        ((функція (поточний-рядок)
           (за-умовою
             ((тотожне? ключ-можливості (перше поточний-рядок))
              поточний-рядок)
             (так
               (можливість-знайти-рядок
                 ключ-можливості (решта рядки-можливостей)))))
         (перше рядки-можливостей))))))

; Лише явний свідок x86-64 має статус witnessed.
; Для невідомої платформи повертаємо атом даних absent, не D1-істину.
(визначити статус-свідка-цілі-машини
  (функція (цільова-платформа)
    ((функція (знайдений-рядок)
       (за-умовою
         ((атом? знайдений-рядок) (як-є absent))
         (так (друге знайдений-рядок))))
     (можливість-знайти-рядок
       цільова-платформа статуси-свідків-цілей-машини-v1))))
