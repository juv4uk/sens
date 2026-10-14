; SENS owns the verdict: D3 EQ/COND compares exact D1; failure calls D1:NO.
; First five laws must succeed; last form mutates one D1 bit of the first.
(110 ((101 (source-ref? (001 (digest packet))) #d1:1) #d1:1) (#d1:1 (#d1:0)))
(110 ((101 (source-ref? (001 (proof packet))) #d1:1) #d1:1) (#d1:1 (#d1:0)))
(110 ((101 (source-ref? (001 (unknown packet))) #d1:0) #d1:1) (#d1:1 (#d1:0)))
(110 ((101 (source-ref? (001 ((digest) packet))) #d1:0) #d1:1) (#d1:1 (#d1:0)))
(110 ((101 (source-ref? (001 ())) #d1:0) #d1:1) (#d1:1 (#d1:0)))
(110 ((101 (source-ref? (001 (digest packet))) #d1:0) #d1:1) (#d1:1 (#d1:0)))
