; #4157 / #4158 — D2 is the sole owner of canonical language structure/control.
;
; This contract is about source/reader structure, not evaluator control flow.
; D3+ semantic operations may affect evaluation but may not mint a competing
; separator/open/close/dot grammar or reinterpret W2 as ordinary payload.

(d2-language-control-contract/1
  ((owner-domain . D2)
   (owner-width . 2)
   (separator . 00)
   (close . 01)
   (open . 10)
   (dot . 11)
   (w2-callable-head . forbidden)
   (w2-ordinary-data . forbidden)
   (d3+-structural-delimiter . forbidden)
   (transport-framing-is-language-semantics . forbidden)
   (transport-private-tags . allowed)
   (transport-may-reinterpret-d2-11 . forbidden)
   (evaluator-control-flow-outside-d2 . out-of-scope)))
