; Мовна політика екосистеми my-lisp.
; Ратифіковано прямою настановою власника 2026-09-07.
;
; Цей контракт стосується людської комунікації в репозиторії: документації,
; інструкцій агентам, пояснень і коментарів у коді. Він НЕ скасовує окремі
; програмні surface мови (зокрема Sanskrit surface), канонічні ідентичності,
; зовнішні API, точні назви символів, протоколів, файлів чи upstream-термінів.

(00001001 *language-policy*
  (00000001
    ((schema . language-policy/1)
     (status . ratified)
     (ratified-at . "2026-09-07")
     (text-encoding . utf-8)
     (primary-language . ukrainian)
     (auxiliary-languages . (english german))
     (human-facing-order . (ukrainian english german))
     (repository-scope . all-owner-authored-repositories)
     (owner-phrase-all-my-repos . all-owner-authored-repositories)
     (authorship-authority . ../ecosystem/docs/policy/REPOSITORIES-LICENSE-AUDIT.md)
     (code-comments . ukrainian-utf8)
     (transliteration-contract . uk-latynka/1)
     (transliterator . scripts/uk-latynka.py)
     (transliteration-role . auxiliary-interoperability-tool)
     (rules .
       ((ukrainian-first . t)
        (auxiliary-may-follow-ukrainian . t)
        (auxiliary-must-not-replace-ukrainian . t)
        (repository-text-utf8 . t)
        (new-code-comments-ukrainian-cyrillic . t)
        (edited-code-comments-migrate-to-ukrainian . t)
        (latynka-not-default-comment-style . t)
        (latynka-only-for-explicit-non-unicode-boundary . t)
        (mass-comment-rewrite-without-task . ())
        (exact-upstream-spelling-preserved . t)
        (identifiers-and-protocol-literals-preserved . t)))
     (repository-boundary .
       ((include . owner-authored-repositories)
        (include-authored-repository-with-third-party-notices . shiva-sutras)
        (exclude . (forks mirrors vendored-dependencies third-party-upstreams))
        (account-or-local-presence-proves-authorship . ())))
     (scope .
       (agent-instructions
        human-facing-documentation
        code-comments
        explanatory-prose
        guard-summaries))
     (outside-scope .
       (canonical-programming-identities
        programming-language-surfaces
        sanskrit-domain-surface
        exact-upstream-quotes
        external-api-identifiers
        protocol-literals
        filenames))
     (migration .
       ((existing-english-or-german-prose . migrate-when-touched)
        (existing-non-ukrainian-code-comments . migrate-when-touched)
        (bulk-rewrite . separate-reviewed-task)))
     (evidence .
       ((guard-topic . language-policy)
        (guard-scope-topic . owner-authored-repository-scope)
        (guard-tool . uk-latynka)
        (encoding . utf-8)
        (round-trip-check . "python3 scripts/uk-latynka.py self-test")
        (latynka-use . "auxiliary only when an explicit non-Unicode boundary requires ASCII"))))))
