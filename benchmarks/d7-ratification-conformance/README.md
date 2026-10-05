# D7 role-boundary conformance — historical #2517 evidence

Historical owner evidence: #2415 / #2490. Current authority: Contract 11.6 / #3572 owner-ratifies D7 at 126/128. This witness preserves the role firewall; occupancy authority lives separately in `knowledge/d7-ratified.json`.

This witness keeps three concepts separate even when the raw payload looks
identical:

- `D7.SoundCell(bits)`
- `D7.LocalOrdinal(bits)`
- arithmetic `Number(value)`

A D7 local ordinal is only local śloka/sūtra numbering/provenance. It does not
inherit arithmetic Number operations. A D7 ordinal may link to a D14 grammar
node for provenance, but that link does not import D14 grammatical semantics.

The witness itself makes no occupancy claim over the 128 width-valid D7 coordinates; Contract 11.6 separately ratifies 126 residents and keeps two coordinates owner-reserved/pinned.
