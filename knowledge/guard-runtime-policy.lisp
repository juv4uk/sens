; Runtime policy for the first Rust + WSM Guard vertical slice.
; Runtime-політика першого вертикального зрізу Rust + WSM Guard.
;
; This is deliberately small. It demonstrates that Rust supplies normalized
; facts while WSM owns classification and can change it without recompilation.
; Політика навмисно мала: Rust подає нормалізовані факти, а WSM визначає
; класифікацію й може змінювати її без перекомпіляції.

(00001001 guard-evaluate
  (00001000 (kind subject evidence)
    (00000111
      ((00000011 evidence (00000001 missing))
       (guard-unknown subject (00000001 runtime-evidence) (00000001 ask-agent)))
      ((00000011 kind (00000001 read))
       (make-guard-finding
         (00000001 allow) (00000001 confirmed) subject kind (00000001 read-only)
         (00000001 ()) (00000001 no-state-change) (00000001 continue) (00100111 evidence)))
      ((00000011 kind (00000001 write))
       (make-guard-finding
         (00000001 warn) (00000001 partial) subject kind (00000001 review-write-scope)
         (00000001 mutation-requested) (00000001 state-may-change)
         (00000001 verify-authority-and-target) (00100111 evidence)))
      ((00000011 kind (00000001 destructive))
       (make-guard-finding
         (00000001 reject) (00000001 confirmed) subject kind
         (00000001 explicit-owner-authority-required)
         (00000001 authority-not-present) (00000001 irreversible-impact)
         (00000001 ask-owner) (00100111 evidence)))
      (t (guard-unknown subject (00000001 unclassified-event-kind)
           (00000001 choose-unknown-route))))))
