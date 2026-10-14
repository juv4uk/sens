; lib/codec-d2.lisp — кодек SENS-ом, СУМІСНИЙ з D2-порядком T5.
;
; D2-закон (контракт): 00 separator, 01 close, 10 open, 11 dot.
; Тут ці слова названо d2-sep/d2-close/d2-open/d2-dot: mixed-читач .lisp читає голе
; 01/00 як ДЕСЯТКОВЕ число, тож D2-слово як дані виражається лише в канонічному
; бінарному джерелі. Порядок — точний T5; атоми — підстановні (1:1 до 00/01/10/11).
; encode(дерево) -> точний D2-потік слів, як його несе канонічний T5.
; decode(потік)  -> дерево; t5-roundtrip = decode∘encode.
;
; Лише дозволене ядро: D3 QUOTE/ATOM/EQ/CAR/CDR/COND/CONS + D4 LAMBDA/DEFINE.
; Жодного нового закону. Це СТРУКТУРНИЙ шар; байтовий T5 лишається за Rust/Zig.

(0011 d2-open  (001 d2-open))
(0011 d2-close (001 d2-close))
(0011 d2-sep   (001 d2-sep))
(0011 d2-dot   (001 d2-dot))
(0011 d3-empty (001 ()))

(0011 t5-enc
  (0010 (x acc)
    (110
      ((010 x)
       (111 x acc))
      ((101 (001 t) (001 t))
       (111 d2-open (t5-spine x (111 d2-close acc)))))))

(0011 t5-spine
  (0010 (s acc)
    (110
      ((010 s)
       (110
         ((101 s d3-empty) acc)
         ((101 (001 t) (001 t)) (111 d2-dot (t5-enc s acc)))))
      ((101 (001 t) (001 t))
       ((0010 (tail)
          (110
            ((010 (011 s))
             (t5-enc (100 s) tail))
            ((101 (001 t) (001 t))
             (t5-enc (100 s) (111 d2-sep tail)))))
        (t5-spine (011 s) acc))))))

(0011 t5-encode
  (0010 (x)
    (t5-enc x ())))

(0011 t5-rev
  (0010 (x acc)
    (110
      ((010 x) acc)
      ((101 (001 t) (001 t)) (t5-rev (011 x) (111 (100 x) acc))))))

(0011 t5-dec
  (0010 (tokens)
    (110
      ((101 (100 tokens) d2-open)
       (t5-dec-form (011 tokens) ()))
      ((101 (001 t) (001 t))
       (111 (100 tokens) (011 tokens))))))

(0011 t5-dec-form
  (0010 (tokens elems)
    (110
      ((101 (100 tokens) d2-close)
       (111 (t5-rev elems ()) (011 tokens)))
      ((101 (100 tokens) d2-sep)
       (t5-dec-form (011 tokens) elems))
      ((101 (100 tokens) d2-dot)
       ((0010 (d)
          (111 (t5-dot-tail (t5-rev elems ()) (100 d)) (011 d)))
        (t5-dec (011 tokens))))
      ((101 (001 t) (001 t))
       ((0010 (d)
          (t5-dec-form (011 d) (111 (100 d) elems)))
        (t5-dec tokens))))))

(0011 t5-dot-tail
  (0010 (lst tail)
    (110
      ((010 lst) tail)
      ((101 (001 t) (001 t)) (111 (100 lst) (t5-dot-tail (011 lst) tail))))))

(0011 t5-decode
  (0010 (tokens)
    (100 (t5-dec tokens))))

(0011 t5-roundtrip
  (0010 (x)
    (t5-decode (t5-encode x))))
