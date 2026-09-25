; Runtime policy for the first Rust + WSM Guard vertical slice.
; Runtime-політика першого вертикального зрізу Rust + WSM Guard.
;
; This is deliberately small. It demonstrates that Rust supplies normalized
; facts while WSM owns classification and can change it without recompilation.
; Політика навмисно мала: Rust подає нормалізовані факти, а WSM визначає
; класифікацію й може змінювати її без перекомпіляції.

(def guard-evaluate
  (lambda (kind subject evidence)
    (cond
      ((eq? evidence (quote missing))
       (guard-unknown subject (quote runtime-evidence) (quote ask-agent)))
      ((eq? kind (quote read))
       (make-guard-finding
         (quote allow) (quote confirmed) subject kind (quote read-only)
         (quote ()) (quote no-state-change) (quote continue) (list evidence)))
      ((eq? kind (quote write))
       (make-guard-finding
         (quote warn) (quote partial) subject kind (quote review-write-scope)
         (quote mutation-requested) (quote state-may-change)
         (quote verify-authority-and-target) (list evidence)))
      ((eq? kind (quote destructive))
       (make-guard-finding
         (quote reject) (quote confirmed) subject kind
         (quote explicit-owner-authority-required)
         (quote authority-not-present) (quote irreversible-impact)
         (quote ask-owner) (list evidence)))
      (t (guard-unknown subject (quote unclassified-event-kind)
           (quote choose-unknown-route))))))
