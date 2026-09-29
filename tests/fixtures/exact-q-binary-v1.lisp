; #1826 — exact-Q comparison predicate witnesses.
;
; `expected` is presentation only: PredicateBit YES/NO currently renders as
; "1"/"0". The semantic result domain is PredicateBit, never Number.
;
; Exact-Q is the admissibility rule for these predicates, not a numeric truth
; algebra. Outside-domain behavior is tracked separately as named domain/type
; failure and is intentionally not encoded as structural () here.

((expr . "(= 1/3 2/6)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . rational-equality-yes))

((expr . "(< 2/3 3/4)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . rational-less-yes))

((expr . "(> 2/3 3/4)")
 (expected . "0")
 (expected-domain . "predicate-bit")
 (case . rational-greater-no))

((expr . "(<= 1/3 1/3 2/3)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . rational-nondecreasing-yes))

((expr . "(>= 3/4 2/3 2/3)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . rational-nonincreasing-yes))

; #295 — strict comparison laws preserved after retiring the legacy Rust
; truth-sentinel test. The mathematical answer stays in the existing exact-Q
; result domain; no new host-side semantic oracle is introduced.
((expr . "(< 1 2 3)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . strict-chain-yes))

((expr . "(< 1 3 2)")
 (expected . "0")
 (expected-domain . "predicate-bit")
 (case . strict-chain-no))

((expr . "(< 5)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . strict-single-argument-vacuous-yes))


; Numeric canonicalization remains a Number-domain law, separate from
; PredicateBit. These rows prove only that 0/1 and 1/1 are ordinary exact
; rational spellings that compact to numeric 0 and 1.
((expr . "(= 0 0/1)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . zero-and-zero-over-one-are-the-same-exact-q-value))

((expr . "(= 1 1/1)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . one-and-one-over-one-are-the-same-exact-q-value))

((expr . "(list 0 0/1 1 1/1)")
 (expected . "(0 0 1 1)")
 (case . denominator-one-source-spellings-write-canonically))
