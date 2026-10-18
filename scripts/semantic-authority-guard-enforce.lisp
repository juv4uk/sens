(визначити verdicts
  (110101001 (110110111 "tests/semantic-authority-verdict.lisp")))

(визначити verdict (перше verdicts))

(визначити verdict-tag
  (за-умовою
    ((атом? verdict)
     (за-умовою
       ((тотожне? verdict (як-є ())) (як-є empty-verdict))
       ((атом? (як-є ())) verdict)))
    ((атом? (як-є ())) (перше verdict))))

(за-умовою
  ((тотожне? verdict-tag (як-є semantic-authority-ok))
   (як-є semantic-authority-ok))
  ((тотожне? verdict-tag (як-є semantic-authority-violation))
   (перше (як-є ())))
  ((атом? (як-є ()))
   (перше (як-є ()))))
