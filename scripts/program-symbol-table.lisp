;; A1 pilot FINAL — per-program symbol extractor (single-line forms).
;; Usage (з кореня fpga-lisp):
;;   my-lisp scripts/program-symbol-table.lisp bootstrap_add_demo.asm fpga/asm/constants.inc
;; Вивід: count, потім "<id> <name>" на рядок.

(визначити nil-marker (як-є ()))

(визначити pos-of (функція (s marker i) (за-умовою ((рядок-порожній? s) -1) ((рядок-префікс? marker s) i) ((атом? (як-є ())) (pos-of (рядок-решта s) marker (додати i 1))))))

(визначити has (функція (s m) (хибне? (однакові? (pos-of s m 0) -1))))

(визначити slice-from (функція (s i) (рядок-зріз s i (рядок-довжина s))))

(визначити digit? (функція (c) (has "0123456789" c)))

(визначити skip-ws (функція (s) (за-умовою ((рядок-префікс? " " s) (skip-ws (slice-from s 1))) ((атом? (як-є ())) s))))

(визначити word-digits (функція (s i) (за-умовою ((не-менше? i (рядок-довжина s)) "") ((digit? (рядок-зріз s i (додати i 1))) (рядок-додати (рядок-зріз s i (додати i 1)) (word-digits s (додати i 1)))) ((атом? (як-є ())) ""))))

(визначити word-nonspace (функція (s i) (за-умовою ((не-менше? i (рядок-довжина s)) "") ((has " " (рядок-перший s)) "") ((атом? (як-є ())) (рядок-додати (рядок-перший s) (word-nonspace s (додати i 1)))))))

(визначити split-lines (функція (s) (за-умовою ((однакові? (pos-of s "\n" 0) -1) (сполучити s (як-є ()))) ((однакові? 0 0) (сполучити (рядок-зріз s 0 (pos-of s "\n" 0)) (split-lines (slice-from s (додати 1 (pos-of s "\n" 0)))))))))

(визначити reverse-acc (функція (lst acc) (за-умовою ((атом? lst) acc)
                                          ((атом? (як-є ())) (reverse-acc (решта lst) (сполучити (перше lst) acc))))))

(визначити count-lst (функція (lst) (за-умовою ((атом? lst) 0)
                                    ((атом? (як-є ())) (додати 1 (count-lst (решта lst)))))))

(визначити asm-id (функція (line) (за-умовою ((has line "LOADSYM") (word-digits (slice-from line (додати 2 (pos-of line ", " 0))) 0)) ((атом? (як-є ())) ""))))

(визначити asm-name (функція (line) (за-умовою ((has line "; '") (word-nonspace (slice-from line (додати 3 (pos-of line "; '" 0))) 0)) ((атом? (як-є ())) ""))))

(визначити keep-pair (функція (id name acc) (за-умовою ((рядок-порожній? id) acc) ((рядок-порожній? name) acc) ((атом? (як-є ())) (сполучити (сполучити id name) acc)))))

(визначити process-asm-line (функція (line acc) (keep-pair (asm-id line) (asm-name line) acc)))

(визначити process-lines-asm (функція (lines acc) (за-умовою ((атом? lines) acc)
                                                  ((атом? (як-є ())) (process-lines-asm (решта lines) (process-asm-line (перше lines) acc))))))

(визначити inc-name (функція (line) (word-nonspace (slice-from line 12) 0)))

(визначити probe
  (функція (tag value)
    (сполучити (друкувати (рядок-додати tag (значення-у-текст value))) value)))

(визначити inc-id
  (функція (line)
    (нехай ((name (probe "name=" (inc-name line))))
      (нехай ((tail (probe "tail=" (skip-ws (slice-from line (додати 12 (рядок-довжина name))) 0))))
        (word-digits tail 0)))))

(визначити process-define-line (функція (line acc) (keep-pair (inc-id line) (inc-name line) acc)))

(визначити process-lines-inc (функція (lines acc) (за-умовою ((атом? lines) acc)
                                                  ((атом? (як-є ())) (process-lines-inc (решта lines) (process-define-line (перше lines) acc))))))

(визначити str-eq? (функція (a b) (за-умовою ((рядок-префікс? a b) (рядок-префікс? b a)) ((атом? (як-є ())) nil-marker))))

(визначити id-in-base? (функція (id base) (за-умовою ((атом? base) nil-marker)
                                          ((str-eq? id (перше (перше base))) t-marker) ((атом? (як-є ())) (id-in-base? id (решта base))))))

(визначити merge-pair (функція (pair base) (за-умовою ((id-in-base? (перше pair) base) base) ((атом? (як-є ())) (сполучити pair base)))))

(визначити merge-all (функція (pairs base) (за-умовою ((атом? pairs) base)
                                           ((атом? (як-є ())) (merge-all (решта pairs) (merge-pair (перше pairs) base))))))

(визначити emit-all (функція (lst) (за-умовою ((атом? lst) (як-є ()))
                                   (t (сполучити (друкувати (рядок-додати (рядок-додати (перше (перше lst)) " ") (решта (перше lst))))) (emit-all (решта lst))))))

(визначити main (функція (asm-path inc-path) (нехай ((asm-pairs (reverse-acc (process-lines-asm (split-lines (читати-файл asm-path)) (як-є ())) (як-є ())))) (нехай ((inc-pairs (reverse-acc (process-lines-inc (split-lines (читати-файл inc-path)) (як-є ())) (як-є ())))) (нехай ((merged (merge-all inc-pairs asm-pairs))) (сполучити (count-lst merged) (emit-all merged)))))))

(main (перше *argv*) (перше (решта *argv*)))
