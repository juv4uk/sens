; Legacy three-field answer clauses are lowered to ((equal? query expected) expression).
; D3 COND stays strict; exact-answer comparison is implemented by Lisp, not the evaluator.
(00001001 identity (00001000 (value) value))(00001001 binary
  (00001000 (width)
    (00100111 (00000001 binary) width)))(00001001 list (00001000 args args))(00001010 and rest
  (00000111
    ((00000010 rest) (00000010 ()))
    ((00000010 (00000110 rest)) (00000101 rest))
    ((00000010 ())
     (00000100 (00000001 00000111)
       (00000100
         (00000100 (00000101 rest)
           (00000100
             (00000100 (00000001 and) (00000110 rest))
             (00000001 ())))
         (00000100
           (00000100
             (00000100 (00000001 00000010)
               (00000100 (00000001 ()) (00000001 ())))
             (00000100
               (00000001 00000010)
               (00000100
                 (00000100 (00000001 00000100)
                   (00000100 (00000001 ())
                     (00000100 (00000001 ()) (00000001 ()))))
                 (00000001 ())))
           (00000001 ()))))))))(00001010 or rest
  (00000111
    ((00000010 rest) (00000010 (00000100 () ())))
    ((00000010 (00000110 rest)) (00000101 rest))
    ((00000010 ())
     (00000100 (00000001 00000111)
       (00000100
         (00000100 (00000101 rest)
           (00000100
             (00000100 (00000001 00000010)
               (00000100 (00000001 ()) (00000001 ())))
             (00000001 ())))
         (00000100
           (00000100
             (00000100 (00000001 00000010)
               (00000100 (00000001 ()) (00000001 ())))
             (00000100
               (00000100 (00000001 or) (00000110 rest))
               (00000001 ())))
           (00000001 ())))))))(00001001 gensym
  (00001000 (prefix)
    (01000011 (00111010 prefix (01001100 (01011010))))))(00001001 pair
  (00001000 (left right)
    (00000100 left (00000100 right (00000001 ())))))(00001001 second
  (00001000 (values)
    (00000101 (00000110 values))))(00001001 third
  (00001000 (values)
    (00000101 (00000110 (00000110 values)))))(00001001 fourth
  (00001000 (values)
    (00000101 (00000110 (00000110 (00000110 values))))))(00001001 cadddr fourth)(00001001 fifth
  (00001000 (values)
    (00000101 (00000110 (00000110 (00000110 (00000110 values)))))))(00001001 caar
  (00001000 (values)
    (00000101 (00000101 values))))(00001001 cadr
  (00001000 (values)
    (00000101 (00000110 values))))(00001001 cddr
  (00001000 (values)
    (00000110 (00000110 values))))(00001001 length-onto
  (00001000 (values acc)
    (00000111
      ((00000010 values)
       (00000111
         ((00000011 values (00000001 ()))
          acc)
         ((00000010 (00000001 ()))
          (00000001 ()))))
      ((00000010 (00000001 ()))
       (length-onto (00000110 values) (00001100 acc 1))))))(00001001 length
  (00001000 (values)
    (length-onto values 0)))(00001001 зворот-до
  (00001000 (values acc)
    (00000111
      ((equal? (00000010 values) ()) acc)
      ((00100010 (00000010 values) (00000001 (0)))
       (зворот-до (00000110 values) (00000100 (00000101 values) acc))))))(00001001 reverse-onto зворот-до)(00001001 reverse
  (00001000 (values)
    (зворот-до values (00000001 ()))))(00001001 append
  (00001000 (left right)
    (зворот-до (00101010 left) right)))(00001001 map-onto
  (00001000 (f values acc)
    (00000111
      ((equal? (00000010 values) ()) (00101010 acc))
      ((00000010 values)  (00000001 ()))
      ((00100010 (00000010 values) (00000001 (0)))
       (map-onto f (00000110 values) (00000100 (f (00000101 values)) acc))))))(00001001 map
  (00001000 (f values)
    (map-onto f values (00000001 ()))))(00001001 filter-onto
  (00001000 (predicate values acc)
    (00000111
      ((equal? (00000010 values) ()) (00101010 acc))
      ((00000010 values)  (00101010 acc))
      ((00000010 values) 
       (10011100 ((decision (predicate (00000101 values))))
         (00000111
           (decision
            (filter-onto predicate (00000110 values) (00000100 (00000101 values) acc)))
           ((00000010 predicate)
            (filter-onto predicate (00000110 values) acc))))))))(00001001 filter
  (00001000 (predicate values)
    (filter-onto predicate values (00000001 ()))))(00001001 reduce
  (00001000 (f acc values)
    (00000111
      ((equal? (00000010 values) ()) acc)
      ((00000010 values) 
       (00111001 f (f acc (00000101 values)) (00000110 values))))))(00001010 let (bindings body)
  (00000100 (00100111 (00000001 00001000) (00110111 (00001000 (binding) (00000101 binding)) bindings) body)
        (00110111 (00001000 (binding) (00101111 binding)) bindings)))(00001001 equal?
  (00001000 (a b)
    (00000111
      ((00000010 a)
       (00000111
         ((00000010 b)
          (00000011 a b))
         ((00000010 (00000001 ())) (00000010 (00000001 (00000000))))))
      ((00000010 (00000001 ()))
       (00000111
         ((00000010 b) (00000010 (00000001 (00000000))))
         ((00000010 (00000001 ()))
          (00000111
            ((equal? (00000101 a) (00000101 b))
             (equal? (00000110 a) (00000110 b)))
            ((00000010 (00000001 ())) (00000010 (00000001 (00000000)))))))))))(00001001 truthy?
  (00001000 (value)
    (00000111
      ((equal? (00000010 value) ()) (00000001 ()))
      ((00000010 value) 
       (00000111
         ((00000011 value 0)  (00000001 ()))
         ((equal? (00000011 value 0) (0)) t)))
      ((00000010 value) 
       (00000111
         ((equal? (00100010 value (00000001 (0))) (1)) (00000001 ()))
         ((equal? (00100010 value (00000001 (0))) (1)) (00000001 ()))
         ((equal? (00100010 value (00000001 (0))) (1)) (00000001 ()))
         ((equal? t t) t))))))(00001001 not?
  (00001000 (value)
    (00000111
      (value
       (00000010 (00000001 (00000000))))
      ((00000010 (00000001 ()))
       (00000010 (00000001 ()))))))(00001001 nth
  (00001000 (i lst)
    (00000111
      ((00000011 i 0)  (00000101 lst))
      ((00000011 i 0) 
       (00101011 (00001101 i 1) (00000110 lst))))))(00001001 member?
  (00001000 (item lst)
    (00000111
      ((equal? (00000010 lst) ()) (00000001 ()))
      ((00000010 lst) 
       (00000111
         ((equal? (00100010 item (00000101 lst)) (1)) t)
         ((equal? (00100010 item (00000101 lst)) (0)) (00101100 item (00000110 lst))))))))(00001001 assoc
  (00001000 (key alist)
    (00000111
      ((equal? (00000010 alist) ()) (00000001 ()))
      ((00000010 alist) 
       (00000111
         ((equal? (00100010 key (00000101 (00000101 alist))) (1)) (00000101 alist))
         ((equal? (00100010 key (00000101 (00000101 alist))) (0)) (00101101 key (00000110 alist))))))))(00001001 спарувати
  (00001000 (keys values tail)
    (00000111
      ((00000010 keys) tail)
      ((00000010 (00000001 ())) 
       (00000100
         (00000100 (00000101 keys) (00000101 values))
         (спарувати (00000110 keys) (00000110 values) tail))))))(00001001 pairlis спарувати)(00001010 let* (bindings body)
  (00000111
    ((00000010 bindings) body)
    ((00000010 (00000001 ())) 
     ; Build the recursive expansion from the primitive tree substrate only.
     ; This keeps let* semantics in Lisp while allowing generic macro
     ; frontends to execute the law without importing the higher-level list
     ; helper as host/compiler semantic authority.
     (00000100 (00000001 let)
           (00000100 (00000100 (00000101 bindings) (00000001 ()))
                 (00000100 (00000100 (00000001 let*)
                             (00000100 (00000110 bindings)
                                   (00000100 body (00000001 ()))))
                       (00000001 ())))))))(00001001 string-membership-helper
  (00001000 (value)
    (00000111
      ((equal? (00000010 value) ()) (00000001 (class-membership string nonmember)))
      ((00000010 value) 
       (00000111
         ((00000011 (00111111 (01001100 value))
              (00111111 (01001100 "")))
          
          (00000001 (class-membership string member)))
         ((00000011 (00111111 (01001100 value))
              (00111111 (01001100 "")))
          
          (00000001 (class-membership string nonmember)))))
      ((00000010 value) 
       (00000001 (class-membership string nonmember))))))(00001001 string-order-helper
  (00001000 (left right)
    (00000111
      ((equal? (00111100 left) (1)) (00000111
         ((equal? (00111100 right) (1)) (00000001 (text-order same)))
         ((equal? (00111100 right) (0)) (00000001 (text-order before)))))
      ((equal? (00111100 left) (0)) (00000001 (text-order after)))
      ((00000011 (00111111 left) (00111111 right))
       
       (string-order-helper (01000000 left) (01000000 right)))
      ((equal? (00011010 (01000101 (00111111 left))
          (01000101 (00111111 right))) 1) (00000001 (text-order before)))
      ((equal? (00011010 (01000101 (00111111 left))
          (01000101 (00111111 right))) 0) (00000001 (text-order after))))))(00001001 nonempty-string-membership-helper
  (00001000 (value)
    (00000111
      ((equal? (string-membership-helper value) (class-membership string member)) (00000111
         ((equal? (00111100 value) (0)) (00000001 (class-membership string nonempty-member)))
         ((equal? (00111100 value) (1)) (00000001 (class-membership string member)))))
      ((equal? (string-membership-helper value) (class-membership string nonmember)) (00000001 (class-membership string nonmember))))))(00001001 string<?
  (00001000 (a b)
    (00000111
      ; Порожній бік: інший перевіряється як рядок (string-append дає Type).
      ((equal? (00111100 b) (1)) (00101111 (00100111 (00111010 a "") (00000001 ()))))
      ((equal? (00111100 a) (1)) (00101111 (00100111 (00111010 b "") t)))
      ((equal? (00011010 (01000101 (00111111 a)) (01000101 (00111111 b))) 1) t)
      ((00000011 (00111111 a) (00111111 b)) 
       (00100101 (01000000 a) (01000000 b)))
      ((equal? t t) (00000001 ())))))(00001001 symbol?
  (00001000 (value)
    (00000111
      ((equal? (00000010 value) ()) (00000001 ()))
      ((00000010 value) 
       (00000111
         ((equal? (00000011 value (01000011 (01001100 value))) (1)) t)
         ((equal? t t) (00000001 ()))))
      ((00000010 value)  (00000001 ())))))(00001001 largest-chunk
  (00001000 (a b chunk mult)
    (00000111
      ((00011010 a (00001100 chunk chunk))
       (00000100 chunk mult))
      ((00000010 (00000001 ()))
       (00011001 a b (00001100 chunk chunk) (00001100 mult mult))))))(00001001 quotient
  (00001000 (a b)
    (00000111
      ((00000011 b 0)
       (00001111 a b))
      ((00000010 (00000001 ()))
       (00000111
         ((00011010 a b)
          0)
         ((00000010 (00000001 ()))
          (10011100 ((chunk+mult (00011001 a b b 1)))
            (00001100 (00000110 chunk+mult)
               (00010100 (00001101 a (00000101 chunk+mult)) b)))))))))(00001001 mod
  (00001000 (a b)
    (00001101 a (00001110 b (00010100 a b)))))(00001001 nondecreasing-from?
  (00001000 (current remaining)
    (00000111
      ((00000010 remaining)
       (00000010 (00000001 ())))
      ((00011010 current (00000101 remaining))
       (nondecreasing-from? (00000101 remaining) (00000110 remaining)))
      ((00011100 current (00000101 remaining))
       (nondecreasing-from? (00000101 remaining) (00000110 remaining)))
      ((00000010 (00000001 ()))
       (00000010 (00000001 (00000000)))))))(00001001 nonincreasing-from?
  (00001000 (current remaining)
    (00000111
      ((00000010 remaining)
       (00000010 (00000101 (00000001 (00000000)))))
      ((00011011 current (00000101 remaining))
       (nonincreasing-from? (00000101 remaining) (00000110 remaining)))
      ((00011100 current (00000101 remaining))
       (nonincreasing-from? (00000101 remaining) (00000110 remaining)))
      ((00000010 (00000001 ()))
       (00000010 (00000001 (00000000)))))))(00001001 <=
  (00001000 (first . remaining)
    (00011111 first remaining)))(00001001 >=
  (00001000 (first . remaining)
    (00100000 first remaining)))(00001001 digit->string
  ; Superseded by number->string's canonical delegation to write-to-string
  ; (FIX-NUMBER-TO-STRING-RATIONAL). Retained because racket/boot/core.lisp
  ; mirrors this file and fpga-lisp's assembler.lisp carries its own local
  ; variant — removal is a separate mirrored-surface decision, not a
  ; silent one.
  (00001000 (d)
    (00101011 d (00000001 ("0" "1" "2" "3" "4" "5" "6" "7" "8" "9")))))(00001001 number->string-onto
  (00001000 (n acc)
    (00000111
      ((equal? (00000011 n 0) (1)) acc)
      ((00000011 n 0) 
       (number->string-onto
         (00010100 n #d10)
         (00111010 (01000111 (00010011 n #d10)) acc))))))(00001001 number->string
  (00001000 (n)
    ; Canonical serialization for every number (FIX-NUMBER-TO-STRING-
    ; RATIONAL, docs/BUG-number-to-string-rational.md): integers render
    ; as themselves, non-integer rationals render REDUCED exactly —
    ; "1/3", never a decimal approximation, per the same G6 law that
    ; makes 10/20 serialize as "1/2". The previous quotient/mod descent
    ; crashed on fractional digit indices ((nth 1/3 <digit-table>)) and
    ; its misleading error surfaced as an apparent memory corruption.
    ; Delegation, not re-implementation: write-to-string is already the
    ; contract-tested renderer (G6 fixtures), so this cannot drift from it.
    (01001100 n)))(00001010 -> forms
  (00000111
    ((equal? (00000010 forms) ()) (00000001 ()))
    ((00000010 forms) 
     (00000111
       ((equal? (00000010 (00000110 forms)) ()) (00000101 forms))
       ((00000010 (00000110 forms)) 
        (10011101 ((x (00000101 forms))
               (next (00000101 (00000110 forms)))
               (rest (00000110 (00000110 forms)))
               (step
                 (00000111
                   ((equal? (00000010 next) ()) (00100111 next x))
                   ((00000010 next)  (00100111 next x))
                   ((00000010 next) 
                    (00000100 (00000101 next) (00000100 x (00000110 next)))))))
          (00000111
            ((equal? (00000010 rest) ()) step)
            ((00000010 rest) 
             (00000100 (00000001 ->) (00000100 step rest))))))))))(00001010 ->> forms
  (00000111
    ((equal? (00000010 forms) ()) (00000001 ()))
    ((00000010 forms) 
     (00000111
       ((equal? (00000010 (00000110 forms)) ()) (00000101 forms))
       ((00000010 (00000110 forms)) 
        (10011101 ((x (00000101 forms))
               (next (00000101 (00000110 forms)))
               (rest (00000110 (00000110 forms)))
               (step
                 (00000111
                   ((equal? (00000010 next) ()) (00100111 next x))
                   ((00000010 next)  (00100111 next x))
                   ((00000010 next) 
                    (00101001 next (00100111 x))))))
          (00000111
            ((equal? (00000010 rest) ()) step)
            ((00000010 rest) 
             (00000100 (00000001 ->>) (00000100 step rest))))))))))(00001001 sqrt-iter
  (00001000 (guess x n)
    (00000111
      ((equal? (00011100 n 0) 1) guess)
      ((equal? (00011100 n 0) 0) (sqrt-iter (00001111 (00001100 guess (00001111 x guess)) 2) x (00001101 n 1))))))(00001001 isqrt
  (00001000 (n)
    (00000111
      ((equal? (00011010 n 2) 1) n)
      ((equal? (00011010 n 2) 0) (isqrt-step n (00010100 n 2))))))(00001001 isqrt-step
  (00001000 (n g)
    (10011100 ((next (00010100 (00001100 g (00010100 n g)) 2)))
      (00000111
        ((equal? (00011010 next g) 1) (isqrt-step n next))
        ((equal? (00011010 next g) 0) g)))))(00001001 sqrt
  (00001000 (x)
    (00000111
      ((equal? (00011010 x 0) 1) (00000001 ()))
      ((equal? (00011100 x 0) 1) 0)
      ((equal? (00011100 x (00010100 x 1)) 1) (10011100 ((r (00010110 x)))
         (00000111
           ((equal? (00011100 (00001110 r r) x) t) r)
           ((equal? t t) (sqrt-iter (00001111 x 2) x 8)))))
      ((equal? t t) (sqrt-iter (00001111 x 2.0) x 5)))))(00001001 abs
  (00001000 (x)
    (00000111
      ((equal? (00011010 x 0) 1) (00001101 0 x))
      ((equal? (00011010 x 0) 0) x))))(00001001 min
  (00001000 (first . rest)
    (00010111 (00000100 first rest))))(00001001 max
  (00001000 (first . rest)
    (00011000 (00000100 first rest))))(00001001 min-list
  (00001000 (items)
    (00000111
      ((equal? (00000010 items) ()) (00000001 ()))
      ((00000010 items) 
       (10011100 ((rest-min (00010111 (00000110 items))))
         (00000111
           ((equal? (00100010 rest-min (00000001 ())) (1)) (00000101 items))
           ((equal? (00100010 rest-min (00000001 ())) (0)) (00000111
              ((equal? (00011010 (00000101 items) rest-min) 1) (00000101 items))
              ((equal? (00011010 (00000101 items) rest-min) 0) rest-min)))))))))(00001001 max-list
  (00001000 (items)
    (00000111
      ((equal? (00000010 items) ()) (00000001 ()))
      ((00000010 items) 
       (10011100 ((rest-max (00011000 (00000110 items))))
         (00000111
           ((equal? (00100010 rest-max (00000001 ())) (1)) (00000101 items))
           ((equal? (00100010 rest-max (00000001 ())) (0)) (00000111
              ((equal? (00011011 (00000101 items) rest-max) 1) (00000101 items))
              ((equal? (00011011 (00000101 items) rest-max) 0) rest-max)))))))))(00001001 my-postcore-stable-peer-projection
  (00000001 (
    (1079 utc-now поточний-всч)
    (1080 utc-from-unix всч-із-юнікс)
    (1081 unix-time-observation->utc юнікс-спостереження-у-всч)
    (1082 milliseconds-from-nanoseconds мілісекунди-із-наносекунд)
    (1083 mono-ms монотонний-мс)
    (1084 timezone-name назва-часового-поясу)
    (1085 timezone-detect визначити-часовий-пояс)
    (1086 timezone-offset-seconds зміщення-часового-поясу-в-секундах)
    (1087 deadline-reached? дедлайн-досягнуто?)
    (1088 deadline-reached-at? дедлайн-досягнуто-на-момент?)
    (1089 elapsed-ns минуло-нс)
    (1090 deadline-from дедлайн-від)
    (1091 deadline-after-ns дедлайн-через-нс)
    (1092 internet-time-sync запитати-інтернет-час)
    (162 process-run запустити-процес)
    (163 tcp-read прочитати-текст-з-з'єднання-протоколу-керування-передаванням)
    (164 tcp-write записати-текст-у-з'єднання-протоколу-керування-передаванням)
    (165 tcp-listen слухати-порт-протоколу-керування-передаванням)
    (166 read-file прочитати-файл)
    (167 write-file записати-файл)
  )))(00001001 my-postcore-peer-group
  (00001000 (semantic-id groups)
    (00000111
      ((equal? (00000010 groups) ()) (00000001 ()))
      ((00000010 groups) 
       (10011100 ((group (00000101 groups)))
         (00000111
           ((equal? (00000011 semantic-id (00000101 group)) (1)) group)
           ((00000011 semantic-id (00000101 group)) 
            (my-postcore-peer-group semantic-id (00000110 groups)))))))))(00001001 my-postcore-binding-status
  (00001000 (surface bindings)
    (00000111
      ((equal? (00000010 bindings) ()) (00000001 absent))
      ((00000010 bindings) 
       (10011100 ((binding (00000101 bindings)))
         (00000111
           ((00000011 (01000010 surface) (00000101 binding)) 
            (00000001 present))
           ((00000011 (01000010 surface) (00000101 binding)) 
            (my-postcore-binding-status surface (00000110 bindings)))))))))(00001001 my-postcore-missing-peers
  (00001000 (source peers bindings)
    (00000111
      ((equal? (00000010 peers) ()) (00000001 ()))
      ((00000010 peers) 
       (10011100 ((peer (00000101 peers)))
         (00000111
           ((00000011 source peer) 
            (my-postcore-missing-peers source (00000110 peers) bindings))
           ((00000011 source peer) 
            (00000111
              ((00000011 (my-postcore-binding-status peer bindings) (00000001 present))
               
               (my-postcore-missing-peers source (00000110 peers) bindings))
              ((00000011 (my-postcore-binding-status peer bindings) (00000001 absent))
               
               (00000100 peer
                     (my-postcore-missing-peers
                       source
                       (00000110 peers)
                       bindings)))))))))))(00001001 my-postcore-build-definitions
  (00001000 (source peers)
    (00000111
      ((equal? (00000010 peers) ()) source)
      ((00000010 peers) 
       (00100111 (00000001 define)
             (00000101 peers)
             (my-postcore-build-definitions source (00000110 peers)))))))(00001010 my-postcore-materialize-stable-peers args
  (10011101 ((semantic-id (00000101 args))
         (source (00101111 args))
         (group
           (my-postcore-peer-group
             semantic-id
             my-postcore-stable-peer-projection)))
    (00000111
      ((equal? (00000010 group) ()) source)
      ((00000010 group) 
       (my-postcore-build-definitions
         source
         (my-postcore-missing-peers source (00000110 group) (01001110)))))))(00001001 divmod
  (00001000 (dividend divisor)
    (00100111 (00010100 dividend divisor) (00010011 dividend divisor))))(00001001 null?
  (00001000 (x)
    (00000111
      ((00000010 x)
       (00000011 x (00000001 ())))
      ((00000011 0 0)
       (00000010 x)))))(00001001 subst
  (00001000 (x y z)
    (00000111
      ((00000010 z) 
       (00000100 (10101100 x y (00000101 z)) (10101100 x y (00000110 z))))
      ((equal? (00000010 z) ()) (00000111
         ((equal? (00000011 z y) (1)) x)
         ((equal? (00000011 z y) (0)) z)))
      ((00000010 z) 
       (00000111
         ((equal? (00000011 z y) (1)) x)
         ((equal? (00000011 z y) (0)) z))))))(00001001 sublis-pair
  (00001000 (x z)
    (00000111
      ((equal? (00000010 x) ()) z)
      ((00000010 x) 
       (00000111
         ((00000011 (00000101 (00000101 x)) z) 
          (00000101 (00000110 (00000101 x))))
         ((00000011 (00000101 (00000101 x)) z) 
          (sublis-pair (00000110 x) z)))))))(00001001 sublis
  (00001000 (x y)
    (00000111
      ((00000010 y) 
       (00000100 (10101101 x (00000101 y)) (10101101 x (00000110 y))))
      ((equal? (00000010 y) ()) (sublis-pair x y))
      ((00000010 y)  (sublis-pair x y)))))(00001001 maplist
  (00001000 (x f)
    (00000111
      ((equal? (00000010 x) ()) (00000001 ()))
      ((00000010 x) 
       (00000100 (f x) (10101110 (00000110 x) f))))))(00001001 apply-quote-args
  (00001000 (m)
    (00000111
      ((equal? (00000010 m) ()) (00000001 ()))
      ((00000010 m) 
       (00000100 (00000100 (00000001 00000001) (00000100 (00000101 m) (00000001 ())))
                 (apply-quote-args (00000110 m)))))))(00001001 apply
  (00001000 (f args)
    (01001101 (00000100 f (apply-quote-args args)))))(00001001 answer-not
  (00001000 (a)
    (00000111
      ((equal? (00000010 a) ()) (00000001 ()))
      ((00000010 a) 
       (00000100
         (00000111
           ((equal? (00000011 (00000101 a) 0) (1)) 1)
           ((equal? (00000011 (00000101 a) 0) (0)) 0))
         (10110001 (00000110 a)))))))(00001001 answer-and
  (00001000 (a b)
    (00000111
      ((equal? (00000010 a) ()) (00000111
         ((equal? (00000010 b) ()) (00000001 ()))
         ((00000010 b) 
          (00000111
            ((equal? (00000011 (00000101 b) 0) (1)) b)
            ((00000011 (00000101 b) 0)  (00000001 ()))))))
      ((00000010 a) 
       (00000111
         ((equal? (00000010 b) ()) (00000111
            ((equal? (00000011 (00000101 a) 0) (1)) a)
            ((00000011 (00000101 a) 0)  (00000001 ()))))
         ((00000010 b) 
          (00000111
            ((00000011 (00000101 a) (00000101 b)) 
             (00000111
               ((equal? (00000011 (00000101 a) 0) (1)) a)
               ((equal? (00000011 (00000101 a) 0) (0)) b)))
            ((00000011 (00000101 a) (00000101 b)) 
             (00000111
               ((equal? (00000010 (00000110 a)) ()) (00000111
                  ((equal? (00000011 (00000101 a) 0) (1)) a)
                  ((equal? (00000011 (00000101 a) 0) (0)) b)))
               ((equal? (00000010 (00000110 b)) ()) (00000111
                  ((equal? (00000011 (00000101 b) 0) (1)) b)
                  ((equal? (00000011 (00000101 b) 0) (0)) a)))
               ((00000010 (00000110 b)) 
                (00000100 (00000101 a)
                          (10110010 (00000110 a) (00000110 b)))))))))))))(00001001 answer-or
  (00001000 (a b)
    (10110001 (10110010 (10110001 a) (10110001 b)))))(00001001 answer-weaken
  (00001000 (a)
    (00000111
      ((equal? (00000010 a) ()) (00000001 ()))
      ((00000010 a) 
       (00000111
         ((00000011 (00101000 a) 7)  (00000001 ()))
         ((00000011 (00101000 a) 7) 
          (00000100 (00000101 a) a)))))))(00001001 answer-atom
  (00001000 (x)
    (00000111
      ((00000010 x)  (00000001 (1)))
      ((00000010 x)  (00000001 (0)))
      ((equal? (00000010 x) ()) (00000001 ())))))(00001001 answer-eq
  (00001000 (a b)
    (00000111
      ((00000011 a b)  (00000001 (1)))
      ((00000011 a b)  (00000001 (0))))))