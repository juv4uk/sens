; Core4 predicate-answer boundary projection — Lisp-owned law for #1256.
;
; Scope is deliberately narrow:
;   * the two endpoint Sid8 identities remain distinct;
;   * the predicate-answer scale may project either endpoint to the same ();
;   * bare Sid8 evaluation and callable dispatch are NOT changed by this law.
;
; In particular this file must never be interpreted as:
;   00000000 == 11111111
; or as permission to make 11111111 an alias of Canon 0.
;
; The projection belongs only to the Core4 predicate-answer boundary introduced
; by #1254/#1255.  First-class SID identity and fail-closed callable behavior
; remain independent concerns.

(core4-predicate-answer-boundary/1

  ((profile . core4)
   (scope . predicate-answer-boundary)
   (answer-scale . "contracts/core4-predicate-answer-scale.lisp")
   (sid-identity . preserved)
   (bare-sid-evaluation . unchanged)
   (callable-dispatch . unchanged)
   (unknown-callable-fail-closed . preserved))

  ((endpoint . lower)
   (direction . no)
   (last-directed-answer-spelling . "0000000")
   (sid-anchor . 00000000)
   (projection . ()))

  ((endpoint . upper)
   (direction . yes)
   (last-directed-answer-spelling . "1111111")
   (sid-anchor . 11111111)
   (projection . ()))

  ((laws . boundary)
   (sid-alias . forbidden)
   (sid-equality . forbidden)
   (projection-equality . required)
   (eighth-directed-step . empty-list)
   (other-sid-ground-projection . forbidden)
   (core1-core2-core3-impact . none)))
