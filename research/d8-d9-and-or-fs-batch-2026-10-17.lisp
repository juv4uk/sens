; D8 AND/OR/DIVIDE uk + D9 FS/map-fact list projections
; Pure aliases to existing Core4 mechanisms.

; D8:11110101 AND / D8:11111100 OR
(0011 та and)
(0011 або or)

; D8:11110110 DIVIDE
(0011 поділити quotient)
(0011 divide поділити)

; D8:00100100 VALUES-LIST (if not yet applied)
(0011 значення-списком
  (0010 (xs) xs))
(0011 values-list значення-списком)

; D9 FS as empty map / contains / list identity
(0011 фс-порожній мапа-порожній)
(0011 fs-empty фс-порожній)

(0011 фс-містить? мапа-містить?)
(0011 fs-contains? фс-містить?)

(0011 фс-список
  (0010 (fs) fs))
(0011 fs-list фс-список)

(0011 фс-зв'язки-з-список
  (0010 (lst) lst))
(0011 fs-bindings-from-list фс-зв'язки-з-список)

; D9:010011001 MAP-FACT-OF → map-get
(0011 мапа-факт-від мапа-отримати)
(0011 map-fact-of мапа-факт-від)
