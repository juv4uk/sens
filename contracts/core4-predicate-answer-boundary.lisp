; Core4 predicate-answer endpoint law — Lisp-owned authority for #1336.
;
; Scope:
;   * the directed NO/YES paths terminate at distinct function-SID endpoints;
;   * () is an independent structural/undirected value outside function-SID space;
;   * bare endpoint SID evaluation and callable dispatch are not redefined here.
;
; Directed law:
;   NO  : 0 -> 00 -> ... -> 0000000 -> 00000000
;   YES : 1 -> 11 -> ... -> 1111111 -> 11111111
;
; This contract MUST NOT be interpreted as:
;   00000000 == ()
;   11111111 == ()
;   00000000 == 11111111
;
; What either endpoint function returns when invoked is a separate function law.

(core4-predicate-answer-boundary/2

  ((profile . core4)
   (scope . predicate-answer-endpoints)
   (answer-scale . "contracts/core4-predicate-answer-scale.lisp")
   (sid-space . function-only)
   (empty-list-space . structural-value)
   (sid-identity . preserved)
   (bare-sid-evaluation . unchanged)
   (callable-dispatch . unchanged))

  ((endpoint . no)
   (direction . no)
   (last-directed-answer-spelling . "0000000")
   (sid-endpoint . 00000000)
   (endpoint-kind . function-sid)
   (empty-list-alias . forbidden))

  ((endpoint . yes)
   (direction . yes)
   (last-directed-answer-spelling . "1111111")
   (sid-endpoint . 11111111)
   (endpoint-kind . function-sid)
   (empty-list-alias . forbidden))

  ((undirected-answer . ())
   (kind . structural-empty-value)
   (function-sid . none))

  ((laws . boundary)
   (sid-alias . forbidden)
   (sid-equality . forbidden)
   (endpoint-to-empty-list-projection . forbidden)
   (eighth-directed-step . reaches-function-sid-endpoint)
   (endpoint-invocation-law . separate)
   (core1-core2-core3-impact . none)))
