(
  ; Exact-domain surface projection.
  ; Authority: domain + exact bits are already ratified elsewhere.
  ; This file admits spellings only; it never creates occupancy.
  ;
  ; Row shape:
  ;   (width "bits" (namespace surface) ...)
  ;
  ; No legacy Function8/Sens8 byte appears here.

  ; D3 bīja3 — surfaced residents.
  (3 "001" (en quote) (ук як-є) (укр як-є) (sa svarūpa) (sym "'"))
  (3 "010" (en atom?) (ук атом?) (укр атом?) (sa aṇu) (sym .?))
  (3 "011" (en cond) (ук за-умовою) (укр за-умовою) (sa anukrama) (sym ?:))
  (3 "100" (en cons) (ук сполучити) (укр сполучити) (sa saṃyuj) (sym ()))
  (3 "101" (en car) (ук перше) (укр перше) (sa ādi) (sym :п))
  (3 "110" (en cdr) (ук решта) (укр решта) (sa śeṣa) (sym :р))
  (3 "111" (en eq?) (ук тотожне?) (укр тотожне?) (sa abheda) (sym =?))

  ; D4 forms whose exact-domain routing is already live.
  (4 "0010" (en lambda) (ук функція) (укр функція) (sa ()) (sym ()))
  (4 "0011" (en define) (ук визначити) (укр визначити) (sa ()) (sym ()))
  (4 "0011" (en def) (ук ()) (укр ()) (sa ()) (sym ()))

  ; D4 selector descendants. Runtime admission is completed by #2928.
  (4 "1010" (en caar) (ук ()) (укр перше-від-першого) (sa ()) (sym ()))
  (4 "1011" (en cadr) (ук ()) (укр перше-від-решти) (sa ()) (sym ()))
  (4 "1101" (en cddr) (ук ()) (укр решта-від-решти) (sa ()) (sym ()))
)
