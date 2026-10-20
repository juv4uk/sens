#lang my-lisp
;;;
;;; constitution.my — канонічний файл мови my-lisp
;;;
;;; У цьому діалекті:
;;;   * quote тільки явний: (quote x); апостроф ' є частиною символу;
;;;   * істина — t, хиба — ();
;;;   * atom/eq повертають t або ();
;;;   * десяткові літерали — exact (0.5 → 1/2).
;;;
;;; Запуск: кнопка Run у DrRacket або `racket constitution.my`.
;;;

;; --- Точна арифметика: дріб лишається дробом ---
(displayln (/ 5 336))                         ; ⇒ 5/336
(displayln (/ 5.0 2))                         ; ⇒ 5/2

;; --- Сім примітивів Маккарті ---
(displayln (quote constitution))              ; quote
(displayln (atom? (quote x)))                  ; atom ⇒ t
(displayln (atom? (quote (x))))                ;      ⇒ ()
(displayln (eq? (quote a) (quote a)))          ; eq   ⇒ t
(displayln (eq? (quote a) (quote b)))          ;      ⇒ ()
(displayln (car (quote (a b))))               ; car  ⇒ a
(displayln (cdr (quote (a b))))               ; cdr  ⇒ (b)
(displayln (cons (quote a) (quote (b))))      ; cons ⇒ (a b)
(displayln (cond ((eq? (quote a) (quote b)) (quote ні))
             (t (quote так))))            ; cond ⇒ так

;; --- Власний макрос з українською назвою ---
;; Спеціальні форми if і begin належать цьому історичному діалекту
;; Racket, тому їх не перейменовуємо без відповідного механізму.
(defmacro (коли умова . тіло)
  `(if ,умова (begin ,@тіло)))

(коли (eq? (quote лісп) (quote лісп))
  (displayln (quote лісп-працює-на-chez-scheme-jit)))
