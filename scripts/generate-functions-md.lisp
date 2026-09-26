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

(def tracked
  (quote ("result-status.lisp" "narrate.lisp" "translation.lisp" "quantity.lisp" "si.lisp")))

(def reference-path "docs/FUNCTIONS.md")

(def str+
  (lambda args
    (reduce (lambda (acc s) (string-append acc s)) "" args)))

(def definition-head?
  (lambda (head)
    (cond
      ((equal? head (quote def)) (1) t)
      ((equal? head (quote define)) (1) t)
      ((equal? head 00001001) (1) t)
      ((equal? head 00001011) (1) t)
      (t t (quote ())))))

(def defined-names
  (lambda (forms)
    (cond
      ((atom? forms) () (quote ()))
      ((atom? forms) (0)
       (cond
         ((atom? (car forms)) (0)
          (cond
            ((definition-head? (car (car forms))) t
             (cons (symbol->string (second (car forms)))
                   (defined-names (cdr forms))))
            (t t (defined-names (cdr forms)))))
         (t t (defined-names (cdr forms))))))))

(def count-items
  (lambda (items)
    (cond
      ((atom? items) () 0)
      ((atom? items) (0) (+ 1 (count-items (cdr items)))))))

(def backtick-join
  (lambda (names)
    (cond
      ((atom? names) () "")
      ((atom? names) (0)
       (cond
         ((atom? (cdr names)) () (str+ "`" (car names) "`"))
         ((atom? (cdr names)) (0)
          (str+ "`" (car names) "`, " (backtick-join (cdr names)))))))))

(def render-section
  (lambda (file)
    (let ((names (defined-names (read-all (read-file (str+ "lib/" file))))))
      (str+ "### " file " (" (number->string (count-items names)) ")\n\n"
            (backtick-join names) "\n"))))

; Позиція першого входження marker у s, починаючи з i; -1 якщо нема.
(def pos-of
  (lambda (s marker i)
    (cond
      ((string-empty? s) (1) -1)
      ((string-prefix? marker s) t i)
      (t t (pos-of (string-rest s) marker (+ i 1))))))

; string-length у ядрі — нехвостова рекурсія (переповнює стек на довгому
; документі); string-slice сам обрізає кінець до довжини рядка.
(def to-end 1000000000)

(def slice-from
  (lambda (s i)
    (string-slice s i to-end)))

; Замінює розділ файлу: від «### файл (» до наступного «\n### » (або кінця).
(def replace-section
  (lambda (doc file)
    (let ((marker (str+ "### " file " (")))
      (let ((start (pos-of doc marker 0)))
        (cond
          ((< start 0) 1 (car (quote ())))
          ((< start 0) 0
           (let ((after (+ start (string-length marker))))
             (let ((offset (pos-of (slice-from doc after) "\n### " 0)))
               (let ((end (cond
                            ((< offset 0) 1 to-end)
                            ((< offset 0) 0 (+ after offset)))))
                 (str+ (string-slice doc 0 start)
                       (render-section file)
                       (slice-from doc end)))))))))))

(def replace-all
  (lambda (doc files)
    (cond
      ((atom? files) () doc)
      ((atom? files) (0) (replace-all (replace-section doc (car files)) (cdr files))))))

(def current (read-file reference-path))
(def generated (replace-all current tracked))

(cond
  ((atom? *argv*)
   ()
   (second
     (list
       (write-file reference-path generated)
       (print "docs/FUNCTIONS.md sections refreshed"))))
  ((equal? (car *argv*) "--check")
   (1)
   (cond
     ((equal? current generated) (1) (print "docs/FUNCTIONS.md sections are current"))
     ((equal? current generated) (0)
      (second
        (list
          (print "docs/FUNCTIONS.md sections are stale")
          (car (quote ())))))))
  (t t
   (second
     (list
       (write-file reference-path generated)
       (print "docs/FUNCTIONS.md sections refreshed")))))
