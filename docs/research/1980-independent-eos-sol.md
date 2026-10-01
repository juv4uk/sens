# #1980 independent EOS review — GPT-5.6 Sol

This implementation was written from the descriptions in issues #1971 and #1980.
It did not inspect `scripts/research-1971-unique-decoding.py`.

Bound:
- every binary word of widths 1..4;
- every sequence of 0..3 such words;
- 27,931 sequences including the empty sequence;
- strict-decoder sweep over every raw bit string of lengths 0..16.

Candidate A:
- widths 1..7: 3-bit header = width-1;
- wider widths: `111` + Elias-gamma(width-7);
- payload follows the width header.

Candidate B:
- Elias-gamma(width);
- payload follows the width header.

Results:

```text
A width3+escape
  sequences=27931
  roundtrip_fail=0
  raw_collisions=0
  strict_noncanonical_accepted=0
  zero_padding_misread=26390
  zero_padding_shared_wires=386
  stop_bit_misread=0
  gamma_length_prefix_misread=0

B gamma-only
  sequences=27931
  roundtrip_fail=0
  raw_collisions=0
  strict_noncanonical_accepted=0
  zero_padding_misread=20602
  zero_padding_shared_wires=0
  stop_bit_misread=0
  gamma_length_prefix_misread=0
```

The racanā2 words `00 01 10 11`, including dot `11`, round-trip as ordinary
payload words in both envelopes.

## Independent conclusion

The published #1980 numbers reproduce exactly under an independent encoder and
decoder.

Plain byte-zero-padding is not an EOS mechanism. The ambiguity/error is at the
**message container boundary**, not in semantic word identity.

A stop bit or explicit meaningful-bit length both solve the bounded test without
stealing any language word.

## Simpler candidate C for follow-up

If the surrounding transport already frames a byte message, it need not make the
inner bitstream self-terminating. The container can carry only:

```text
payload bytes
+ valid bits in final byte   (1..8)
```

or equivalently the total meaningful bit length.

This is transport metadata, not a SENS word. It can be compared against:
- suffix stop bit;
- gamma total-length prefix.

The useful law is:

```text
word codec owns word decoding
message container owns end-of-stream
```

Self-termination should be required only for channels that genuinely lack an
outer message boundary.
