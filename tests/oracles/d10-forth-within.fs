\ Independent Forth 2012 CORE EXT native-cell donor for WITHIN.
\ This is NOT SENS runtime and does NOT test an arbitrary 256/4096 modulus.
\ Its native-cell wrap is demonstrated by negative signed values.
: check-within ( test lo hi expected -- )
  >r within r> <> if
    cr ." D10-FORTH-WITHIN: FAIL"
    -1 throw
  then ;

0 0 0 0 check-within
0 0 1 -1 check-within
1 0 1 0 check-within
5 3 10 -1 check-within
10 3 10 0 check-within
3 3 10 -1 check-within
-1 -5 5 -1 check-within
-5 -5 5 -1 check-within
5 -5 5 0 check-within
-6 -5 5 0 check-within
0 5 -5 0 check-within
6 5 -5 -1 check-within
-6 5 -5 -1 check-within
-3 5 -5 0 check-within
7 7 7 0 check-within

cr ." D10-FORTH-WITHIN: PASS 15/15 native-cell Forth 2012 cases" cr
bye
