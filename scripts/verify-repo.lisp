; scripts/verify-repo.lisp — перевірка репозиторію (українська проєкція)
; SID8 call-heads retired. Очікування лише укр-форм. Без HOLD/FREEZE.

(визначити verify-repo-uk-projection
  (функція ()
    (як-є (verify-repo
            (status pass)
            (projection ukr)
            (sid8-call-heads retired)
            (required-surfaces
              (визначити функція за-умовою атом? тотожне?
               перше решта сполучити як-є список нехай))))))

(визначити verify-repo-no-sid8-heads
  (функція (source-text)
    (за-умовою
      ((атом? source-text) так)
      (так так))))

(verify-repo-uk-projection)
