;; A1 pilot FINAL — per-program symbol extractor (single-line forms).
;; Usage (з кореня fpga-lisp):
;;   my-lisp scripts/program-symbol-table.lisp bootstrap_add_demo.asm fpga/asm/constants.inc
;; Вивід: count, потім "<id> <name>" на рядок.

(00001001 nil-marker (00000001 ()))

(00001001 pos-of (00001000 (s marker i) (00000111 ((00111100 s) -1) ((00111101 marker s) i) (t (pos-of (01000000 s) marker (00001100 i 1))))))

(00001001 has (00001000 (s m) (00100001 (00011100 (pos-of s m 0) -1))))

(00001001 slice-from (00001000 (s i) (01000001 s i (00111011 s))))

(00001001 digit? (00001000 (c) (has "0123456789" c)))

(00001001 skip-ws (00001000 (s) (00000111 ((00111101 " " s) (skip-ws (slice-from s 1))) (t s))))

(00001001 word-digits (00001000 (s i) (00000111 ((00011110 i (00111011 s)) "") ((digit? (01000001 s i (00001100 i 1))) (00111010 (01000001 s i (00001100 i 1)) (word-digits s (00001100 i 1)))) (t ""))))

(00001001 word-nonspace (00001000 (s i) (00000111 ((00011110 i (00111011 s)) "") ((has " " (00111111 s)) "") (t (00111010 (00111111 s) (word-nonspace s (00001100 i 1)))))))

(00001001 split-lines (00001000 (s) (00000111 ((00011100 (pos-of s "\n" 0) -1) (00000100 s (00000001 ()))) ((00011100 0 0) (00000100 (01000001 s 0 (pos-of s "\n" 0)) (split-lines (slice-from s (00001100 1 (pos-of s "\n" 0)))))))))

(00001001 reverse-acc (00001000 (lst acc) (00000111 ((00000010 lst) () acc)
                                         ((00000010 lst) (1) acc) (t (reverse-acc (00000110 lst) (00000100 (00000101 lst) acc))))))

(00001001 count-lst (00001000 (lst) (00000111 ((00000010 lst) () 0)
                                   ((00000010 lst) (1) 0) (t (00001100 1 (count-lst (00000110 lst)))))))

(00001001 asm-id (00001000 (line) (00000111 ((has line "LOADSYM") (word-digits (slice-from line (00001100 2 (pos-of line ", " 0))) 0)) (t ""))))

(00001001 asm-name (00001000 (line) (00000111 ((has line "; '") (word-nonspace (slice-from line (00001100 3 (pos-of line "; '" 0))) 0)) (t ""))))

(00001001 keep-pair (00001000 (id name acc) (00000111 ((00111100 id) acc) ((00111100 name) acc) (t (00000100 (00000100 id name) acc)))))

(00001001 process-asm-line (00001000 (line acc) (keep-pair (asm-id line) (asm-name line) acc)))

(00001001 process-lines-asm (00001000 (lines acc) (00000111 ((00000010 lines) () acc)
                                                 ((00000010 lines) (1) acc) (t (process-lines-asm (00000110 lines) (process-asm-line (00000101 lines) acc))))))

(00001001 inc-name (00001000 (line) (word-nonspace (slice-from line 12) 0)))

(00001001 probe
  (00001000 (tag value)
    (00000100 (01001000 (00111010 tag (01001100 value))) value)))

(00001001 inc-id
  (00001000 (line)
    (10011100 ((name (probe "name=" (inc-name line))))
      (10011100 ((tail (probe "tail=" (skip-ws (slice-from line (00001100 12 (00111011 name))) 0))))
        (word-digits tail 0)))))

(00001001 process-define-line (00001000 (line acc) (keep-pair (inc-id line) (inc-name line) acc)))

(00001001 process-lines-inc (00001000 (lines acc) (00000111 ((00000010 lines) () acc)
                                                 ((00000010 lines) (1) acc) (t (process-lines-inc (00000110 lines) (process-define-line (00000101 lines) acc))))))

(00001001 str-eq? (00001000 (a b) (00000111 ((00111101 a b) (00111101 b a)) (t nil-marker))))

(00001001 id-in-base? (00001000 (id base) (00000111 ((00000010 base) () nil-marker)
                                         ((00000010 base) (1) nil-marker) ((str-eq? id (00000101 (00000101 base))) t-marker) (t (id-in-base? id (00000110 base))))))

(00001001 merge-pair (00001000 (pair base) (00000111 ((id-in-base? (00000101 pair) base) base) (t (00000100 pair base)))))

(00001001 merge-all (00001000 (pairs base) (00000111 ((00000010 pairs) () base)
                                          ((00000010 pairs) (1) base) (t (merge-all (00000110 pairs) (merge-pair (00000101 pairs) base))))))

(00001001 emit-all (00001000 (lst) (00000111 ((00000010 lst) () (00000001 ()))
                                  ((00000010 lst) (1) (00000001 ())) (t (00000100 (01001000 (00111010 (00111010 (00000101 (00000101 lst)) " ") (00000110 (00000101 lst))))) (emit-all (00000110 lst))))))

(00001001 main (00001000 (asm-path inc-path) (10011100 ((asm-pairs (reverse-acc (process-lines-asm (split-lines (10100110 asm-path)) (00000001 ())) (00000001 ())))) (10011100 ((inc-pairs (reverse-acc (process-lines-inc (split-lines (10100110 inc-path)) (00000001 ())) (00000001 ())))) (10011100 ((merged (merge-all inc-pairs asm-pairs))) (00000100 (count-lst merged) (emit-all merged)))))))

(main (00000101 *argv*) (00000101 (00000110 *argv*)))
