; research batch — D8 DIV / LOGNOT (d8:10000010 DIV, d8:10000100 LOGNOT)
; Applied via scripts/apply-d8-div-lognot-batch.py → lib/core4.lisp
; Surfaces: укр only (ділити, логічне-не)

(визначити (ділити a b)
  "D8:10000010 DIV — integer division"
  (якщо (дорівнює b 0)
    (помилка "ділення-на-нуль")
    (частка a b)))

(визначити (логічне-не x)
  "D8:10000100 LOGNOT — bitwise not"
  (логне x))
