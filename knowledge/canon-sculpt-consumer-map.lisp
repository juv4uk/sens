; #419 consumer/dependency map. Audit navigation only.

(canon-sculpt-consumer-map
  (schema-version 1)
  (rule (read-only-consumer-audit))

  (candidate
    (identity PRIM_ATOM)
    (known-semantic-surface structural-kind)
    (migration-hazard "do not infer old t/() predicate behavior; current structural observation is richer"))
  (candidate
    (identity PRIM_EQ)
    (known-semantic-surface identity-relation)
    (migration-hazard "do not infer generic truthiness or host pointer identity"))
  (candidate
    (identity PRIM_COND)
    (consumer-hazard "control semantics include evaluation selection/order, so textual replacement is not a derivation proof"))
  (candidate
    (identity PRIM_QUOTE)
    (consumer-hazard "ordinary function consumers cannot reproduce suppression of argument evaluation without another control mechanism"))
  (candidate
    (identity PRIM_CONS)
    (consumer-hazard "construction consumers must be distinguished from pair representation/backend allocation"))
  (candidate
    (identity PRIM_CAR)
    (consumer-hazard "observation consumers must be distinguished from machine load/addressing mechanism"))
  (candidate
    (identity PRIM_CDR)
    (consumer-hazard "observation consumers must be distinguished from machine load/addressing mechanism"))

  (coordination-exclusion
    (active-work
      421
      418 410 406 396
      392
      328
      402 403
      409 413
      317))
  (next
    "replace each hazard-only row with mechanically discovered live consumers after current overlapping migrations settle; unknown stays unknown until then"))
