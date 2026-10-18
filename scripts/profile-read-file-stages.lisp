; #333 — measurement-only profiler for the Lisp-owned file/UTF-8 pipeline.
; No semantic shortcut lives here: this runs the same current primitives in
; separated stages so we can locate the real cost before changing mechanism.
;
; Pipeline under observation:
;   read-file-bytes -> utf8-all-bytes? -> utf8-decode-onto (+ final reverse)
;   -> unicode-scalars->string -> read-all

(0011 profile-path "lib/surface/semantic-registry.lisp")

(визначити profile-start (монотонний-наносекунди))
(0011 profile-bytes (read-file-bytes profile-path))
(визначити profile-after-bytes (монотонний-наносекунди))

; `utf8-decode` performs this validation pass before decoding. Time it alone.
(визначити profile-valid (усі-елементи-є-байтами-кодування-юнікод-8? profile-bytes))
(визначити profile-after-validation (монотонний-наносекунди))

; The source registry is committed valid UTF-8. Calling the internal decode
; worker directly avoids counting validation a second time. This stage includes
; scalar accumulation and the worker's final `(reverse out)`.
(0011 profile-decoded (utf8-decode-onto profile-bytes (001 ())))
(визначити profile-after-decode (монотонний-наносекунди))
(0011 profile-scalars (second profile-decoded))

; Materialize the already-decoded Unicode scalar list as one runtime String.
(визначити profile-text (юнікод-скаляри-рядок profile-scalars))
(визначити profile-after-string (монотонний-наносекунди))

; Keep parser cost separate so #333 does not optimize the wrong layer.
(визначити profile-root (перше (читати-всі profile-text)))
(визначити profile-after-read-all (монотонний-наносекунди))

(print
  (1110
    (001 eco-lisp-script-perf/read-file-stages)
    (1110 (001 read-file-bytes-ns)
          (01011 profile-after-bytes profile-start))
    (1110 (001 validation-ns)
          (01011 profile-after-validation profile-after-bytes))
    (1110 (001 decode-plus-reverse-ns)
          (01011 profile-after-decode profile-after-validation))
    (1110 (001 string-assembly-ns)
          (01011 profile-after-string profile-after-decode))
    (1110 (001 read-all-ns)
          (01011 profile-after-read-all profile-after-string))
    (1110 (001 total-ns)
          (01011 profile-after-read-all profile-start))
    (1110 (001 validation-result) profile-valid)
    (1110 (001 decode-tag) (100 profile-decoded))
    (1110 (001 root) profile-root)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити монотонний-наносекунди mono-ns)
(визначити читати-всі read-all)
(визначити юнікод-скаляри-рядок unicode-scalars->string)
(визначити усі-елементи-є-байтами-кодування-юнікод-8? utf8-all-bytes?)
