; #300 — Lisp owns the Rust retirement verdict.
; CI transports only Rust diff facts into tests/rust-retirement-changes.lisp.
;
; Change rows:
;   (rust-change "path" additions deletions status)
; status is one of: existing | new | deleted
;
; Verdicts:
;   (rust-retirement-ok)
;   (rust-retirement-violation "path" additions status "diagnostic")
;
; Active #299 rule: Lisp may grow; Rust may only shrink.

(визначити друге (функція (х) (перше (решта х))))
(визначити третє (функція (х) (перше (решта (решта х)))))
(визначити четверте (функція (х) (перше (решта (решта (решта х))))))
(визначити п'яте (функція (х) (перше (решта (решта (решта (решта х)))))))

(визначити зміни-rust (читати-всі (читати-файл "tests/rust-retirement-changes.lisp")))

(визначити вердикт-виведення-rust-для
  (функція (зміни)
    (за-умовою
      ((атом? зміни) (structural-kind empty-list)
       (як-є (rust-retirement-ok)))
      ((атом? зміни) (structural-kind pair)
       (нехай ((зміна (перше зміни)))
         (нехай ((шлях (друге зміна)))
           (нехай ((додавання (третє зміна)))
             (нехай ((статус (п'яте зміна)))
               (за-умовою
                 ((тотожне? статус (як-є new)) (identity-relation same)
                  (список
                    (як-є rust-retirement-violation)
                    шлях
                    додавання
                    статус
                    "New Rust paths are forbidden during retirement. See #299."))
                 ((тотожне? статус (як-є new)) (identity-relation distinct)
                  (за-умовою
                    ((числовий-рівність додавання 0) 1
                     (вердикт-виведення-rust-для (решта зміни)))
                    ((числовий-рівність додавання 0) 0
                     (список
                       (як-є rust-retirement-violation)
                       шлях
                       додавання
                       статус
                       "Rust may only shrink; added Rust lines are forbidden. See #299.")))))))))))))

(вердикт-виведення-rust-для зміни-rust)

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити читати-всі read-all)
