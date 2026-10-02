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

(00001001 tracked
  (00000001 ("result-status.lisp" "narrate.lisp" "translation.lisp" "quantity.lisp" "si.lisp")))

(00001001 reference-path "docs/FUNCTIONS.md")

(00001001 str+
  (00001000 args
    (00111001 (00001000 (acc s) (00111010 acc s)) "" args)))

; Exact D1 helpers for documentation-generator control only.
(00001001 functions-predicate-yes
  (00001000 ()
    (00000010 (00000001 ()))))

(00001001 functions-predicate-no
  (00001000 ()
    (00000010 (00000001 (00000000)))))

(00001001 functions-empty-list?
  (00001000 (value)
    (00100010 value (00000001 ()))))

(00001001 functions-pair?
  (00001000 (value)
    (00000111
      ((00000010 value) (functions-predicate-no))
      ((functions-predicate-yes) (functions-predicate-yes)))))

(00001001 definition-head?
  (00001000 (head)
    (00000111
      ((00100010 head (00000001 def)) (functions-predicate-yes))
      ((00100010 head (00000001 define)) (functions-predicate-yes))
      ((00100010 head 00001001) (functions-predicate-yes))
      ((00100010 head 00001011) (functions-predicate-yes))
      ((functions-predicate-yes) (functions-predicate-no)))))

(00001001 defined-names
  (00001000 (forms)
    (00000111
      ((functions-empty-list? forms) (00000001 ()))
      ((functions-pair? forms)
       (00000111
         ((functions-pair? (00000101 forms))
          (00000111
            ((definition-head? (00000101 (00000101 forms)))
             (00000100 (01000010 (00101111 (00000101 forms)))
                   (defined-names (00000110 forms))))
            ((functions-predicate-yes)
             (defined-names (00000110 forms)))))
         ((functions-predicate-yes)
          (defined-names (00000110 forms))))))))

(00001001 count-items
  (00001000 (items)
    (00000111
      ((functions-empty-list? items) 0)
      ((functions-pair? items) (00001100 1 (count-items (00000110 items)))))))

; Markdown is human presentation. number->string owns canonical machine
; numeric wire, so it must not render human section counts.  Build decimal
; radix ten only from base-neutral single-bit numeric source; this generator
; must not create new numeric-reader migration debt.
(00001001 functions-md-decimal-radix
  (00001100 1 1 1 1 1 1 1 1 1 1))

; Use only two-part COND with EQ.  On current main EQ yields the existing
; answer carrier; on the PredicateBit runtime it yields the one-bit carrier.
; That keeps this human-presentation helper valid across the active migration.
(00001001 decimal-count->string-onto
  (00001000 (n acc)
    (00000111
      ((00000011 n 0) acc)
      ((00000011 0 0)
       (decimal-count->string-onto
         (00010100 n functions-md-decimal-radix)
         (00111010
           (01000111 (00010011 n functions-md-decimal-radix))
           acc))))))

(00001001 decimal-count->string
  (00001000 (n)
    (00000111
      ((00000011 n 0) "0")
      ((00000011 0 0) (decimal-count->string-onto n "")))))

(00001001 backtick-join
  (00001000 (names)
    (00000111
      ((functions-empty-list? names) "")
      ((functions-pair? names)
       (00000111
         ((functions-empty-list? (00000110 names)) (str+ "`" (00000101 names) "`"))
         ((functions-pair? (00000110 names))
          (str+ "`" (00000101 names) "`, " (backtick-join (00000110 names)))))))))

(00001001 render-section
  (00001000 (file)
    (10011100 ((names (defined-names (01001011 (10100110 (str+ "lib/" file))))))
      (str+ "### " file " (" (decimal-count->string (count-items names)) ")\n\n"
            (backtick-join names) "\n"))))

; Позиція першого входження marker у s, починаючи з i; -1 якщо нема.
(00001001 pos-of
  (00001000 (s marker i)
    (00000111
      ((00111100 s) -1)
      ((00111101 marker s) i)
      ((functions-predicate-yes) (pos-of (01000000 s) marker (00001100 i 1))))))

; string-length у ядрі — нехвостова рекурсія (переповнює стек на довгому
; документі); string-slice сам обрізає кінець до довжини рядка.
(00001001 to-end 1000000000)

(00001001 slice-from
  (00001000 (s i)
    (01000001 s i to-end)))

; Замінює розділ файлу: від «### файл (» до наступного «\n### » (або кінця).
(00001001 replace-section
  (00001000 (doc file)
    (10011100 ((marker (str+ "### " file " (")))
      (10011100 ((start (pos-of doc marker 0)))
        (00000111
          ((00011010 start 0) (00000101 (00000001 ())))
          ((functions-predicate-yes)
           (10011100 ((after (00001100 start (00111011 marker))))
             (10011100 ((offset (pos-of (slice-from doc after) "\n### " 0)))
               (10011100 ((end (00000111
                            ((00011010 offset 0) to-end)
                            ((functions-predicate-yes) (00001100 after offset)))))
                 (str+ (01000001 doc 0 start)
                       (render-section file)
                       (slice-from doc end)))))))))))

(00001001 replace-all
  (00001000 (doc files)
    (00000111
      ((functions-empty-list? files) doc)
      ((functions-pair? files) (replace-all (replace-section doc (00000101 files)) (00000110 files))))))

(00001001 current (10100110 reference-path))
(00001001 generated (replace-all current tracked))

(00000111
  ((functions-empty-list? *argv*)
   (00101111
     (00100111
       (10100111 reference-path generated)
       (01001000 "docs/FUNCTIONS.md sections refreshed"))))
  ((00100010 (00000101 *argv*) "--check")
   (00000111
     ((00100010 current generated) (01001000 "docs/FUNCTIONS.md sections are current"))
     ((functions-predicate-yes)
      (00101111
        (00100111
          (01001000 "docs/FUNCTIONS.md sections are stale")
          (00000101 (00000001 ())))))))
  ((functions-predicate-yes)
   (00101111
     (00100111
       (10100111 reference-path generated)
       (01001000 "docs/FUNCTIONS.md sections refreshed")))))