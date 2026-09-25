;; A1 pilot FINAL — per-program symbol extractor (single-line forms).
;; Usage (з кореня fpga-lisp):
;;   my-lisp scripts/program-symbol-table.lisp bootstrap_add_demo.asm fpga/asm/constants.inc
;; Вивід: count, потім "<id> <name>" на рядок.

(def nil-marker (quote ()))

(def pos-of (lambda (s marker i) (cond ((string-empty? s) -1) ((string-prefix? marker s) i) (t (pos-of (string-rest s) marker (+ i 1))))))

(def has (lambda (s m) (not? (= (pos-of s m 0) -1))))

(def slice-from (lambda (s i) (string-slice s i (string-length s))))

(def digit? (lambda (c) (has "0123456789" c)))

(def skip-ws (lambda (s) (cond ((string-prefix? " " s) (skip-ws (slice-from s 1))) (t s))))

(def word-digits (lambda (s i) (cond ((>= i (string-length s)) "") ((digit? (string-slice s i (+ i 1))) (string-append (string-slice s i (+ i 1)) (word-digits s (+ i 1)))) (t ""))))

(def word-nonspace (lambda (s i) (cond ((>= i (string-length s)) "") ((has " " (string-first s)) "") (t (string-append (string-first s) (word-nonspace s (+ i 1)))))))

(def split-lines (lambda (s) (cond ((= (pos-of s "\n" 0) -1) 1 (cons s (quote ()))) ((= (pos-of s "\n" 0) -1) 0 (cons (string-slice s 0 (pos-of s "\n" 0)) (split-lines (slice-from s (+ 1 (pos-of s "\n" 0)))))))))

(def reverse-acc (lambda (lst acc) (cond ((atom? lst) acc) (t (reverse-acc (cdr lst) (cons (car lst) acc))))))

(def count-lst (lambda (lst) (cond ((atom? lst) 0) (t (+ 1 (count-lst (cdr lst)))))))

(def asm-id (lambda (line) (cond ((has line "LOADSYM") (word-digits (slice-from line (+ 2 (pos-of line ", " 0))) 0)) (t ""))))

(def asm-name (lambda (line) (cond ((has line "; '") (word-nonspace (slice-from line (+ 3 (pos-of line "; '" 0))) 0)) (t ""))))

(def keep-pair (lambda (id name acc) (cond ((string-empty? id) acc) ((string-empty? name) acc) (t (cons (cons id name) acc)))))

(def process-asm-line (lambda (line acc) (keep-pair (asm-id line) (asm-name line) acc)))

(def process-lines-asm (lambda (lines acc) (cond ((atom? lines) acc) (t (process-lines-asm (cdr lines) (process-asm-line (car lines) acc))))))

(def inc-name (lambda (line) (word-nonspace (slice-from line 12) 0)))

(def probe
  (lambda (tag value)
    (cons (print (string-append tag (write-to-string value))) value)))

(def inc-id
  (lambda (line)
    (let ((name (probe "name=" (inc-name line))))
      (let ((tail (probe "tail=" (skip-ws (slice-from line (+ 12 (string-length name))) 0))))
        (word-digits tail 0)))))

(def process-define-line (lambda (line acc) (keep-pair (inc-id line) (inc-name line) acc)))

(def process-lines-inc (lambda (lines acc) (cond ((atom? lines) acc) (t (process-lines-inc (cdr lines) (process-define-line (car lines) acc))))))

(def str-eq? (lambda (a b) (cond ((string-prefix? a b) (string-prefix? b a)) (t nil-marker))))

(def id-in-base? (lambda (id base) (cond ((atom? base) nil-marker) ((str-eq? id (car (car base))) t-marker) (t (id-in-base? id (cdr base))))))

(def merge-pair (lambda (pair base) (cond ((id-in-base? (car pair) base) base) (t (cons pair base)))))

(def merge-all (lambda (pairs base) (cond ((atom? pairs) base) (t (merge-all (cdr pairs) (merge-pair (car pairs) base))))))

(def emit-all (lambda (lst) (cond ((atom? lst) (quote ())) (t (cons (print (string-append (string-append (car (car lst)) " ") (cdr (car lst))))) (emit-all (cdr lst))))))

(def main (lambda (asm-path inc-path) (let ((asm-pairs (reverse-acc (process-lines-asm (split-lines (read-file asm-path)) (quote ())) (quote ())))) (let ((inc-pairs (reverse-acc (process-lines-inc (split-lines (read-file inc-path)) (quote ())) (quote ())))) (let ((merged (merge-all inc-pairs asm-pairs))) (cons (count-lst merged) (emit-all merged)))))))

(main (car *argv*) (car (cdr *argv*)))
