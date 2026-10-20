(sanskrit-cyrillic-keyboard
  (note "Gesture layer specification for Sanskrit Cyrillic input. Base: standard Ukrainian layout. Dead-key layer on Compose/AltGr. Maps gestures → SOUND_ID → VedaBase-UA surface.")
  (provenance
    (surface "VedaBase UA corpus")
    (sound-id-registry "knowledge/sanskrit-cyrillic-phoneme-map.lisp")
    (audit "knowledge/sanskrit-cyrillic-audit.lisp"))

  ;; ====================================================================
  ;; БАЗОВА РОЗКЛАДКА
  ;; ====================================================================
  (base-layout
    (id "ua")
    (name "Standard Ukrainian")
    (variant "standard")
    (note "Untouched. Sanskrit layer is an additive dead-key/Compose layer."))

  ;; ====================================================================
  ;; ВИЗНАЧЕННЯ МЕРТВИХ КЛАВІШ (фонологічні оператори)
  ;; ====================================================================
  (dead-key
    (id "retro")
    (name "RETRO")
    (description "Retroflex articulation: dot below")
    (keysym "dead_belowdot")
    (combinations
      (combo (base "т") (result "т̣") (sound-id SA_TTA))
      (combo (base "д") (result "д̣") (sound-id SA_DDA))
      (combo (base "н") (result "н̣") (sound-id SA_NNA))
      (combo (base "ш") (result "ш̣") (sound-id SA_SSA))
      (combo (base "р") (result "р̣") (sound-id SA_VOCALIC_R))
      (combo (base "с") (result "с̣") (sound-id UA_S_RETRO))))

  (dead-key
    (id "palatal")
    (name "PAL")
    (description "Palatal articulation: acute accent")
    (keysym "dead_acute")
    (combinations
      (combo (base "ш") (result "ш́") (sound-id SA_SHA))
      (combo (base "н") (result "н̃") (sound-id SA_NYA))
      (combo (base "с") (result "с́") (sound-id UA_S_PAL))
      (combo (base "з") (result "з́") (sound-id UA_Z_PAL))))

  (dead-key
    (id "velar-nasal")
    (name "VEL")
    (description "Velar nasal: dot above on base nasal")
    (keysym "dead_abovedot")
    (combinations
      (combo (base "н") (result "н̇") (sound-id SA_NGA))
      (combo (base "м") (result "м̇") (sound-id SA_ANUSVARA))))

  (dead-key
    (id "long")
    (name "LONG")
    (description "Vowel lengthening: macron")
    (keysym "dead_macron")
    (combinations
      (combo (base "а") (result "а̄") (sound-id SA_A_LONG))
      (combo (base "и") (result "ӣ") (sound-id SA_I_LONG))
      (combo (base "у") (result "ӯ") (sound-id SA_U_LONG))
      (combo (base "е") (result "е̄") (sound-id SA_E_LONG))
      (combo (base "о") (result "о̄") (sound-id SA_O_LONG))))

  (dead-key
    (id "palatal-nasal")
    (name "PAL-NASAL")
    (description "Palatal nasal: tilde on н")
    (keysym "dead_tilde")
    (combinations
      (combo (base "н") (result "н̃") (sound-id SA_NYA))))

  (dead-key
    (id "visarga")
    (name "VISARGA")
    (description "Visarga: dot below on х")
    (keysym "dead_belowdot")
    (combinations
      (combo (base "х") (result "х̣") (sound-id SA_VISARGA))))

  (dead-key
    (id "vocalic")
    (name "VOCALIC")
    (description "Vocalic r/l: dot below on р/л")
    (keysym "dead_belowdot")
    (combinations
      (combo (base "р") (result "р̣") (sound-id SA_VOCALIC_R))
      (combo (base "л") (result "л̣") (sound-id SA_VOCALIC_L))))

  ;; ====================================================================
  ;; ПРИДИХОВА СЕРІЯ — диграфи, породжені мертвою клавішею ASP
  ;; ====================================================================
  (dead-key
    (id "asp")
    (name "ASP")
    (description "Aspiration: generates digraph per VedaBase convention")
    (keysym "dead_breve")  ;; або власне відображення; XKB використовує level3 для диграфів
    (note "XKB implementation: ASP + base = digraph via compose sequences")
    (combinations
      (combo (base "к") (result "кг") (sound-id SA_KHA))
      (combo (base "г") (result "ґг") (sound-id SA_GHA))
      (combo (base "д") (result "дг") (sound-id SA_DHA))
      (combo (base "б") (result "бг") (sound-id SA_BHA))
      (combo (base "п") (result "пг") (sound-id SA_PHA))
      (combo (base "ґ") (result "ґг") (sound-id SA_GHA))))

  ;; ====================================================================
  ;; ПОСЛІДОВНОСТІ COMPOSE (мульти-клавіша для кон'юнктів і складних)
  ;; ====================================================================
  (compose-sequences
    (note "Multi-key (Compose key) for conjuncts and complex forms")
    (sequence (keys "dead_retro" "т" "dead_retro") (result "т̣т̣") (sound-id SA_TTA_CONJ))
    (sequence (keys "d" "h") (result "дг") (sound-id SA_DHA))  ;; for digraph input without dead key
    (sequence (keys "k" "h") (result "кг") (sound-id SA_KHA))
    (sequence (keys "g" "h") (result "ґг") (sound-id SA_GHA))
    (sequence (keys "d" "g") (result "дг") (sound-id SA_DHA))
    (sequence (keys "b" "h") (result "бг") (sound-id SA_BHA))
    (sequence (keys "j" "n") (result "джн̃") (sound-id SA_JNYA))
    (sequence (keys "s" "t" "dead_retro") (result "шт̣") (sound-id SA_TTA_CONJ)))

  ;; ====================================================================
  ;; ТАБЛИЦЯ ВІДОБРАЖЕННЯ: ЖЕСТ → SOUND_ID → ПОВЕРХНЯ VedaBase-UA
  ;; ====================================================================
  (gesture-map
    ;; Голосні
    (mapping (gesture "а") (sound-id SA_A) (surface "а"))
    (mapping (gesture "LONG+а") (sound-id SA_A_LONG) (surface "а̄"))
    (mapping (gesture "и") (sound-id SA_I) (surface "и"))
    (mapping (gesture "LONG+и") (sound-id SA_I_LONG) (surface "ı̄"))
    (mapping (gesture "у") (sound-id SA_U) (surface "у"))
    (mapping (gesture "LONG+у") (sound-id SA_U_LONG) (surface "ӯ"))
    (mapping (gesture "е") (sound-id SA_E) (surface "е"))
    (mapping (gesture "о") (sound-id SA_O_LONG) (surface "о"))

    ;; Складові
    (mapping (gesture "VOCALIC+р") (sound-id SA_VOCALIC_R) (surface "р̣"))
    (mapping (gesture "LONG+VOCALIC+р") (sound-id SA_VOCALIC_R_LONG) (surface "р̣̄"))
    (mapping (gesture "VOCALIC+л") (sound-id SA_VOCALIC_L) (surface "л̣"))
    (mapping (gesture "LONG+VOCALIC+л") (sound-id SA_VOCALIC_L_LONG) (surface "л̣̄"))

    ;; Приголосні — велярні
    (mapping (gesture "к") (sound-id SA_KA) (surface "к"))
    (mapping (gesture "ASP+к") (sound-id SA_KHA) (surface "кг"))
    (mapping (gesture "ґ") (sound-id SA_GA) (surface "ґ"))
    (mapping (gesture "ASP+ґ") (sound-id SA_GHA) (surface "ґг"))
    (mapping (gesture "VEL+н") (sound-id SA_NGA) (surface "н̇"))

    ;; Палатальні
    (mapping (gesture "ч") (sound-id SA_CA) (surface "ч"))
    (mapping (gesture "ASP+ч") (sound-id SA_CHA) (surface "чг"))
    (mapping (gesture "дж") (sound-id SA_JA) (surface "дж"))
    (mapping (gesture "ASP+дж") (sound-id SA_JHA) (surface "джг"))
    (mapping (gesture "PAL-NASAL+н") (sound-id SA_NYA) (surface "н̃"))

    ;; Ретрофлексні
    (mapping (gesture "RETRO+т") (sound-id SA_TTA) (surface "т̣"))
    (mapping (gesture "RETRO+д") (sound-id SA_DDA) (surface "д̣"))
    (mapping (gesture "RETRO+н") (sound-id SA_NNA) (surface "н̣"))
    (mapping (gesture "RETRO+ш") (sound-id SA_SSA) (surface "ш̣"))
    (mapping (gesture "RETRO+р") (sound-id SA_VOCALIC_R) (surface "р̣"))

    ;; Зубні
    (mapping (gesture "т") (sound-id SA_TA) (surface "т"))
    (mapping (gesture "ASP+т") (sound-id SA_THA) (surface "тг"))
    (mapping (gesture "д") (sound-id SA_DA) (surface "д"))
    (mapping (gesture "ASP+д") (sound-id SA_DHA) (surface "дг"))
    (mapping (gesture "н") (sound-id SA_NA) (surface "н"))

    ;; Губні
    (mapping (gesture "п") (sound-id SA_PA) (surface "п"))
    (mapping (gesture "ASP+п") (sound-id SA_PHA) (surface "пг"))
    (mapping (gesture "б") (sound-id SA_BA) (surface "б"))
    (mapping (gesture "ASP+б") (sound-id SA_BHA) (surface "бг"))
    (mapping (gesture "м") (sound-id SA_MA) (surface "м"))

    ;; Напівголосні / плавні / фрикативні
    (mapping (gesture "й") (sound-id SA_YA) (surface "й"))
    (mapping (gesture "р") (sound-id SA_RA) (surface "р"))
    (mapping (gesture "л") (sound-id SA_LA) (surface "л"))
    (mapping (gesture "в") (sound-id SA_VA) (surface "в"))
    (mapping (gesture "ш") (sound-id SA_SSA) (surface "ш̣"))
    (mapping (gesture "PAL+ш") (sound-id SA_SHA) (surface "ш́"))
    (mapping (gesture "с") (sound-id SA_SA) (surface "с"))
    (mapping (gesture "PAL+с") (sound-id SA_SA_PAL) (surface "с́"))
    (mapping (gesture "г") (sound-id SA_HA) (surface "г"))

    ;; Особливі
    (mapping (gesture "VEL+м") (sound-id SA_ANUSVARA) (surface "м̇"))
    (mapping (gesture "VISARGA+х") (sound-id SA_VISARGA) (surface "х̣"))
    (mapping (gesture "PAL+ш") (sound-id SA_SHA) (surface "ш́"))
    (mapping (gesture "PAL-NASAL+н") (sound-id SA_NYA) (surface "н̃"))

    ;; Кон'юнкти
    (mapping (gesture "джн̃") (sound-id SA_JNYA) (surface "джн̃"))
    (mapping (gesture "шт̣") (sound-id SA_TTA_CONJ) (surface "шт̣"))

    ;; Особливі одиниці
    (mapping (gesture "VISARGA+х") (sound-id SA_VISARGA) (surface "х̣"))
    (mapping (gesture "VEL+м") (sound-id SA_ANUSVARA) (surface "м̇"))
    (mapping (gesture "CANDRABINDU") (sound-id SA_CHANDRA_BINDU) (surface "м̐"))
    (mapping (gesture "VOCALIC+р") (sound-id SA_VOCALIC_R) (surface "р̣"))
    (mapping (gesture "VOCALIC+л") (sound-id SA_VOCALIC_L) (surface "л̣")))

  ;; ====================================================================
  ;; ПІДКАЗКИ ЩОДО РЕАЛІЗАЦІЇ XKB
  ;; ====================================================================
  (xkb-hints
    (dead-keys
      (retro "key <AB02> { [ dead_belowdot ] };")  ;; приклад позиції клавіші
      (palatal "key <AC01> { [ dead_acute ] };")
      (long "key <AD03> { [ dead_macron ] };")
      (velar-nasal "key <AC02> { [ dead_abovedot ] };")
      (palatal-nasal "key <AD04> { [ dead_tilde ] };")
      (visarga "key <AB05> { [ dead_belowdot ] };")
      (vocalic "key <AB03> { [ dead_belowdot ] };")
      (asp "key <AD01> { [ dead_breve ] };"))
    (compose-key "Multi_key")
    (level3-switch "AltGr")
    (note "Actual key positions to be tuned for ergonomics; mappings above are logical"))

  ;; ====================================================================
  ;; ІНТЕРФЕЙС РЕНДЕРЕРА
  ;; ====================================================================
  (renderer-interface
    (note "SOUND_ID → surface mapping is handled by renderer, not keyboard")
    (renderers
      (veda-base-ua
        (note "Uses VedaBase-UA diacritics as defined in audit"))
      (iast
        (note "Maps SOUND_ID → Unicode IAST"))
      (devanagari
        (note "Maps SOUND_ID → Devanāgarī"))
      (upc8
        (note "Maps SOUND_ID → UPC-8 byte code"))
      (slp1
        (note "Maps SOUND_ID → SLP1"))))
)
