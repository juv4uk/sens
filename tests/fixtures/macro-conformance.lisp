; macro-conformance — українська проєкція
; Очікування корпусу: як-є / функція / за-умовою, без SID8/Latin call-heads.

((expr . "(як-є ())") (expected . "()") (tier . 1) (role . "constitutive"))
((expr . "(сполучити (як-є a) (як-є (b)))") (expected . "(a b)") (tier . 1) (role . "constitutive"))
((expr . "(перше (як-є (a b)))") (expected . "a") (tier . 1) (role . "constitutive"))
((expr . "(решта (як-є (a b)))") (expected . "(b)") (tier . 1) (role . "constitutive"))
((expr . "(атом? (як-є x))") (expected . "t") (tier . 1) (role . "constitutive"))
((expr . "(тотожне? (як-є a) (як-є a))") (expected . "t") (tier . 1) (role . "constitutive"))
((expr . "(за-умовою ((тотожне? 1 1) (як-є yes)) (t (як-є no)))") (expected . "yes") (tier . 1) (role . "constitutive"))
