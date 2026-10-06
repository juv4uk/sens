# Domain tables D1–D6

**Authority:** `knowledge/d1-d7-foundation.json` (#3572).

These are human projections only. Exact identity remains `bits + domain + ratified law`.
The historical 8-bit registry is consulted only as a lexical donor and never as coordinate authority.

Canonical surface order: **ук → укр → san → eng → LISP → SUM**.

## uttara1 (D1)

| bits | ук | укр | san | eng | LISP | SUM |
|---|---|---|---|---|---|---|
| `0` | `ні` | `ні` | `na` | `no` | `NIL` | `uttara1:0=NO` |
| `1` | `так` | `так` | `ām` | `yes` | `T` | `uttara1:1=YES` |

## racanā2 (D2)

| bits | ук | укр | san | eng | LISP | SUM |
|---|---|---|---|---|---|---|
| `00` | `пропуск` | `пропуск` | `antarāla` | `separator` | `—` | `racanā2:00=SEPARATOR` |
| `01` | `закрити` | `закрити` | `samāpana` | `close` | `—` | `racanā2:01=CLOSE` |
| `10` | `відкрити` | `відкрити` | `udghāṭana` | `open` | `—` | `racanā2:10=OPEN` |
| `11` | `крапка` | `крапка` | `bindu` | `dot` | `—` | `racanā2:11=DOT` |

## bīja3 (D3)

| bits | ук | укр | san | eng | LISP | SUM |
|---|---|---|---|---|---|---|
| `000` | `порожнє` | `порожнє` | `śūnya` | `empty` | `NIL` | `bīja3:000=EMPTY` |
| `001` | `як-є` | `як-є` | `svarūpa` | `quote` | `QUOTE` | `bīja3:001=QUOTE` |
| `010` | `атом?` | `атом?` | `aṇu?` | `atom` | `ATOM` | `bīja3:010=ATOM` |
| `011` | `решта` | `решта` | `śeṣa` | `cdr` | `CDR` | `bīja3:011=CDR` |
| `100` | `перше` | `перше` | `ādi` | `car` | `CAR` | `bīja3:100=CAR` |
| `101` | `тотожне?` | `тотожне?` | `abheda?` | `eq` | `EQ` | `bīja3:101=EQ` |
| `110` | `за-умовою` | `за-умовою` | `krama` | `cond` | `COND` | `bīja3:110=COND` |
| `111` | `сполучити` | `сполучити` | `saṃyuj` | `cons` | `CONS` | `bīja3:111=CONS` |

## pravartana4 (D4)

| bits | ук | укр | san | eng | LISP | SUM |
|---|---|---|---|---|---|---|
| `0000` | `застосувати` | `застосувати` | `prayoga` | `apply` | `APPLY` | `pravartana4:0000=APPLY` |
| `0001` | `обчислити` | `обчислити` | `vicāraṇa` | `eval` | `EVAL` | `pravartana4:0001=EVAL` |
| `0010` | `функція` | `функція` | `phalana` | `lambda` | `LAMBDA` | `pravartana4:0010=LAMBDA` |
| `0011` | `визначити` | `визначити` | `nirvacana` | `define` | `DEFINE` | `pravartana4:0011=DEFINE` |
| `0100` | `не` | `не` | `niṣedha` | `not` | `NOT` | `pravartana4:0100=NOT` |
| `0101` | `порожнє?` | `порожнє?` | `śūnya?` | `null` | `NULL` | `pravartana4:0101=NULL` |
| `0110` | `решта-від-першого` | `решта-від-першого` | `śeṣa-ādi` | `cdar` | `CDAR` | `pravartana4:0110=CDAR` |
| `0111` | `решта-від-решти` | `решта-від-решти` | `śeṣa-śeṣa` | `cddr` | `CDDR` | `pravartana4:0111=CDDR` |
| `1000` | `перше-від-першого` | `перше-від-першого` | `ādi-ādi` | `caar` | `CAAR` | `pravartana4:1000=CAAR` |
| `1001` | `перше-від-решти` | `перше-від-решти` | `ādi-śeṣa` | `cadr` | `CADR` | `pravartana4:1001=CADR` |
| `1010` | `знайти` | `знайти` | `anveṣaṇa` | `lookup` | `LOOKUP` | `pravartana4:1010=LOOKUP` |
| `1011` | `зв'язати` | `зв'язати` | `bandha` | `bind` | `BIND` | `pravartana4:1011=BIND` |
| `1100` | `обчислити-умови` | `обчислити-умови` | `krama-vicāraṇa` | `evcon` | `EVCON` | `pravartana4:1100=EVCON` |
| `1101` | `обчислити-список` | `обчислити-список` | `śreṇī-vicāraṇa` | `evlis` | `EVLIS` | `pravartana4:1101=EVLIS` |
| `1110` | `список` | `список` | `śreṇī` | `list` | `LIST` | `pravartana4:1110=LIST` |
| `1111` | `приєднати` | `приєднати` | `saṅkalana` | `append` | `APPEND` | `pravartana4:1111=APPEND` |

## vistāra5 (D5)

| bits | ук | укр | san | eng | LISP | SUM |
|---|---|---|---|---|---|---|
| `00000` | `обчислити-як-є` | `обчислити-як-є` | `svarūpa-vicāraṇa` | `evalquote` | `EVALQUOTE` | `vistāra5:00000=EVALQUOTE` |
| `00001` | `функція-значення` | `функція-значення` | `phalana-rūpa` | `function` | `FUNCTION` | `vistāra5:00001=FUNCTION` |
| `00010` | `необчислений-вираз` | `необчислений-вираз` | `avicārita-rūpa` | `fexpr` | `FEXPR` | `vistāra5:00010=FEXPR` |
| `00011` | `макрос` | `макрос` | `vistāra-rūpa` | `macro` | `MACRO` | `vistāra5:00011=MACRO` |
| `00100` | `мітка` | `мітка` | `cihna` | `label` | `LABEL` | `vistāra5:00100=LABEL` |
| `00101` | `програма` | `програма` | `kāryakrama` | `prog` | `PROG` | `vistāra5:00101=PROG` |
| `00110` | `встановити` | `встановити` | `sthāpana` | `set` | `SET` | `vistāra5:00110=SET` |
| `00111` | `встановити-ім'я` | `встановити-ім'я` | `nāma-sthāpana` | `setq` | `SETQ` | `vistāra5:00111=SETQ` |
| `01000` | `нуль?` | `нуль?` | `saṅkhyā-śūnya?` | `zerop` | `ZEROP` | `vistāra5:01000=ZEROP` |
| `01001` | `число?` | `число?` | `saṅkhyā?` | `numberp` | `NUMBERP` | `vistāra5:01001=NUMBERP` |
| `01010` | `додати` | `додати` | `yoga` | `plus` | `PLUS` | `vistāra5:01010=PLUS` |
| `01011` | `відняти` | `відняти` | `viyoga` | `difference` | `DIFFERENCE` | `vistāra5:01011=DIFFERENCE` |
| `01100` | `решта-від-першого-від-першого` | `решта-від-першого-від-першого` | `śeṣa-ādi-ādi` | `cdaar` | `CDAAR` | `vistāra5:01100=CDAAR` |
| `01101` | `решта-від-першого-від-решти` | `решта-від-першого-від-решти` | `śeṣa-ādi-śeṣa` | `cdadr` | `CDADR` | `vistāra5:01101=CDADR` |
| `01110` | `решта-від-решти-від-першого` | `решта-від-решти-від-першого` | `śeṣa-śeṣa-ādi` | `cddar` | `CDDAR` | `vistāra5:01110=CDDAR` |
| `01111` | `решта-від-решти-від-решти` | `решта-від-решти-від-решти` | `śeṣa-śeṣa-śeṣa` | `cdddr` | `CDDDR` | `vistāra5:01111=CDDDR` |
| `10000` | `перше-від-першого-від-першого` | `перше-від-першого-від-першого` | `ādi-ādi-ādi` | `caaar` | `CAAAR` | `vistāra5:10000=CAAAR` |
| `10001` | `перше-від-першого-від-решти` | `перше-від-першого-від-решти` | `ādi-ādi-śeṣa` | `caadr` | `CAADR` | `vistāra5:10001=CAADR` |
| `10010` | `перше-від-решти-від-першого` | `перше-від-решти-від-першого` | `ādi-śeṣa-ādi` | `cadar` | `CADAR` | `vistāra5:10010=CADAR` |
| `10011` | `перше-від-решти-від-решти` | `перше-від-решти-від-решти` | `ādi-śeṣa-śeṣa` | `caddr` | `CADDR` | `vistāra5:10011=CADDR` |
| `10100` | `зворот` | `зворот` | `viloma` | `reverse` | `REVERSE` | `vistāra5:10100=REVERSE` |
| `10101` | `зворот-до` | `зворот-до` | `viloma-saṅkalana` | `reverse-onto` | `REVERSE-ONTO` | `vistāra5:10101=REVERSE-ONTO` |
| `10110` | `помножити` | `помножити` | `guṇana` | `times` | `TIMES` | `vistāra5:10110=TIMES` |
| `10111` | `частка` | `частка` | `bhāga` | `quotient` | `QUOTIENT` | `vistāra5:10111=QUOTIENT` |
| `11000` | `перейти` | `перейти` | `gamana` | `go` | `GO` | `vistāra5:11000=GO` |
| `11001` | `повернути` | `повернути` | `nivartana` | `return` | `RETURN` | `vistāra5:11001=RETURN` |
| `11010` | `менше?` | `менше?` | `hīna?` | `lessp` | `LESSP` | `vistāra5:11010=LESSP` |
| `11011` | `більше?` | `більше?` | `adhika?` | `greaterp` | `GREATERP` | `vistāra5:11011=GREATERP` |
| `11100` | `знайти-за-ключем` | `знайти-за-ключем` | `saṃbandha` | `assoc` | `ASSOC` | `vistāra5:11100=ASSOC` |
| `11101` | `значення-у-списку?` | `значення-у-списку?` | `sambaddha?` | `member` | `MEMBER` | `vistāra5:11101=MEMBER` |
| `11110` | `спарувати` | `спарувати` | `yugma-bandha` | `pairlis` | `PAIRLIS` | `vistāra5:11110=PAIRLIS` |
| `11111` | `замінити` | `замінити` | `ādeśa` | `subst` | `SUBST` | `vistāra5:11111=SUBST` |

## saṃghaṭana6 (D6)

| bits | ук | укр | san | eng | LISP | SUM |
|---|---|---|---|---|---|---|
| `000000` | `довжина` | `довжина` | `pramāṇa` | `length` | `LENGTH` | `saṃghaṭana6:000000=LENGTH` |
| `000001` | `—` | `—` | `—` | `length-onto` | `LENGTH-ONTO` | `saṃghaṭana6:000001=LENGTH-ONTO` |
| `000010` | `найменше-у-списку` | `найменше-у-списку` | `—` | `min-list` | `MIN-LIST` | `saṃghaṭana6:000010=MIN-LIST` |
| `000011` | `найбільше-у-списку` | `найбільше-у-списку` | `—` | `max-list` | `MAX-LIST` | `saṃghaṭana6:000011=MAX-LIST` |
| `000100` | `елемент-списку-за-індексом` | `елемент-списку-за-індексом` | `kramāṅka` | `nth` | `NTH` | `saṃghaṭana6:000100=NTH` |
| `000101` | `відобразити-залишки` | `відобразити-залишки` | `—` | `maplist` | `MAPLIST` | `saṃghaṭana6:000101=MAPLIST` |
| `000110` | `—` | `—` | `—` | `macroexpand-1` | `MACROEXPAND-1` | `saṃghaṭana6:000110=MACROEXPAND-1` |
| `000111` | `—` | `—` | `—` | `macroexpand` | `MACROEXPAND` | `saṃghaṭana6:000111=MACROEXPAND` |
| `001000` | `нехай` | `нехай` | `—` | `let` | `LET` | `saṃghaṭana6:001000=LET` |
| `001001` | `нехай*` | `нехай-послідовно` | `—` | `let*` | `LET*` | `saṃghaṭana6:001001=LET*` |
| `001010` | `підставити-пари` | `підставити-пари` | `—` | `sublis` | `SUBLIS` | `saṃghaṭana6:001010=SUBLIS` |
| `001011` | `—` | `—` | `—` | `compose` | `COMPOSE` | `saṃghaṭana6:001011=COMPOSE` |
| `001100` | `—` | `—` | `—` | `rassoc` | `RASSOC` | `saṃghaṭana6:001100=RASSOC` |
| `001101` | `—` | `—` | `—` | `acons` | `ACONS` | `saṃghaṭana6:001101=ACONS` |
| `001110` | `—` | `—` | `—` | `add1` | `ADD1` | `saṃghaṭana6:001110=ADD1` |
| `001111` | `—` | `—` | `—` | `sub1` | `SUB1` | `saṃghaṭana6:001111=SUB1` |
| `010000` | `—` | `—` | `—` | `evenp` | `EVENP` | `saṃghaṭana6:010000=EVENP` |
| `010001` | `—` | `—` | `—` | `oddp` | `ODDP` | `saṃghaṭana6:010001=ODDP` |
| `010010` | `—` | `—` | `—` | `neg` | `NEG` | `saṃghaṭana6:010010=NEG` |
| `010011` | `модуль` | `модуль` | `rūpa` | `abs` | `ABS` | `saṃghaṭana6:010011=ABS` |
| `010100` | `остача` | `остача` | `avasiṣṭa` | `remainder` | `REMAINDER` | `saṃghaṭana6:010100=REMAINDER` |
| `010101` | `—` | `—` | `—` | `gcd` | `GCD` | `saṃghaṭana6:010101=GCD` |
| `010110` | `—` | `—` | `—` | `recip` | `RECIP` | `saṃghaṭana6:010110=RECIP` |
| `010111` | `—` | `—` | `—` | `expt` | `EXPT` | `saṃghaṭana6:010111=EXPT` |
| `011000` | `—` | `—` | `—` | `cdaaar` | `CDAAAR` | `saṃghaṭana6:011000=CDAAAR` |
| `011001` | `—` | `—` | `—` | `cdaadr` | `CDAADR` | `saṃghaṭana6:011001=CDAADR` |
| `011010` | `—` | `—` | `—` | `cdadar` | `CDADAR` | `saṃghaṭana6:011010=CDADAR` |
| `011011` | `—` | `—` | `—` | `cdaddr` | `CDADDR` | `saṃghaṭana6:011011=CDADDR` |
| `011100` | `—` | `—` | `—` | `cddaar` | `CDDAAR` | `saṃghaṭana6:011100=CDDAAR` |
| `011101` | `—` | `—` | `—` | `cddadr` | `CDDADR` | `saṃghaṭana6:011101=CDDADR` |
| `011110` | `—` | `—` | `—` | `cdddar` | `CDDDAR` | `saṃghaṭana6:011110=CDDDAR` |
| `011111` | `—` | `—` | `—` | `cddddr` | `CDDDDR` | `saṃghaṭana6:011111=CDDDDR` |
| `100000` | `—` | `—` | `—` | `caaaar` | `CAAAAR` | `saṃghaṭana6:100000=CAAAAR` |
| `100001` | `—` | `—` | `—` | `caaadr` | `CAAADR` | `saṃghaṭana6:100001=CAAADR` |
| `100010` | `—` | `—` | `—` | `caadar` | `CAADAR` | `saṃghaṭana6:100010=CAADAR` |
| `100011` | `—` | `—` | `—` | `caaddr` | `CAADDR` | `saṃghaṭana6:100011=CAADDR` |
| `100100` | `—` | `—` | `—` | `cadaar` | `CADAAR` | `saṃghaṭana6:100100=CADAAR` |
| `100101` | `—` | `—` | `—` | `cadadr` | `CADADR` | `saṃghaṭana6:100101=CADADR` |
| `100110` | `—` | `—` | `—` | `caddar` | `CADDAR` | `saṃghaṭana6:100110=CADDAR` |
| `100111` | `—` | `перше-після-трьох-решт` | `—` | `cadddr` | `CADDDR` | `saṃghaṭana6:100111=CADDDR` |
| `101000` | `відобразити` | `відобразити` | `āvartana` | `map` | `MAP` | `saṃghaṭana6:101000=MAP` |
| `101001` | `відсіяти` | `відсіяти` | `kalpana` | `filter` | `FILTER` | `saṃghaṭana6:101001=FILTER` |
| `101010` | `—` | `—` | `—` | `map-onto` | `MAP-ONTO` | `saṃghaṭana6:101010=MAP-ONTO` |
| `101011` | `—` | `—` | `—` | `filter-onto` | `FILTER-ONTO` | `saṃghaṭana6:101011=FILTER-ONTO` |
| `101100` | `—` | `—` | `—` | `curry` | `CURRY` | `saṃghaṭana6:101100=CURRY` |
| `101101` | `—` | `—` | `—` | `flip` | `FLIP` | `saṃghaṭana6:101101=FLIP` |
| `101110` | `згорнути` | `згорнути` | `saṅgraha` | `reduce` | `REDUCE` | `saṃghaṭana6:101110=REDUCE` |
| `101111` | `—` | `—` | `—` | `scan` | `SCAN` | `saṃghaṭana6:101111=SCAN` |
| `110000` | `—` | `—` | `—` | `take` | `TAKE` | `saṃghaṭana6:110000=TAKE` |
| `110001` | `—` | `—` | `—` | `drop` | `DROP` | `saṃghaṭana6:110001=DROP` |
| `110010` | `—` | `—` | `—` | `do` | `DO` | `saṃghaṭana6:110010=DO` |
| `110011` | `—` | `—` | `—` | `while` | `WHILE` | `saṃghaṭana6:110011=WHILE` |
| `110100` | `не-більше?` | `не-більше?` | `na-adhika?` | `leq` | `LEQ` | `saṃghaṭana6:110100=LEQ` |
| `110101` | `найменше` | `найменше` | `alpatara` | `min` | `MIN` | `saṃghaṭana6:110101=MIN` |
| `110110` | `не-менше?` | `не-менше?` | `na-hīna?` | `geq` | `GEQ` | `saṃghaṭana6:110110=GEQ` |
| `110111` | `найбільше` | `найбільше` | `brhattara` | `max` | `MAX` | `saṃghaṭana6:110111=MAX` |
| `111000` | `—` | `—` | `—` | `zip` | `ZIP` | `saṃghaṭana6:111000=ZIP` |
| `111001` | `—` | `—` | `—` | `unzip` | `UNZIP` | `saṃghaṭana6:111001=UNZIP` |
| `111010` | `—` | `—` | `—` | `intersection` | `INTERSECTION` | `saṃghaṭana6:111010=INTERSECTION` |
| `111011` | `—` | `—` | `—` | `union` | `UNION` | `saṃghaṭana6:111011=UNION` |
| `111100` | `—` | `—` | `—` | `any` | `ANY` | `saṃghaṭana6:111100=ANY` |
| `111101` | `—` | `—` | `—` | `all` | `ALL` | `saṃghaṭana6:111101=ALL` |
| `111110` | `—` | `—` | `—` | `integerp` | `INTEGERP` | `saṃghaṭana6:111110=INTEGERP` |
| `111111` | `—` | `—` | `—` | `rationalp` | `RATIONALP` | `saṃghaṭana6:111111=RATIONALP` |
