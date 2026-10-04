(
  ; Exact-domain human-surface projection DATA.
  ; Semantic authority remains the ratified exact-domain maps/laws; this file is projection-only.
  ; Human spellings live here as data only; they never create occupancy or semantic identity.
  ;
  ; Row shape:
  ;   ("width-bits" "identity-bits" (namespace surface) ...)
  ;
  ; No legacy Function8/Sens8 byte appears here.

  ; D3 bīja3 — surfaced residents.
  ("11" "001" (en quote) (ук як-є) (укр як-є) (sa svarūpa) (sym "'"))
  ("11" "010" (en atom?) (ук атом?) (укр атом?) (sa aṇu) (sym .?))
  ("11" "011" (en cond) (ук за-умовою) (укр за-умовою) (sa anukrama) (sym ?:))
  ("11" "100" (en cons) (ук сполучити) (укр сполучити) (sa saṃyuj) (sym ()))
  ("11" "101" (en car) (ук перше) (укр перше) (sa ādi) (sym :п))
  ("11" "110" (en cdr) (ук решта) (укр решта) (sa śeṣa) (sym :р))
  ("11" "111" (en eq?) (ук тотожне?) (укр тотожне?) (sa abheda) (sym =?))

  ; D4 forms whose exact-domain routing is already live.
  ("100" "0010" (en lambda) (ук функція) (укр функція) (sa ()) (sym ()))
  ("100" "0011" (en define) (ук визначити) (укр визначити) (sa ()) (sym ()))
  ("100" "0011" (en def) (ук ()) (укр ()) (sa ()) (sym ()))

  ; D4 selector descendants. Runtime admission is completed by #2928.
  ("100" "1010" (en caar) (ук ()) (укр перше-від-першого) (sa ()) (sym ()))
  ("100" "1011" (en cadr) (ук ()) (укр перше-від-решти) (sa ()) (sym ()))
  ("100" "1101" (en cddr) (ук ()) (укр решта-від-решти) (sa ()) (sym ()))

  ; D5 Lisp-owned residents whose closures are already bound into exact D5 slots.
  ("101" "10000" (en append) (ук приєднати) (укр приєднати) (sa saṅkalana) (sym ()))
  ("101" "10001" (en reverse) (ук зворот) (укр зворот) (sa viloma) (sym ()))
  ("101" "11100" (en assoc) (ук знайти-за-ключем) (укр знайти-за-ключем) (sa saṃbandha) (sym ()))
  ("101" "11101" (en member?) (ук значення-у-списку?) (укр значення-у-списку?) (sa sambaddha?) (sym ()))
  ("101" "11111" (en subst) (ук замінити) (укр замінити) (sa ()) (sym ()))

  ; D5 owner-map residents with live exact-domain mechanisms.
  ("101" "01010" (en plus) (ук додати) (укр додати) (sa yoga) (sym +))
  ("101" "01011" (en difference) (ук відняти) (укр відняти) (sa viyoga) (sym -))
  ("101" "01110" (en lessp?) (ук менше?) (укр менше?) (sa hīna?) (sym <))
  ("101" "01111" (en greaterp?) (ук більше?) (укр більше?) (sa adhika?) (sym >))
  ("101" "10010" (en times) (ук помножити) (укр помножити) (sa guṇana) (sym *))
  ("101" "10011" (en divide) (ук поділити) (укр поділити) (sa haraṇa) (sym /))
)
