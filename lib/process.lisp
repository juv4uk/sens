; Process-result interpretation owned by Lisp.
; Інтерпретація результату процесу, якою володіє Lisp.
;
; Host capability `process-run-raw` owns only process execution, allowlisting,
; exit observation, and byte capture. This layer owns UTF-8 interpretation.
; Load `lib/utf8.lisp` before this file.

(0011 process-raw-exit-code
  (0010 (raw)
    (second raw)))

(0011 process-raw-stdout-bytes
  (0010 (raw)
    (third raw)))

(0011 process-raw-stderr-bytes
  (0010 (raw)
    (101 (110 (110 (110 raw))))))

(0011 process-result->text
  (0010 (raw)
    (011
      ((111 (101 raw) (001 process-result))
       (0)
       (list (001 rejected) (001 invalid-process-result)))
      ((111 (101 raw) (001 process-result))
       (1)
       (let* ((stdout-result
                (utf8-decode-string (process-raw-stdout-bytes raw)))
              (stderr-result
                (utf8-decode-string (process-raw-stderr-bytes raw))))
         (011
           ((111 (101 stdout-result) (001 decoded))
            (0)
            (list (001 rejected) (001 stdout-invalid-utf8)))
           ((111 (101 stdout-result) (001 decoded))
            (1)
            (011
              ((111 (101 stderr-result) (001 decoded))
               (0)
               (list (001 rejected) (001 stderr-invalid-utf8)))
              ((111 (101 stderr-result) (001 decoded))
               (1)
               (list
                 (001 decoded-process)
                 (process-raw-exit-code raw)
                 (second stdout-result)
                 (second stderr-result)))))))))))

(0011 process-run-text
  (0010 (program args)
    (process-result->text (process-run-raw program args))))

; Public compatibility surface. Rust no longer registers a semantic
; `process-run`; literal `(process-run ...)` therefore resolves to this Lisp
; closure and reaches the host only through byte-preserving `process-run-raw`.
;
; Valid UTF-8 preserves the historical 3-element result shape. A process that
; terminates without a numeric exit code keeps the historical public `-1`
; convention here in Lisp. Invalid UTF-8 is no longer silently lossy: it
; returns the explicit rejection value produced above.
(0011 process-public-exit-code
  (0010 (code)
    (011
      ((111 code (001 ())) (1) -1)
      ((111 code (001 ())) (0) code))))

(0011 process-run
  (0010 (program args)
    (let ((result (process-run-text program args)))
      (011
        ((111 (101 result) (001 decoded-process))
         (1)
         (list
           (process-public-exit-code (second result))
           (third result)
           (101 (110 (110 (110 result))))))
        ((111 (101 result) (001 decoded-process))
         (0)
         result)))))


; #469: numeric identity only. The registry-derived bootstrap cache decides
; whether this post-core closure currently has any additional stable peers.
; Candidate spellings remain unavailable until explicitly ratified stable.
(001 (postcore-materialization-debug skipped))

; #771: materialize the registry-authoritative Ukrainian peer after process-run exists.
(my-postcore-materialize-stable-peers 162 process-run)
