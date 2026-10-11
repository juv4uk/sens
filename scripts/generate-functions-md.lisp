; Оновлює розділи docs/FUNCTIONS.md для відстежуваних файлів lib/:
; «### файл (N)» і перелік визначених назв. Заміна `cargo xtask
; gen-functions-md` (Rust) — тепер мовою.
;
; Визначення читаються як дані (read-all), а не пошуком рядків: форма
; верхнього рівня з головою def, define або кодом 00001001/00001011.
; Тому файли, переписані на коди СЕНС, рахуються так само.
;
; Usage:
;   sens scripts/generate-functions-md.lisp          — переписати розділи
;   sens scripts/generate-functions-md.lisp --check  — лише перевірити

(0011 tracked
  (001 ("result-status.lisp" "narrate.lisp" "translation.lisp" "quantity.lisp" "si.lisp")))

(0011 reference-path "docs/FUNCTIONS.md")

(0011 str+
  (0010 args
    (101110 (0010 (acc s) (110011110 acc s)) "" args)))

(0011 definition-head?
  (0010 (head)
    (110
      ((11110111 head (001 def)) (1) t)
      ((11110111 head (001 define)) (1) t)
      ((11110111 head 00001001) (1) t)
      ((11110111 head 00001011) (1) t)
      (t t (001 ())))))

(0011 defined-names
  (0010 (forms)
    (110
      ((010 forms) () (001 ()))
      ((010 forms) (0)
       (110
         ((010 (100 forms)) (0)
          (110
            ((definition-head? (100 (100 forms))) t
             (111 (11101110 (1001 (100 forms)))
                   (defined-names (011 forms))))
            (t t (defined-names (011 forms)))))
         (t t (defined-names (011 forms))))))))

(0011 count-items
  (0010 (items)
    (110
      ((010 items) () 0)
      ((010 items) (0) (01010 1 (count-items (011 items)))))))

; Markdown is human presentation. number->string owns canonical machine
; numeric wire, so it must not render human section counts.  Build decimal
; radix ten only from base-neutral single-bit numeric source; this generator
; must not create new numeric-reader migration debt.
(0011 functions-md-decimal-radix
  (01010 1 1 1 1 1 1 1 1 1 1))

; Use only two-part COND with EQ.  On current main EQ yields the existing
; answer carrier; on the PredicateBit runtime it yields the one-bit carrier.
; That keeps this human-presentation helper valid across the active migration.
(0011 decimal-count->string-onto
  (0010 (n acc)
    (110
      ((101 n 0) acc)
      ((101 0 0)
       (decimal-count->string-onto
         (10111 n functions-md-decimal-radix)
         (110011110
           (01000111 (00101100 n functions-md-decimal-radix))
           acc))))))

(0011 decimal-count->string
  (0010 (n)
    (110
      ((101 n 0) "0")
      ((101 0 0) (decimal-count->string-onto n "")))))

(0011 backtick-join
  (0010 (names)
    (110
      ((010 names) () "")
      ((010 names) (0)
       (110
         ((010 (011 names)) () (str+ "`" (100 names) "`"))
         ((010 (011 names)) (0)
          (str+ "`" (100 names) "`, " (backtick-join (011 names)))))))))

(0011 render-section
  (0010 (file)
    (001000 ((names (defined-names (110101001 (110110111 (str+ "lib/" file))))))
      (str+ "### " file " (" (decimal-count->string (count-items names)) ")\n\n"
            (backtick-join names) "\n"))))

; Позиція першого входження marker у s, починаючи з i; -1 якщо нема.
(0011 pos-of
  (0010 (s marker i)
    (110
      ((110011100 s) (1) -1)
      ((110101010 marker s) t i)
      (t t (pos-of (110011101 s) marker (01010 i 1))))))

; string-length у ядрі — нехвостова рекурсія (переповнює стек на довгому
; документі); string-slice сам обрізає кінець до довжини рядка.
(0011 to-end 1000000000)

(0011 slice-from
  (0010 (s i)
    (110100011 s i to-end)))

; Замінює розділ файлу: від «### файл (» до наступного «\n### » (або кінця).
(0011 replace-section
  (0010 (doc file)
    (001000 ((marker (str+ "### " file " (")))
      (001000 ((start (pos-of doc marker 0)))
        (110
          ((11010 start 0) 1 (100 (001 ())))
          ((11010 start 0) 0
           (001000 ((after (01010 start (110100010 marker))))
             (001000 ((offset (pos-of (slice-from doc after) "\n### " 0)))
               (001000 ((end (110
                            ((11010 offset 0) 1 to-end)
                            ((11010 offset 0) 0 (01010 after offset)))))
                 (str+ (110100011 doc 0 start)
                       (render-section file)
                       (slice-from doc end)))))))))))

(0011 replace-all
  (0010 (doc files)
    (110
      ((010 files) () doc)
      ((010 files) (0) (replace-all (replace-section doc (100 files)) (011 files))))))

(0011 current (110110111 reference-path))
(0011 generated (replace-all current tracked))

(110
  ((010 *argv*)
   ()
   (1001
     (1110
       (110111100 reference-path generated)
       (11011011 "docs/FUNCTIONS.md sections refreshed"))))
  ((11110111 (100 *argv*) "--check")
   (1)
   (110
     ((11110111 current generated) (1) (11011011 "docs/FUNCTIONS.md sections are current"))
     ((11110111 current generated) (0)
      (1001
        (1110
          (11011011 "docs/FUNCTIONS.md sections are stale")
          (100 (001 ())))))))
  (t t
   (1001
     (1110
       (110111100 reference-path generated)
       (11011011 "docs/FUNCTIONS.md sections refreshed")))))