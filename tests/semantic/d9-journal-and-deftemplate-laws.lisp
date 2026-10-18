; Додаткові дев'ять незалежних SENS D1 свідків D9/FS та CLIPS.
(список
  (equal? (фс-журнал-додати (quote ()) (quote подія-а))
          (список (quote подія-а)))
  (equal? (фс-журнал-додати (список (quote подія-а)) (quote подія-б))
          (список (quote подія-а) (quote подія-б)))
  (equal? (фс-журнал-додати (список (quote подія-а) (quote подія-б))
                            (quote подія-в))
          (список (quote подія-а) (quote подія-б) (quote подія-в)))
  (equal? (фс-журнал-додати (quote ()) (список (quote write) (quote документ)))
          (список (список (quote write) (quote документ))))
  (clips-deftemplate-форма? (quote (deftemplate питання)))
  (хибне? (clips-deftemplate-форма? (quote (deffacts питання))))
  (хибне? (clips-deftemplate-форма? (quote ())))
  (хибне? (clips-deftemplate-форма? (quote ((deftemplate) питання))))
  (хибне? (clips-deftemplate-форма? (quote не-форма))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити хибне? not?)
