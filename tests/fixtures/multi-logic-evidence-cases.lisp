; #219 MULTI-LOGIC-RESEARCH-1
; Data-only research corpus. These forms are observations to compare across
; candidate projections. They are NOT ratified truth values or language laws.
;
; Shape:
;   (evidence-case ID
;     (positive SOURCES...)
;     (negative SOURCES...)
;     (search STATE)
;     (note ...))
;
; Canon 0 / () is deliberately represented by the absence of an evidence-case
; value at the language boundary. E0 below is a named laboratory specimen so
; candidate projections can be compared without redefining () itself.

(evidence-case E0
  (positive)
  (negative)
  (search not-started)
  (note canon-zero-ocean-before-projection))

(evidence-case E1
  (positive (source prolog proof-1))
  (negative)
  (search completed)
  (note one-positive-derivation))

(evidence-case E2
  (positive)
  (negative (source knowledge explicit-negative-1))
  (search completed)
  (note one-explicit-negative-derivation))

(evidence-case E3
  (positive (source prolog proof-1))
  (negative (source datalog counter-evidence-1))
  (search completed)
  (note independent-positive-and-negative-evidence))

(evidence-case E4
  (positive
    (source prolog proof-1)
    (source prolog proof-2)
    (source datalog derivation-7))
  (negative)
  (search completed)
  (note three-independent-positive-derivations))

(evidence-case E5
  (positive)
  (negative)
  (search incomplete)
  (note no-result-yet-is-not-completed-no-evidence))

(evidence-case E6
  (positive)
  (negative)
  (search completed-zero-answers)
  (note completed-zero-answer-search-is-a-search-fact-not-false))

; Expected *research projections*. These describe what a candidate can express,
; not what my-lisp must mean.
(candidate-expectation classical
  (E0 outside)
  (E1 true)
  (E2 false)
  (E3 unsupported-without-extra-policy)
  (E4 true-provenance-collapses)
  (E5 outside)
  (E6 outside))

(candidate-expectation k3
  (E0 indeterminate-if-explicitly-projected)
  (E1 true)
  (E2 false)
  (E3 no-distinct-both-state)
  (E4 true-provenance-collapses)
  (E5 indeterminate-if-explicitly-projected)
  (E6 indeterminate-if-explicitly-projected))

(candidate-expectation lp
  (E0 no-distinct-gap-state)
  (E1 true)
  (E2 false)
  (E3 both)
  (E4 true-provenance-collapses)
  (E5 no-distinct-gap-state)
  (E6 no-distinct-gap-state))

(candidate-expectation belnap-dunn-four
  (E0 neither-if-explicitly-projected)
  (E1 true-only)
  (E2 false-only)
  (E3 both)
  (E4 true-only-provenance-collapses)
  (E5 neither-if-explicitly-projected-search-state-still-external)
  (E6 neither-if-explicitly-projected-search-state-still-external))

(candidate-expectation lukasiewicz-l3
  (E0 middle-requires-extra-interpretation)
  (E1 true)
  (E2 false)
  (E3 middle-is-lossy-for-evidence-conflict)
  (E4 true-provenance-collapses)
  (E5 middle-requires-extra-interpretation)
  (E6 middle-requires-extra-interpretation))
