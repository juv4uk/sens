; Runtime policy for the first Rust + WSM Guard vertical slice.
; Runtime-політика першого вертикального зрізу Rust + WSM Guard.
;
; This is deliberately small. It demonstrates that Rust supplies normalized
; facts while WSM owns classification and can change it without recompilation.
; Політика навмисно мала: Rust подає нормалізовані факти, а WSM визначає
; класифікацію й може змінювати її без перекомпіляції.

(визначити guard-evaluate
  (функція (вид суб'єкт докази)
    (за-умовою
      ((тотожне? докази (як-є missing))
       (guard-unknown суб'єкт (як-є runtime-evidence) (як-є ask-agent)))
      ((тотожне? вид (як-є read))
       (make-guard-finding
         (як-є allow) (як-є confirmed) суб'єкт вид (як-є read-only)
         (як-є ()) (як-є no-state-change) (як-є continue) (список докази)))
      ((тотожне? вид (як-є write))
       (make-guard-finding
         (як-є warn) (як-є partial) суб'єкт вид (як-є review-write-scope)
         (як-є mutation-requested) (як-є state-may-change)
         (як-є verify-authority-and-target) (список докази)))
      ((тотожне? вид (як-є destructive))
       (make-guard-finding
         (як-є reject) (як-є confirmed) суб'єкт вид
         (як-є explicit-owner-authority-required)
         (як-є authority-not-present) (як-є irreversible-impact)
         (як-є ask-owner) (список докази)))
      (1 (guard-unknown суб'єкт (як-є unclassified-event-kind)
           (як-є choose-unknown-route))))))
