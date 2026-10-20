; Український виконавчий свідок прямого виведення Д3.
; Використовує чинні бібліотеки уніфікації та повного зіставлення умов.
; Попередні локальні аналоги MEMBER, APPEND, SUBST і числового циклу
; вилучено: семантика та механізми тепер належать lib/forward.lisp.
; Атоми parent, ancestor, var і status — протокольні дані, не викличні голови.
; Попередній стан збережено окремо у forward-d3-before.lisp.

(завантажити-файл "lib/unify.lisp")
(завантажити-файл "lib/forward.lisp")

(визначити свідок-прямого-виведення-д3-кандидат
  (функція ()
    (нехай-послідовно
      ((правила
         (як-є
           (((ancestor (var x) (var y))
             (parent (var x) (var y)))
            ((ancestor (var x) (var z))
             (ancestor (var x) (var y))
             (parent (var y) (var z))))))
       (факти
         (як-є ((parent alice bob) (parent bob carol))))
       (результат
         (виконати-багатоваріантне-виведення правила факти)))
      (за-умовою
        ((факт-наявний? (як-є (ancestor alice carol)) результат)
         (за-умовою
           ((факт-наявний? (як-є (ancestor bob alice)) результат)
            (як-є (forward-d3-candidate-witness (status fail))))
           (так (як-є (forward-d3-candidate-witness (status pass))))))
        (так (як-є (forward-d3-candidate-witness (status fail))))))))

(свідок-прямого-виведення-д3-кандидат)
