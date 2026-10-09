; #333 — measurement-only profiler for the Lisp-owned file/UTF-8 pipeline.
; No semantic shortcut lives here: this runs the same current primitives in
; separated stages so we can locate the real cost before changing mechanism.
;
; Pipeline under observation:
;   read-file-bytes -> utf8-all-bytes? -> utf8-decode-onto (+ final reverse)
;   -> unicode-scalars->string -> read-all

(def profile-path "lib/surface/semantic-registry.lisp")

(def profile-start (mono-ns))
(def profile-bytes (read-file-bytes profile-path))
(def profile-after-bytes (mono-ns))

; `utf8-decode` performs this validation pass before decoding. Time it alone.
(def profile-valid (utf8-all-bytes? profile-bytes))
(def profile-after-validation (mono-ns))

; The source registry is committed valid UTF-8. Calling the internal decode
; worker directly avoids counting validation a second time. This stage includes
; scalar accumulation and the worker's final `(reverse out)`.
(def profile-decoded (utf8-decode-onto profile-bytes (quote ())))
(def profile-after-decode (mono-ns))
(def profile-scalars (second profile-decoded))

; Materialize the already-decoded Unicode scalar list as one runtime String.
(def profile-text (unicode-scalars->string profile-scalars))
(def profile-after-string (mono-ns))

; Keep parser cost separate so #333 does not optimize the wrong layer.
(def profile-root (car (read-all profile-text)))
(def profile-after-read-all (mono-ns))

(print
  (list
    (quote eco-lisp-script-perf/read-file-stages)
    (list (quote read-file-bytes-ns)
          (- profile-after-bytes profile-start))
    (list (quote validation-ns)
          (- profile-after-validation profile-after-bytes))
    (list (quote decode-plus-reverse-ns)
          (- profile-after-decode profile-after-validation))
    (list (quote string-assembly-ns)
          (- profile-after-string profile-after-decode))
    (list (quote read-all-ns)
          (- profile-after-read-all profile-after-string))
    (list (quote total-ns)
          (- profile-after-read-all profile-start))
    (list (quote validation-result) profile-valid)
    (list (quote decode-tag) (car profile-decoded))
    (list (quote root) profile-root)))
