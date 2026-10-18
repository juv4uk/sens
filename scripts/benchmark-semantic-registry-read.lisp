; #74 real workload harvested from #76 Python -> my-lisp migration.
; Measure the exact heavy phase profiled in PR #317, but split it into the
; public Lisp-owned read-file path and read-all parser phase. Do not call
; core.lisp's recursive string-length here: on a registry-sized String that is
; a separate non-tail recursion benchmark and can overflow the host stack.

(визначити початок (монотонний-наносекунди))
(визначити текст-реєстру (читати-файл "lib/surface/semantic-registry.lisp"))
(визначити після-читання (монотонний-наносекунди))
(визначити форма-реєстру (перше (читати-всі текст-реєстру)))
(визначити після-розбору (монотонний-наносекунди))

(друкувати
  (список (як-є eco-lisp-script-perf/read-semantic-registry)
        (список (як-є read-file-ns) (відняти після-читання початок))
        (список (як-є read-all-ns) (відняти після-розбору після-читання))
        (список (як-є total-ns) (відняти після-розбору початок))
        (список (як-є root) (перше форма-реєстру))))
