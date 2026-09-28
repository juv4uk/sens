; #219 — first reasoning-honesty witness.
; Absence of a proof for P is not evidence for (not P).
;
; Historical negation-as-failure proves (safe ocean) from the rule below merely
; because no (danger ocean) proof exists. Under Canon 0 accumulator semantics,
; that missing proof remains unspecialized as (), so the outer goal must not be
; fabricated as proved.

((expr . "(reason (quote (safe ocean)) (quote (((safe (var x)) (not (danger (var x)))))))")
 (expected . "()")
 (active . t)
 (law . no-proof-is-not-negation))
