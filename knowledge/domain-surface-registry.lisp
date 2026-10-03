(
  ; Exact-domain human-surface projection DATA.
  ; Semantic authority remains the ratified exact-domain maps/laws; this file is projection-only.
  ; Human spellings live here as data only; they never create occupancy or semantic identity.
  ;
  ; Row shape:
  ;   (width "bits" (namespace surface) ...)
  ;
  ; No legacy Function8/Sens8 byte appears here.

  ; D3 bīja3 — surfaced residents.
  (#b11 "001" (en quote) (ук як-є) (укр як-є) (sa svarūpa) (sym "'"))
  (#b11 "010" (en atom?) (ук атом?) (укр атом?) (sa aṇu) (sym .?))
  (#b11 "011" (en cond) (ук за-умовою) (укр за-умовою) (sa anukrama) (sym ?:))
  (#b11 "100" (en cons) (ук сполучити) (укр сполучити) (sa saṃyuj) (sym ()))
  (#b11 "101" (en car) (ук перше) (укр перше) (sa ādi) (sym :п))
  (#b11 "110" (en cdr) (ук решта) (укр решта) (sa śeṣa) (sym :р))
  (#b11 "111" (en eq?) (ук тотожне?) (укр тотожне?) (sa abheda) (sym =?))

  ; D4 forms whose exact-domain routing is already live.
  (#b100 "0010" (en lambda) (ук функція) (укр функція) (sa ()) (sym ()))
  (#b100 "0011" (en define) (ук визначити) (укр визначити) (sa ()) (sym ()))
  (#b100 "0011" (en def) (ук ()) (укр ()) (sa ()) (sym ()))

  ; D4 selector descendants. Runtime admission is completed by #2928.
  (#b100 "1010" (en caar) (ук ()) (укр перше-від-першого) (sa ()) (sym ()))
  (#b100 "1011" (en cadr) (ук ()) (укр перше-від-решти) (sa ()) (sym ()))
  (#b100 "1101" (en cddr) (ук ()) (укр решта-від-решти) (sa ()) (sym ()))
)
