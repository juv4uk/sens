# Ratified D7 conformance — #2517

Owner authority: #2415 / #2490.

This witness keeps three concepts separate even when the raw payload looks
identical:

- `D7.SoundCell(bits)`
- `D7.LocalOrdinal(bits)`
- arithmetic `Number(value)`

A D7 local ordinal is only local śloka/sūtra numbering/provenance. It does not
inherit arithmetic Number operations. A D7 ordinal may link to a D14 grammar
node for provenance, but that link does not import D14 grammatical semantics.

The witness makes no occupancy claim over the 128 width-valid D7 coordinates.
