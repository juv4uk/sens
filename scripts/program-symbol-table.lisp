;; A1 pilot FINAL — per-program symbol extractor (single-line forms).
;; Usage (з кореня fpga-lisp):
;;   my-lisp scripts/program-symbol-table.lisp bootstrap_add_demo.asm fpga/asm/constants.inc
;; Вивід: count, потім "<id> <name>" на рядок.

(визначити nil-marker (як-є ()))

(0011 pos-of (0010 (s marker i) (110 ((110011100 s) -1) ((110101010 marker s) i) ((010 (001 ())) (pos-of (110011101 s) marker (01010 i 1))))))

(0011 has (0010 (s m) (0100 (11110111 (pos-of s m 0) -1))))

(0011 slice-from (0010 (s i) (110100011 s i (110100010 s))))

(визначити digit? (функція (c) (has "0123456789" c)))

(0011 skip-ws (0010 (s) (110 ((110101010 " " s) (skip-ws (slice-from s 1))) ((010 (001 ())) s))))

(0011 word-digits (0010 (s i) (110 ((110110 i (110100010 s)) "") ((digit? (110100011 s i (01010 i 1))) (110011110 (110100011 s i (01010 i 1)) (word-digits s (01010 i 1)))) ((010 (001 ())) ""))))

(0011 word-nonspace (0010 (s i) (110 ((110110 i (110100010 s)) "") ((has " " (110101011 s)) "") ((010 (001 ())) (110011110 (110101011 s) (word-nonspace s (01010 i 1)))))))

(0011 split-lines (0010 (s) (110 ((11110111 (pos-of s "\n" 0) -1) (111 s (001 ()))) ((11110111 0 0) (111 (110100011 s 0 (pos-of s "\n" 0)) (split-lines (slice-from s (01010 1 (pos-of s "\n" 0)))))))))

(визначити reverse-acc (функція (lst acc) (за-умовою ((атом? lst) acc)
                                          ((атом? (як-є ())) (reverse-acc (решта lst) (сполучити (перше lst) acc))))))

(визначити count-lst (функція (lst) (за-умовою ((атом? lst) 0)
                                    ((010 (001 ())) (01010 1 (count-lst (011 lst)))))))

(0011 asm-id (0010 (line) (110 ((has line "LOADSYM") (word-digits (slice-from line (01010 2 (pos-of line ", " 0))) 0)) ((010 (001 ())) ""))))

(0011 asm-name (0010 (line) (110 ((has line "; '") (word-nonspace (slice-from line (01010 3 (pos-of line "; '" 0))) 0)) ((010 (001 ())) ""))))

(0011 keep-pair (0010 (id name acc) (110 ((110011100 id) acc) ((110011100 name) acc) ((010 (001 ())) (111 (111 id name) acc)))))

(визначити process-asm-line (функція (line acc) (keep-pair (asm-id line) (asm-name line) acc)))

(визначити process-lines-asm (функція (lines acc) (за-умовою ((атом? lines) acc)
                                                  ((атом? (як-є ())) (process-lines-asm (решта lines) (process-asm-line (перше lines) acc))))))

(визначити inc-name (функція (line) (word-nonspace (slice-from line 12) 0)))

(визначити probe
  (функція (tag value)
    (111 (11011011 (110011110 tag (11110100 value))) value)))

(визначити inc-id
  (функція (line)
    (001000 ((name (probe "name=" (inc-name line))))
      (001000 ((tail (probe "tail=" (skip-ws (slice-from line (01010 12 (110100010 name))) 0))))
        (word-digits tail 0)))))

(визначити process-define-line (функція (line acc) (keep-pair (inc-id line) (inc-name line) acc)))

(визначити process-lines-inc (функція (lines acc) (за-умовою ((атом? lines) acc)
                                                  ((атом? (як-є ())) (process-lines-inc (решта lines) (process-define-line (перше lines) acc))))))

(0011 str-eq? (0010 (a b) (110 ((110101010 a b) (110101010 b a)) ((010 (001 ())) nil-marker))))

(визначити id-in-base? (функція (id base) (за-умовою ((атом? base) nil-marker)
                                          ((str-eq? id (перше (перше base))) t-marker) ((атом? (як-є ())) (id-in-base? id (решта base))))))

(визначити merge-pair (функція (pair base) (за-умовою ((id-in-base? (перше pair) base) base) ((атом? (як-є ())) (сполучити pair base)))))

(визначити merge-all (функція (pairs base) (за-умовою ((атом? pairs) base)
                                           ((атом? (як-є ())) (merge-all (решта pairs) (merge-pair (перше pairs) base))))))

(визначити emit-all (функція (lst) (за-умовою ((атом? lst) (як-є ()))
                                   (t (111 (11011011 (110011110 (110011110 (100 (100 lst)) " ") (011 (100 lst))))) (emit-all (011 lst))))))

(0011 main (0010 (asm-path inc-path) (001000 ((asm-pairs (reverse-acc (process-lines-asm (split-lines (110110111 asm-path)) (001 ())) (001 ())))) (001000 ((inc-pairs (reverse-acc (process-lines-inc (split-lines (110110111 inc-path)) (001 ())) (001 ())))) (001000 ((merged (merge-all inc-pairs asm-pairs))) (111 (count-lst merged) (emit-all merged)))))))

(main (перше *argv*) (перше (решта *argv*)))
