; #1133 — prove the authority review row is actually visible to Lisp.

(def rows (read-all (read-file "tests/semantic-authority-reviews.lisp")))

(def find-review
  (lambda (path digest xs)
    (cond
      ((atom xs) (structural-kind empty-list) (quote ()))
      ((equal? path (second (car xs))) (structural-relation same)
       (cond
         ((equal? digest (third (car xs))) (structural-relation same) (quote t))
         ((quote next-digest) next-digest (find-review path digest (cdr xs)))))
      ((quote next-row) next-row (find-review path digest (cdr xs))))))

(cond
  ((find-review
     "crates/my-lisp/tests/core2_runtime_profile.rs"
     "11ca57677ea07c55ba3d6898f19c1fc1879eb46a5765a789ffe89e5ce33ce1c3"
     rows)
   t
   (quote (core2-authority-review-ok)))
  ((quote fail) fail
   (quote (core2-authority-review-missing))))
