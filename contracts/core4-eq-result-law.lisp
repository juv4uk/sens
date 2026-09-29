; #1711 — RETIRED ACTIVE CONTRACT.
;
; The former Core4-specific EQ result law was part of the abandoned graded
; predicate experiment. Git history preserves the full research artifact.
;
; Current authority:
;   #1703 shared Core1-Core4 binary foundation
;   #1705 Function8 00000011 EQ law
;   #1709 Lisp-owned semantic witnesses
;
; Active law:
;   same admitted atom     -> exact one-bit YES
;   distinct admitted atom -> exact one-bit NO
;   pair/outside-domain    -> named domain/type error

(core4-eq-result-law/retired
  (status historical-only)
  (active-authority forbidden)
  (superseded-by shared-eq-one-bit)
  (function 00000011)
  (profile-specific-result-law forbidden)
  (graded-answer-projection deferred-research))