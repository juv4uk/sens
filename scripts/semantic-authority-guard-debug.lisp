; Diagnostic helper for #1049 self-test failures only.
(load "scripts/semantic-authority-guard.lisp")

(def semantic-authority-debug-path
  "tests/semantic-authority-guard-probe.rs")

(def semantic-authority-debug-source
  (read-file semantic-authority-debug-path))

(print
  (list
    (quote semantic-authority-debug)
    (list (quote path-is-string) (string? semantic-authority-debug-path))
    (list (quote active-host-source)
          (active-host-source? semantic-authority-debug-path))
    (list (quote source-is-string)
          (string? semantic-authority-debug-source))
    (list (quote has-SemanticId)
          (cond
            ((string? semantic-authority-debug-source)
             (string-contains? "SemanticId" semantic-authority-debug-source))
            (t (quote unreadable))))
    (list (quote has-CanonicalIdentity)
          (cond
            ((string? semantic-authority-debug-source)
             (string-contains? "CanonicalIdentity" semantic-authority-debug-source))
            (t (quote unreadable))))
    (list (quote violation-class)
          (cond
            ((string? semantic-authority-debug-source)
             (violation-class
               semantic-authority-debug-path
               semantic-authority-debug-source))
            (t (quote unreadable))))))
