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

(визначити tracked
  (як-є ("result-status.lisp" "narrate.lisp" "translation.lisp" "quantity.lisp" "si.lisp")))

(визначити reference-path "docs/FUNCTIONS.md")

(визначити str+
  (функція args
    (101110 (0010 (acc s) (110011110 acc s)) "" args)))

(визначити definition-head?
  (функція (head)
    (за-умовою
      ((11110111 head (001 def)) (1) t)
      ((11110111 head (001 define)) (1) t)
      ((11110111 head 00001001) (1) t)
      ((11110111 head 00001011) (1) t)
      (t t (як-є ())))))

(визначити defined-names
  (функція (forms)
    (за-умовою
      ((010 forms) () (001 ()))
      ((010 forms) (0)
       (за-умовою
         ((010 (100 forms)) (0)
          (за-умовою
            ((definition-head? (100 (100 forms))) t
             (111 (11101110 (1001 (100 forms)))
                   (defined-names (решта forms))))
            (t t (defined-names (решта forms)))))
         (t t (defined-names (решта forms))))))))

(визначити count-items
  (функція (items)
    (за-умовою
      ((010 items) () 0)
      ((010 items) (0) (01010 1 (count-items (011 items)))))))

; Markdown is human presentation. number->string owns canonical machine
; numeric wire, so it must not render human section counts.  Build decimal
; radix ten only from base-neutral single-bit numeric source; this generator
; must not create new numeric-reader migration debt.
(визначити functions-md-decimal-radix
  (01010 1 1 1 1 1 1 1 1 1 1))

; Use only two-part COND with EQ.  On current main EQ yields the existing
; answer carrier; on the PredicateBit runtime it yields the one-bit carrier.
; That keeps this human-presentation helper valid across the active migration.
(визначити decimal-count->string-onto
  (функція (n acc)
    (за-умовою
      ((101 n 0) acc)
      ((101 0 0)
       (decimal-count->string-onto
         (10111 n functions-md-decimal-radix)
         (110011110
           (01000111 (00101100 n functions-md-decimal-radix))
           acc))))))

(визначити decimal-count->string
  (функція (n)
    (за-умовою
      ((101 n 0) "0")
      ((101 0 0) (decimal-count->string-onto n "")))))

(визначити backtick-join
  (функція (names)
    (за-умовою
      ((010 names) () "")
      ((010 names) (0)
       (за-умовою
         ((010 (011 names)) () (str+ "`" (100 names) "`"))
         ((010 (011 names)) (0)
          (str+ "`" (перше names) "`, " (backtick-join (решта names)))))))))

(визначити render-section
  (функція (file)
    (001000 ((names (defined-names (110101001 (110110111 (str+ "lib/" file))))))
      (str+ "### " file " (" (decimal-count->string (count-items names)) ")\n\n"
            (backtick-join names) "\n"))))

; Позиція першого входження marker у s, починаючи з i; -1 якщо нема.
(визначити pos-of
  (функція (s marker i)
    (за-умовою
      ((110011100 s) (1) -1)
      ((110101010 marker s) t i)
      (t t (pos-of (110011101 s) marker (01010 i 1))))))

; string-length у ядрі — нехвостова рекурсія (переповнює стек на довгому
; документі); string-slice сам обрізає кінець до довжини рядка.
(визначити to-end 1000000000)

(визначити slice-from
  (функція (s i)
    (110100011 s i to-end)))

; Замінює розділ файлу: від «### файл (» до наступного «\n### » (або кінця).
(визначити replace-section
  (функція (doc file)
    (001000 ((marker (str+ "### " file " (")))
      (001000 ((start (pos-of doc marker 0)))
        (за-умовою
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

(визначити replace-all
  (функція (doc files)
    (за-умовою
      ((010 files) () doc)
      ((010 files) (0) (replace-all (replace-section doc (100 files)) (011 files))))))

(0011 current (110110111 reference-path))
(визначити generated (replace-all current tracked))

(за-умовою
  ((010 *argv*)
   ()
   (друге
     (список
       (110111100 reference-path generated)
       (11011011 "docs/FUNCTIONS.md sections refreshed"))))
  ((11110111 (100 *argv*) "--check")
   (1)
   (за-умовою
     ((11110111 current generated) (1) (11011011 "docs/FUNCTIONS.md sections are current"))
     ((11110111 current generated) (0)
      (друге
        (список
          (11011011 "docs/FUNCTIONS.md sections are stale")
          (перше (як-є ())))))))
  (t t
   (друге
     (список
       (110111100 reference-path generated)
       (11011011 "docs/FUNCTIONS.md sections refreshed")))))