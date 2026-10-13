; #333 — measurement-only profiler for the Lisp-owned file/UTF-8 pipeline.
; No semantic shortcut lives here: this runs the same current primitives in
; separated stages so we can locate the real cost before changing mechanism.
;
; Pipeline under observation:
;   read-file-bytes -> utf8-all-bytes? -> utf8-decode-onto (+ final reverse)
;   -> unicode-scalars->string -> read-all

(0011 profile-path "lib/surface/semantic-registry.lisp")

(0011 profile-start (mono-ns))
(0011 profile-bytes (read-file-bytes profile-path))
(0011 profile-after-bytes (mono-ns))

; `utf8-decode` performs this validation pass before decoding. Time it alone.
(0011 profile-valid (utf8-all-bytes? profile-bytes))
(0011 profile-after-validation (mono-ns))

; The source registry is committed valid UTF-8. Calling the internal decode
; worker directly avoids counting validation a second time. This stage includes
; scalar accumulation and the worker's final `(reverse out)`.
(0011 profile-decoded (utf8-decode-onto profile-bytes (001 ())))
(0011 profile-after-decode (mono-ns))
(0011 profile-scalars (second profile-decoded))

; Materialize the already-decoded Unicode scalar list as one runtime String.
(0011 profile-text (unicode-scalars->string profile-scalars))
(0011 profile-after-string (mono-ns))

; Keep parser cost separate so #333 does not optimize the wrong layer.
(0011 profile-root (100 (read-all profile-text)))
(0011 profile-after-read-all (mono-ns))

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
