; docs/uk-projection-status.lisp — стан укр-проєкції (дані, не блокер)
; Оновлено агентом міграції. Без HOLD/FREEZE.

(uk-projection-status/1
  (sid8-call-heads . retired)
  (latin-call-heads . retired-in-active-code)
  (domains-d1-d10 . binary-keys-as-address-not-call-heads)
  (bija3-labels . domain-identity-not-call-heads)
  (surface-tables . map-sid-to-uk-names)
  (boot . racket/boot/core-ukr)
  (fixtures . cohorts-canaries-semantic-conformance-ukr)
  (scripts . verify-repo-ukr)
  (release-lexical . near)
  (release-physical-sens-run . required-for-release)
  (blockers . none))
