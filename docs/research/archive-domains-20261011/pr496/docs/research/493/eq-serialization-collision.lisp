; #493 EQ serialization collision
; Research-only. NOT semantic authority. NO production change.

(eq-serialization-collision/2
  (issue 493)
  (parent 471)
  (grandparent 419)
  (role research-only)

  (target
    (identity "0003")
    (surface eq)
    (input-domain (atom atom))
    (result-domain identity-relation))

  (live-boundary
    (closure-equality allocation-identity)
    (write-to-string-rendering closure "<lambda>")
    (important
      "Identity information is already lost at serialization; the particular exact-text comparator used afterwards cannot reconstruct information absent from the serialized representation."))

  (candidate-route
    (name serialized-text-equality)
    (allowed write-to-string string<? cond lambda/application quote)
    (forbidden eq eq-aliases host-Value-equality)
    (shape
      ((lambda (left right)
         ((lambda (left-text right-text)
            (cond
              ((string<? left-text right-text) ()
               (cond
                 ((string<? right-text left-text) () (quote text-same))
                 ((quote fallback) fallback (quote text-distinct))))
              ((quote fallback) fallback (quote text-distinct))))
          (write-to-string left)
          (write-to-string right)))
       LEFT RIGHT)))

  (predictions-and-observations
    (same-closure
      (predicted-eq (identity-relation same))
      (observed-eq (identity-relation same)))
    (two-fresh-closures
      (predicted-eq (identity-relation distinct))
      (observed-eq (identity-relation distinct))
      (predicted-left-serialization "<lambda>")
      (observed-left-serialization "<lambda>")
      (predicted-right-serialization "<lambda>")
      (observed-right-serialization "<lambda>")
      (predicted-text-route text-same)
      (observed-text-route text-same))
    (distinct-symbol-control
      (left radio)
      (right antenna)
      (predicted-text-route text-distinct)
      (observed-text-route text-distinct)))

  (invalid-observer-run
    (verification-pr 495)
    (actions-run 35285903457)
    (verification-head "2baefdffeef562e1981af79476f0b4e0de8501e8")
    (status invalid-observer)
    (reason
      "The generated temporary Rust test contained malformed quoting for the expected string literal and did not compile; it produced no semantic evidence."))

  (fresh-run
    (verification-pr 495)
    (actions-run 35286031013)
    (verification-head "96c50d864f32b8b4da2a2358fc6e37a16946eba3")
    (runner ubuntu-24.04)
    (observer temporary-integration-test-removed-before-diff-check)
    (tests 4)
    (passed 4)
    (failed 0)
    (same-closure-eq pass)
    (fresh-closures-eq-distinct pass)
    (closure-serialization-collision pass)
    (no-eq-text-route-false-positive pass)
    (distinct-symbol-control pass)
    (diff-check pass))

  (classification
    (route serialization/text->EQ)
    (result route-falsified-by-serialization-collision))

  (classification-reason
    "Two separately allocated closures are admitted EQ atoms and are EQ-distinct, but write-to-string maps both to the same text <lambda>. A route restricted to serialized text therefore cannot preserve closure identity: the executed no-EQ text route classified the distinct closures as text-same. The information loss occurs before text equality is applied.")

  (bounded-consequence
    "Current write-to-string is a presentation/serialization observation, not an injective encoding of EQ identity across the full atom domain. It cannot by itself serve as a lower semantic basis for EQ.")

  (surviving-hypotheses
    (other-weaker-dynamic-identity-observer
      "Still open only if it preserves all admitted atom identity distinctions without simply renaming host Value equality.")
    (restricted-serializable-subdomain
      "A serialization-based equality may be valid for a narrower explicitly admitted data subdomain, but that would not derive full PRIM_EQ."))

  (non-claims
    no-global-eq-irreducibility-proof
    no-writer-bug-claim
    no-string-comparison-reclassification
    no-canon-change-authorized
    no-production-change-authorized))
