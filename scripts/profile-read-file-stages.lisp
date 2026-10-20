; #333 — measurement-only profiler for the Lisp-owned file/UTF-8 pipeline.
; No semantic shortcut lives here: this runs the same current primitives in
; separated stages so we can locate the real cost before changing mechanism.
;
; Pipeline under observation:
;   read-file-bytes -> utf8-all-bytes? -> utf8-decode-onto (+ final reverse)
;   -> unicode-scalars->string -> read-all

(визначити шлях-профілю "lib/surface/semantic-registry.lisp")

(визначити початок-профілю (монотонний-наносекунди))
(визначити байти-профілю (read-file-bytes шлях-профілю))
(визначити після-байтів-профілю (монотонний-наносекунди))

; `utf8-decode` performs this validation pass before decoding. Time it alone.
(визначити чинність-профілю (усі-елементи-є-байтами-кодування-юнікод-8? байти-профілю))
(визначити після-валідації-профілю (монотонний-наносекунди))

; The source registry is committed valid UTF-8. Calling the internal decode
; worker directly avoids counting validation a second time. This stage includes
; scalar accumulation and the worker's final `(reverse out)`.
(визначити декодоване-профілю (utf8-decode-onto байти-профілю (як-є ())))
(визначити після-декодування-профілю (монотонний-наносекунди))
(визначити скаляри-профілю (друге декодоване-профілю))

; Materialize the already-decoded Unicode scalar list as one runtime String.
(визначити текст-профілю (юнікод-скаляри-рядок скаляри-профілю))
(визначити після-рядка-профілю (монотонний-наносекунди))

; Keep parser cost separate so #333 does not optimize the wrong layer.
(визначити корінь-профілю (перше (читати-всі текст-профілю)))
(визначити після-читання-всього-профілю (монотонний-наносекунди))

(друкувати
  (список
    (як-є eco-lisp-script-perf/read-file-stages)
    (список (як-є read-file-bytes-ns)
          (відняти після-байтів-профілю початок-профілю))
    (список (як-є validation-ns)
          (відняти після-валідації-профілю після-байтів-профілю))
    (список (як-є decode-plus-reverse-ns)
          (відняти після-декодування-профілю після-валідації-профілю))
    (список (як-є string-assembly-ns)
          (відняти після-рядка-профілю після-декодування-профілю))
    (список (як-є read-all-ns)
          (відняти після-читання-всього-профілю після-рядка-профілю))
    (список (як-є total-ns)
          (відняти після-читання-всього-профілю початок-профілю))
    (список (як-є validation-result) чинність-профілю)
    (список (як-є decode-tag) (перше декодоване-профілю))
    (список (як-є root) корінь-профілю)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити монотонний-наносекунди mono-ns)
(визначити читати-всі read-all)
(визначити юнікод-скаляри-рядок unicode-scalars->string)
(визначити усі-елементи-є-байтами-кодування-юнікод-8? utf8-all-bytes?)
