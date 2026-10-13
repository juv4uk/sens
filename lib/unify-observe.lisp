; SENS exact-domain migration of the historical unification observer.
; D4:0011 owns both definitions; D4:0010 owns argument binding.
; D3:010 tests the raw result's structural shape before D3:101 EQ.
; The private historical atom fail is compared ONLY after ATOM is true.
; Empty substitution () is a successful result, never failure or D1:0.
; The bare surface unify is an already existing compatibility mechanism;
; it is invoked exactly once. No historical D6 LET/D9 callability is inferred.
; The fallbacks use D3 ATOM on D3 empty (), yielding exact D1:1.
; The runtime law remains SENS-owned; the host may inspect transport only.
; Separate physical binary self-witness: tests/semantic/unify-observe-d1-fallback-law.sens

(0011 уніфікація-спостереження-стан
  (0010 (raw left right substitution)
    (110
      ((010 raw)
       (110
         ((101 raw (001 fail))
          (1110 (001 unification-failure) left right substitution))
         ((010 ())
          (1110 (001 unified) raw))))
      ((010 ())
       (1110 (001 unified) raw)))))

(0011 unify-observe
  (0010 (left right substitution)
    (уніфікація-спостереження-стан
      (unify left right substitution)
      left right substitution)))
