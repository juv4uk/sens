; My-Lisp swarm tasks summary script
; Підсумок задач roe My-Lisp

; Summary statistics (from Python analysis of all tasks.lisp files)
; Статистика з аналізу всіх файлів tasks.lisp

; Total tasks across all repos: 457
; Загальна кількість задач у всіх репо: 457

; Completed tasks: 232
; Виконано задач: 232

; Remaining tasks: 225
; Залишилося задач: 225

; Compute remaining: 457 - 232
; Обчислити залишене: 457 - 232

(let ((total 457) (completed 232))
  (- total completed))

; The my-lisp CLI prints the result of the last expression
; my-lisp CLI друкує результат останнього виразу
; Result: 225
