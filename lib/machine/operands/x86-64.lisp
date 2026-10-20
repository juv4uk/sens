; Типізовані операнди машинної архітектури x86-64, описані мовою СЕНС.
; Цей модуль визначає форму операнда, але не допуск інструкцій і не кодування.
; Відповідність регістрів повторно використовує наявний машинний кодер.
; Другої таблиці загальних регістрів тут не створюємо.
; Коректна форма операнда не доводить, що інструкцію дозволено виконати.

(визначити x86-machine-operand-rejection
  (функція (очікуване фактичне)
    (список (як-є rejected) (як-є machine-operand) очікуване фактичне)))

(визначити x86-machine-rejected?
  (функція (значення)
    (за-умовою
      ((атом? значення) (тотожне? (як-є ()) (як-є rejected)))
      ((атом? ()) (тотожне? (перше значення) (як-є rejected))))))

(визначити x86-gpr8-name?
  (функція (назва)
    (за-умовою
      ((символ? назва)
       (значення-у-списку?
         назва
         (як-є
           (al cl dl bl spl bpl sil dil
               r8b r9b r10b r11b r12b r13b r14b r15b))))
      )))

(визначити x86-gpr64-name?
  (функція (назва)
    (за-умовою
      ((символ? назва)
       (та
         (хибне? (тотожне? (x86-reg-code назва) (як-є ())))
         (хибне? (x86-gpr8-name? назва))))
      )))

(визначити x86-gpr8?
  (функція (operand)
    (за-умовою
      
      ((атом? operand)  (як-є ()))
      ((тотожне? (перше operand) (як-є gpr8))
       (за-умовою
         
         ((атом? (решта operand))  (як-є ()))
         ((тотожне? (решта (решта operand)) (як-є ()))
          (x86-gpr8-name? (друге operand)))
         ))
      )))

(визначити x86-gpr8
  (функція (name)
    (за-умовою
      ((x86-gpr8-name? name) (список (як-є gpr8) name))
      ((атом? ()) (x86-machine-operand-rejection (як-є gpr8) name)))))

(визначити x86-as-gpr8
  (функція (operand)
    (за-умовою
      ((x86-machine-rejected? operand) operand)
      ((x86-gpr8? operand) operand)
      ((атом? ()) (x86-gpr8 operand)))))

(визначити x86-gpr8-value
  (функція (operand)
    (друге operand)))

(визначити x86-gpr64?
  (функція (operand)
    (за-умовою
      
      ((атом? operand)  (як-є ()))
      ((тотожне? (перше operand) (як-є gpr64))
       (за-умовою
         
         ((атом? (решта operand))  (як-є ()))
         ((тотожне? (решта (решта operand)) (як-є ()))
          (x86-gpr64-name? (друге operand)))
         ))
      )))

(визначити x86-gpr64
  (функція (name)
    (за-умовою
      ((x86-gpr64-name? name) (список (як-є gpr64) name))
      ((атом? ()) (x86-machine-operand-rejection (як-є gpr64) name)))))

(визначити x86-as-gpr64
  (функція (operand)
    (за-умовою
      ((x86-machine-rejected? operand) operand)
      ((x86-gpr64? operand) operand)
      ((атом? ()) (x86-gpr64 operand)))))

(визначити x86-gpr64-value
  (функція (operand)
    (друге operand)))

; Операнд загального регістра на 32 біти є видом того самого фізичного
; регістра з канонічною 64-бітною назвою. Кодування регістрів уже належить
; машинному кодеру, а ширину визначає форма інструкції.
; Цей вид не створює другої таблиці адрес машинних регістрів.
(визначити x86-gpr32-name?
  (функція (назва)
    (x86-gpr64-name? назва)))

(визначити x86-gpr32?
  (функція (operand)
    (за-умовою
      
      ((атом? operand)  (як-є ()))
      ((тотожне? (перше operand) (як-є gpr32))
       (за-умовою
         
         ((атом? (решта operand))  (як-є ()))
         ((тотожне? (решта (решта operand)) (як-є ()))
          (x86-gpr32-name? (друге operand)))
         ))
      )))

