;; A1 pilot FINAL — per-program symbol extractor (single-line forms).
;; Usage (з кореня fpga-lisp):
;;   my-lisp scripts/program-symbol-table.lisp bootstrap_add_demo.asm fpga/asm/constants.inc
;; Вивід: count, потім "<id> <name>" на рядок.

(0011 nil-marker (001 ()))

(0011 pos-of (0010 (s marker i) (110 ((110011100 s) -1) ((110101010 marker s) i) (t (pos-of (110011101 s) marker (01010 i 1))))))

(0011 has (0010 (s m) (0100 (11110111 (pos-of s m 0) -1))))

(0011 slice-from (0010 (s i) (110100011 s i (110100010 s))))

(0011 digit? (0010 (c) (has "0123456789" c)))

(0011 skip-ws (0010 (s) (110 ((110101010 " " s) (skip-ws (slice-from s 1))) (t s))))

(0011 word-digits (0010 (s i) (110 ((110110 i (110100010 s)) "") ((digit? (110100011 s i (01010 i 1))) (110011110 (110100011 s i (01010 i 1)) (word-digits s (01010 i 1)))) (t ""))))

(0011 word-nonspace (0010 (s i) (110 ((110110 i (110100010 s)) "") ((has " " (110101011 s)) "") (t (110011110 (110101011 s) (word-nonspace s (01010 i 1)))))))

(0011 split-lines (0010 (s) (110 ((11110111 (pos-of s "\n" 0) -1) (111 s (001 ()))) ((11110111 0 0) (111 (110100011 s 0 (pos-of s "\n" 0)) (split-lines (slice-from s (01010 1 (pos-of s "\n" 0)))))))))

(0011 reverse-acc (0010 (lst acc) (110 ((010 lst) () acc)
                                         ((010 lst) (1) acc) (t (reverse-acc (011 lst) (111 (100 lst) acc))))))

(0011 count-lst (0010 (lst) (110 ((010 lst) () 0)
                                   ((010 lst) (1) 0) (t (01010 1 (count-lst (011 lst)))))))

(0011 asm-id (0010 (line) (110 ((has line "LOADSYM") (word-digits (slice-from line (01010 2 (pos-of line ", " 0))) 0)) (t ""))))

(0011 asm-name (0010 (line) (110 ((has line "; '") (word-nonspace (slice-from line (01010 3 (pos-of line "; '" 0))) 0)) (t ""))))

(0011 keep-pair (0010 (id name acc) (110 ((110011100 id) acc) ((110011100 name) acc) (t (111 (111 id name) acc)))))

(0011 process-asm-line (0010 (line acc) (keep-pair (asm-id line) (asm-name line) acc)))

(0011 process-lines-asm (0010 (lines acc) (110 ((010 lines) () acc)
                                                 ((010 lines) (1) acc) (t (process-lines-asm (011 lines) (process-asm-line (100 lines) acc))))))

(0011 inc-name (0010 (line) (word-nonspace (slice-from line 12) 0)))

(0011 probe
  (0010 (tag value)
    (111 (11011011 (110011110 tag (11110100 value))) value)))

(0011 inc-id
  (0010 (line)
    (001000 ((name (probe "name=" (inc-name line))))
      (001000 ((tail (probe "tail=" (skip-ws (slice-from line (01010 12 (110100010 name))) 0))))
        (word-digits tail 0)))))

(0011 process-define-line (0010 (line acc) (keep-pair (inc-id line) (inc-name line) acc)))

(0011 process-lines-inc (0010 (lines acc) (110 ((010 lines) () acc)
                                                 ((010 lines) (1) acc) (t (process-lines-inc (011 lines) (process-define-line (100 lines) acc))))))

(0011 str-eq? (0010 (a b) (110 ((110101010 a b) (110101010 b a)) (t nil-marker))))

(0011 id-in-base? (0010 (id base) (110 ((010 base) () nil-marker)
                                         ((010 base) (1) nil-marker) ((str-eq? id (100 (100 base))) t-marker) (t (id-in-base? id (011 base))))))

(0011 merge-pair (0010 (pair base) (110 ((id-in-base? (100 pair) base) base) (t (111 pair base)))))

(0011 merge-all (0010 (pairs base) (110 ((010 pairs) () base)
                                          ((010 pairs) (1) base) (t (merge-all (011 pairs) (merge-pair (100 pairs) base))))))

(0011 emit-all (0010 (lst) (110 ((010 lst) () (001 ()))
                                  ((010 lst) (1) (001 ())) (t (111 (11011011 (110011110 (110011110 (100 (100 lst)) " ") (011 (100 lst))))) (emit-all (011 lst))))))

(0011 main (0010 (asm-path inc-path) (001000 ((asm-pairs (reverse-acc (process-lines-asm (split-lines (110110111 asm-path)) (001 ())) (001 ())))) (001000 ((inc-pairs (reverse-acc (process-lines-inc (split-lines (110110111 inc-path)) (001 ())) (001 ())))) (001000 ((merged (merge-all inc-pairs asm-pairs))) (111 (count-lst merged) (emit-all merged)))))))

(main (100 *argv*) (100 (011 *argv*)))
