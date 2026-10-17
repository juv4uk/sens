; D10 CLIPS — 10 фізичних D1-законів split-at-arrow + assert-conclusions.
; Лише похідні функції SENS: не прямий допуск D10 opcode.
(list
  (equal? (розділити-правило-clips (quote ()))
          (quote (() ())))
  (equal? (розділити-правило-clips
            (quote (=> (assert (готово)))))
          (quote (() ((assert (готово))))))
  (equal? (розділити-правило-clips
            (quote ((умова-а) => (assert (факт-а)))))
          (quote (((умова-а)) ((assert (факт-а))))))
  (equal? (розділити-правило-clips
            (quote ((умова-а) (умова-б) => (assert (факт-а)) (assert (факт-б)))))
          (quote (((умова-а) (умова-б))
                  ((assert (факт-а)) (assert (факт-б))))))
  (equal? (розділити-правило-clips
            (quote ((умова-а) (умова-б))))
          (quote (((умова-а) (умова-б)) ())))
  (equal? (розділити-правило-clips
            (quote (((=>) умова-а) => хвіст)))
          (quote ((((=>) умова-а)) (хвіст))))
  (equal? (зібрати-висновки-clips (quote ()))
          (quote ()))
  (equal? (зібрати-висновки-clips
            (quote ((assert (факт-а)))))
          (quote ((факт-а))))
  (equal? (зібрати-висновки-clips
            (quote ((assert (факт-а) (факт-б)))))
          (quote ((факт-а) (факт-б))))
  (equal? (зібрати-висновки-clips
            (quote ((assert (факт-а))
                    (assert (факт-б) (факт-в)))))
          (quote ((факт-а) (факт-б) (факт-в)))))
