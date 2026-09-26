; scripts/fixtures-for-tier.lisp — filters tests/fixtures/conformance.lisp down
; to one tier, on demand (2026-08-09, my-lisp replacing the old Python
; version now that conformance.lisp is native data and print escapes
; strings correctly — no parser or string-append needed for this either).
;
; conformance.lisp deliberately stays one file (see PLAN.md) — this script
; makes "which fixtures must I pass to be my-lisp at Tier N?" trivial to
; answer without a future implementer reinventing the filter logic. This
; is exactly the tool fpga-lisp's own roadmap step 28 ("run the real
; Tier-1 fixtures, not a hand-picked subset") needs repeatedly during
; bring-up — friction here is friction there too.
;
; Usage:
;   cargo run -p my-lisp-cli -- scripts/fixtures-for-tier.lisp 1
; *argv* (added 2026-08-09 for scripts/release.lisp, general-purpose in
; my-lisp-cli since then) carries the tier as a string; assoc (added
; 2026-08-10, lib/core.lisp) replaced this file's own hand-rolled
; assoc-my — both were dead weight this script no longer needs to carry
; on its own, updated here as soon as the underlying gaps closed instead
; of leaving the workaround comment stale.

(def target-tier
  (cond
    ((atom? *argv*) () (missing-tier-argument))
    ((atom? *argv*) (1) (missing-tier-argument))
    (t (read (car *argv*)))))

; `missing-tier-argument` is deliberately unbound — calling it is a real
; named ErrorKind::UnknownSymbol (S2), not an invented ad-hoc error
; primitive, same convention scripts/release.lisp already uses for its own
; missing-argument case.
; `missing-tier-argument` навмисно незв'язаний — виклик дає реальну
; названу ErrorKind::UnknownSymbol (S2), не вигаданий ad-hoc примітив
; помилки, та сама конвенція, яку вже використовує scripts/release.lisp
; для власного випадку відсутнього аргументу.

(def fixture-tier
  (lambda (fixture)
    (cdr (assoc (quote tier) fixture))))

(def print-matching
  (lambda (remaining)
    (cond
      ((atom? remaining) () (quote ()))
      ((atom? remaining) (1) (quote ()))
      (t ((lambda ()
            (cond
              ((eq? (fixture-tier (car remaining)) target-tier)
               (print (car remaining)))
              (t (quote ())))
            (print-matching (cdr remaining))))))))

(print-matching (read-all (read-file "tests/fixtures/conformance.lisp")))
