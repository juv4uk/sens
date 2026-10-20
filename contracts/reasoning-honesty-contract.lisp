; #219/#244 — контракт чесності міркування, власність Lisp.
; Чисті дані: міркування може спеціалізувати лише те, що справді встановлює.

(reasoning-honesty-contract/1
  ((law . no-proof-is-not-negation)
   (observed . no-proof)
   (forbidden-specialization . proved-not)
   (unspecialized-result . ()))

  ((law . explicit-negation-requires-evidence)
   (result . proved-not)
   (requires . explicit-negative-evidence))

  ((law . canon-zero-is-not-refutation)
   (left . ())
   (not-equal . (proved-not refuted false 0/1)))

  ((law . missing-module-is-blocked)
   (observed . module-absent-after-complete-journal-scan)
   (result . blocked)
   (reason-form . (module-not-found name))
   (forbidden-specialization . unknown))

  ((law . no-evidence-is-not-unknown)
   (observed . neither-side-proved)
   (requires-for-unknown . named-completeness-or-search-contract)
   (forbidden-default-specialization . unknown)
   (unspecialized-result . ())))
