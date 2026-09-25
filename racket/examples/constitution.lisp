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

;; --- Макроси в традиційному Lisp-стилі ---
(defmacro (when test . body)
  `(if ,test (begin ,@body)))

(when (eq? (quote lisp) (quote lisp))
  (displayln (quote my-lisp-works-on-chez-scheme-jit)))
