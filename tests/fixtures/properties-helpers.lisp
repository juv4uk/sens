; Допоміжні функції для property-тестів. Українська проєкція.

(визначити build-map
  (функція (keys map)
    (за-умовою
      ((атом? keys) map)
      (так (build-map (решта keys) (спарувати (перше keys) (перше keys) map))))))

(визначити map-keys-sorted?
  (функція (l)
    (за-умовою
      ((атом? l) так)
      ((атом? (решта l)) так)
      ((менше? (перше (перше (решта l))) (перше (перше l))) (як-є ()))
      (так (map-keys-sorted? (решта l))))))

(визначити fib
  (функція (n)
    (за-умовою
      ((менше? n 2) n)
      (так (додати (fib (додати n -1)) (fib (додати n -2)))))))

(визначити build-world
  (функція (events w)
    (за-умовою
      ((атом? events) w)
      (так (build-world (решта events) (world-tell w "mod" (перше events)))))))

(визначити tell-all-events
  (функція (events)
    (за-умовою
      ((атом? events) так)
      (так (нехай ((_ (defmodule "mod" (список (перше events)))))
           (tell-all-events (решта events)))))))
