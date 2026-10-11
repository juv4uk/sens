; Runtime policy for the first Rust + WSM Guard vertical slice.
; Runtime-політика першого вертикального зрізу Rust + WSM Guard.
;
; This is deliberately small. It demonstrates that Rust supplies normalized
; facts while WSM owns classification and can change it without recompilation.
; Політика навмисно мала: Rust подає нормалізовані факти, а WSM визначає
; класифікацію й може змінювати її без перекомпіляції.

(0011 guard-evaluate
  (0010 (kind subject evidence)
    (110
      ((101 evidence (001 missing))
       (guard-unknown subject (001 runtime-evidence) (001 ask-agent)))
      ((101 kind (001 read))
       (make-guard-finding
         (001 allow) (001 confirmed) subject kind (001 read-only)
         (001 ()) (001 no-state-change) (001 continue) (1110 evidence)))
      ((101 kind (001 write))
       (make-guard-finding
         (001 warn) (001 partial) subject kind (001 review-write-scope)
         (001 mutation-requested) (001 state-may-change)
         (001 verify-authority-and-target) (1110 evidence)))
      ((101 kind (001 destructive))
       (make-guard-finding
         (001 reject) (001 confirmed) subject kind
         (001 explicit-owner-authority-required)
         (001 authority-not-present) (001 irreversible-impact)
         (001 ask-owner) (1110 evidence)))
      (1 (guard-unknown subject (001 unclassified-event-kind)
           (001 choose-unknown-route))))))
