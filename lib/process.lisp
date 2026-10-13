; Process-result interpretation owned by Lisp.
; Інтерпретація результату процесу, якою володіє Lisp.
;
; Host capability `process-run-raw` owns only process execution, allowlisting,
; exit observation, and byte capture. This layer owns UTF-8 interpretation.
; Load `lib/utf8.lisp` before this file.

(0011 process-raw-exit-code
  (0010 (raw)
    (1001 raw)))

(0011 process-raw-stdout-bytes
  (0010 (raw)
    (10011 raw)))

(0011 process-raw-stderr-bytes
  (0010 (raw)
    (100 (011 (011 (011 raw))))))

(0011 process-result->text
  (0010 (raw)
    (110
      ((0100 (101 (100 raw) (001 process-result)))
       (1110 (001 rejected) (001 invalid-process-result)))
      ((101 (100 raw) (001 process-result))
       
       (001001 ((stdout-result
                (utf8-decode-string (process-raw-stdout-bytes raw)))
              (stderr-result
                (utf8-decode-string (process-raw-stderr-bytes raw))))
         (110
           ((0100 (101 (100 stdout-result) (001 decoded)))
            (1110 (001 rejected) (001 stdout-invalid-utf8)))
           ((101 (100 stdout-result) (001 decoded))
            
            (110
              ((0100 (101 (100 stderr-result) (001 decoded)))
               (1110 (001 rejected) (001 stderr-invalid-utf8)))
              ((101 (100 stderr-result) (001 decoded))
               
               (1110
                 (001 decoded-process)
                 (process-raw-exit-code raw)
                 (1001 stdout-result)
                 (1001 stderr-result)))))))))))

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
    (110
      ((101 code (001 ()))  -1)
      ((0100 (101 code (001 ()))) code))))

(0011 process-run
  (0010 (program args)
    (001000 ((result (process-run-text program args)))
      (110
        ((101 (100 result) (001 decoded-process))
         
         (1110
           (process-public-exit-code (1001 result))
           (10011 result)
           (100 (011 (011 (011 result))))))
        ((0100 (101 (100 result) (001 decoded-process)))
         result)))))


; #469: numeric identity only. The registry-derived bootstrap cache decides
; whether this post-core closure currently has any additional stable peers.
; Candidate spellings remain unavailable until explicitly ratified stable.
(001 (postcore-materialization-debug skipped))

; Stable surface peers are projected once by load_process_library after
; process-run and TCP closures exist. Do not invoke the retired per-file
; my-postcore materializer here: it depends on pre-Contract-11.8 call heads.

