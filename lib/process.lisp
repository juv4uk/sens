; Process-result interpretation owned by Lisp.
; Інтерпретація результату процесу, якою володіє Lisp.
;
; Host capability `process-run-raw` owns only process execution, allowlisting,
; exit observation, and byte capture. This layer owns UTF-8 interpretation.
; Load `lib/utf8.lisp` before this file.

(00001001 process-raw-exit-code
  (00001000 (raw)
    (00101111 raw)))

(00001001 process-raw-stdout-bytes
  (00001000 (raw)
    (00110000 raw)))

(00001001 process-raw-stderr-bytes
  (00001000 (raw)
    (00000101 (00000110 (00000110 (00000110 raw))))))

(00001001 process-result->text
  (00001000 (raw)
    (00000111
      ((0100 (00000011 (00000101 raw) (00000001 process-result)))
       (00100111 (00000001 rejected) (00000001 invalid-process-result)))
      ((00000011 (00000101 raw) (00000001 process-result))
       
       (10011101 ((stdout-result
                (utf8-decode-string (process-raw-stdout-bytes raw)))
              (stderr-result
                (utf8-decode-string (process-raw-stderr-bytes raw))))
         (00000111
           ((0100 (00000011 (00000101 stdout-result) (00000001 decoded)))
            (00100111 (00000001 rejected) (00000001 stdout-invalid-utf8)))
           ((00000011 (00000101 stdout-result) (00000001 decoded))
            
            (00000111
              ((0100 (00000011 (00000101 stderr-result) (00000001 decoded)))
               (00100111 (00000001 rejected) (00000001 stderr-invalid-utf8)))
              ((00000011 (00000101 stderr-result) (00000001 decoded))
               
               (00100111
                 (00000001 decoded-process)
                 (process-raw-exit-code raw)
                 (00101111 stdout-result)
                 (00101111 stderr-result)))))))))))

(00001001 process-run-text
  (00001000 (program args)
    (process-result->text (process-run-raw program args))))

; Public compatibility surface. Rust no longer registers a semantic
; `process-run`; literal `(process-run ...)` therefore resolves to this Lisp
; closure and reaches the host only through byte-preserving `process-run-raw`.
;
; Valid UTF-8 preserves the historical 3-element result shape. A process that
; terminates without a numeric exit code keeps the historical public `-1`
; convention here in Lisp. Invalid UTF-8 is no longer silently lossy: it
; returns the explicit rejection value produced above.
(00001001 process-public-exit-code
  (00001000 (code)
    (00000111
      ((00000011 code (00000001 ()))  -1)
      ((0100 (00000011 code (00000001 ()))) code))))

(00001001 process-run
  (00001000 (program args)
    (10011100 ((result (process-run-text program args)))
      (00000111
        ((00000011 (00000101 result) (00000001 decoded-process))
         
         (00100111
           (process-public-exit-code (00101111 result))
           (00110000 result)
           (00000101 (00000110 (00000110 (00000110 result))))))
        ((0100 (00000011 (00000101 result) (00000001 decoded-process)))
         result)))))


; #469: numeric identity only. The registry-derived bootstrap cache decides
; whether this post-core closure currently has any additional stable peers.
; Candidate spellings remain unavailable until explicitly ratified stable.
(00000001 (postcore-materialization-debug skipped))

; Stable surface peers are projected once by load_process_library after
; process-run and TCP closures exist. Do not invoke the retired per-file
; my-postcore materializer here: it depends on pre-Contract-11.8 call heads.

