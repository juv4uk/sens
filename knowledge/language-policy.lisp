; Мовна політика екосистеми my-lisp.
; Ратифіковано прямою настановою власника 2026-09-07.
;
; Цей контракт стосується ВСЬОГО людського тексту у власних репозиторіях,
; Git, GitHub, CI, релізах, задачах, комітах, повідомленнях агентів та діалозі.
; Для нових людських назв Git-гілок: українська, якщо підтримує інтерфейс.
; Він НЕ скасовує окремі
; програмні surface мови (зокрема Sanskrit surface), канонічні ідентичності,
; зовнішні API, точні назви символів, протоколів, файлів чи upstream-термінів.

(0011 *language-policy*
  (001
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
        (identifiers-and-protocol-literals-preserved . t)
        (git-tasks-and-issues-ukrainian-first . t)
        (git-pull-requests-and-reviews-ukrainian-first . t)
        (git-commit-subject-and-body-ukrainian-first . t)
        (git-branch-human-names-ukrainian-first . t)
        (all-agent-and-owner-messages-ukrainian-first . t)
        (workflow-job-and-ci-human-labels-ukrainian-first . t)
        (release-and-project-human-names-ukrainian-first . t)
        (git-ci-bot-human-text-ukrainian-first . t)
        (human-text-any-channel-ukrainian-first . t)
        (machine-token-exceptions-are-not-prose-exceptions . t)
        (existing-git-history-no-language-only-rewrite . t)))
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
        guard-summaries
        git-issue-titles-bodies-and-comments
        git-pull-request-titles-bodies-and-reviews
        git-commit-subject-and-body
        git-branch-human-names
        git-workflow-and-job-human-labels
        human-agent-messages-and-bus
        all-owner-facing-and-agent-facing-channels
        git-project-tasks-and-agent-statuses
        git-ci-bot-human-messages
        release-titles-and-notes))
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
        (bulk-rewrite . separate-reviewed-task)
        (existing-git-issues-and-prs . migrate-when-touched)
        (existing-git-commit-history . preserve-without-rewrite)))
     (evidence .
       ((guard-topic . language-policy)
        (guard-scope-topic . owner-authored-repository-scope)
        (guard-tool . uk-latynka)
        (encoding . utf-8)
        (round-trip-check . "python3 scripts/uk-latynka.py self-test")
        (latynka-use . "auxiliary only when an explicit non-Unicode boundary requires ASCII"))))))
