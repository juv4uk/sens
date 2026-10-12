(0011 x86-reg-code
  (0010 (register)
    (110
      ((101 register (001 rax)) 0)
      ((101 register (001 al)) 0)
      ((101 register (001 rcx)) 1)
      ((101 register (001 cl)) 1)
      ((101 register (001 rdx)) 2)
      ((101 register (001 dl)) 2)
      ((101 register (001 rbx)) 3)
      ((101 register (001 bl)) 3)
      ((101 register (001 rsp)) 4)
      ((101 register (001 spl)) 4)
      ((101 register (001 rbp)) 5)
      ((101 register (001 bpl)) 5)
      ((101 register (001 rsi)) 6)
      ((101 register (001 sil)) 6)
      ((101 register (001 rdi)) 7)
      ((101 register (001 dil)) 7)
      ((101 register (001 r8)) 8)
      ((101 register (001 r8b)) 8)
      ((101 register (001 r9)) 9)
      ((101 register (001 r9b)) 9)
      ((101 register (001 r10)) #d10)
      ((101 register (001 r10b)) #d10)
      ((101 register (001 r11)) #d11)
      ((101 register (001 r11b)) #d11)
      ((101 register (001 r12)) 12)
      ((101 register (001 r12b)) 12)
      ((101 register (001 r13)) 13)
      ((101 register (001 r13b)) 13)
      ((101 register (001 r14)) 14)
      ((101 register (001 r14b)) 14)
      ((101 register (001 r15)) 15)
      ((101 register (001 r15b)) 15)
      ((010 (001 ())) (001 ())))))

(0011 x86-xmm-reg-code
  (0010 (register)
    (110
      ((101 register (001 xmm0)) 0)
      ((101 register (001 xmm1)) 1)
      ((101 register (001 xmm2)) 2)
      ((101 register (001 xmm3)) 3)
      ((101 register (001 xmm4)) 4)
      ((101 register (001 xmm5)) 5)
      ((101 register (001 xmm6)) 6)
      ((101 register (001 xmm7)) 7)
      ((101 register (001 xmm8)) 8)
      ((101 register (001 xmm9)) 9)
      ((101 register (001 xmm10)) #d10)
      ((101 register (001 xmm11)) #d11)
      ((101 register (001 xmm12)) 12)
      ((101 register (001 xmm13)) 13)
      ((101 register (001 xmm14)) 14)
      ((101 register (001 xmm15)) 15)
      ((010 (001 ())) (001 ())))))

(0011 x86-low3
  (0010 (code)
    (110
      ((101 code 0) 0)
      ((101 code 1) 1)
      ((101 code 2) 2)
      ((101 code 3) 3)
      ((101 code 4) 4)
      ((101 code 5) 5)
      ((101 code 6) 6)
      ((101 code 7) 7)
      ((101 code 8) 0)
      ((101 code 9) 1)
      ((101 code #d10) 2)
      ((101 code #d11) 3)
      ((101 code 12) 4)
      ((101 code 13) 5)
      ((101 code 14) 6)
      ((101 code 15) 7)
      ((010 (001 ())) (001 ())))))

(0011 x86-high1
  (0010 (code)
    (110
      ((101 code 0) 0)
      ((101 code 1) 0)
      ((101 code 2) 0)
      ((101 code 3) 0)
      ((101 code 4) 0)
      ((101 code 5) 0)
      ((101 code 6) 0)
      ((101 code 7) 0)
      ((101 code 8) 1)
      ((101 code 9) 1)
      ((101 code #d10) 1)
      ((101 code #d11) 1)
      ((101 code 12) 1)
      ((101 code 13) 1)
      ((101 code 14) 1)
      ((101 code 15) 1)
      ((010 (001 ())) (001 ())))))

; REX is a finite four-bit field. Keep encoding as an explicit Lisp-owned
; transducer rather than arithmetic over unqualified language Numbers.
(0011 x86-encode-rex
  (0010 (w r x b)
    (110
      ((101 w 0)
       (110
      ((101 r 0)
       (110
      ((101 x 0)
       (110
      ((101 b 0)
       64)
      ((101 b 1)
       65)
      ((010 (001 ())) (001 ()))))
      ((101 x 1)
       (110
      ((101 b 0)
       66)
      ((101 b 1)
       67)
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ()))))
      ((101 r 1)
       (110
      ((101 x 0)
       (110
      ((101 b 0)
       68)
      ((101 b 1)
       69)
      ((010 (001 ())) (001 ()))))
      ((101 x 1)
       (110
      ((101 b 0)
       70)
      ((101 b 1)
       71)
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ()))))
      ((101 w 1)
       (110
      ((101 r 0)
       (110
      ((101 x 0)
       (110
      ((101 b 0)
       72)
      ((101 b 1)
       73)
      ((010 (001 ())) (001 ()))))
      ((101 x 1)
       (110
      ((101 b 0)
       74)
      ((101 b 1)
       75)
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ()))))
      ((101 r 1)
       (110
      ((101 x 0)
       (110
      ((101 b 0)
       76)
      ((101 b 1)
       77)
      ((010 (001 ())) (001 ()))))
      ((101 x 1)
       (110
      ((101 b 0)
       78)
      ((101 b 1)
       79)
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ())))))

; ModR/M is a finite (mode:2, reg:3, rm:3) machine field.
; Each admitted tuple maps directly to its byte; unsupported values fail closed.
(0011 x86-encode-modrm
  (0010 (mode reg rm)
    (110
      ((101 mode 0)
       (110
      ((101 reg 0)
       (110
      ((101 rm 0)
       0)
      ((101 rm 1)
       1)
      ((101 rm 2)
       2)
      ((101 rm 3)
       3)
      ((101 rm 4)
       4)
      ((101 rm 5)
       5)
      ((101 rm 6)
       6)
      ((101 rm 7)
       7)
      ((010 (001 ())) (001 ()))))
      ((101 reg 1)
       (110
      ((101 rm 0)
       8)
      ((101 rm 1)
       9)
      ((101 rm 2)
       10)
      ((101 rm 3)
       11)
      ((101 rm 4)
       12)
      ((101 rm 5)
       13)
      ((101 rm 6)
       14)
      ((101 rm 7)
       15)
      ((010 (001 ())) (001 ()))))
      ((101 reg 2)
       (110
      ((101 rm 0)
       16)
      ((101 rm 1)
       17)
      ((101 rm 2)
       18)
      ((101 rm 3)
       19)
      ((101 rm 4)
       20)
      ((101 rm 5)
       21)
      ((101 rm 6)
       22)
      ((101 rm 7)
       23)
      ((010 (001 ())) (001 ()))))
      ((101 reg 3)
       (110
      ((101 rm 0)
       24)
      ((101 rm 1)
       25)
      ((101 rm 2)
       26)
      ((101 rm 3)
       27)
      ((101 rm 4)
       28)
      ((101 rm 5)
       29)
      ((101 rm 6)
       30)
      ((101 rm 7)
       31)
      ((010 (001 ())) (001 ()))))
      ((101 reg 4)
       (110
      ((101 rm 0)
       32)
      ((101 rm 1)
       33)
      ((101 rm 2)
       34)
      ((101 rm 3)
       35)
      ((101 rm 4)
       36)
      ((101 rm 5)
       37)
      ((101 rm 6)
       38)
      ((101 rm 7)
       39)
      ((010 (001 ())) (001 ()))))
      ((101 reg 5)
       (110
      ((101 rm 0)
       40)
      ((101 rm 1)
       41)
      ((101 rm 2)
       42)
      ((101 rm 3)
       43)
      ((101 rm 4)
       44)
      ((101 rm 5)
       45)
      ((101 rm 6)
       46)
      ((101 rm 7)
       47)
      ((010 (001 ())) (001 ()))))
      ((101 reg 6)
       (110
      ((101 rm 0)
       48)
      ((101 rm 1)
       49)
      ((101 rm 2)
       50)
      ((101 rm 3)
       51)
      ((101 rm 4)
       52)
      ((101 rm 5)
       53)
      ((101 rm 6)
       54)
      ((101 rm 7)
       55)
      ((010 (001 ())) (001 ()))))
      ((101 reg 7)
       (110
      ((101 rm 0)
       56)
      ((101 rm 1)
       57)
      ((101 rm 2)
       58)
      ((101 rm 3)
       59)
      ((101 rm 4)
       60)
      ((101 rm 5)
       61)
      ((101 rm 6)
       62)
      ((101 rm 7)
       63)
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ()))))
      ((101 mode 1)
       (110
      ((101 reg 0)
       (110
      ((101 rm 0)
       64)
      ((101 rm 1)
       65)
      ((101 rm 2)
       66)
      ((101 rm 3)
       67)
      ((101 rm 4)
       68)
      ((101 rm 5)
       69)
      ((101 rm 6)
       70)
      ((101 rm 7)
       71)
      ((010 (001 ())) (001 ()))))
      ((101 reg 1)
       (110
      ((101 rm 0)
       72)
      ((101 rm 1)
       73)
      ((101 rm 2)
       74)
      ((101 rm 3)
       75)
      ((101 rm 4)
       76)
      ((101 rm 5)
       77)
      ((101 rm 6)
       78)
      ((101 rm 7)
       79)
      ((010 (001 ())) (001 ()))))
      ((101 reg 2)
       (110
      ((101 rm 0)
       80)
      ((101 rm 1)
       81)
      ((101 rm 2)
       82)
      ((101 rm 3)
       83)
      ((101 rm 4)
       84)
      ((101 rm 5)
       85)
      ((101 rm 6)
       86)
      ((101 rm 7)
       87)
      ((010 (001 ())) (001 ()))))
      ((101 reg 3)
       (110
      ((101 rm 0)
       88)
      ((101 rm 1)
       89)
      ((101 rm 2)
       90)
      ((101 rm 3)
       91)
      ((101 rm 4)
       92)
      ((101 rm 5)
       93)
      ((101 rm 6)
       94)
      ((101 rm 7)
       95)
      ((010 (001 ())) (001 ()))))
      ((101 reg 4)
       (110
      ((101 rm 0)
       96)
      ((101 rm 1)
       97)
      ((101 rm 2)
       98)
      ((101 rm 3)
       99)
      ((101 rm 4)
       100)
      ((101 rm 5)
       101)
      ((101 rm 6)
       102)
      ((101 rm 7)
       103)
      ((010 (001 ())) (001 ()))))
      ((101 reg 5)
       (110
      ((101 rm 0)
       104)
      ((101 rm 1)
       105)
      ((101 rm 2)
       106)
      ((101 rm 3)
       107)
      ((101 rm 4)
       108)
      ((101 rm 5)
       109)
      ((101 rm 6)
       110)
      ((101 rm 7)
       111)
      ((010 (001 ())) (001 ()))))
      ((101 reg 6)
       (110
      ((101 rm 0)
       112)
      ((101 rm 1)
       113)
      ((101 rm 2)
       114)
      ((101 rm 3)
       115)
      ((101 rm 4)
       116)
      ((101 rm 5)
       117)
      ((101 rm 6)
       118)
      ((101 rm 7)
       119)
      ((010 (001 ())) (001 ()))))
      ((101 reg 7)
       (110
      ((101 rm 0)
       120)
      ((101 rm 1)
       121)
      ((101 rm 2)
       122)
      ((101 rm 3)
       123)
      ((101 rm 4)
       124)
      ((101 rm 5)
       125)
      ((101 rm 6)
       126)
      ((101 rm 7)
       127)
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ()))))
      ((101 mode 2)
       (110
      ((101 reg 0)
       (110
      ((101 rm 0)
       128)
      ((101 rm 1)
       129)
      ((101 rm 2)
       130)
      ((101 rm 3)
       131)
      ((101 rm 4)
       132)
      ((101 rm 5)
       133)
      ((101 rm 6)
       134)
      ((101 rm 7)
       135)
      ((010 (001 ())) (001 ()))))
      ((101 reg 1)
       (110
      ((101 rm 0)
       136)
      ((101 rm 1)
       137)
      ((101 rm 2)
       138)
      ((101 rm 3)
       139)
      ((101 rm 4)
       140)
      ((101 rm 5)
       141)
      ((101 rm 6)
       142)
      ((101 rm 7)
       143)
      ((010 (001 ())) (001 ()))))
      ((101 reg 2)
       (110
      ((101 rm 0)
       144)
      ((101 rm 1)
       145)
      ((101 rm 2)
       146)
      ((101 rm 3)
       147)
      ((101 rm 4)
       148)
      ((101 rm 5)
       149)
      ((101 rm 6)
       150)
      ((101 rm 7)
       151)
      ((010 (001 ())) (001 ()))))
      ((101 reg 3)
       (110
      ((101 rm 0)
       152)
      ((101 rm 1)
       153)
      ((101 rm 2)
       154)
      ((101 rm 3)
       155)
      ((101 rm 4)
       156)
      ((101 rm 5)
       157)
      ((101 rm 6)
       158)
      ((101 rm 7)
       159)
      ((010 (001 ())) (001 ()))))
      ((101 reg 4)
       (110
      ((101 rm 0)
       160)
      ((101 rm 1)
       161)
      ((101 rm 2)
       162)
      ((101 rm 3)
       163)
      ((101 rm 4)
       164)
      ((101 rm 5)
       165)
      ((101 rm 6)
       166)
      ((101 rm 7)
       167)
      ((010 (001 ())) (001 ()))))
      ((101 reg 5)
       (110
      ((101 rm 0)
       168)
      ((101 rm 1)
       169)
      ((101 rm 2)
       170)
      ((101 rm 3)
       171)
      ((101 rm 4)
       172)
      ((101 rm 5)
       173)
      ((101 rm 6)
       174)
      ((101 rm 7)
       175)
      ((010 (001 ())) (001 ()))))
      ((101 reg 6)
       (110
      ((101 rm 0)
       176)
      ((101 rm 1)
       177)
      ((101 rm 2)
       178)
      ((101 rm 3)
       179)
      ((101 rm 4)
       180)
      ((101 rm 5)
       181)
      ((101 rm 6)
       182)
      ((101 rm 7)
       183)
      ((010 (001 ())) (001 ()))))
      ((101 reg 7)
       (110
      ((101 rm 0)
       184)
      ((101 rm 1)
       185)
      ((101 rm 2)
       186)
      ((101 rm 3)
       187)
      ((101 rm 4)
       188)
      ((101 rm 5)
       189)
      ((101 rm 6)
       190)
      ((101 rm 7)
       191)
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ()))))
      ((101 mode 3)
       (110
      ((101 reg 0)
       (110
      ((101 rm 0)
       192)
      ((101 rm 1)
       193)
      ((101 rm 2)
       194)
      ((101 rm 3)
       195)
      ((101 rm 4)
       196)
      ((101 rm 5)
       197)
      ((101 rm 6)
       198)
      ((101 rm 7)
       199)
      ((010 (001 ())) (001 ()))))
      ((101 reg 1)
       (110
      ((101 rm 0)
       200)
      ((101 rm 1)
       201)
      ((101 rm 2)
       202)
      ((101 rm 3)
       203)
      ((101 rm 4)
       204)
      ((101 rm 5)
       205)
      ((101 rm 6)
       206)
      ((101 rm 7)
       207)
      ((010 (001 ())) (001 ()))))
      ((101 reg 2)
       (110
      ((101 rm 0)
       208)
      ((101 rm 1)
       209)
      ((101 rm 2)
       210)
      ((101 rm 3)
       211)
      ((101 rm 4)
       212)
      ((101 rm 5)
       213)
      ((101 rm 6)
       214)
      ((101 rm 7)
       215)
      ((010 (001 ())) (001 ()))))
      ((101 reg 3)
       (110
      ((101 rm 0)
       216)
      ((101 rm 1)
       217)
      ((101 rm 2)
       218)
      ((101 rm 3)
       219)
      ((101 rm 4)
       220)
      ((101 rm 5)
       221)
      ((101 rm 6)
       222)
      ((101 rm 7)
       223)
      ((010 (001 ())) (001 ()))))
      ((101 reg 4)
       (110
      ((101 rm 0)
       224)
      ((101 rm 1)
       225)
      ((101 rm 2)
       226)
      ((101 rm 3)
       227)
      ((101 rm 4)
       228)
      ((101 rm 5)
       229)
      ((101 rm 6)
       230)
      ((101 rm 7)
       231)
      ((010 (001 ())) (001 ()))))
      ((101 reg 5)
       (110
      ((101 rm 0)
       232)
      ((101 rm 1)
       233)
      ((101 rm 2)
       234)
      ((101 rm 3)
       235)
      ((101 rm 4)
       236)
      ((101 rm 5)
       237)
      ((101 rm 6)
       238)
      ((101 rm 7)
       239)
      ((010 (001 ())) (001 ()))))
      ((101 reg 6)
       (110
      ((101 rm 0)
       240)
      ((101 rm 1)
       241)
      ((101 rm 2)
       242)
      ((101 rm 3)
       243)
      ((101 rm 4)
       244)
      ((101 rm 5)
       245)
      ((101 rm 6)
       246)
      ((101 rm 7)
       247)
      ((010 (001 ())) (001 ()))))
      ((101 reg 7)
       (110
      ((101 rm 0)
       248)
      ((101 rm 1)
       249)
      ((101 rm 2)
       250)
      ((101 rm 3)
       251)
      ((101 rm 4)
       252)
      ((101 rm 5)
       253)
      ((101 rm 6)
       254)
      ((101 rm 7)
       255)
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ())))))

; #4104 — explicit representation boundary for an exact 3-bit machine field.
; Canonical BinaryNumber remains the source identity (#b...).  The shared
; legacy byte packer below still consumes mechanical Number fields, so project
; only the closed u3 domain 0..7 here.  This is intentionally not a general
; BinaryNumber -> legacy Number coercion.
(0011 x86-project-bin3-to-mechanism-u3
  (0010 (value)
    (110
      ((11010 value #b1)    #d0)
      ((11010 value #b10)   #d1)
      ((11010 value #b11)   #d2)
      ((11010 value #b100)  #d3)
      ((11010 value #b101)  #d4)
      ((11010 value #b110)  #d5)
      ((11010 value #b111)  #d6)
      ((11010 value #b1000) #d7)
      ((010 ()) (001 ())))))


; SIB is a finite (scale:2, index:3, base:3) machine field.
; Explicit tuples preserve the exact byte without semantic-number arithmetic.
(0011 x86-encode-sib
  (0010 (scale index base)
    (110
      ((101 scale 0)
       (110
      ((101 index 0)
       (110
      ((101 base 0)
       0)
      ((101 base 1)
       1)
      ((101 base 2)
       2)
      ((101 base 3)
       3)
      ((101 base 4)
       4)
      ((101 base 5)
       5)
      ((101 base 6)
       6)
      ((101 base 7)
       7)
      ((010 (001 ())) (001 ()))))
      ((101 index 1)
       (110
      ((101 base 0)
       8)
      ((101 base 1)
       9)
      ((101 base 2)
       10)
      ((101 base 3)
       11)
      ((101 base 4)
       12)
      ((101 base 5)
       13)
      ((101 base 6)
       14)
      ((101 base 7)
       15)
      ((010 (001 ())) (001 ()))))
      ((101 index 2)
       (110
      ((101 base 0)
       16)
      ((101 base 1)
       17)
      ((101 base 2)
       18)
      ((101 base 3)
       19)
      ((101 base 4)
       20)
      ((101 base 5)
       21)
      ((101 base 6)
       22)
      ((101 base 7)
       23)
      ((010 (001 ())) (001 ()))))
      ((101 index 3)
       (110
      ((101 base 0)
       24)
      ((101 base 1)
       25)
      ((101 base 2)
       26)
      ((101 base 3)
       27)
      ((101 base 4)
       28)
      ((101 base 5)
       29)
      ((101 base 6)
       30)
      ((101 base 7)
       31)
      ((010 (001 ())) (001 ()))))
      ((101 index 4)
       (110
      ((101 base 0)
       32)
      ((101 base 1)
       33)
      ((101 base 2)
       34)
      ((101 base 3)
       35)
      ((101 base 4)
       36)
      ((101 base 5)
       37)
      ((101 base 6)
       38)
      ((101 base 7)
       39)
      ((010 (001 ())) (001 ()))))
      ((101 index 5)
       (110
      ((101 base 0)
       40)
      ((101 base 1)
       41)
      ((101 base 2)
       42)
      ((101 base 3)
       43)
      ((101 base 4)
       44)
      ((101 base 5)
       45)
      ((101 base 6)
       46)
      ((101 base 7)
       47)
      ((010 (001 ())) (001 ()))))
      ((101 index 6)
       (110
      ((101 base 0)
       48)
      ((101 base 1)
       49)
      ((101 base 2)
       50)
      ((101 base 3)
       51)
      ((101 base 4)
       52)
      ((101 base 5)
       53)
      ((101 base 6)
       54)
      ((101 base 7)
       55)
      ((010 (001 ())) (001 ()))))
      ((101 index 7)
       (110
      ((101 base 0)
       56)
      ((101 base 1)
       57)
      ((101 base 2)
       58)
      ((101 base 3)
       59)
      ((101 base 4)
       60)
      ((101 base 5)
       61)
      ((101 base 6)
       62)
      ((101 base 7)
       63)
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ()))))
      ((101 scale 1)
       (110
      ((101 index 0)
       (110
      ((101 base 0)
       64)
      ((101 base 1)
       65)
      ((101 base 2)
       66)
      ((101 base 3)
       67)
      ((101 base 4)
       68)
      ((101 base 5)
       69)
      ((101 base 6)
       70)
      ((101 base 7)
       71)
      ((010 (001 ())) (001 ()))))
      ((101 index 1)
       (110
      ((101 base 0)
       72)
      ((101 base 1)
       73)
      ((101 base 2)
       74)
      ((101 base 3)
       75)
      ((101 base 4)
       76)
      ((101 base 5)
       77)
      ((101 base 6)
       78)
      ((101 base 7)
       79)
      ((010 (001 ())) (001 ()))))
      ((101 index 2)
       (110
      ((101 base 0)
       80)
      ((101 base 1)
       81)
      ((101 base 2)
       82)
      ((101 base 3)
       83)
      ((101 base 4)
       84)
      ((101 base 5)
       85)
      ((101 base 6)
       86)
      ((101 base 7)
       87)
      ((010 (001 ())) (001 ()))))
      ((101 index 3)
       (110
      ((101 base 0)
       88)
      ((101 base 1)
       89)
      ((101 base 2)
       90)
      ((101 base 3)
       91)
      ((101 base 4)
       92)
      ((101 base 5)
       93)
      ((101 base 6)
       94)
      ((101 base 7)
       95)
      ((010 (001 ())) (001 ()))))
      ((101 index 4)
       (110
      ((101 base 0)
       96)
      ((101 base 1)
       97)
      ((101 base 2)
       98)
      ((101 base 3)
       99)
      ((101 base 4)
       100)
      ((101 base 5)
       101)
      ((101 base 6)
       102)
      ((101 base 7)
       103)
      ((010 (001 ())) (001 ()))))
      ((101 index 5)
       (110
      ((101 base 0)
       104)
      ((101 base 1)
       105)
      ((101 base 2)
       106)
      ((101 base 3)
       107)
      ((101 base 4)
       108)
      ((101 base 5)
       109)
      ((101 base 6)
       110)
      ((101 base 7)
       111)
      ((010 (001 ())) (001 ()))))
      ((101 index 6)
       (110
      ((101 base 0)
       112)
      ((101 base 1)
       113)
      ((101 base 2)
       114)
      ((101 base 3)
       115)
      ((101 base 4)
       116)
      ((101 base 5)
       117)
      ((101 base 6)
       118)
      ((101 base 7)
       119)
      ((010 (001 ())) (001 ()))))
      ((101 index 7)
       (110
      ((101 base 0)
       120)
      ((101 base 1)
       121)
      ((101 base 2)
       122)
      ((101 base 3)
       123)
      ((101 base 4)
       124)
      ((101 base 5)
       125)
      ((101 base 6)
       126)
      ((101 base 7)
       127)
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ()))))
      ((101 scale 2)
       (110
      ((101 index 0)
       (110
      ((101 base 0)
       128)
      ((101 base 1)
       129)
      ((101 base 2)
       130)
      ((101 base 3)
       131)
      ((101 base 4)
       132)
      ((101 base 5)
       133)
      ((101 base 6)
       134)
      ((101 base 7)
       135)
      ((010 (001 ())) (001 ()))))
      ((101 index 1)
       (110
      ((101 base 0)
       136)
      ((101 base 1)
       137)
      ((101 base 2)
       138)
      ((101 base 3)
       139)
      ((101 base 4)
       140)
      ((101 base 5)
       141)
      ((101 base 6)
       142)
      ((101 base 7)
       143)
      ((010 (001 ())) (001 ()))))
      ((101 index 2)
       (110
      ((101 base 0)
       144)
      ((101 base 1)
       145)
      ((101 base 2)
       146)
      ((101 base 3)
       147)
      ((101 base 4)
       148)
      ((101 base 5)
       149)
      ((101 base 6)
       150)
      ((101 base 7)
       151)
      ((010 (001 ())) (001 ()))))
      ((101 index 3)
       (110
      ((101 base 0)
       152)
      ((101 base 1)
       153)
      ((101 base 2)
       154)
      ((101 base 3)
       155)
      ((101 base 4)
       156)
      ((101 base 5)
       157)
      ((101 base 6)
       158)
      ((101 base 7)
       159)
      ((010 (001 ())) (001 ()))))
      ((101 index 4)
       (110
      ((101 base 0)
       160)
      ((101 base 1)
       161)
      ((101 base 2)
       162)
      ((101 base 3)
       163)
      ((101 base 4)
       164)
      ((101 base 5)
       165)
      ((101 base 6)
       166)
      ((101 base 7)
       167)
      ((010 (001 ())) (001 ()))))
      ((101 index 5)
       (110
      ((101 base 0)
       168)
      ((101 base 1)
       169)
      ((101 base 2)
       170)
      ((101 base 3)
       171)
      ((101 base 4)
       172)
      ((101 base 5)
       173)
      ((101 base 6)
       174)
      ((101 base 7)
       175)
      ((010 (001 ())) (001 ()))))
      ((101 index 6)
       (110
      ((101 base 0)
       176)
      ((101 base 1)
       177)
      ((101 base 2)
       178)
      ((101 base 3)
       179)
      ((101 base 4)
       180)
      ((101 base 5)
       181)
      ((101 base 6)
       182)
      ((101 base 7)
       183)
      ((010 (001 ())) (001 ()))))
      ((101 index 7)
       (110
      ((101 base 0)
       184)
      ((101 base 1)
       185)
      ((101 base 2)
       186)
      ((101 base 3)
       187)
      ((101 base 4)
       188)
      ((101 base 5)
       189)
      ((101 base 6)
       190)
      ((101 base 7)
       191)
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ()))))
      ((101 scale 3)
       (110
      ((101 index 0)
       (110
      ((101 base 0)
       192)
      ((101 base 1)
       193)
      ((101 base 2)
       194)
      ((101 base 3)
       195)
      ((101 base 4)
       196)
      ((101 base 5)
       197)
      ((101 base 6)
       198)
      ((101 base 7)
       199)
      ((010 (001 ())) (001 ()))))
      ((101 index 1)
       (110
      ((101 base 0)
       200)
      ((101 base 1)
       201)
      ((101 base 2)
       202)
      ((101 base 3)
       203)
      ((101 base 4)
       204)
      ((101 base 5)
       205)
      ((101 base 6)
       206)
      ((101 base 7)
       207)
      ((010 (001 ())) (001 ()))))
      ((101 index 2)
       (110
      ((101 base 0)
       208)
      ((101 base 1)
       209)
      ((101 base 2)
       210)
      ((101 base 3)
       211)
      ((101 base 4)
       212)
      ((101 base 5)
       213)
      ((101 base 6)
       214)
      ((101 base 7)
       215)
      ((010 (001 ())) (001 ()))))
      ((101 index 3)
       (110
      ((101 base 0)
       216)
      ((101 base 1)
       217)
      ((101 base 2)
       218)
      ((101 base 3)
       219)
      ((101 base 4)
       220)
      ((101 base 5)
       221)
      ((101 base 6)
       222)
      ((101 base 7)
       223)
      ((010 (001 ())) (001 ()))))
      ((101 index 4)
       (110
      ((101 base 0)
       224)
      ((101 base 1)
       225)
      ((101 base 2)
       226)
      ((101 base 3)
       227)
      ((101 base 4)
       228)
      ((101 base 5)
       229)
      ((101 base 6)
       230)
      ((101 base 7)
       231)
      ((010 (001 ())) (001 ()))))
      ((101 index 5)
       (110
      ((101 base 0)
       232)
      ((101 base 1)
       233)
      ((101 base 2)
       234)
      ((101 base 3)
       235)
      ((101 base 4)
       236)
      ((101 base 5)
       237)
      ((101 base 6)
       238)
      ((101 base 7)
       239)
      ((010 (001 ())) (001 ()))))
      ((101 index 6)
       (110
      ((101 base 0)
       240)
      ((101 base 1)
       241)
      ((101 base 2)
       242)
      ((101 base 3)
       243)
      ((101 base 4)
       244)
      ((101 base 5)
       245)
      ((101 base 6)
       246)
      ((101 base 7)
       247)
      ((010 (001 ())) (001 ()))))
      ((101 index 7)
       (110
      ((101 base 0)
       248)
      ((101 base 1)
       249)
      ((101 base 2)
       250)
      ((101 base 3)
       251)
      ((101 base 4)
       252)
      ((101 base 5)
       253)
      ((101 base 6)
       254)
      ((101 base 7)
       255)
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ()))))
      ((010 (001 ())) (001 ())))))

; Reuse the already proved exact Lisp long-division byte extractor.
; Four iterations are the imm32 wire shape; historical W8 quotient/remainder
; heads are not executable machine authority under strict D1 COND.
(0011 x86-u32-bytes
  (0010 (value)
    (x86-байти-без-знака value 4)))

; Точне двійкове ділення з цілою часткою і залишком.
; Механізм x86, не новий закон D5/D6: лише вже ратифіковані
; додавання, віднімання, порівняння і структурна пара D3.
; Кожна рекурсія подвоює масштаб; жодного лінійного віднімання 256.
(0011 x86-ціла-частка-залишок
  (0010 (значення масштаб кратність)
    (110
      ((менше? значення масштаб)
       (111 0 значення))
      ((010 ())
       ((0010 (пара)
          (110
            ((менше? (011 пара) масштаб) пара)
            ((010 ())
             (111
               (додати (100 пара) кратність)
               (відняти (011 пара) масштаб)))))
        (x86-ціла-частка-залишок
          значення
          (додати масштаб масштаб)
          (додати кратність кратність)))))))

; Матеріалізація рівно восьми байтів little-endian.
; Довжина визначена механізмом x86; нічого не змінює в T5.
(0011 x86-байти-без-знака
  (0010 (значення кількість)
    (110
      ((менше? кількість 1) (001 ()))
      ((010 ())
       ((0010 (пара)
          (111
            (011 пара)
            (x86-байти-без-знака
              (100 пара)
              (відняти кількість 1))))
        (x86-ціла-частка-залишок значення 256 1))))))

(0011 x86-u64-bytes
  (0010 (значення)
    (x86-байти-без-знака значення 8)))

(0011 x86-encode-ret
  (0010 ()
    (1110 195)))

(0011 x86-encode-mov-eax-imm32
  (0010 (immediate)
    (111 184 (x86-u32-bytes immediate))))

(0011 x86-encode-mov-r64-imm64
  (0010 (register immediate)
    ((0010 (code)
       (111
         (x86-encode-rex 1 0 0 (x86-high1 code))
         (111
           (01010 184 (x86-low3 code))
           (x86-u64-bytes immediate))))
     (x86-reg-code register))))

; Project a signed disp8 to its canonical byte after adding 256.
; The biased input is in [128,383], so the existing Lisp-owned binary
; long-division routine can return the exact remainder without borrowing the
; historical D8:00010011 coordinate (currently MAPLIST-right, not MOD).
; D3 CDR selects the remainder from the returned (quotient . remainder) pair.
; Signed disp8 is a finite machine field. Negative values map by the
; two's-complement byte projection, without invoking Core math or host coercion.
(0011 x86-disp8-byte
  (0010 (displacement)
    (110
      ((101 displacement -128)
       128)
      ((101 displacement -127)
       129)
      ((101 displacement -126)
       130)
      ((101 displacement -125)
       131)
      ((101 displacement -124)
       132)
      ((101 displacement -123)
       133)
      ((101 displacement -122)
       134)
      ((101 displacement -121)
       135)
      ((101 displacement -120)
       136)
      ((101 displacement -119)
       137)
      ((101 displacement -118)
       138)
      ((101 displacement -117)
       139)
      ((101 displacement -116)
       140)
      ((101 displacement -115)
       141)
      ((101 displacement -114)
       142)
      ((101 displacement -113)
       143)
      ((101 displacement -112)
       144)
      ((101 displacement -111)
       145)
      ((101 displacement -110)
       146)
      ((101 displacement -109)
       147)
      ((101 displacement -108)
       148)
      ((101 displacement -107)
       149)
      ((101 displacement -106)
       150)
      ((101 displacement -105)
       151)
      ((101 displacement -104)
       152)
      ((101 displacement -103)
       153)
      ((101 displacement -102)
       154)
      ((101 displacement -101)
       155)
      ((101 displacement -100)
       156)
      ((101 displacement -99)
       157)
      ((101 displacement -98)
       158)
      ((101 displacement -97)
       159)
      ((101 displacement -96)
       160)
      ((101 displacement -95)
       161)
      ((101 displacement -94)
       162)
      ((101 displacement -93)
       163)
      ((101 displacement -92)
       164)
      ((101 displacement -91)
       165)
      ((101 displacement -90)
       166)
      ((101 displacement -89)
       167)
      ((101 displacement -88)
       168)
      ((101 displacement -87)
       169)
      ((101 displacement -86)
       170)
      ((101 displacement -85)
       171)
      ((101 displacement -84)
       172)
      ((101 displacement -83)
       173)
      ((101 displacement -82)
       174)
      ((101 displacement -81)
       175)
      ((101 displacement -80)
       176)
      ((101 displacement -79)
       177)
      ((101 displacement -78)
       178)
      ((101 displacement -77)
       179)
      ((101 displacement -76)
       180)
      ((101 displacement -75)
       181)
      ((101 displacement -74)
       182)
      ((101 displacement -73)
       183)
      ((101 displacement -72)
       184)
      ((101 displacement -71)
       185)
      ((101 displacement -70)
       186)
      ((101 displacement -69)
       187)
      ((101 displacement -68)
       188)
      ((101 displacement -67)
       189)
      ((101 displacement -66)
       190)
      ((101 displacement -65)
       191)
      ((101 displacement -64)
       192)
      ((101 displacement -63)
       193)
      ((101 displacement -62)
       194)
      ((101 displacement -61)
       195)
      ((101 displacement -60)
       196)
      ((101 displacement -59)
       197)
      ((101 displacement -58)
       198)
      ((101 displacement -57)
       199)
      ((101 displacement -56)
       200)
      ((101 displacement -55)
       201)
      ((101 displacement -54)
       202)
      ((101 displacement -53)
       203)
      ((101 displacement -52)
       204)
      ((101 displacement -51)
       205)
      ((101 displacement -50)
       206)
      ((101 displacement -49)
       207)
      ((101 displacement -48)
       208)
      ((101 displacement -47)
       209)
      ((101 displacement -46)
       210)
      ((101 displacement -45)
       211)
      ((101 displacement -44)
       212)
      ((101 displacement -43)
       213)
      ((101 displacement -42)
       214)
      ((101 displacement -41)
       215)
      ((101 displacement -40)
       216)
      ((101 displacement -39)
       217)
      ((101 displacement -38)
       218)
      ((101 displacement -37)
       219)
      ((101 displacement -36)
       220)
      ((101 displacement -35)
       221)
      ((101 displacement -34)
       222)
      ((101 displacement -33)
       223)
      ((101 displacement -32)
       224)
      ((101 displacement -31)
       225)
      ((101 displacement -30)
       226)
      ((101 displacement -29)
       227)
      ((101 displacement -28)
       228)
      ((101 displacement -27)
       229)
      ((101 displacement -26)
       230)
      ((101 displacement -25)
       231)
      ((101 displacement -24)
       232)
      ((101 displacement -23)
       233)
      ((101 displacement -22)
       234)
      ((101 displacement -21)
       235)
      ((101 displacement -20)
       236)
      ((101 displacement -19)
       237)
      ((101 displacement -18)
       238)
      ((101 displacement -17)
       239)
      ((101 displacement -16)
       240)
      ((101 displacement -15)
       241)
      ((101 displacement -14)
       242)
      ((101 displacement -13)
       243)
      ((101 displacement -12)
       244)
      ((101 displacement -11)
       245)
      ((101 displacement -10)
       246)
      ((101 displacement -9)
       247)
      ((101 displacement -8)
       248)
      ((101 displacement -7)
       249)
      ((101 displacement -6)
       250)
      ((101 displacement -5)
       251)
      ((101 displacement -4)
       252)
      ((101 displacement -3)
       253)
      ((101 displacement -2)
       254)
      ((101 displacement -1)
       255)
      ((101 displacement 0)
       0)
      ((101 displacement 1)
       1)
      ((101 displacement 2)
       2)
      ((101 displacement 3)
       3)
      ((101 displacement 4)
       4)
      ((101 displacement 5)
       5)
      ((101 displacement 6)
       6)
      ((101 displacement 7)
       7)
      ((101 displacement 8)
       8)
      ((101 displacement 9)
       9)
      ((101 displacement 10)
       10)
      ((101 displacement 11)
       11)
      ((101 displacement 12)
       12)
      ((101 displacement 13)
       13)
      ((101 displacement 14)
       14)
      ((101 displacement 15)
       15)
      ((101 displacement 16)
       16)
      ((101 displacement 17)
       17)
      ((101 displacement 18)
       18)
      ((101 displacement 19)
       19)
      ((101 displacement 20)
       20)
      ((101 displacement 21)
       21)
      ((101 displacement 22)
       22)
      ((101 displacement 23)
       23)
      ((101 displacement 24)
       24)
      ((101 displacement 25)
       25)
      ((101 displacement 26)
       26)
      ((101 displacement 27)
       27)
      ((101 displacement 28)
       28)
      ((101 displacement 29)
       29)
      ((101 displacement 30)
       30)
      ((101 displacement 31)
       31)
      ((101 displacement 32)
       32)
      ((101 displacement 33)
       33)
      ((101 displacement 34)
       34)
      ((101 displacement 35)
       35)
      ((101 displacement 36)
       36)
      ((101 displacement 37)
       37)
      ((101 displacement 38)
       38)
      ((101 displacement 39)
       39)
      ((101 displacement 40)
       40)
      ((101 displacement 41)
       41)
      ((101 displacement 42)
       42)
      ((101 displacement 43)
       43)
      ((101 displacement 44)
       44)
      ((101 displacement 45)
       45)
      ((101 displacement 46)
       46)
      ((101 displacement 47)
       47)
      ((101 displacement 48)
       48)
      ((101 displacement 49)
       49)
      ((101 displacement 50)
       50)
      ((101 displacement 51)
       51)
      ((101 displacement 52)
       52)
      ((101 displacement 53)
       53)
      ((101 displacement 54)
       54)
      ((101 displacement 55)
       55)
      ((101 displacement 56)
       56)
      ((101 displacement 57)
       57)
      ((101 displacement 58)
       58)
      ((101 displacement 59)
       59)
      ((101 displacement 60)
       60)
      ((101 displacement 61)
       61)
      ((101 displacement 62)
       62)
      ((101 displacement 63)
       63)
      ((101 displacement 64)
       64)
      ((101 displacement 65)
       65)
      ((101 displacement 66)
       66)
      ((101 displacement 67)
       67)
      ((101 displacement 68)
       68)
      ((101 displacement 69)
       69)
      ((101 displacement 70)
       70)
      ((101 displacement 71)
       71)
      ((101 displacement 72)
       72)
      ((101 displacement 73)
       73)
      ((101 displacement 74)
       74)
      ((101 displacement 75)
       75)
      ((101 displacement 76)
       76)
      ((101 displacement 77)
       77)
      ((101 displacement 78)
       78)
      ((101 displacement 79)
       79)
      ((101 displacement 80)
       80)
      ((101 displacement 81)
       81)
      ((101 displacement 82)
       82)
      ((101 displacement 83)
       83)
      ((101 displacement 84)
       84)
      ((101 displacement 85)
       85)
      ((101 displacement 86)
       86)
      ((101 displacement 87)
       87)
      ((101 displacement 88)
       88)
      ((101 displacement 89)
       89)
      ((101 displacement 90)
       90)
      ((101 displacement 91)
       91)
      ((101 displacement 92)
       92)
      ((101 displacement 93)
       93)
      ((101 displacement 94)
       94)
      ((101 displacement 95)
       95)
      ((101 displacement 96)
       96)
      ((101 displacement 97)
       97)
      ((101 displacement 98)
       98)
      ((101 displacement 99)
       99)
      ((101 displacement 100)
       100)
      ((101 displacement 101)
       101)
      ((101 displacement 102)
       102)
      ((101 displacement 103)
       103)
      ((101 displacement 104)
       104)
      ((101 displacement 105)
       105)
      ((101 displacement 106)
       106)
      ((101 displacement 107)
       107)
      ((101 displacement 108)
       108)
      ((101 displacement 109)
       109)
      ((101 displacement 110)
       110)
      ((101 displacement 111)
       111)
      ((101 displacement 112)
       112)
      ((101 displacement 113)
       113)
      ((101 displacement 114)
       114)
      ((101 displacement 115)
       115)
      ((101 displacement 116)
       116)
      ((101 displacement 117)
       117)
      ((101 displacement 118)
       118)
      ((101 displacement 119)
       119)
      ((101 displacement 120)
       120)
      ((101 displacement 121)
       121)
      ((101 displacement 122)
       122)
      ((101 displacement 123)
       123)
      ((101 displacement 124)
       124)
      ((101 displacement 125)
       125)
      ((101 displacement 126)
       126)
      ((101 displacement 127)
       127)
      ((010 (001 ())) (001 ())))))

; MOV r64, [base + disp8], opcode 8B /r.
; ModR/M mode 01 always carries one displacement byte. RSP/R12 bases use the
; required no-index SIB byte instead of silently emitting an invalid address.
(0011 x86-encode-mov-r64-mem-disp8
  (0010 (destination base displacement)
    (let ((dst (x86-reg-code destination)))
      (let ((base-code (x86-reg-code base)))
        (let ((rex (x86-encode-rex 1 (x86-high1 dst) 0 (x86-high1 base-code))))
          (let ((modrm (x86-encode-modrm 1 (x86-low3 dst) (x86-low3 base-code))))
            (110
              ((101 (x86-low3 base-code) 4)
                (1110
                  rex
                  139
                  modrm
                  (x86-encode-sib 0 4 4)
                  (x86-disp8-byte displacement)))
              ((010 ())
                (1110 rex 139 modrm (x86-disp8-byte displacement))))))))))

; MOV [base + disp8], r64, opcode 89 /r.
(0011 x86-encode-mov-mem-disp8-r64
  (0010 (base displacement source)
    (let ((base-code (x86-reg-code base)))
      (let ((src (x86-reg-code source)))
        (let ((rex (x86-encode-rex 1 (x86-high1 src) 0 (x86-high1 base-code))))
          (let ((modrm (x86-encode-modrm 1 (x86-low3 src) (x86-low3 base-code))))
            (110
              ((101 (x86-low3 base-code) 4)
                (1110
                  rex
                  137
                  modrm
                  (x86-encode-sib 0 4 4)
                  (x86-disp8-byte displacement)))
              ((010 ())
                (1110 rex 137 modrm (x86-disp8-byte displacement))))))))))

; LEA r64, [base + disp8], opcode 0x8D /r -- per #175's pinned XED evidence
; (`PATTERN : 0x8D MOD[mm] MOD!=3 REG[rrr] RM[nnn] MODRM() REMOVE_SEGMENT()`,
; `OPERANDS : REG0=GPRv_R():w AGEN:r`). AGEN means the operand is an address
; computed from the ModRM/SIB/displacement, never an actual memory read --
; the identical addressing shape #199's mov-r64-mem-disp8 already encodes,
; only the opcode byte differs and no memory access happens. This is the
; first form the encoder admits that computes an address without touching
; any flags, needed once pointer/offset arithmetic (e.g. advancing a
; bump-pointer arena, or computing a struct field's address) must not
; disturb a CMP result still pending in a nearby branch.
(0011 x86-encode-lea-r64-mem-disp8
  (0010 (destination base displacement)
    (let ((dst (x86-reg-code destination)))
      (let ((base-code (x86-reg-code base)))
        (let ((rex (x86-encode-rex 1 (x86-high1 dst) 0 (x86-high1 base-code))))
          (let ((modrm (x86-encode-modrm 1 (x86-low3 dst) (x86-low3 base-code))))
            (110
              ((101 (x86-low3 base-code) 4)
                (1110
                  rex
                  141
                  modrm
                  (x86-encode-sib 0 4 4)
                  (x86-disp8-byte displacement)))
              ((010 ())
                (1110 rex 141 modrm (x86-disp8-byte displacement))))))))))

; Group-1 ALU r/m64, r64 (mod=3 register/register), opcode base+1: ADD 0x01,
; OR 0x09, AND 0x21, SUB 0x29, XOR 0x31, CMP 0x39 (Intel SDM, confirmed
; against #175's pinned XED evidence: lib/machine/xed/vendor/base/xed-isa.txt
; PATTERN lines for each ICLASS's `MOD[0b11] MOD=3 REG[rrr] RM[nnn]` form).
; All six share one shape; only the opcode byte differs.
(0011 x86-encode-alu-r64-r64
  (0010 (opcode destination source)
    ((0010 (dst src)
       (1110
         (x86-encode-rex 1 (x86-high1 src) 0 (x86-high1 dst))
         opcode
         (x86-encode-modrm 3 (x86-low3 src) (x86-low3 dst))))
     (x86-reg-code destination)
     (x86-reg-code source))))

(0011 x86-encode-add-r64-r64
  (0010 (destination source)
    (x86-encode-alu-r64-r64 1 destination source)))

(0011 x86-encode-or-r64-r64
  (0010 (destination source)
    (x86-encode-alu-r64-r64 9 destination source)))

(0011 x86-encode-and-r64-r64
  (0010 (destination source)
    (x86-encode-alu-r64-r64 33 destination source)))

(0011 x86-encode-sub-r64-r64
  (0010 (destination source)
    (x86-encode-alu-r64-r64 41 destination source)))

(0011 x86-encode-xor-r64-r64
  (0010 (destination source)
    (x86-encode-alu-r64-r64 49 destination source)))

(0011 x86-encode-cmp-r64-r64
  (0010 (destination source)
    (x86-encode-alu-r64-r64 57 destination source)))

; MOV r/m64, r64 (opcode 0x89 /r, mod=3 register/register): copies source
; into destination with no flags touched -- per #175's pinned XED evidence
; (`PATTERN : 0x89 MOD[0b11] MOD=3 REG[rrr] RM[nnn]`, `OPERANDS : REG0=
; GPRv_B():w REG1=GPRv_R():r`, i.e. the reg field is the source being read
; and the rm field is the destination being written, the identical
; source/destination assignment the group-1 ALU family already uses). Same
; REX.W+opcode+ModRM shape, so it reuses x86-encode-alu-r64-r64 directly.
; This is the most elementary data-movement form still missing until now:
; every other admitted form can only load an immediate or a memory operand
; into a register, never copy register-to-register.
(0011 x86-encode-mov-r64-r64
  (0010 (destination source)
    (x86-encode-alu-r64-r64 137 destination source)))

; Two's-complement little-endian bytes for a sign-extended imm32 value
; already known to be in [-2147483648,2147483647]. Same wrap-before-split
; discipline #199 proved for disp8 (x86-disp8-byte) -- `mod` in this Lisp
; does not wrap negative operands, so adding 2^32 before reducing mod 2^32
; is exact for the whole imm32 domain.
(0011 x86-imm32-bytes
  (0010 (immediate)
    (x86-u32-bytes
      (011
        (x86-ціла-частка-залишок
          (01010 immediate 4294967296)
          4294967296
          1)))))

; ALU r/m64, imm32 (mod=3, sign-extended to 64 bits): opcode 0x81, ModRM reg
; field selects the operation (ADD=0, OR=1, AND=4, SUB=5, XOR=6, CMP=7,
; matching the same fixed group-1 numbering the register/register family's
; own opcodes already encode), rm field is the destination register -- per
; #175's pinned XED evidence (`PATTERN : 0x81 MOD[0b11] MOD=3 REG[rrr]
; RM[nnn] SIMMz()`). Lets a comparison/arithmetic-against-a-constant (the
; #196 COND base-case shape: compare a variable to a literal) skip loading
; the constant into a scratch register first.
(0011 x86-encode-alu-r64-imm32
  (0010 (opcode-extension destination immediate)
    (let ((dst (x86-reg-code destination)))
      (111
        (x86-encode-rex 1 0 0 (x86-high1 dst))
        (111
          129
          (111
            (x86-encode-modrm 3 opcode-extension (x86-low3 dst))
            (x86-imm32-bytes immediate)))))))

(0011 x86-encode-add-r64-imm32
  (0010 (destination immediate)
    (x86-encode-alu-r64-imm32 0 destination immediate)))

(0011 x86-encode-or-r64-imm32
  (0010 (destination immediate)
    (x86-encode-alu-r64-imm32 1 destination immediate)))

(0011 x86-encode-and-r64-imm32
  (0010 (destination immediate)
    (x86-encode-alu-r64-imm32 4 destination immediate)))

(0011 x86-encode-sub-r64-imm32
  (0010 (destination immediate)
    (x86-encode-alu-r64-imm32 5 destination immediate)))

(0011 x86-encode-xor-r64-imm32
  (0010 (destination immediate)
    (x86-encode-alu-r64-imm32 6 destination immediate)))

(0011 x86-encode-cmp-r64-imm32
  (0010 (destination immediate)
    (x86-encode-alu-r64-imm32 7 destination immediate)))

; TEST r/m64, r64 (opcode 0x85 /r, mod=3 register/register): destination AND
; source, result discarded, flags set only -- per #175's pinned XED evidence
; (`PATTERN : 0x85 MOD[0b11] MOD=3 REG[rrr] RM[nnn]`). Same REX.W+opcode+
; ModRM shape used by the group-1 ALU family, so it reuses x86-encode-alu-r64-r64
; directly rather than duplicating the REX/ModRM arithmetic.
(0011 x86-encode-test-r64-r64
  (0010 (destination source)
    (x86-encode-alu-r64-r64 133 destination source)))

; PUSH r64 (opcode 0x50+rd, ICLASS PUSH: `0b0101_0 SRM[rrr] ... DF64()`) and
; POP r64 (opcode 0x58+rd, ICLASS POP: `0b0101_1 SRM[rrr] ... DF64()`), per
; #175's pinned XED evidence. Both default to 64-bit operand size in long
; mode (`DF64()`), so no REX.W is emitted; only REX.B is needed, and only
; for r8-r15.
(0011 x86-encode-push-r64
  (0010 (register)
    (let ((code (x86-reg-code register)))
      (110
        ((101 (x86-high1 code) 1)
          (1110 (x86-encode-rex 0 0 0 1) (01010 80 (x86-low3 code))))
        ((010 ())
          (1110 (01010 80 (x86-low3 code))))))))

(0011 x86-encode-pop-r64
  (0010 (register)
    (let ((code (x86-reg-code register)))
      (110
        ((101 (x86-high1 code) 1)
          (1110 (x86-encode-rex 0 0 0 1) (01010 88 (x86-low3 code))))
        ((010 ())
          (1110 (01010 88 (x86-low3 code))))))))

; INC r64 / DEC r64: group-5 opcode 0xFF, /reg extension (not a register
; operand) selects the operation -- INC is /0, DEC is /1 -- per #175's
; pinned XED evidence (`PATTERN : 0xFF MOD[0b11] MOD=3 REG[0b000] RM[nnn]`
; / `REG[0b001]`). Unlike PUSH/POP, this form always needs REX.W: the
; legacy single-byte 0x40+r/0x48+r INC/DEC opcodes exist in the same pinned
; evidence tagged `not64` -- those byte values became REX prefixes in
; 64-bit mode, so encoding INC/DEC in long mode always goes through this
; ModRM group-5 path, never the legacy one.
(0011 x86-encode-inc-r64
  (0010 (register)
    (let ((code (x86-reg-code register)))
      (1110
        (x86-encode-rex 1 0 0 (x86-high1 code))
        255
        (x86-encode-modrm 3 0 (x86-low3 code))))))

(0011 x86-encode-dec-r64
  (0010 (register)
    (let ((code (x86-reg-code register)))
      (1110
        (x86-encode-rex 1 0 0 (x86-high1 code))
        255
        (x86-encode-modrm 3 1 (x86-low3 code))))))

; NOT r64 / NEG r64: group-3 opcode 0xF7, /reg extension (not a register
; operand) selects the operation -- NOT is /2, NEG is /3 -- per #175's
; pinned XED evidence (`PATTERN : 0xF7 MOD[0b11] MOD=3 REG[0b010] RM[nnn]`
; / `REG[0b011]`). This matches INC/DEC's group-5 shape: always REX.W,
; REX.B only for r8-r15.
(0011 x86-encode-not-r64
  (0010 (register)
    (let ((code (x86-reg-code register)))
      (1110
        (x86-encode-rex 1 0 0 (x86-high1 code))
        247
        (x86-encode-modrm 3 2 (x86-low3 code))))))

(0011 x86-encode-neg-r64
  (0010 (register)
    (let ((code (x86-reg-code register)))
      (1110
        (x86-encode-rex 1 0 0 (x86-high1 code))
        247
        (x86-encode-modrm 3 3 (x86-low3 code))))))

; SHL/SHR/SAR r64, imm8: group-2 opcode 0xC1, /reg extension selects the
; operation -- SHL is /4, SHR is /5, SAR is /7 (/6 duplicates SHL under an
; undocumented encoding and is intentionally not admitted) -- per #175's pinned XED
; evidence (`PATTERN : 0xC1 MOD[0b11] MOD=3 REG[0b100] RM[nnn] UIMM8()`
; for SHL, `REG[0b101]` for SHR, `REG[0b111]` for SAR). Unlike disp8/
; rel8/rel32/imm32, UIMM8 is an *unsigned* byte in [0,255], so no
; two's-complement wrap-before-split is needed -- the admitted count
; becomes the raw trailing byte directly.
(0011 x86-encode-shift-r64-imm8
  (0010 (opcode-extension register count)
    (let ((code (x86-reg-code register)))
      (1110
        (x86-encode-rex 1 0 0 (x86-high1 code))
        193
        (x86-encode-modrm 3 opcode-extension (x86-low3 code))
        count))))

(0011 x86-encode-shl-r64-imm8
  (0010 (register count)
    (x86-encode-shift-r64-imm8 4 register count)))

(0011 x86-encode-shr-r64-imm8
  (0010 (register count)
    (x86-encode-shift-r64-imm8 5 register count)))

(0011 x86-encode-sar-r64-imm8
  (0010 (register count)
    (x86-encode-shift-r64-imm8 7 register count)))

; Jcc rel8: opcode 0x70+cc followed by a signed 8-bit relative displacement
; (from the address of the *next* instruction). No REX prefix -- this is a
; control-transfer, not a GPR operation. The 16 condition codes and their
; opcode offsets are fixed by Intel's encoding and confirmed against #175's
; pinned XED evidence (`PATTERN : 0x7<cc> mode64 ... BRDISP8()` for each
; ICLASS in order: JO,JNO,JB,JNB,JZ,JNZ,JBE,JNBE,JS,JNS,JP,JNP,JL,JNL,JLE,
; JNLE). Reuses x86-disp8-byte for the same two's-complement byte
; conversion #199 already proved correct for MOV's disp8 slot.
(0011 x86-encode-jcc-rel8
  (0010 (condition-code displacement)
    (1110
      (01010 112 condition-code)
      (x86-disp8-byte displacement))))

(0011 x86-encode-jo-rel8 (0010 (displacement) (x86-encode-jcc-rel8 0 displacement)))
(0011 x86-encode-jno-rel8 (0010 (displacement) (x86-encode-jcc-rel8 1 displacement)))
(0011 x86-encode-jb-rel8 (0010 (displacement) (x86-encode-jcc-rel8 2 displacement)))
(0011 x86-encode-jnb-rel8 (0010 (displacement) (x86-encode-jcc-rel8 3 displacement)))
(0011 x86-encode-jz-rel8 (0010 (displacement) (x86-encode-jcc-rel8 4 displacement)))
(0011 x86-encode-jnz-rel8 (0010 (displacement) (x86-encode-jcc-rel8 5 displacement)))
(0011 x86-encode-jbe-rel8 (0010 (displacement) (x86-encode-jcc-rel8 6 displacement)))
(0011 x86-encode-jnbe-rel8 (0010 (displacement) (x86-encode-jcc-rel8 7 displacement)))
(0011 x86-encode-js-rel8 (0010 (displacement) (x86-encode-jcc-rel8 8 displacement)))
(0011 x86-encode-jns-rel8 (0010 (displacement) (x86-encode-jcc-rel8 9 displacement)))
(0011 x86-encode-jp-rel8 (0010 (displacement) (x86-encode-jcc-rel8 #d10 displacement)))
(0011 x86-encode-jnp-rel8 (0010 (displacement) (x86-encode-jcc-rel8 #d11 displacement)))
(0011 x86-encode-jl-rel8 (0010 (displacement) (x86-encode-jcc-rel8 12 displacement)))
(0011 x86-encode-jnl-rel8 (0010 (displacement) (x86-encode-jcc-rel8 13 displacement)))
(0011 x86-encode-jle-rel8 (0010 (displacement) (x86-encode-jcc-rel8 14 displacement)))
(0011 x86-encode-jnle-rel8 (0010 (displacement) (x86-encode-jcc-rel8 15 displacement)))

; JMP rel8: opcode 0xEB followed by a signed 8-bit relative displacement,
; confirmed against #175's pinned XED evidence
; (`PATTERN : 0xEB mode64 norex2_prefix FORCE64() BRDISP8()`). Unlike Jcc,
; JMP is unconditional -- no condition-code byte, no ModRM, no REX -- but
; reuses the same x86-disp8-byte two's-complement conversion.
(0011 x86-encode-jmp-rel8
  (0010 (displacement)
    (1110
      235
      (x86-disp8-byte displacement))))

; Two's-complement little-endian bytes for a rel32 value already known to be
; in [-2147483648,2147483647]. Same wrap-before-split fix #199 proved for
; disp8 (x86-disp8-byte) and this file's own x86-u64-bytes lack for
; mov-r64-imm64 (#220's truth-sentinel audit documented this being an
; existing, out-of-scope gap) -- `mod` in this Lisp does not wrap negative operands, so
; adding 2^32 before reducing mod 2^32 is exact for the whole rel32 domain.
(0011 x86-rel32-bytes
  (0010 (displacement)
    (x86-u32-bytes
      (011
        (x86-ціла-частка-залишок
          (01010 displacement 4294967296)
          4294967296
          1)))))

; CALL rel32: opcode 0xE8 followed by a signed 32-bit relative displacement
; (from the address of the *next* instruction), confirmed against #175's
; pinned XED evidence (`PATTERN : 0xE8 mode64 norex2_prefix BRDISP32()
; DF64() FORCE64()`). No REX, no ModRM -- like JMP rel8/Jcc rel8, this is a
; control-transfer, not a GPR operation. Unlike JMP, CALL also pushes the
; return address (XED_REG_STACKPUSH) -- on real hardware this is the actual
; RSP-based machine stack, so a CALL executed through native-call-u64-raw
; pushes/pops for real; nothing in the arena model needs to know about it,
; the same "guest ABI is Lisp's, host mechanism is the CPU's" split #204
; already established for the Windows/Linux execution adapters.
(0011 x86-encode-call-rel32
  (0010 (displacement)
    (111 232 (x86-rel32-bytes displacement))))

; Jcc rel32: opcode 0x0F, then 0x80+cc, then a signed 32-bit relative
; displacement -- the conditional counterpart to JMP rel32, needed for the
; same reason: #196's own growth-v0 witnesses lean on CMP+Jcc far more than
; unconditional JMP (an arena-bounds check is inherently a Jcc), and their
; hand-derived disp8 offsets (e.g. "JNZ +11", "JNZ +33") will not survive
; much further composition. Confirmed against #175's pinned XED evidence
; (`PATTERN : 0x0F 0x8<cc> mode64 norex2_prefix FORCE64() BRANCH_HINT()
; BRDISP32()` for each ICLASS in the identical order the rel8 family
; already uses: JO,JNO,JB,JNB,JZ,JNZ,JBE,JNBE,JS,JNS,JP,JNP,JL,JNL,JLE,
; JNLE) -- reuses that same condition-code-to-opcode-offset mapping, just
; with a 2-byte opcode and a 4-byte displacement instead of 1+1.
(0011 x86-encode-jcc-rel32
  (0010 (condition-code displacement)
    (111
      15
      (111
        (01010 128 condition-code)
        (x86-rel32-bytes displacement)))))

(0011 x86-encode-jo-rel32 (0010 (displacement) (x86-encode-jcc-rel32 0 displacement)))
(0011 x86-encode-jno-rel32 (0010 (displacement) (x86-encode-jcc-rel32 1 displacement)))
(0011 x86-encode-jb-rel32 (0010 (displacement) (x86-encode-jcc-rel32 2 displacement)))
(0011 x86-encode-jnb-rel32 (0010 (displacement) (x86-encode-jcc-rel32 3 displacement)))
(0011 x86-encode-jz-rel32 (0010 (displacement) (x86-encode-jcc-rel32 4 displacement)))
(0011 x86-encode-jnz-rel32 (0010 (displacement) (x86-encode-jcc-rel32 5 displacement)))
(0011 x86-encode-jbe-rel32 (0010 (displacement) (x86-encode-jcc-rel32 6 displacement)))
(0011 x86-encode-jnbe-rel32 (0010 (displacement) (x86-encode-jcc-rel32 7 displacement)))
(0011 x86-encode-js-rel32 (0010 (displacement) (x86-encode-jcc-rel32 8 displacement)))
(0011 x86-encode-jns-rel32 (0010 (displacement) (x86-encode-jcc-rel32 9 displacement)))
(0011 x86-encode-jp-rel32 (0010 (displacement) (x86-encode-jcc-rel32 #d10 displacement)))
(0011 x86-encode-jnp-rel32 (0010 (displacement) (x86-encode-jcc-rel32 #d11 displacement)))
(0011 x86-encode-jl-rel32 (0010 (displacement) (x86-encode-jcc-rel32 12 displacement)))
(0011 x86-encode-jnl-rel32 (0010 (displacement) (x86-encode-jcc-rel32 13 displacement)))
(0011 x86-encode-jle-rel32 (0010 (displacement) (x86-encode-jcc-rel32 14 displacement)))
(0011 x86-encode-jnle-rel32 (0010 (displacement) (x86-encode-jcc-rel32 15 displacement)))

; JMP rel32: opcode 0xE9 followed by a signed 32-bit relative displacement,
; confirmed against #175's pinned XED evidence (`PATTERN : 0xE9 mode64
; norex2_prefix FORCE64() BRDISP32()`). Matches JMP rel8's own
; unconditional, no-ModRM, no-REX shape -- only the opcode byte and
; displacement width differ.
(0011 x86-encode-jmp-rel32
  (0010 (displacement)
    (111 233 (x86-rel32-bytes displacement))))

; CALL r64 / JMP r64 (indirect through a register): group-5 opcode 0xFF,
; /reg extension selects the operation -- CALL is /2, JMP is /4 -- per
; #175's pinned XED evidence (`PATTERN : 0xFF MOD[0b11] MOD=3 REG[0b010]
; RM[nnn] DF64() ...` for CALL, `REG[0b100]` for JMP). Both are `DF64()`
; (default 64-bit operand size in long mode), matching PUSH/POP's own
; default-64-bit shape, so no REX.W is emitted -- only REX.B, and only for
; r8-r15. Unlike CALL rel32,
; the target here is whatever absolute address the admitted register holds
; at runtime, not a displacement fixed at encode time; CALL still pushes a
; real return address via XED_REG_STACKPUSH, onto the same real machine
; stack #204 already established. This is the first indirect (register-
; target) control transfer the encoder admits: the destination is
; genuinely a runtime value, not something knowable from the bytes alone.
(0011 x86-encode-group5-indirect-r64
  (0010 (opcode-extension register)
    (let ((code (x86-reg-code register)))
      (110
        ((101 (x86-high1 code) 1)
          (1110
            (x86-encode-rex 0 0 0 1)
            255
            (x86-encode-modrm 3 opcode-extension (x86-low3 code))))
        ((010 ())
          (1110
            255
            (x86-encode-modrm 3 opcode-extension (x86-low3 code))))))))

(0011 x86-encode-call-r64
  (0010 (register)
    (x86-encode-group5-indirect-r64 2 register)))

(0011 x86-encode-jmp-r64
  (0010 (register)
    (x86-encode-group5-indirect-r64 4 register)))

; SETcc r8: opcode 0x0F 0x90+cc, ModRM mod=3, reg=0, rm=low3(code).
; In 64-bit mode:
; - codes 0..3 (al, cl, dl, bl) require no REX prefix.
; - codes 4..7 (spl, bpl, sil, dil) require REX prefix (0x40) to distinguish
;   them from legacy high bytes (ah, ch, dh, bh).
; - codes 8..15 (r8b..r15b) require REX.B=1 prefix (0x41).
(0011 x86-encode-setcc-r8
  (0010 (condition-code register)
    (let ((code (x86-reg-code register)))
      ; Exact-D1 predicate selects REX; structural default is the
      ; explicit D1 true witness, never legacy (query expected result).
      (110
        ((11011 code 3)
         (1110
           (x86-encode-rex 0 0 0 (x86-high1 code))
           15
           (01010 144 condition-code)
           (x86-encode-modrm 3 0 (x86-low3 code))))
        ((010 (001 ()))
         (1110
           15
           (01010 144 condition-code)
           (x86-encode-modrm 3 0 (x86-low3 code))))))))

(0011 x86-encode-seto-r8 (0010 (register) (x86-encode-setcc-r8 0 register)))
(0011 x86-encode-setno-r8 (0010 (register) (x86-encode-setcc-r8 1 register)))
(0011 x86-encode-setb-r8 (0010 (register) (x86-encode-setcc-r8 2 register)))
(0011 x86-encode-setc-r8 (0010 (register) (x86-encode-setcc-r8 2 register)))
(0011 x86-encode-setnb-r8 (0010 (register) (x86-encode-setcc-r8 3 register)))
(0011 x86-encode-setnc-r8 (0010 (register) (x86-encode-setcc-r8 3 register)))
(0011 x86-encode-setae-r8 (0010 (register) (x86-encode-setcc-r8 3 register)))
(0011 x86-encode-setz-r8 (0010 (register) (x86-encode-setcc-r8 4 register)))
(0011 x86-encode-sete-r8 (0010 (register) (x86-encode-setcc-r8 4 register)))
(0011 x86-encode-setnz-r8 (0010 (register) (x86-encode-setcc-r8 5 register)))
(0011 x86-encode-setne-r8 (0010 (register) (x86-encode-setcc-r8 5 register)))
(0011 x86-encode-setbe-r8 (0010 (register) (x86-encode-setcc-r8 6 register)))
(0011 x86-encode-setna-r8 (0010 (register) (x86-encode-setcc-r8 6 register)))
(0011 x86-encode-setnbe-r8 (0010 (register) (x86-encode-setcc-r8 7 register)))
(0011 x86-encode-seta-r8 (0010 (register) (x86-encode-setcc-r8 7 register)))
(0011 x86-encode-sets-r8 (0010 (register) (x86-encode-setcc-r8 8 register)))
(0011 x86-encode-setns-r8 (0010 (register) (x86-encode-setcc-r8 9 register)))
(0011 x86-encode-setp-r8 (0010 (register) (x86-encode-setcc-r8 #d10 register)))
(0011 x86-encode-setpe-r8 (0010 (register) (x86-encode-setcc-r8 #d10 register)))
(0011 x86-encode-setnp-r8 (0010 (register) (x86-encode-setcc-r8 #d11 register)))
(0011 x86-encode-setpo-r8 (0010 (register) (x86-encode-setcc-r8 #d11 register)))
(0011 x86-encode-setl-r8 (0010 (register) (x86-encode-setcc-r8 12 register)))
(0011 x86-encode-setnge-r8 (0010 (register) (x86-encode-setcc-r8 12 register)))
(0011 x86-encode-setnl-r8 (0010 (register) (x86-encode-setcc-r8 13 register)))
(0011 x86-encode-setge-r8 (0010 (register) (x86-encode-setcc-r8 13 register)))
(0011 x86-encode-setle-r8 (0010 (register) (x86-encode-setcc-r8 14 register)))
(0011 x86-encode-setng-r8 (0010 (register) (x86-encode-setcc-r8 14 register)))
(0011 x86-encode-setnle-r8 (0010 (register) (x86-encode-setcc-r8 15 register)))
(0011 x86-encode-setg-r8 (0010 (register) (x86-encode-setcc-r8 15 register)))

; MOVZX r64, r8: opcode 0x0F 0xB6, ModRM mod=3, reg=dest, rm=src.
; REX.W=1 extends the 8-bit source into the full 64-bit destination register.
(0011 x86-encode-movzx-r64-r8
  (0010 (destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (1110
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        182
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; IMUL r64, r64: two-operand signed multiply, opcode 0x0F 0xAF.
; Destination receives the low 64 bits of the signed product.
(0011 x86-encode-imul-r64-r64
  (0010 (destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (1110
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        175
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; CQO: Convert Quadword to Octword (sign-extend RAX into RDX:RAX).
; Opcode 0x48 0x99. Prepares dividend for 64-bit IDIV.
(0011 x86-encode-cqo
  (0010 ()
    (1110 72 153)))

; IDIV r64: signed division of RDX:RAX by r64 operand.
; Group 3 opcode 0xF7 /7, ModRM mod=3, reg=7, rm=src.
; Quotient is stored in RAX, remainder in RDX.
(0011 x86-encode-idiv-r64
  (0010 (source)
    (let ((src-code (x86-reg-code source)))
      (1110
        (x86-encode-rex 1 0 0 (x86-high1 src-code))
        247
        (x86-encode-modrm 3 7 (x86-low3 src-code))))))

; CMOVcc r64, r64: conditional move, opcode 0x0F 0x40+cc.
; Moves source to destination if condition code is satisfied.
(0011 x86-encode-cmovcc-r64-r64
  (0010 (condition-code destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (1110
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        (01010 64 condition-code)
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

(0011 x86-encode-cmovo-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 0 dest src)))
(0011 x86-encode-cmovno-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 1 dest src)))
(0011 x86-encode-cmovb-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 2 dest src)))
(0011 x86-encode-cmovc-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 2 dest src)))
(0011 x86-encode-cmovnb-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 3 dest src)))
(0011 x86-encode-cmovnc-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 3 dest src)))
(0011 x86-encode-cmovae-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 3 dest src)))
(0011 x86-encode-cmovz-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 4 dest src)))
(0011 x86-encode-cmove-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 4 dest src)))
(0011 x86-encode-cmovnz-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 5 dest src)))
(0011 x86-encode-cmovne-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 5 dest src)))
(0011 x86-encode-cmovbe-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 6 dest src)))
(0011 x86-encode-cmovna-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 6 dest src)))
(0011 x86-encode-cmovnbe-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 7 dest src)))
(0011 x86-encode-cmova-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 7 dest src)))
(0011 x86-encode-cmovs-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 8 dest src)))
(0011 x86-encode-cmovns-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 9 dest src)))
(0011 x86-encode-cmovp-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 #d10 dest src)))
(0011 x86-encode-cmovpe-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 #d10 dest src)))
(0011 x86-encode-cmovnp-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 #d11 dest src)))
(0011 x86-encode-cmovpo-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 #d11 dest src)))
(0011 x86-encode-cmovl-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 12 dest src)))
(0011 x86-encode-cmovnge-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 12 dest src)))
(0011 x86-encode-cmovnl-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 13 dest src)))
(0011 x86-encode-cmovge-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 13 dest src)))
(0011 x86-encode-cmovle-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 14 dest src)))
(0011 x86-encode-cmovng-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 14 dest src)))
(0011 x86-encode-cmovnle-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 15 dest src)))
(0011 x86-encode-cmovg-r64-r64 (0010 (dest src) (x86-encode-cmovcc-r64-r64 15 dest src)))

; NOP: opcode 0x90.
(0011 x86-encode-nop
  (0010 ()
    (1110 144)))

; TEST r/m64, imm32: Group 3 opcode 0xF7 /0 id, ModRM mod=3, reg=0, rm=dest.
(0011 x86-encode-test-r64-imm32
  (0010 (destination immediate)
    (let ((code (x86-reg-code destination)))
      (1111
        (1110
          (x86-encode-rex 1 0 0 (x86-high1 code))
          247
          (x86-encode-modrm 3 0 (x86-low3 code)))
        (x86-imm32-bytes immediate)))))

; BT r/m64, r64: opcode 0x0F 0xA3 /r. ModRM reg=index, rm=base.
; Sets Carry Flag (CF) to the value of the bit at the given index.
(0011 x86-encode-bt-r64-r64
  (0010 (base index)
    (let ((base-code (x86-reg-code base))
          (index-code (x86-reg-code index)))
      (1110
        (x86-encode-rex 1 (x86-high1 index-code) 0 (x86-high1 base-code))
        15
        163
        (x86-encode-modrm 3 (x86-low3 index-code) (x86-low3 base-code))))))

; Group 8 bit operations with imm8: opcode 0x0F 0xBA /reg ib.
(0011 x86-encode-group8-r64-imm8
  (0010 (opcode-extension register bit-index)
    (let ((code (x86-reg-code register)))
      (1110
        (x86-encode-rex 1 0 0 (x86-high1 code))
        15
        186
        (x86-encode-modrm 3 opcode-extension (x86-low3 code))
        bit-index))))

(0011 x86-encode-bt-r64-imm8
  (0010 (register bit-index)
    (x86-encode-group8-r64-imm8 4 register bit-index)))

(0011 x86-encode-bts-r64-imm8
  (0010 (register bit-index)
    (x86-encode-group8-r64-imm8 5 register bit-index)))

(0011 x86-encode-btr-r64-imm8
  (0010 (register bit-index)
    (x86-encode-group8-r64-imm8 6 register bit-index)))

(0011 x86-encode-btc-r64-imm8
  (0010 (register bit-index)
    (x86-encode-group8-r64-imm8 7 register bit-index)))

; MOVSX r64, r/m8: opcode 0x0F 0xBE /r. Sign-extend 8-bit to 64-bit.
(0011 x86-encode-movsx-r64-r8
  (0010 (destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (1110
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        190
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; MOVSXD r64, r/m32: opcode 0x63 /r. Sign-extend 32-bit to 64-bit.
(0011 x86-encode-movsxd-r64-r32
  (0010 (destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (1110
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        99
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; POPCNT r64, r/m64: opcode 0xF3 0x0F 0xB8 /r. Count set bits (population count).
(0011 x86-encode-popcnt-r64-r64
  (0010 (destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (1110
        243
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        184
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; TZCNT r64, r/m64: opcode 0xF3 0x0F 0xBC /r. Count trailing zeros.
(0011 x86-encode-tzcnt-r64-r64
  (0010 (destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (1110
        243
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        188
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; BSF r64, r/m64: opcode 0x0F 0xBC /r. Bit Scan Forward (first set bit).
(0011 x86-encode-bsf-r64-r64
  (0010 (destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (1110
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        188
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; BSR r64, r/m64: opcode 0x0F 0xBD /r. Bit Scan Reverse (last set bit).
(0011 x86-encode-bsr-r64-r64
  (0010 (destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (1110
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        189
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; BSWAP r64: opcode 0x0F (0xC8 + rd). Byte Swap (reverse byte order).
(0011 x86-encode-bswap-r64
  (0010 (register)
    (let ((code (x86-reg-code register)))
      (1110
        (x86-encode-rex 1 0 0 (x86-high1 code))
        15
        (01010 200 (x86-low3 code))))))

; ROL / ROR r64, imm8: group-2 opcode 0xC1, /0 for ROL, /1 for ROR.
(0011 x86-encode-rol-r64-imm8
  (0010 (register count)
    (x86-encode-shift-r64-imm8 0 register count)))

(0011 x86-encode-ror-r64-imm8
  (0010 (register count)
    (x86-encode-shift-r64-imm8 1 register count)))

; XCHG r64, r64: opcode 0x87 /r. Exchange register values.
(0011 x86-encode-xchg-r64-r64
  (0010 (dst src)
    (let ((dst-code (x86-reg-code dst))
          (src-code (x86-reg-code src)))
      (1110
        (x86-encode-rex 1 (x86-high1 dst-code) 0 (x86-high1 src-code))
        135
        (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))

; CLD: opcode 0xFC (252). Clear direction flag (DF=0).
(0011 x86-encode-cld
  (0010 ()
    (1110 252)))

; STD: opcode 0xFD (253). Set direction flag (DF=1).
(0011 x86-encode-std
  (0010 ()
    (1110 253)))

; STOSQ: opcode 0x48 0xAB (72 171). Store RAX to [RDI], increment RDI by 8.
(0011 x86-encode-stosq
  (0010 ()
    (1110 (x86-encode-rex 1 0 0 0) 171)))

; REP STOSQ: opcode 0xF3 0x48 0xAB. Fill RCX qwords at [RDI] with RAX.
(0011 x86-encode-rep-stosq
  (0010 ()
    (1110 243 (x86-encode-rex 1 0 0 0) 171)))

; STOSB: opcode 0xAA (170). Store AL to [RDI], increment RDI by 1.
(0011 x86-encode-stosb
  (0010 ()
    (1110 170)))

; REP STOSB: opcode 0xF3 0xAA. Fill RCX bytes at [RDI] with AL.
(0011 x86-encode-rep-stosb
  (0010 ()
    (1110 243 170)))

; MOVSQ: opcode 0x48 0xA5 (72 165). Move qword from [RSI] to [RDI].
(0011 x86-encode-movsq
  (0010 ()
    (1110 (x86-encode-rex 1 0 0 0) 165)))

; REP MOVSQ: opcode 0xF3 0x48 0xA5. Copy RCX qwords from [RSI] to [RDI].
(0011 x86-encode-rep-movsq
  (0010 ()
    (1110 243 (x86-encode-rex 1 0 0 0) 165)))

; MOVSB: opcode 0xA4 (164). Move byte from [RSI] to [RDI].
(0011 x86-encode-movsb
  (0010 ()
    (1110 164)))

; REP MOVSB: opcode 0xF3 0xA4. Copy RCX bytes from [RSI] to [RDI].
(0011 x86-encode-rep-movsb
  (0010 ()
    (1110 243 164)))

(0011 x86-encode-sse2-f2-xmm-xmm
  (0010 (opcode-byte dst src)
    (let ((dst-code (x86-xmm-reg-code dst))
          (src-code (x86-xmm-reg-code src)))
      (110
        ((менше? (додати (x86-high1 dst-code) (x86-high1 src-code)) 1)
         (1110 242 15 opcode-byte (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))
        ((010 ())
         (1110 242 (x86-encode-rex 0 (x86-high1 dst-code) 0 (x86-high1 src-code))
               15 opcode-byte (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))))

(0011 x86-encode-sse2-66-xmm-xmm
  (0010 (opcode-byte dst src)
    (let ((dst-code (x86-xmm-reg-code dst))
          (src-code (x86-xmm-reg-code src)))
      (110
        ((менше? (додати (x86-high1 dst-code) (x86-high1 src-code)) 1)
         (1110 102 15 opcode-byte (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))
        ((010 ())
         (1110 102 (x86-encode-rex 0 (x86-high1 dst-code) 0 (x86-high1 src-code))
               15 opcode-byte (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))))

; AES-NI register-source форми з pinned #175 XED evidence мають спільну
; будову: mandatory 0x66, optional REX.R/REX.B для XMM8-XMM15, далі
; 0F 38 або 0F 3A, opcode і ModR/M з mode=3. Цей helper описує лише
; машинне кодування; значення AES-операцій тут не визначається.
(0011 x86-encode-sse-66-map-xmm-xmm
  (0010 (map-byte opcode-byte dst src)
    (let ((dst-code (x86-xmm-reg-code dst))
          (src-code (x86-xmm-reg-code src)))
      (110
        ((менше? (додати (x86-high1 dst-code) (x86-high1 src-code)) 1)
         (1110
           102
           15
           map-byte
           opcode-byte
           (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))
        ((010 ())
         (1110
           102
           (x86-encode-rex 0 (x86-high1 dst-code) 0 (x86-high1 src-code))
           15
           map-byte
           opcode-byte
           (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))))

; AESENC xmm, xmm: 66 0F 38 DC /r.
(0011 x86-encode-aesenc-xmm-xmm
  (0010 (dst src)
    (x86-encode-sse-66-map-xmm-xmm 56 220 dst src)))

; AESENCLAST xmm, xmm: 66 0F 38 DD /r.
(0011 x86-encode-aesenclast-xmm-xmm
  (0010 (dst src)
    (x86-encode-sse-66-map-xmm-xmm 56 221 dst src)))

; AESDEC xmm, xmm: 66 0F 38 DE /r.
(0011 x86-encode-aesdec-xmm-xmm
  (0010 (dst src)
    (x86-encode-sse-66-map-xmm-xmm 56 222 dst src)))

; AESDECLAST xmm, xmm: 66 0F 38 DF /r.
(0011 x86-encode-aesdeclast-xmm-xmm
  (0010 (dst src)
    (x86-encode-sse-66-map-xmm-xmm 56 223 dst src)))

; AESIMC xmm, xmm: 66 0F 38 DB /r.
(0011 x86-encode-aesimc-xmm-xmm
  (0010 (dst src)
    (x86-encode-sse-66-map-xmm-xmm 56 219 dst src)))

; AESKEYGENASSIST xmm, xmm, imm8: 66 0F 3A DF /r ib.
; Межа imm8 перевіряється admission-шаром до матеріалізації байтів.
(0011 x86-encode-aeskeygenassist-xmm-xmm-imm8
  (0010 (dst src immediate)
    (1111
      (x86-encode-sse-66-map-xmm-xmm 58 223 dst src)
      (1110 immediate))))

; AES-NI memory-source bounded base+disp8 використовує ту саму x86
; адресацію, що вже доведена для MOV/LEA: ModR/M mode=01, SIB для rsp/r12,
; REX.R для xmm8-xmm15 і REX.B для r8-r15. Ширину пам'яті визначає сама
; інструкція AES, тому цей helper не створює окремої семантики пам'яті.
(0011 x86-encode-sse-66-map-xmm-mem-disp8
  (0010 (map-byte opcode-byte dst base displacement)
    (let ((dst-code (x86-xmm-reg-code dst))
          (base-code (x86-reg-code base)))
      (let ((modrm
              (x86-encode-modrm
                1
                (x86-low3 dst-code)
                (x86-low3 base-code)))
            (disp-byte (x86-disp8-byte displacement)))
        (let ((address-tail
                (110
                  ((101 (x86-low3 base-code) 4)
                   (1110 modrm (x86-encode-sib 0 4 4) disp-byte))
                  ((010 ())
                   (1110 modrm disp-byte)))))
          (110
            ((менше? (додати (x86-high1 dst-code) (x86-high1 base-code)) 1)
             (1111
               (1110 102 15 map-byte opcode-byte)
               address-tail))
            ((010 ())
             (1111
               (1110
                 102
                 (x86-encode-rex
                   0
                   (x86-high1 dst-code)
                   0
                   (x86-high1 base-code))
                 15
                 map-byte
                 opcode-byte)
               address-tail))))))))

(0011 x86-encode-aesenc-xmm-mem-disp8
  (0010 (dst base displacement)
    (x86-encode-sse-66-map-xmm-mem-disp8
      56 220 dst base displacement)))

(0011 x86-encode-aesenclast-xmm-mem-disp8
  (0010 (dst base displacement)
    (x86-encode-sse-66-map-xmm-mem-disp8
      56 221 dst base displacement)))

(0011 x86-encode-aesdec-xmm-mem-disp8
  (0010 (dst base displacement)
    (x86-encode-sse-66-map-xmm-mem-disp8
      56 222 dst base displacement)))

(0011 x86-encode-aesdeclast-xmm-mem-disp8
  (0010 (dst base displacement)
    (x86-encode-sse-66-map-xmm-mem-disp8
      56 223 dst base displacement)))

(0011 x86-encode-aesimc-xmm-mem-disp8
  (0010 (dst base displacement)
    (x86-encode-sse-66-map-xmm-mem-disp8
      56 219 dst base displacement)))

(0011 x86-encode-aeskeygenassist-xmm-mem-disp8-imm8
  (0010 (dst base displacement immediate)
    (1111
      (x86-encode-sse-66-map-xmm-mem-disp8
        58 223 dst base displacement)
      (1110 immediate))))

; PCLMULQDQ xmm, xmm, imm8: 66 0F 3A 44 /r ib.
; Pinned #175 XED evidence exposes exactly register-source and memory-source
; forms. The immediate selects the source 64-bit lanes; that ISA meaning is
; not redefined here -- this layer only materializes the admitted bytes.
(0011 x86-encode-pclmulqdq-xmm-xmm-imm8
  (0010 (dst src immediate)
    (1111
      (x86-encode-sse-66-map-xmm-xmm #d58 #d68 dst src)
      (1110 immediate))))

; Bounded memory projection: base+disp8 reuses the already witnessed
; ModR/M/SIB/REX mechanism. This is not a claim of general x86 addressing.
(0011 x86-encode-pclmulqdq-xmm-mem-disp8-imm8
  (0010 (dst base displacement immediate)
    (1111
      (x86-encode-sse-66-map-xmm-mem-disp8
        #d58 #d68 dst base displacement)
      (1110 immediate))))

; MOVSD xmm, xmm: opcode 0xF2 0x0F 0x10 /r
(0011 x86-encode-movsd-xmm-xmm
  (0010 (dst src)
    (x86-encode-sse2-f2-xmm-xmm 16 dst src)))

; SQRTSD xmm, xmm: opcode 0xF2 0x0F 0x51 /r
(0011 x86-encode-sqrtsd-xmm-xmm
  (0010 (dst src)
    (x86-encode-sse2-f2-xmm-xmm 81 dst src)))

; ADDSD xmm, xmm: opcode 0xF2 0x0F 0x58 /r
(0011 x86-encode-addsd-xmm-xmm
  (0010 (dst src)
    (x86-encode-sse2-f2-xmm-xmm 88 dst src)))

; MULSD xmm, xmm: opcode 0xF2 0x0F 0x59 /r
(0011 x86-encode-mulsd-xmm-xmm
  (0010 (dst src)
    (x86-encode-sse2-f2-xmm-xmm 89 dst src)))

; SUBSD xmm, xmm: opcode 0xF2 0x0F 0x5C /r
(0011 x86-encode-subsd-xmm-xmm
  (0010 (dst src)
    (x86-encode-sse2-f2-xmm-xmm 92 dst src)))

; MINSD xmm, xmm: opcode 0xF2 0x0F 0x5D /r
(0011 x86-encode-minsd-xmm-xmm
  (0010 (dst src)
    (x86-encode-sse2-f2-xmm-xmm 93 dst src)))

; DIVSD xmm, xmm: opcode 0xF2 0x0F 0x5E /r
(0011 x86-encode-divsd-xmm-xmm
  (0010 (dst src)
    (x86-encode-sse2-f2-xmm-xmm 94 dst src)))

; MAXSD xmm, xmm: opcode 0xF2 0x0F 0x5F /r
(0011 x86-encode-maxsd-xmm-xmm
  (0010 (dst src)
    (x86-encode-sse2-f2-xmm-xmm 95 dst src)))

; UCOMISD xmm, xmm: opcode 0x66 0x0F 0x2E /r
(0011 x86-encode-ucomisd-xmm-xmm
  (0010 (dst src)
    (x86-encode-sse2-66-xmm-xmm 46 dst src)))

; XORPD xmm, xmm: opcode 0x66 0x0F 0x57 /r
(0011 x86-encode-xorpd-xmm-xmm
  (0010 (dst src)
    (x86-encode-sse2-66-xmm-xmm 87 dst src)))

; CVTSI2SD xmm, r64: opcode 0xF2 REX.W 0x0F 0x2A /r
(0011 x86-encode-cvtsi2sd-xmm-r64
  (0010 (dst src)
    (let ((dst-code (x86-xmm-reg-code dst))
          (src-code (x86-reg-code src)))
      (1110 242 (x86-encode-rex 1 (x86-high1 dst-code) 0 (x86-high1 src-code))
            15 42 (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))

; CVTTSD2SI r64, xmm: opcode 0xF2 REX.W 0x0F 0x2C /r
(0011 x86-encode-cvttsd2si-r64-xmm
  (0010 (dst src)
    (let ((dst-code (x86-reg-code dst))
          (src-code (x86-xmm-reg-code src)))
      (1110 242 (x86-encode-rex 1 (x86-high1 dst-code) 0 (x86-high1 src-code))
            15 44 (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))

; MOVQ xmm, r64: opcode 0x66 REX.W 0x0F 0x6E /r
(0011 x86-encode-movq-xmm-r64
  (0010 (dst src)
    (let ((dst-code (x86-xmm-reg-code dst))
          (src-code (x86-reg-code src)))
      (1110 102 (x86-encode-rex 1 (x86-high1 dst-code) 0 (x86-high1 src-code))
            15 #d110 (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))

; MOVQ r64, xmm: opcode 0x66 REX.W 0x0F 0x7E /r
(0011 x86-encode-movq-r64-xmm
  (0010 (dst src)
    (let ((dst-code (x86-reg-code dst))
          (src-code (x86-xmm-reg-code src)))
      (1110 102 (x86-encode-rex 1 (x86-high1 src-code) 0 (x86-high1 dst-code))
            15 126 (x86-encode-modrm 3 (x86-low3 src-code) (x86-low3 dst-code))))))

; RDRAND/RDSEED r64 — positive control for #2372 generator-first machine grammar.
; Both descend from one XED-proven shape: REX.W + 0F C7 /digit, MOD=3, RM=GPRv.
; The shared helper is the encoding law; mnemonic wrappers are derived projections.
(0011 x86-encode-0f-c7-group-r64
  (0010 (opcode-extension register)
    (let ((code (x86-reg-code register))
          (mechanism-extension
            (x86-project-bin3-to-mechanism-u3 opcode-extension)))
      ; Emitted instruction bytes are the legacy/mechanical byte carrier.
      ; Keep the opcode-extension input canonical (#b...) above, but do not
      ; leak BinaryNumber into the byte list: equal? intentionally keeps
      ; canonical BinaryNumber distinct from legacy/mechanical Number.
      (1110
        (x86-encode-rex 1 0 0 (x86-high1 code))
        #d15
        #d199
        (x86-encode-modrm 3 mechanism-extension (x86-low3 code))))))

(0011 x86-encode-rdrand-r64
  (0010 (register)
    (x86-encode-0f-c7-group-r64 #b110 register)))

(0011 x86-encode-rdseed-r64
  (0010 (register)
    (x86-encode-0f-c7-group-r64 #b111 register)))

; RDTSC: opcode 0x0F 0x31
(0011 x86-encode-rdtsc
  (0010 ()
    (1110 15 49)))

; CMPXCHG r64, r64: opcode REX.W 0x0F 0xB1 /r
(0011 x86-encode-cmpxchg-r64-r64
  (0010 (dst src)
    (let ((dst-code (x86-reg-code dst))
          (src-code (x86-reg-code src)))
      (1110 (x86-encode-rex 1 (x86-high1 src-code) 0 (x86-high1 dst-code))
            15 177 (x86-encode-modrm 3 (x86-low3 src-code) (x86-low3 dst-code))))))

; Механічне, замкнене складання двох списків байтів із D3 CONS/CAR/CDR.
; Жодна історична W8 APPEND-голова не отримує права виклику.
; Byte-list traversal must feed exact PredicateBit values to D3 COND.
; Legacy surface aliases atom?/eq?/car/cdr/append retain answer/compatibility
; domains; the machine path uses the canonical 3-bit heads directly.
; Byte-list traversal drives exact D3 COND using only exact PredicateBit
; operations. ATOM distinguishes empty-list from pair; D4 NOT complements that
; bit for the recursive branch. Avoid D3 EQ here: compatibility EQ answers are
; graded lists and are intentionally invalid as D3 COND controls.
(0011 x86-сполучити-байти
  (0010 (ліво право)
    (110
      ((010 ліво) право)
      ((0100 (010 ліво))
       (111
         (100 ліво)
         (x86-сполучити-байти (011 ліво) право))))))

(0011 x86-encode-program
  (0010 (instructions)
    (110
      ((0101 instructions) (001 ()))
      ((0100 (010 instructions))
       (x86-сполучити-байти
         (100 instructions)
         (x86-encode-program (011 instructions))))
      ((010 instructions)
       (1110 (001 rejected) (001 machine-operand) (001 instruction-list) instructions)))))

; #2372 reusable VEX3 XMM register law.
; byte1 = C4; byte2 = ~R ~X ~B m-mmmm; byte3 = W ~vvvv L pp.
; These are machine bytes in the exact Number carrier already used by the
; x86 encoder, so the instruction-set witness compares identity, not print.
(0011 x86-vex3-byte2
  (0010 (mmmmm r x b)
    (01010
      (10110 (01011 1 r) 128)
      (01010
        (10110 (01011 1 x) 64)
        (01010
          (10110 (01011 1 b) 32)
          mmmmm)))))

(0011 x86-vex3-byte3
  (0010 (w vvvv l pp)
    (01010
      (10110 w 128)
      (01010
        (10110 (01011 15 vvvv) 8)
        (01010
          (10110 l 4)
          pp)))))

(0011 x86-encode-vex3-xmm-xmm-xmm
  (0010 (mmmmm w l pp opcode dst src1 src2)
    (001000
      ((dst-code (x86-xmm-reg-code dst))
       (src1-code (x86-xmm-reg-code src1))
       (src2-code (x86-xmm-reg-code src2)))
      (1110
        196
        (x86-vex3-byte2
          mmmmm
          (x86-high1 dst-code)
          0
          (x86-high1 src2-code))
        (x86-vex3-byte3 w src1-code l pp)
        opcode
        (x86-encode-modrm
          3
          (x86-low3 dst-code)
          (x86-low3 src2-code))))))

; VANDNPS xmm,xmm,xmm: VEX.128.0F.WIG 55 /r.
(0011 x86-encode-vandnps-xmm-xmm-xmm
  (0010 (dst src1 src2)
    (x86-encode-vex3-xmm-xmm-xmm
      1 0 0 0 85 dst src1 src2)))

; VANDNPD xmm,xmm,xmm: VEX.128.66.0F.WIG 55 /r.
(0011 x86-encode-vandnpd-xmm-xmm-xmm
  (0010 (dst src1 src2)
    (x86-encode-vex3-xmm-xmm-xmm
      1 0 0 1 85 dst src1 src2)))

; VADDPD xmm,xmm,xmm: VEX.128.66.0F.WIG 58 /r.
(0011 x86-encode-vaddpd-xmm-xmm-xmm
  (0010 (dst src1 src2)
    (x86-encode-vex3-xmm-xmm-xmm
      1 0 0 1 88 dst src1 src2)))

; VADDPS xmm,xmm,xmm: VEX.128.0F.WIG 58 /r.
(0011 x86-encode-vaddps-xmm-xmm-xmm
  (0010 (dst src1 src2)
    (x86-encode-vex3-xmm-xmm-xmm
      1 0 0 0 88 dst src1 src2)))

