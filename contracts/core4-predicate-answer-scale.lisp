; Core4 predicate-answer scale — Lisp-owned semantic data for #1255.
;
; This file defines ONLY the answer domain for Core4 predicates.
; It is not a function/SID registry and does not mint or alias any SID.
;
; Core law:
;   answer ::= 0^n | 1^n | ()
;   n = 1..7
;
; Exactly eight bare bits remain the independent Sid8 lexical space.
; Until #1257 teaches the reader to preserve 1..7-bit homogeneous spellings,
; the short answers below are stored as exact spelling strings.  The strings
; are transport for this contract only; the intended public values are the
; bit spellings themselves, never (truth ...), confidence records, percentages,
; or a fifteen-case semantic enum.
;
; Sanskrit notes are terminology anchors, not a claim that a historical
; eight-level Nyaya scale existed.  The vocabulary is deliberately modest:
;   dṛḍha-niścaya — firm certainty / firm conviction
;   niścaya       — ascertainment, conviction, certainty
;   nirṇaya       — decision / ascertainment
;   saṃbhāvanā    — supposition / possibility
;   saṃśaya       — doubt / uncertainty
;   aniścaya      — uncertainty / indecision
;   ajñāta        — unknown
; Level 7 uses the my-lisp compound ajñāta-sīmā ("unknown-boundary") to mark
; the last directed answer immediately before the shared () boundary.
;
; Lexical sources consulted for the Sanskrit anchors:
; Monier-Williams / Macdonell / Apte entries surfaced by SanskritDictionary:
; niścaya, aniścaya, saṃśaya, saṃbhāvanā, ajñāta, sīmā.
;
; IMPORTANT:
;   00000000 and 11111111 below are Sid8 boundary anchors only.
;   They remain distinct SID identities.  Their relation to () is a projection
;   question owned by #1256, not an equality/alias law in this table.

(core4-predicate-answer-scale/1

  ((identity . predicate-answer-domain)
   (profile . core4)
   (status . proposed-1255)
   (answer-grammar . "0^n | 1^n | (), n=1..7")
   (semantic-form . homogeneous-bits)
   (runtime-cutover . pending-1257)
   (sid-space . unchanged-00000000-through-11111111)
   (probability-model . forbidden)
   (host-bool-authority . forbidden)
   (record-wrapper . forbidden))

  ((direction . no)
   (bit . "0")
   (levels .
     (("0"       1 dṛḍha-niścaya)
      ("00"      2 niścaya)
      ("000"     3 nirṇaya)
      ("0000"    4 saṃbhāvanā)
      ("00000"   5 saṃśaya)
      ("000000"  6 aniścaya)
      ("0000000" 7 ajñāta-sīmā))))

  ((boundary . ())
   (sanskrit . ajñāta)
   (meaning-uk . "невідомо")
   (lower-sid-anchor . 00000000)
   (upper-sid-anchor . 11111111)
   (sid-alias . forbidden)
   (projection-owner . issue-1256))

  ((direction . yes)
   (bit . "1")
   (levels .
     (("1"       1 dṛḍha-niścaya)
      ("11"      2 niścaya)
      ("111"     3 nirṇaya)
      ("1111"    4 saṃbhāvanā)
      ("11111"   5 saṃśaya)
      ("111111"  6 aniścaya)
      ("1111111" 7 ajñāta-sīmā))))

  ((algebra . minimal)
   (not-law . same-width-bit-inversion)
   (weakening-law . append-same-bit)
   (boundary-law . eighth-directed-step-projects-to-empty-list)
   (and-or-cond-law . deliberately-unratified)))
