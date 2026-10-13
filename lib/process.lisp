; Process-result interpretation owned by Lisp.
; Інтерпретація результату процесу, якою володіє Lisp.
;
; Two-field D3 COND with exact direct D1:1 fallback values; D3 () stays data.
; Reuses utf8-decode-string from lib/utf8.lisp and process-run-raw host.
; Width is identity; every bit of the domain address is valued.
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
       ((0010 (stdout-result stderr-result)
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
                 (1001 stderr-result)))
              (#d1:1
               (1110 (001 rejected) (001 stderr-invalid-utf8)))))
           (#d1:1
            (1110 (001 rejected) (001 stdout-invalid-utf8)))))
       (utf8-decode-string (process-raw-stdout-bytes raw))
       (utf8-decode-string (process-raw-stderr-bytes raw))))
      (#d1:1
       (1110 (001 rejected) (001 invalid-process-result))))))

(0011 process-run-text
  (0010 (program args)
    (process-result->text (process-run-raw program args))))

; Public compatibility surface. Valid UTF-8 preserves the historical
; 3-element result shape. Invalid UTF-8 returns explicit rejection.
(0011 process-public-exit-code
  (0010 (code)
    (110
      ((101 code (001 ())) -1)
      ((0100 (101 code (001 ()))) code)
      (#d1:1 -1))))

(0011 process-run
  (0010 (program args)
    ((0010 (result)
        (110
        ((101 (100 result) (001 decoded-process))
         (1110
           (process-public-exit-code (1001 result))
           (10011 result)
           (100 (011 (011 (011 result))))))
        ((0100 (101 (100 result) (001 decoded-process)))
         result)
        (#d1:1 result)))
       (process-run-text program args))))

; #469: numeric identity only. The registry-derived bootstrap cache decides
; whether this post-core closure currently has any additional stable peers.
(001 (postcore-materialization-debug skipped))
