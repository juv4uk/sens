;;; phonetics.my — фонетична база знань у S-виразах і правила виведення
;;; Епістемічний шар: шар 6 (інженерія й виконання) / шар 2 (механіка Паніні)
;;; Відповідність: language-contract 2.0 (явний quote, жодного цукру reader-макросів)

((knowledge-base . phonetics-v1)
 (description . "Authoritative phonological facts, feature matrices, and Sūtra inference rules for My-Lisp.")

 ;; 1. Факти місця артикуляції (Sthāna)
 (sthana-definitions . (
   (kanthya   . ((code . 1) (name . "Guttural / Velar") (slp1-sounds . ("a" "A" "k" "K" "g" "G" "N" "h"))))
   (talavya   . ((code . 2) (name . "Palatal")          (slp1-sounds . ("i" "I" "c" "C" "j" "J" "Y" "y" "S"))))
   (murdhanya . ((code . 3) (name . "Retroflex")        (slp1-sounds . ("f" "F" "w" "W" "q" "Q" "R" "r" "z"))))
   (dantya    . ((code . 4) (name . "Dental")           (slp1-sounds . ("x" "X" "t" "T" "d" "D" "n" "l" "s"))))
   (oshthya   . ((code . 5) (name . "Labial")           (slp1-sounds . ("u" "U" "p" "P" "b" "B" "m" "v"))))
 ))

 ;; 2. Специфікації 64-бітових бітмасок класичного Pratyāhāra
 (pratyahara-masks . (
   (ac  . ((mask . #x00000000000001FF) (description . "All 9 vowels (sūtras 1-4)")))
   (hal . ((mask . #x000007FFFFFFFE00) (description . "All 33 consonants (sūtras 5-14)")))
   (al  . ((mask . #x000007FFFFFFFFFF) (description . "All 42 canonical sounds")))
   (ik  . ((mask . #x000000000000001E) (description . "Vowels i, u, ṛ, ḷ")))
   (ec  . ((mask . #x00000000000001E0) (description . "Diphthongs e, o, ai, au")))
   (yar . ((mask . #x000003FFFFFFFC00) (description . "All consonants except initial h")))
   (Sar . ((mask . #x000003800000000000) (description . "Sibilants ś, ṣ, s")))
   (JaS . ((mask . #x000000001F00000000) (description . "Voiced unaspirated stops j, b, g, ḍ, d")))
   (Jal . ((mask . #x000003FFFF000200) (description . "Stops, sibilants, and h")))
 ))

 ;; 3. Правила міркування за сутрами
 (rules . (
   ;; Sūtra 1.1.9: tulyāsyaprayatnaṁ savarṇam
   (rule-savarna . (
     (sutra . "1.1.9")
     (sanskrit-text . "तुल्यास्यप्रयत्नं सवर्णम्")
     (predicate . savarna?)
     (condition . (lambda (p1 p2)
       (savarna? p1 p2)))
     (derivation-target . homogeneity)
   ))

   ;; Sūtra 8.2.39: jhalāṁ jaśo'nte (дзвінкість кінцевого приголосного до Jaś)
   (rule-sandhi-jhal-jas . (
     (sutra . "8.2.39")
     (sanskrit-text . "झलां जशोऽन्ते")
     (target-class . (quote Jal))
     (result-class . (quote JaS))
     (transform . (lambda (p) (sandhi-voice p)))
   ))

   ;; Sūtra 8.4.40: stoḥ ścunā ścuḥ (зубний до палатальної асиміляції)
   (rule-sandhi-scuna-scu . (
     (sutra . "8.4.40")
     (sanskrit-text . "स्तोः श्चुना श्चुः")
     (trigger-class . (quote talavya))
     (transform . (lambda (p) (palatalize p)))
   ))
 ))

 ;; 4. Міжмовні українські розширення
 (ukrainian-extensions . (
   (palatalized-dentals . ("т'" "д'" "н'" "л'" "с'" "з'" "ц'"))
   (bit-modifier . #x4000)
   (description . "16-bit PVC-16 bit 14 palatalization flag mapped directly to Ukrainian soft sign (ь).")
 ))
)
