; #834 — mathematical-law coordinate axis.
;
; Composition-only view over existing Lisp-owned semantic identities.
; This file does NOT mint SIDs and does not define runtime meaning.
; Canonical identity source: lib/surface/semantic-registry.lisp (sr/2).
; Existing law/result authorities remain:
;   #216 exact-Q binary domain,
;   #218 structural observation / identity relations,
;   #217 explicit-result control dispatch.
;
(semantic-mathematical-coordinate/1
  (authority-source . "lib/surface/semantic-registry.lisp")
  (axis . mathematical-law)
  (scope . bounded-first-slice)
  (rows
    (((sid . "00001100")
      (status . witnessed)
      (domain . exact-rational)
      (law . addition-result)
      (witness . "tests/fixtures/semantic-coordinate-math-834.lisp"))
     ((sid . "00000011")
      (status . witnessed)
      (domain . atom-identity)
      (law . identity-relation)
      (witness . "tests/fixtures/semantic-coordinate-math-834.lisp"))
     ((sid . "00000100")
      (status . witnessed)
      (domain . structural-pair)
      (law . cons-car-equation)
      (witness . "tests/fixtures/semantic-coordinate-math-834.lisp"))
     ((sid . "00000101")
      (status . witnessed)
      (domain . structural-pair)
      (law . car-cons-equation)
      (witness . "tests/fixtures/semantic-coordinate-math-834.lisp"))
     ((sid . "00000111")
      (status . no-mathematical-law-witness)
      (domain . control-semantics)
      (law . ())
      (witness . "tests/fixtures/semantic-coordinate-math-834.lisp")))))
