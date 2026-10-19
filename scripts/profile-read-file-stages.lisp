; #333 — measurement-only profiler for the Lisp-owned file/UTF-8 pipeline.
; No semantic shortcut lives here: this runs the same current primitives in
; separated stages so we can locate the real cost before changing mechanism.
;
; Pipeline under observation:
;   read-file-bytes -> utf8-all-bytes? -> utf8-decode-onto (+ final reverse)
;   -> unicode-scalars->string -> read-all

(визначити profile-path "lib/surface/semantic-registry.lisp")

(визначити profile-start (монотонний-наносекунди))
(визначити profile-bytes (read-file-bytes profile-path))
(визначити profile-after-bytes (монотонний-наносекунди))

; `utf8-decode` performs this validation pass before decoding. Time it alone.
(визначити profile-valid (усі-елементи-є-байтами-кодування-юнікод-8? profile-bytes))
(визначити profile-after-validation (монотонний-наносекунди))

; The source registry is committed valid UTF-8. Calling the internal decode
; worker directly avoids counting validation a second time. This stage includes
; scalar accumulation and the worker's final `(reverse out)`.
(визначити profile-decoded (utf8-decode-onto profile-bytes (як-є ())))
(визначити profile-after-decode (монотонний-наносекунди))
(визначити profile-scalars (друге profile-decoded))

; Materialize the already-decoded Unicode scalar list as one runtime String.
(визначити profile-text (юнікод-скаляри-рядок profile-scalars))
(визначити profile-after-string (монотонний-наносекунди))

; Keep parser cost separate so #333 does not optimize the wrong layer.
(визначити profile-root (перше (читати-всі profile-text)))
(визначити profile-after-read-all (монотонний-наносекунди))

(друкувати
  (список
    (як-є eco-lisp-script-perf/read-file-stages)
    (список (як-є read-file-bytes-ns)
          (відняти profile-after-bytes profile-start))
    (список (як-є validation-ns)
          (відняти profile-after-validation profile-after-bytes))
    (список (як-є decode-plus-reverse-ns)
          (відняти profile-after-decode profile-after-validation))
    (список (як-є string-assembly-ns)
          (відняти profile-after-string profile-after-decode))
    (список (як-є read-all-ns)
          (відняти profile-after-read-all profile-after-string))
    (список (як-є total-ns)
          (відняти profile-after-read-all profile-start))
    (список (як-є validation-result) profile-valid)
    (список (як-є decode-tag) (перше profile-decoded))
    (список (як-є root) profile-root)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити монотонний-наносекунди mono-ns)
(визначити читати-всі read-all)
(визначити юнікод-скаляри-рядок unicode-scalars->string)
(визначити усі-елементи-є-байтами-кодування-юнікод-8? utf8-all-bytes?)
