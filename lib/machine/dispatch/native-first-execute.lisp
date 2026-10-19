; #506 — Lisp-owned native-first execution bridge.
;
; #505 owns classification only. This file is the mechanical next step:
;   expression -> native-first-plan
;      native-plan        -> closed admission -> Lisp encoder -> raw CPU call
;      evaluator-fallback -> ordinary Lisp eval
;
; Language meaning remains outside this bridge. A plan that has already chosen
; the native route MUST NOT silently retry through the evaluator if admission
; or native mechanism rejects it; doing so would hide machine bugs.
;
; The host's existing `load` boundary uses the bounded mixed exact-domain reader.
; Current D3/D4 heads are exact domain identities. D4:1110 LIST is deliberately NOT used here because
; residency does not grant callability; records are built from exact D3 CONS.
; The remaining EVAL/READ-ALL seams stay compatibility mechanisms until their
; own current-domain owners migrate them.
;
; Required layers are loaded by the caller:
;   lib/machine/encoding/x86-64.lisp
;   lib/machine/operands/x86-64.lisp
;   lib/machine/admission/x86-64.lisp
;   lib/machine/dispatch/native-first.lisp

(визначити native-first-list-2
  (функція (перший-елемент другий-елемент)
    (сполучити перший-елемент (сполучити другий-елемент (як-є ())))))

(визначити нативний-список-чотирьох
  (функція (перший-елемент другий-елемент третій-елемент четвертий-елемент)
    (сполучити перший-елемент (сполучити другий-елемент (сполучити третій-елемент (сполучити четвертий-елемент (як-є ())))))))

(визначити native-first-execution-completed
  (функція (маршрут-виконання значення-відповіді)
    (нативний-список-чотирьох
      (як-є execution-route)
      маршрут-виконання
      (як-є (status completed))
      (native-first-list-2 (як-є value) значення-відповіді))))

(визначити native-first-execution-rejected
  (функція (маршрут-виконання подробиці-відмови)
    (нативний-список-чотирьох
      (як-є execution-route)
      маршрут-виконання
      (як-є (status rejected))
      (native-first-list-2 (як-є detail) подробиці-відмови))))

(визначити native-first-proper-list-length-2?
  (функція (значення-відповіді)
    (за-умовою
      ((атом? значення-відповіді)
       ні)
      ((атом? (решта значення-відповіді))
       ні)
      ((порожній? (решта (решта значення-відповіді)))
       так)
      (так
       ні))))

(визначити нативний-список-трьох-елементів?
  (функція (значення-відповіді)
    (за-умовою
      ((атом? значення-відповіді)
       ні)
      ((атом? (решта значення-відповіді))
       ні)
      ((атом? (решта (решта значення-відповіді)))
       ні)
      ((порожній? (решта (решта (решта значення-відповіді))))
       так)
      (так
       ні))))

(визначити native-first-plan-tag-state
  (функція (план-виконання мітка-плану)
    (за-умовою
      ((атом? план-виконання)
       (як-є distinct))
      ; D3 EQ порівнює атоми; складена голова — некоректний тег плану.
      ((атом? (перше план-виконання))
       (за-умовою
         ((тотожне? (перше план-виконання) мітка-плану)
          (як-є same))
         (так
          (як-є distinct))))
      (так
       (як-є distinct)))))

(визначити нативне-виконання-результат-плану
  (функція (план-виконання результат-виконання)
    (за-умовою
      ((атом? результат-виконання)
       (native-first-execution-completed (як-є native) результат-виконання))
      ; Некоректний складений тег не можна подавати у D3 EQ.
      ; Це помилка native-результату, а не дозвіл на evaluator-fallback.
      ((атом? (перше результат-виконання))
       (за-умовою
         ((тотожне? (перше результат-виконання) (як-є rejected))
          (native-first-execution-rejected (як-є native) результат-виконання))
         (так
          (native-first-execution-completed (як-є native) результат-виконання))))
      (так
       (native-first-execution-rejected
         (як-є native)
         (native-first-list-2 (як-є malformed-native-result) результат-виконання))))))

(визначити нативне-виконання-плану
  (функція (план-виконання)
    (нативне-виконання-результат-плану
      план-виконання
      (x86-call-admitted-u64
        (перше (решта план-виконання))
        (перше (решта (решта план-виконання)))))))

(визначити native-first-execute-plan
  (функція (план-виконання)
    (за-умовою
      ((тотожне? (native-first-plan-tag-state план-виконання (як-є native-plan)) (як-є same))
       (за-умовою
         ((нативний-список-трьох-елементів? план-виконання)
          (нативне-виконання-плану план-виконання))
         (так
          (native-first-execution-rejected
            (як-є native)
            (native-first-list-2 (як-є malformed-native-plan) план-виконання)))))
      ((тотожне? (native-first-plan-tag-state план-виконання (як-є native-plan)) (як-є distinct))
       (за-умовою
         ((тотожне? (native-first-plan-tag-state план-виконання (як-є evaluator-fallback)) (як-є same))
          (за-умовою
            ((native-first-proper-list-length-2? план-виконання)
             (native-first-execution-completed
               (як-є evaluator)
               (обчислити (перше (решта план-виконання)))))
            (так
             (native-first-execution-rejected
               (як-є invalid-plan)
               (native-first-list-2
                 (як-є malformed-evaluator-fallback-plan)
                 план-виконання)))))
         ((тотожне? (native-first-plan-tag-state план-виконання (як-є evaluator-fallback)) (як-є distinct))
          (native-first-execution-rejected
            (як-є invalid-plan)
            (native-first-list-2 (як-є unknown-native-first-plan) план-виконання)))
         (так
          (native-first-execution-rejected
            (як-є invalid-plan)
            (native-first-list-2 (як-є malformed-fallback-tag-state) план-виконання)))))
      (так
       (native-first-execution-rejected
         (як-є invalid-plan)
         (native-first-list-2 (як-є unknown-native-first-plan) план-виконання))))))
(визначити native-first-execute-expression
  (функція (вираз-джерела)
    (native-first-execute-plan
      (native-first-plan вираз-джерела))))

(визначити native-first-execute-source-forms
  (функція (форми-джерела)
    (за-умовою
      ((атом? форми-джерела)
       (за-умовою
         ((тотожне? форми-джерела ())
          (як-є ()))
         (так
          (сполучити
            (native-first-execution-rejected
              (як-є evaluator)
              (native-first-list-2
                (як-є malformed-source-form-tail)
                форми-джерела))
            (як-є ())))))
      (так
       (сполучити
         (native-first-execute-expression (перше форми-джерела))
         (native-first-execute-source-forms (решта форми-джерела)))))))

(визначити native-first-execute-source
  (функція (текст-джерела)
    (native-first-list-2
      (як-є source-execution)
      (native-first-execute-source-forms
        (читати-всі текст-джерела)))))