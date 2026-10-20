; #1145 executable witness for the yantraOS bridge contract.
; Ukrainian projection only.
;
; The witness proves the intended composition without network access:
; SENS constructs a typed action envelope, yantraOS is represented as
; the execution owner, and the returned execution observation remains data.

(визначити yo-proper-list?
  (функція (value)
    (за-умовою
      ((атом? value)
       (за-умовою
         ((однакові? value (як-є ()))
          (як-є yes))
         (так (як-є invalid))))
      (так (yo-proper-list? (решта value))))))

(визначити yo-field
  (функція (name record)
    (нехай ((found (знайти-за-ключем name record)))
      (за-умовою
        ((однакові? found (як-є ()))
         (як-є ()))
        (так (решта found))))))

(визначити yo-has-field?
  (функція (name record)
    (нехай ((found (знайти-за-ключем name record)))
      (за-умовою
        ((однакові? found (як-є ()))
         (як-є no))
        (так (як-є yes))))))

(визначити yo-no-raw-shell?
  (функція (envelope)
    (нехай ((action (yo-field (як-є action) envelope))
          (parameters (yo-field (як-є parameters) envelope)))
      (за-умовою
        ((однакові?
           (yo-field (як-є capability) action)
           (як-є shell))
         (як-є no))
        ((тотожне? (yo-has-field? (як-є command) parameters) (як-є yes))
         (як-є no))
        (так (як-є yes))))))

(визначити yo-action-envelope
  (функція (goal capability operation target parameters verification provenance approval)
    (список
      (сполучити (як-є protocol) (як-є (yantraos-bridge 1)))
      (сполучити (як-є intent)
            (список
              (сполучити (як-є goal) goal)
              (сполучити (як-є requires) (як-є ()))
              (сполучити (як-є stop-on) (як-є (verified)))
              (сполучити (як-є produces) (як-є (execution-observation)))))
      (сполучити (як-є action)
            (список
              (сполучити (як-є capability) capability)
              (сполучити (як-є operation) operation)
              (сполучити (як-є target) target)))
      (сполучити (як-є parameters) parameters)
      (сполучити (як-є verification) verification)
      (сполучити (як-є provenance) provenance)
      (сполучити (як-є approval) approval))))

(визначити yo-action-envelope?
  (функція (value)
    (за-умовою
      ((тотожне? (yo-proper-list? value) (як-є yes))
       (за-умовою
         ((тотожне? (yo-has-field? (як-є protocol) value) (як-є yes))
          (за-умовою
            ((тотожне? (yo-has-field? (як-є intent) value) (як-є yes))
             (за-умовою
               ((тотожне? (yo-has-field? (як-є action) value) (як-є yes))
                (за-умовою
                  ((тотожне? (yo-has-field? (як-є parameters) value) (як-є yes))
                   (за-умовою
                     ((тотожне? (yo-has-field? (як-є verification) value) (як-є yes))
                      (за-умовою
                        ((тотожне? (yo-has-field? (як-є provenance) value) (як-є yes))
                         (за-умовою
                           ((тотожне? (yo-has-field? (як-є approval) value) (як-є yes))
                            (yo-no-raw-shell? value))
                           (так (як-є no))))
                        (так (як-є no))))
                     (так (як-є no))))
                  (так (як-є no))))
               (так (як-є no))))
            (так (як-є no))))
         (так (як-є no))))
      (так (як-є no)))))

(визначити yo-execution-observation
  (функція (result route evidence audit-ref provenance)
    (список
      (сполучити (як-є protocol) (як-є (yantraos-bridge 1)))
      (сполучити (як-є result) result)
      (сполучити (як-є route) route)
      (сполучити (як-є evidence) evidence)
      (сполучити (як-є audit-ref) audit-ref)
      (сполучити (як-є provenance) provenance))))

(визначити yo-execution-observation?
  (функція (value)
    (за-умовою
      ((тотожне? (yo-proper-list? value) (як-є yes))
       (за-умовою
         ((тотожне? (yo-has-field? (як-є protocol) value) (як-є yes))
          (за-умовою
            ((тотожне? (yo-has-field? (як-є result) value) (як-є yes))
             (за-умовою
               ((тотожне? (yo-has-field? (як-є route) value) (як-є yes))
                (за-умовою
                  ((тотожне? (yo-has-field? (як-є evidence) value) (як-є yes))
                   (за-умовою
                     ((тотожне? (yo-has-field? (як-є audit-ref) value) (як-є yes))
                      (yo-has-field? (як-є provenance) value))
                     (так (як-є no))))
                  (так (як-є no))))
               (так (як-є no))))
            (так (як-є no))))
         (так (як-є no))))
      (так (як-є no)))))