(визначити x86-gpr32
  (функція (name)
    (за-умовою
      ((x86-gpr32-name? name) (список (як-є gpr32) name))
      ((атом? ()) (x86-machine-operand-rejection (як-є gpr32) name)))))

(визначити x86-as-gpr32
  (функція (operand)
    (за-умовою
      ((x86-machine-rejected? operand) operand)
      ((x86-gpr32? operand) operand)
      ((атом? ()) (x86-gpr32 operand)))))

(визначити x86-gpr32-value
  (функція (operand)
    (друге operand)))

; Векторні регістри становлять окремий клас, хоча кодування використовує
; спільний простір чотирибітних полів. Допустимість визначає наявний
; кодер векторних регістрів, а не нова таблиця в цьому модулі.
(визначити x86-xmm-name?
  (функція (name)
    (за-умовою
      ((символ? name)
       (за-умовою
         ((тотожне? (x86-xmm-reg-code name) (як-є ()))
          (010 (001 (000))))
         ((тотожне? (x86-xmm-reg-code name) (x86-xmm-reg-code name))
          (атом? ()))
         ((010 ()) (010 (001 (000))))))
      ((010 ()) (010 (001 (000)))))))
(визначити x86-xmm?
  (функція (operand)
    (за-умовою
      
      ((атом? operand)  (як-є ()))
      ((тотожне? (перше operand) (як-є xmm))
       (за-умовою
         
         ((атом? (решта operand))  (як-є ()))
         ((тотожне? (решта (решта operand)) (як-є ()))
          (x86-xmm-name? (друге operand)))
         ))
      )))

(визначити x86-xmm
  (функція (name)
    (за-умовою
      ((x86-xmm-name? name) (список (як-є xmm) name))
      ((атом? ()) (x86-machine-operand-rejection (як-є xmm) name)))))

(визначити x86-as-xmm
  (функція (operand)
    (за-умовою
      ((x86-machine-rejected? operand) operand)
      ((x86-xmm? operand) operand)
      ((атом? ()) (x86-xmm operand)))))

(визначити x86-xmm-value
  (функція (operand)
    (друге operand)))

; Розпізнавання точного цілого належить мові, не новому примітиву господаря.
; Фізичне представлення чисел не змінює математичної тотожності.
; Після скорочення точне раціональне число є цілим тоді й тільки тоді,
; коли його знаменник дорівнює одиниці.
(визначити x86-wire-denominator-one?
  (функція (text)
    (за-умовою
      ((рядок-порожній? text) (як-є ()))
      ((тотожне? (рядок-перший text) "/")
       (нехай ((rest (рядок-решта text)))
         (за-умовою
           ((рядок-порожній? rest) (як-є ()))
           ((тотожне? (рядок-перший rest) "1")
            (за-умовою
              ((рядок-порожній? (рядок-решта rest)) t)
              ((тотожне? 0 0) (як-є ()))))
           ((тотожне? 0 0) (як-є ())))))
      ((тотожне? 0 0) (x86-wire-denominator-one? (рядок-решта text))))))

(визначити x86-exact-integer?
  (функція (value)
    (нехай ((wire (значення-у-текст value)))
      (за-умовою
        ((рядок-префікс? "#q2:" wire) (x86-wire-denominator-one? wire))
        ((тотожне? 0 0) (як-є ()))))))

(визначити x86-operand-in-inclusive-range?
  (функція (value lower upper)
    ; Числові результати порівняння не можна неявно вважати логічною хибою
    ; за їхнім нульовим значенням: це допускало переповнення операндів.
    ; Допустимість вимагає явного очікуваного домену результату
    ; та структурного предиката для умовного вибору.
    (за-умовою
      ((не-менше? value lower) 
        (за-умовою
          ((не-більше? value upper)  t)
          ))
      )))

