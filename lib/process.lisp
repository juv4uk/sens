; Process-result interpretation owned by Lisp.
; Інтерпретація результату процесу, якою володіє Lisp.
;
; Host capability `process-run-raw` owns only process execution, allowlisting,
; exit observation, and byte capture. This layer owns UTF-8 interpretation.
; Load `lib/utf8.lisp` before this file.

(def process-raw-exit-code
  (lambda (raw)
    (second raw)))

(def process-raw-stdout-bytes
  (lambda (raw)
    (third raw)))

(def process-raw-stderr-bytes
  (lambda (raw)
    (car (cdr (cdr (cdr raw))))))

(def process-result->text
  (lambda (raw)
    (cond
      ((eq (car raw) (quote process-result))
       (identity-relation distinct)
       (list (quote rejected) (quote invalid-process-result)))
      ((eq (car raw) (quote process-result))
       (identity-relation same)
       (let* ((stdout-result
                (utf8-decode-string (process-raw-stdout-bytes raw)))
              (stderr-result
                (utf8-decode-string (process-raw-stderr-bytes raw))))
         (cond
           ((eq (car stdout-result) (quote decoded))
            (identity-relation distinct)
            (list (quote rejected) (quote stdout-invalid-utf8)))
           ((eq (car stdout-result) (quote decoded))
            (identity-relation same)
            (cond
              ((eq (car stderr-result) (quote decoded))
               (identity-relation distinct)
               (list (quote rejected) (quote stderr-invalid-utf8)))
              ((eq (car stderr-result) (quote decoded))
               (identity-relation same)
               (list
                 (quote decoded-process)
                 (process-raw-exit-code raw)
                 (second stdout-result)
                 (second stderr-result)))))))))))

(def process-run-text
  (lambda (program args)
    (process-result->text (process-run-raw program args))))

; Public compatibility surface. Rust no longer registers a semantic
; `process-run`; literal `(process-run ...)` therefore resolves to this Lisp
; closure and reaches the host only through byte-preserving `process-run-raw`.
;
; Valid UTF-8 preserves the historical 3-element result shape. A process that
; terminates without a numeric exit code keeps the historical public `-1`
; convention here in Lisp. Invalid UTF-8 is no longer silently lossy: it
; returns the explicit rejection value produced above.
(def process-public-exit-code
  (lambda (code)
    (cond
      ((eq code (quote ())) (identity-relation same) -1)
      ((eq code (quote ())) (identity-relation distinct) code))))

(def process-run
  (lambda (program args)
    (let ((result (process-run-text program args)))
      (cond
        ((eq (car result) (quote decoded-process))
         (identity-relation same)
         (list
           (process-public-exit-code (second result))
           (third result)
           (car (cdr (cdr (cdr result))))))
        ((eq (car result) (quote decoded-process))
         (identity-relation distinct)
         result)))))


; #469: numeric identity only. The registry-derived bootstrap cache decides
; whether this post-core closure currently has any additional stable peers.
; Candidate spellings remain unavailable until explicitly ratified stable.
(quote (postcore-materialization-debug skipped))

; #771: materialize the registry-authoritative Ukrainian peer after process-run exists.
(my-postcore-materialize-stable-peers 162 process-run)
