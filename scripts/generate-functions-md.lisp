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
    (згорнути (функція (acc s) (рядок-додати acc s)) "" args)))

(визначити definition-head?
  (функція (head)
    (за-умовою
      ((однакові? head (як-є def)) (1) t)
      ((однакові? head (як-є define)) (1) t)
      ((однакові? head 00001001) (1) t)
      ((однакові? head 00001011) (1) t)
      (t t (як-є ())))))

(визначити defined-names
  (функція (forms)
    (за-умовою
      ((атом? forms) () (як-є ()))
      ((атом? forms) (0)
       (за-умовою
         ((атом? (перше forms)) (0)
          (за-умовою
            ((definition-head? (перше (перше forms))) t
             (сполучити (символ-у-текст (друге (перше forms)))
                   (defined-names (решта forms))))
            (t t (defined-names (решта forms)))))
         (t t (defined-names (решта forms))))))))

(визначити count-items
  (функція (items)
    (за-умовою
      ((атом? items) () 0)
      ((атом? items) (0) (додати 1 (count-items (решта items)))))))

; Markdown is human presentation. number->string owns canonical machine
; numeric wire, so it must not render human section counts.  Build decimal
; radix ten only from base-neutral single-bit numeric source; this generator
; must not create new numeric-reader migration debt.
(визначити functions-md-decimal-radix
  (додати 1 1 1 1 1 1 1 1 1 1))

; Use only two-part COND with EQ.  On current main EQ yields the existing
; answer carrier; on the PredicateBit runtime it yields the one-bit carrier.
; That keeps this human-presentation helper valid across the active migration.
(визначити decimal-count->string-onto
  (функція (n acc)
    (за-умовою
      ((тотожне? n 0) acc)
      ((тотожне? 0 0)
       (decimal-count->string-onto
         (частка n functions-md-decimal-radix)
         (рядок-додати
           (відобразити-доки-істина (модульна-остача n functions-md-decimal-radix))
           acc))))))

(визначити decimal-count->string
  (функція (n)
    (за-умовою
      ((тотожне? n 0) "0")
      ((тотожне? 0 0) (decimal-count->string-onto n "")))))

(визначити backtick-join
  (функція (names)
    (за-умовою
      ((атом? names) () "")
      ((атом? names) (0)
       (за-умовою
         ((атом? (решта names)) () (str+ "`" (перше names) "`"))
         ((атом? (решта names)) (0)
          (str+ "`" (перше names) "`, " (backtick-join (решта names)))))))))

(визначити render-section
  (функція (file)
    (нехай ((names (defined-names (читати-всі (читати-файл (str+ "lib/" file))))))
      (str+ "### " file " (" (decimal-count->string (count-items names)) ")\n\n"
            (backtick-join names) "\n"))))

; Позиція першого входження marker у s, починаючи з i; -1 якщо нема.
(визначити pos-of
  (функція (s marker i)
    (за-умовою
      ((рядок-порожній? s) (1) -1)
      ((рядок-префікс? marker s) t i)
      (t t (pos-of (рядок-решта s) marker (додати i 1))))))

; string-length у ядрі — нехвостова рекурсія (переповнює стек на довгому
; документі); string-slice сам обрізає кінець до довжини рядка.
(визначити to-end 1000000000)

(визначити slice-from
  (функція (s i)
    (рядок-зріз s i to-end)))

; Замінює розділ файлу: від «### файл (» до наступного «\n### » (або кінця).
(визначити replace-section
  (функція (doc file)
    (нехай ((marker (str+ "### " file " (")))
      (нехай ((start (pos-of doc marker 0)))
        (за-умовою
          ((менше? start 0) 1 (перше (як-є ())))
          ((менше? start 0) 0
           (нехай ((after (додати start (рядок-довжина marker))))
             (нехай ((offset (pos-of (slice-from doc after) "\n### " 0)))
               (нехай ((end (за-умовою
                            ((менше? offset 0) 1 to-end)
                            ((менше? offset 0) 0 (додати after offset)))))
                 (str+ (рядок-зріз doc 0 start)
                       (render-section file)
                       (slice-from doc end)))))))))))

(визначити replace-all
  (функція (doc files)
    (за-умовою
      ((атом? files) () doc)
      ((атом? files) (0) (replace-all (replace-section doc (перше files)) (решта files))))))

(визначити current (читати-файл reference-path))
(визначити generated (replace-all current tracked))

(за-умовою
  ((атом? *argv*)
   ()
   (друге
     (список
       (записати-файл reference-path generated)
       (друкувати "docs/FUNCTIONS.md sections refreshed"))))
  ((однакові? (перше *argv*) "--check")
   (1)
   (за-умовою
     ((однакові? current generated) (1) (друкувати "docs/FUNCTIONS.md sections are current"))
     ((однакові? current generated) (0)
      (друге
        (список
          (друкувати "docs/FUNCTIONS.md sections are stale")
          (перше (як-є ())))))))
  (t t
   (друге
     (список
       (записати-файл reference-path generated)
       (друкувати "docs/FUNCTIONS.md sections refreshed")))))