; Native-first coverage ledger witness. Ukrainian projection only.

(load "lib/core.lisp")

(визначити native-first-coverage-check
  (функція (left right)
    (однакові? left right)))

(визначити native-first-coverage-all-pass-state
  (функція (verdicts)
    (за-умовою
      ((атом? verdicts) так)
      ((native-first-coverage-check (перше verdicts) (як-є pass))
       (native-first-coverage-all-pass-state (решта verdicts)))
      (так ні))))

(визначити native-first-coverage-ledger-witness
  (функція ()
    (нехай ((verdicts (як-є (pass pass pass))))
      (за-умовою
        ((native-first-coverage-all-pass-state verdicts)
         (як-є (native-first-coverage-ledger-witness (status pass))))
        (так
         (список
           (як-є native-first-coverage-ledger-witness)
           (як-є (status fail))
           (список (як-є verdicts) verdicts)))))))

(native-first-coverage-ledger-witness)
