# 4455 bounded CAR/CDR/CONS migration canary

Two historical Core1 sources use proven legacy SID8 heads for CAR, CDR, CONS and QUOTE/EMPTY. The real three-pass migrator projects them to current exact D3/D2 words, then to physical T5 `.sens` bytes. The `.lisp` files remain provenance.
