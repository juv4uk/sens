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

(00001001 definition-head?
  (00001000 (head)
    (00000111
      ((00100010 head (00000001 def)) (1) t)
      ((00100010 head (00000001 define)) (1) t)
      ((00100010 head 00001001) (1) t)
      ((00100010 head 00001011) (1) t)
      (t t (00000001 ())))))

(00001001 defined-names
  (00001000 (forms)
    (00000111
      ((00000010 forms) () (00000001 ()))
      ((00000010 forms) (0)
       (00000111
         ((00000010 (00000101 forms)) (0)
          (00000111
            ((definition-head? (00000101 (00000101 forms))) t
             (00000100 (01000010 (00101111 (00000101 forms)))
                   (defined-names (00000110 forms))))
            (t t (defined-names (00000110 forms)))))
         (t t (defined-names (00000110 forms))))))))

(00001001 count-items
  (00001000 (items)
    (00000111
      ((00000010 items) () 0)
      ((00000010 items) (0) (00001100 1 (count-items (00000110 items)))))))

; Markdown is human presentation. 01000110 number->string is the canonical
; machine wire (#q2:<bits>/1), so it must not render section counts.
; Counts are non-negative integers; derive their decimal spelling locally
; from the existing digit/quotient/remainder functions.  (00001100 5 5)
; spells decimal ten without depending on a future reader interpretation of
; the ambiguous source token 10.
(00001001 decimal-count->string
  (00001000 (n)
    (00000111
      ((00011010 n (00001100 5 5)) (1) (01000111 n))
      ((00011010 n (00001100 5 5)) (0)
       (00111010
         (decimal-count->string (00010100 n (00001100 5 5)))
         (01000111 (00010011 n (00001100 5 5))))))))

(00001001 backtick-join
  (00001000 (names)
    (00000111
      ((00000010 names) () "")
      ((00000010 names) (0)
       (00000111
         ((00000010 (00000110 names)) () (str+ "`" (00000101 names) "`"))
         ((00000010 (00000110 names)) (0)
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
      ((00111100 s) (1) -1)
      ((00111101 marker s) t i)
      (t t (pos-of (01000000 s) marker (00001100 i 1))))))

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
          ((00011010 start 0) 1 (00000101 (00000001 ())))
          ((00011010 start 0) 0
           (10011100 ((after (00001100 start (00111011 marker))))
             (10011100 ((offset (pos-of (slice-from doc after) "\n### " 0)))
               (10011100 ((end (00000111
                            ((00011010 offset 0) 1 to-end)
                            ((00011010 offset 0) 0 (00001100 after offset)))))
                 (str+ (01000001 doc 0 start)
                       (render-section file)
                       (slice-from doc end)))))))))))

(00001001 replace-all
  (00001000 (doc files)
    (00000111
      ((00000010 files) () doc)
      ((00000010 files) (0) (replace-all (replace-section doc (00000101 files)) (00000110 files))))))

(00001001 current (10100110 reference-path))
(00001001 generated (replace-all current tracked))

(00000111
  ((00000010 *argv*)
   ()
   (00101111
     (00100111
       (10100111 reference-path generated)
       (01001000 "docs/FUNCTIONS.md sections refreshed"))))
  ((00100010 (00000101 *argv*) "--check")
   (1)
   (00000111
     ((00100010 current generated) (1) (01001000 "docs/FUNCTIONS.md sections are current"))
     ((00100010 current generated) (0)
      (00101111
        (00100111
          (01001000 "docs/FUNCTIONS.md sections are stale")
          (00000101 (00000001 ())))))))
  (t t
   (00101111
     (00100111
       (10100111 reference-path generated)
       (01001000 "docs/FUNCTIONS.md sections refreshed")))))