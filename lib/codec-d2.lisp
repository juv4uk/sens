; lib/codec-d2.lisp — структурний кодек, написаний SENS-ом.
;
; encode: дерево -> плаский потік токенів із D2-межами (codec-open / codec-close).
; decode: плаский потік -> дерево.
; codec-roundtrip(x) = decode(encode(x)) і мусить дорівнювати x.
;
; Використано ЛИШЕ дозволене ядро: D3 QUOTE/ATOM/EQ/CAR/CDR/COND/CONS та
; D4 LAMBDA/DEFINE. Жодного нового закону не введено; жодного числа не вжито.
;
; Це НЕ байтовий T5-кодек: ядро не допускає бітових/байтових операцій, тому
; байтовий шар лишається за Rust/Zig-кодеком. Це структурна половина — саме та
; межа, яку SENS сьогодні виражає сам.

(0011 codec-open (001 codec-open))
(0011 codec-close (001 codec-close))

(0011 codec-encode
  (0010 (x acc)
    (110
      ((010 x)
       (111 x acc))
      (#d1:1
       (111 codec-open
         (codec-encode (100 x)
           (codec-encode (011 x)
             (111 codec-close acc))))))))

(0011 codec-decode (0010 (tokens) (110 ((101 (100 tokens) codec-open) ((0010 (r1) ((0010 (v1) ((0010 (r2) (111 (111 v1 (100 (codec-decode r2))) (011 (011 (codec-decode r2))))) (011 r1))) (100 r1))) (codec-decode (011 tokens)))) (#d1:1 (111 (100 tokens) (011 tokens))))))

(0011 codec-roundtrip
  (0010 (x)
    (100 (codec-decode (codec-encode x ())))))
