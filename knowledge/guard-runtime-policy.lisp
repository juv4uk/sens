; Політика виконання першого спільного зрізу Rust та гвардії СЕНС.
; Rust передає лише нормалізовані факти, а класифікація належить
; мові СЕНС і може змінюватися без перекомпіляції виконавця.

(визначити гвардія-оцінити
  (функція (вид суб'єкт докази)
    (за-умовою
      ((тотожне? докази (як-є missing))
       (захист-невідоме суб'єкт (як-є runtime-evidence) (як-є ask-agent)))
      ((тотожне? вид (як-є read))
       (створити-захист-висновок
         (як-є allow) (як-є confirmed) суб'єкт вид (як-є read-only)
         (як-є ()) (як-є no-state-change) (як-є continue) (список докази)))
      ((тотожне? вид (як-є write))
       (створити-захист-висновок
         (як-є warn) (як-є partial) суб'єкт вид (як-є review-write-scope)
         (як-є mutation-requested) (як-є state-may-change)
         (як-є verify-authority-and-target) (список докази)))
      ((тотожне? вид (як-є destructive))
       (створити-захист-висновок
         (як-є reject) (як-є confirmed) суб'єкт вид
         (як-є explicit-owner-authority-required)
         (як-є authority-not-present) (як-є irreversible-impact)
         (як-є ask-owner) (список докази)))
      (так (захист-невідоме суб'єкт (як-є unclassified-event-kind)
           (як-є choose-unknown-route))))))

; Сумісна історична назва для зовнішніх споживачів.
(визначити guard-evaluate гвардія-оцінити)
