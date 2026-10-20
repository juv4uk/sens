; #2234 — D4 fixed-point capture escape. Ukrainian projection only.

(обчислити
  (як-є
    (((функція (mark)
        ((функція (fix)
           (fix
             (функція (recur)
               (функція (xs)
                 (за-умовою
                   ((тотожне? xs (як-є ())) mark)
                   (так (recur (решта xs))))))))
         (функція (f)
           ((функція (x)
              (f
                (функція (v)
                  ((x x) v))))
            (функція (x)
              (f
                (функція (v)
                  ((x x) v))))))))
      (як-є captured))
     (як-є (A B))))
  (як-є ())
  (як-є ()))
