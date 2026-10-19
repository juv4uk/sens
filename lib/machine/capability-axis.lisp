; Вісь можливостей машини: точна доменна адреса, а не історичний байт.
; Семантику задає ратифікований закон SENS. Таблиця нижче лише описує
; доступні обмежені машинні реалізації та їхні підтверджені свідчення.
;
; Ключ таблиці: (ширина-домену упаковані-біти). Обидва поля — звичайні
; десяткові дані механізму, отримані з точного домену поза цим файлом.
; Рівність другого поля не дає права відкидати перше.
; Жодних SID8/Sens8-псевдонімів, повторного визначення семантики
; або прихованого перенесення значень між доменами.
;
; Назви машинних властивостей, платформ і свідчень є цитованими даними,
; а не виконуваними головами SENS. Відкритий зовнішній API цього файлу
; використовується чинними машинними споживачами.
;
; Каталоги перевіряються на збереження точних наявних записів.

(визначити machine-capability-axis-v3
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

(визначити machine-capability-target-witnesses-v2
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

(визначити machine-target-witness-status-v1
  (як-є
    ((x86-64 witnessed)
     (arm64 absent)
     (risc-v absent)
     (fpga absent))))

; Знайти запис з одночасним збігом ширини та упакованого значення.
; Невідомий ключ повертає порожній список без підміни іншого домену.
(визначити можливість-знайти-рядок-домену
  (функція (ширина-домену біти-домену рядки-доменів)
    (за-умовою
      ((тотожне? рядки-доменів (як-є ()))
       (як-є ()))
      ((тотожне? ширина-домену (перше (перше рядки-доменів)))
       (за-умовою
         ((тотожне? біти-домену (друге (перше рядки-доменів)))
          (перше рядки-доменів))
         (так
          (можливість-знайти-рядок-домену
            ширина-домену біти-домену (решта рядки-доменів)))))
      (так
       (можливість-знайти-рядок-домену
         ширина-домену біти-домену (решта рядки-доменів))))))

; Обчислюємо пошук лише один раз і повертаємо саме поле можливостей.
(визначити machine-capabilities-for-domain
  (функція (ширина-домену біти-домену)
    ((функція (знайдений-рядок)
       (за-умовою
         ((тотожне? знайдений-рядок (як-є ())) (як-є ()))
         (так
          (перше (решта (решта знайдений-рядок))))))
     (можливість-знайти-рядок-домену
       ширина-домену біти-домену machine-capability-axis-v3))))

; Для цілей використовується окрема таблиця свідчень. Її статус
; не є доказом повноти машинного кодування або семантичним предикатом.
(визначити можливість-знайти-рядок
  (функція (ключ-можливості рядки-можливостей)
    (за-умовою
      ((тотожне? рядки-можливостей (як-є ())) (як-є ()))
      ((тотожне? ключ-можливості (перше (перше рядки-можливостей)))
       (перше рядки-можливостей))
      (так
       (можливість-знайти-рядок
         ключ-можливості (решта рядки-можливостей))))))

; Невідома ціль має явний статус absent, не «довільне true/false».
(визначити machine-target-witness-status
  (функція (цільова-платформа)
    ((функція (знайдений-рядок)
       (за-умовою
         ((тотожне? знайдений-рядок (як-є ())) (як-є absent))
         (так (друге знайдений-рядок))))
     (можливість-знайти-рядок
       цільова-платформа machine-target-witness-status-v1))))
