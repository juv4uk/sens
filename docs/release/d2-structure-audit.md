# D2 structure audit — release blocker #4160

**Current authority:** Contract 11.8 / D1–D9  
**Invariant:** D2 alone owns canonical language structure.

```text
00 separator
01 close
10 open
11 dot
```

Audit scope:

| Path | Status | Result |
| --- | --- | --- |
| canonical_reader.rs | PASS | W2 only owns list structure; W1/W3–W9 remain payload identities |
| source_words.rs | PASS | exact widths W1–W9 preserved; no competing structural meaning |
| migrate-three-pass.py | PASS | emits D2 structure and rejects W2 as head/data |
| translate-domain-program.py | PASS | display-only structural labels are never translated into source structure |
| source_packing.rs | PASS | semantic payload packing is separate from framing/boundary metadata |
| binary_framing.rs | DEBT-OWNED #4164 | private framing still uses stale CONTROL_* naming on current main |

The binary_framing debt is not a second semantic authority: the file already states that framing tags are metadata, not the canonical semantic payload. PR #4164 finishes the naming/claim separation by replacing private CONTROL_* with WIRE_* and explicitly protecting D2:11 DOT from wire escape.

The guard accepts exactly two states:
1. current owned debt exists and is still assigned to #4164;
2. #4164 has landed and WIRE_* transport tags are present.

It never accepts transport framing becoming D2 language semantics.

Release rule: #4164 must resolve the owned debt before l0.42.0 freeze.