(визначити x86-u64-imm?
  (функція (operand)
    (за-умовою
      
      ((атом? operand)  (як-є ()))
      ((тотожне? (перше operand) (як-є u64-imm))
       (за-умовою
         
         ((атом? (решта operand))  (як-є ()))
         ((тотожне? (решта (решта operand)) (як-є ()))
          (нехай ((value (друге operand)))
            (за-умовою
              ((x86-exact-integer? value)
               (x86-operand-in-inclusive-range? value 0 18446744073709551615))
              )))
         ))
      )))

(визначити x86-u64-imm
  (функція (value)
    (за-умовою
      ((x86-exact-integer? value)
       (за-умовою
         ((x86-operand-in-inclusive-range? value 0 18446744073709551615)
          (список (як-є u64-imm) value))
         ((атом? ()) (x86-machine-operand-rejection (як-є u64-imm) value))))
      ((атом? ()) (x86-machine-operand-rejection (як-є u64-imm) value)))))

(визначити типізувати-беззнаковий-машинний-операнд
  (функція (operand)
    (за-умовою
      ((x86-machine-rejected? operand) operand)
      ((x86-u64-imm? operand) operand)
      ((атом? ()) (x86-u64-imm operand)))))

(визначити x86-as-u64-imm типізувати-беззнаковий-машинний-операнд)

(визначити значення-беззнакового-машинного-операнда
  (функція (operand)
    (друге operand)))

(визначити x86-u64-imm-value значення-беззнакового-машинного-операнда)

(визначити x86-disp8?
  (функція (operand)
    (за-умовою
      
      ((атом? operand)  (як-є ()))
      ((тотожне? (перше operand) (як-є disp8))
       (за-умовою
         
         ((атом? (решта operand))  (як-є ()))
         ((тотожне? (решта (решта operand)) (як-є ()))
          (нехай ((value (друге operand)))
            (за-умовою
              ((x86-exact-integer? value)
               (x86-operand-in-inclusive-range? value -128 127))
              )))
         ))
      )))

(визначити x86-disp8
  (функція (value)
    (за-умовою
      ((x86-exact-integer? value)
       (за-умовою
         ((x86-operand-in-inclusive-range? value -128 127)
          (список (як-є disp8) value))
         ((атом? ()) (x86-machine-operand-rejection (як-є disp8) value))))
      ((атом? ()) (x86-machine-operand-rejection (як-є disp8) value)))))

(визначити x86-as-disp8
  (функція (operand)
    (за-умовою
      ((x86-machine-rejected? operand) operand)
      ((x86-disp8? operand) operand)
      ((атом? ()) (x86-disp8 operand)))))

(визначити x86-disp8-value
  (функція (operand)
    (друге operand)))

(визначити x86-mem64-disp8?
  (функція (operand)
    (за-умовою
      
      ((атом? operand)  (як-є ()))
      ((тотожне? (перше operand) (як-є mem64-disp8))
       (за-умовою
         
         ((атом? ()) (як-є ()))
         
         ((атом? (решта (решта operand)))  (як-є ()))
         ((тотожне? (решта (решта (решта operand))) (як-є ()))
          (та (x86-gpr64? (друге operand))
               (x86-disp8? (третє operand))))
         ))
      )))

(визначити x86-mem64-disp8
  (функція (base displacement)
    (нехай ((typed-base (x86-as-gpr64 base)))
      (за-умовою
        ((x86-machine-rejected? typed-base) typed-base)
        ((атом? ())
         (нехай ((typed-displacement (x86-as-disp8 displacement)))
           (за-умовою
             ((x86-machine-rejected? typed-displacement) typed-displacement)
             ((атом? ())
              (список (як-є mem64-disp8)
                    typed-base
                    typed-displacement)))))))))

(визначити x86-as-mem64-disp8
  (функція (operand)
    (за-умовою
      ((x86-machine-rejected? operand) operand)
      ((x86-mem64-disp8? operand) operand)
      ((атом? ()) (x86-machine-operand-rejection (як-є mem64-disp8) operand)))))

(визначити x86-mem64-disp8-base
  (функція (operand)
    (x86-gpr64-value (друге operand))))

(визначити x86-mem64-disp8-displacement
  (функція (operand)
    (x86-disp8-value (третє operand))))
