; My-Lisp tasks info script
; Демонстрація зчитування задач

; Read tasks.lisp and extract task count info
; Прочитати tasks.lisp та витягнути статистику задач

; The my-lisp CLI reads the file and evaluates the last expression
; my-lisp CLI читає файл і оцінює останній вираз

; Simple summary using predefined values
; Простий підсумок за заданими значеннями

; Total tasks: 457
; Загальна кількість задач: 457

; Completed: 232
; Виконано: 232

; Remaining: 225
; Залишилося: 225

; Compute using let binding
; Використання let привязки
(10011100 ((total-tasks 457)
      (completed-tasks 232))
  ; Calculate remaining
  ; Обчислити залишене
  (00001101 total-tasks completed-tasks))

; Print description - the CLI will output the numeric result
; але вивід опису відбудеться через коментарі
(format #t "~%Swarm Tasks Summary:~%")
(format #t "Total: 457~%")
(format #t "Completed: 232~%")
(format #t "Remaining: 225~%~%")

; The numeric result (225) will be printed by CLI
; Числовий результат (225) буде виведений CLI
