; D8:00001010 REPEAT; D6:110000 TAKE; D6:110001 DROP; D8:00100001 SUBSEQ.
; Рівно вісім D1:YES результатів: нуль, непорожні списки, порядок і фальсифікатори.
; Канонічні індекси лише D24. Немає прямої D8 callability / legacy SID8.
(список
  (equal? (повторити #d24:000000000000000000000000 (quote а)) (quote ()))
  (equal? (повторити #d24:000000000000000000000001 (quote а)) (list (quote а)))
  (equal? (повторити #d24:000000000000000000000010 (quote а)) (list (quote а) (quote а)))
  (not? (equal? (повторити #d24:000000000000000000000010 (quote а)) (list (quote а) (quote б))))
  (equal? (взяти #d24:000000000000000000000010 (list (quote а) (quote б) (quote в))) (list (quote а) (quote б)))
  (equal? (відкинути #d24:000000000000000000000010 (list (quote а) (quote б) (quote в))) (list (quote в)))
  (equal? (підпослідовність (list (quote а) (quote б) (quote в)) #d24:000000000000000000000001 #d24:000000000000000000000011) (list (quote б) (quote в)))
  (not? (equal? (взяти #d24:000000000000000000000001 (list (quote а) (quote б) (quote в))) (list (quote б)))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити хибне? not?)
