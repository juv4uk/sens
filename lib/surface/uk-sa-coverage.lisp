; ІСТОРИЧНИЙ АУДИТ — НЕ ДЖЕРЕЛО СЕМАНТИЧНИХ ПОВНОВАЖЕНЬ.
; Машинно-читана таблиця покриття англійської, української
; та санскритської поверхонь (EN ↔ UK ↔ SA).
; Історичні машинні ідентичності тут — лише дані обліку;
; вони не замінюють чинних доменних таблиць СЕНС.
;
; Кожний рядок зіставляє назви вже наявної публічної функції.
; Таблиця не визначає її семантики й не ратифікує нової координати.
;
; Стани (літерали поля status не перейменовуємо):
;   stable             — назву обрано, реалізовано й перевірено
;   candidate          — пропозиція, ще не ратифікована
;   missing            — чинного зіставлення поки немає
;   compatibility-only — історичне англійське ім'я без окремого перекладу
;
; Форма запису: (entry (category EN UK SA uk-status sa-status notes)).
; Системні ключі запису є протокольними даними.
;
; Історично Canon 0+7 та необхідні форми мали стан stable.
; Для відповідних рядків української поверхні стан перевіряв
; uk_surface_equivalence.rs за наявністю зв'язування в uk.lisp.
; Перша санскритська партія: основні форми, арифметика,
; порівняння, предикати та списки; решта термінів потребувала розгляду.
; Друга партія: введення-виведення, вектори, перетворення,
; час, сталі мапи, логічне виведення, уніфікація й епістеміка.
; Актуальну семантику та назви перевіряти за ратифікованими D1–D10.

(uk-sa-coverage
  (schema uk-sa-coverage/3)

  ;; ── Canon 0+7 ──────────────────────────────────────────────
  (entry (canon quote як-є svarūpa stable stable "AS 1.1.68 svam rūpam"))
  (entry (canon atom атом? aṇu stable stable "niravayava"))
  (entry (canon eq тотожне? abheda stable stable "TS §80"))
  (entry (canon cons сполучити saṃyuj stable stable "TS §27"))
  (entry (canon car перше ādi stable stable "VS 4.2.9"))
  (entry (canon cdr решта śeṣa stable stable "NS 1.1.5 śeṣavat"))
  (entry (canon cond за-умовою krama stable stable "Mīmāṃsā"))

  ;; ── Necessary forms ────────────────────────────────────────
  (entry (necessary lambda функція — stable missing "Макрос, що розгортається у форму lambda"))
  (entry (necessary define визначити — stable missing "Макрос, що розгортається у форму define"))
  (entry (language-macro defmacro визначити-макрос — stable missing "Те саме першокласне значення макроса; окремого механізму макросів немає"))
  (entry (compatibility def — — compatibility-only compatibility-only "Історичний псевдонім форми визначення"))

  ;; ── Arithmetic ─────────────────────────────────────────────
  (entry (arithmetic + додати yoga stable stable "Brahmagupta/Bhāskara: yoga = addition"))
  (entry (arithmetic - відняти viyoga stable stable "vi- + yoga = subtraction"))
  (entry (arithmetic * помножити guṇana stable stable "Стандартний математичний термін"))
  (entry (arithmetic / поділити haraṇa stable stable "haraṇa — операція ділення"))
  (entry (arithmetic abs модуль rūpa stable candidate "rūpa = form; candidate — polysemous"))
  (entry (arithmetic min найменше alpatara stable stable "alpa = small, -tara = comparative"))
  (entry (arithmetic max найбільше brhattara stable stable "bṛhat = great, -tara = comparative"))
  (entry (arithmetic mod остача avasiṣṭa stable stable "ava-śiṣ = remain; ≠ śeṣa (CDR)"))
  (entry (arithmetic quotient частка bhāga stable stable "bhāga = result of division"))
  (entry (arithmetic sqrt корінь mūla stable stable "Стандартний математичний термін"))
  (entry (arithmetic isqrt цілий-корінь sakalamūla stable stable "sakala = whole/integer"))
  (entry (arithmetic min-list найменше-у-списку — stable missing "Згортання списку операцією найменшого значення"))
  (entry (arithmetic max-list найбільше-у-списку — stable missing "Згортання списку операцією найбільшого значення"))
  (entry (arithmetic largest-chunk — — compatibility-only compatibility-only "Внутрішня допоміжна функція частки"))

  ;; ── Comparisons ────────────────────────────────────────────
  (entry (comparison < менше? hīna? stable stable "hīna = lower/lesser"))
  (entry (comparison > більше? adhika? stable stable "adhika = greater"))
  (entry (comparison = рівне? sama? stable stable "sama = equal in quantity; ≠ abheda (eq)"))
  (entry (comparison <= не-більше? na-adhika? stable candidate "Складна назва з na та adhika"))
  (entry (comparison >= не-менше? na-hīna? stable candidate "Складна назва з na та hīna"))
  (entry (comparison nondecreasing-from? — — compatibility-only compatibility-only "Внутрішня рекурсивна допоміжна функція порівняння <="))
  (entry (comparison nonincreasing-from? — — compatibility-only compatibility-only "Внутрішня рекурсивна допоміжна функція порівняння >="))

  ;; ── Predicates ─────────────────────────────────────────────
  (entry (predicate not хибне? na stable stable "Істина рівно тоді, коли аргумент хибний"))
  (entry (predicate equal? однакові? tulya? stable stable "tulya — структурна рівність"))
  (entry (predicate symbol? символ? nāman? stable stable "Pāṇini 1.1.62: pratyayaḥ sa nāma"))
  (entry (predicate string? текст? śabda? stable stable "śabda = word/sound/text"))
  (entry (predicate string<? текст-передує? śabda-hīna? stable candidate "compound"))
  (entry (predicate numeric-buffer? числовий-буфер? — stable missing "Тип буфера низького рівня"))

  ;; ── Lists ──────────────────────────────────────────────────
  (entry (список список список śreṇī stable stable "śreṇī — впорядкована послідовність"))
  (entry (список length довжина pramāṇa stable stable "pramāṇa = measure/quantity"))
  (entry (список append приєднати saṅkalana stable stable "saṅkalana = collection; ≠ saṃyuj"))
  (entry (список reverse зворот viloma stable stable "viloma — зворотний порядок"))
  (entry (список nth елемент-списку-за-індексом kramāṅka stable stable "kramāṅka — порядковий номер"))
  (entry (список member? значення-у-списку? sambaddha? stable candidate "sam-badh — поєднувати"))
  (entry (список assoc знайти-за-ключем saṃbandha stable stable "lookup an association by key"))
  (entry (список pair пара dvandva stable stable "Pāṇini 2.2.29-34: dvandva samāsa"))
  (entry (список second друге dvitīya stable stable "Порядковий номер; повертає елемент"))
  (entry (список third третє tṛtīya stable stable "ordinal"))
  (entry (список fourth четверте caturtha stable stable "ordinal"))
  (entry (список fifth п'яте pañcama stable stable "ordinal"))
  (entry (список caar — — compatibility-only compatibility-only "Композиція низького рівня над CAR/CDR"))
  (entry (список cadr — — compatibility-only compatibility-only "Натомість уживати українське ім'я друге"))
  (entry (список cddr — — compatibility-only compatibility-only "Композиція низького рівня"))
  (entry (список cadddr — — compatibility-only compatibility-only "Натомість уживати українське ім'я четверте"))

  ;; ── Higher-order ───────────────────────────────────────────
  (entry (higher-order map відобразити āvartana stable candidate "āvartana — повторне застосування; кандидат без прямого традиційного джерела"))
  (entry (higher-order filter відсіяти kalpana stable candidate "kalpana = selection (Mīmāṃsā); candidate"))
  (entry (higher-order reduce згорнути saṅgraha stable candidate "saṅgraha = comprehension; candidate"))

  ;; ── Strings ────────────────────────────────────────────────
  (entry (string string-append зчепити śabdasaṃyoga stable candidate "śabda + saṃyoga; ≠ saṃyuj"))
  (entry (string string-length довжина-тексту śabdapramāṇa stable candidate "śabda + pramāṇa"))
  (entry (string string-empty? текст-порожній? śūnya? stable stable "Предикат домену рядків"))
  (entry (string string-prefix? префікс-тексту? pūrva? stable candidate "Предикат домену рядків; не тотожний ādi (CAR)"))
  (entry (string string-contains? фрагмент-у-тексті? śabdasambaddha? stable candidate "Складне слово; можливе скорочення"))
  (entry (string string-first перший-символ-тексту prathamavarṇa stable candidate "varṇa = letter; ≠ ādi (CAR)"))
  (entry (string string-rest решта-символів-тексту śeṣavarṇa stable candidate "Суфікс varṇa відрізняє назву від канонічного śeṣa"))
  (entry (string string-slice відрізати cheda stable candidate "cheda = cut/slice"))
  (entry (string symbol->string символ-у-текст nāman-śabda stable candidate "conversion"))
  (entry (string string->symbol текст-у-символ śabda-nāman stable candidate "conversion"))
  (entry (string codepoint->string кодова-точка-у-текст varṇa-śabda stable candidate "conversion"))
  (entry (string string->codepoint текст-у-кодову-точку śabda-varṇa stable candidate "conversion"))
  (entry (string number->string число-у-текст saṅkhyā-śabda stable candidate "conversion"))
  (entry (string digit->string — — compatibility-only compatibility-only "Замінена внутрішня допоміжна функція перетворення"))

  ;; ── I/O ────────────────────────────────────────────────────
  (entry (io print друкувати mudraṇa stable candidate "mudraṇa = impression/printing"))
  (entry (io princ показати darśana stable candidate "darśana = showing/display"))
  (entry (io read прочитати pāṭhana stable candidate "pāṭhana = reading"))
  (entry (io read-all прочитати-усе pāṭhana-sarva stable candidate "pāṭhana + sarva — прочитати все"))
  (entry (io write-to-string значення-у-текст likhana stable candidate "likhana = writing"))
  (entry (io eval обчислити vicāraṇa stable candidate "vicāraṇa = deliberation/evaluation"))
  (entry (io env середовище āśraya stable candidate "āśraya = substrate/environment"))

  ;; ── Vectors ────────────────────────────────────────────────
  (entry (вектор вектор вектор samūha stable candidate "samūha = collection/aggregate"))
  (entry (вектор make-vector створити-вектор samūha-nirmāṇa stable candidate "samūha + nirmāṇa = creation"))
  (entry (вектор vector-length довжина-вектора samūha-pramāṇa stable candidate "samūha + pramāṇa = measure"))
  (entry (вектор vector-ref елемент-вектора samūha-āvartana stable candidate "samūha + āvartana = access"))
  (entry (вектор vector-set! встановити-елемент-вектора! — stable missing "Зміна елемента; санскритської назви ще немає"))

  ;; ── Buffers ───────────────────────────────────────────────
  (entry (buffer i32-buffer — — compatibility-only compatibility-only "Низькорівневий інтерфейс FFI"))
  (entry (buffer f32-buffer — — compatibility-only compatibility-only "Низькорівневий інтерфейс FFI"))
  (entry (buffer numeric-buffer-type — — compatibility-only compatibility-only "Низькорівневий механізм"))
  (entry (buffer numeric-buffer-length — — compatibility-only compatibility-only "Низькорівневий механізм"))
  (entry (buffer numeric-buffer-ref — — compatibility-only compatibility-only "Низькорівневий механізм"))
  (entry (buffer numeric-buffer-map — — compatibility-only compatibility-only "Низькорівневий механізм"))

  ;; ── Time ──────────────────────────────────────────────────
  (entry (time mono-ns монотонний-нс kāla-mono stable candidate "kāla — час; монотонні наносекунди"))
  (entry (time unix-time-now поточний-юнікс-час kāla-unix stable candidate "Поточний час Unix; українське написання фонетичне"))
  (entry (time ntp-query-raw — — compatibility-only compatibility-only "Низькорівневий запит NTP"))
  (entry (time timezone-declarations-raw — — compatibility-only compatibility-only "Низькорівневий механізм"))

  ;; ── Time library (Batch 2) ─────────────────────────────────
  (entry (time utc-now поточний-всч kāla-adya stable candidate "ВСЧ = всесвітній скоординований час"))
  (entry (time utc-from-unix всч-із-юнікс — stable missing "Перетворення позначки часу Unix на ВСЧ"))
  (entry (time unix-time-observation->utc юнікс-спостереження-у-всч — stable missing "Перетворення спостереження часу на ВСЧ"))
  (entry (time milliseconds-from-nanoseconds мілісекунди-із-наносекунд kāla-millisecondāni stable candidate "kāla-millisecondāni = time-milliseconds"))
  (entry (time mono-ms монотонний-мс kāla-mono-ms stable candidate "Монотонні мілісекунди"))
  (entry (time timezone-name назва-часового-поясу deśa-kāla-nāma stable candidate "deśa-kāla = timezone"))
  (entry (time timezone-detect визначити-часовий-пояс deśa-kāla-jñāna stable candidate "deśa-kāla-jñāna — визначення часового поясу"))
  (entry (time timezone-offset-seconds зміщення-часового-поясу-в-секундах deśa-kāla-śeṣa stable candidate "deśa-kāla-śeṣa = timezone offset"))
  (entry (time deadline-reached? дедлайн-досягнуто? avadhi-gatā? stable candidate "avadhi = deadline; gatā = reached"))
  (entry (time deadline-reached-at? дедлайн-досягнуто-на-момент? avadhi-gatā-kadā? stable candidate "kadā = when"))
  (entry (time elapsed-ns минуло-нс atīta-ns stable candidate "atīta = elapsed/past"))
  (entry (time deadline-from дедлайн-від avadhi-nirmāṇa stable candidate "avadhi-nirmāṇa = deadline creation"))
  (entry (time deadline-after-ns дедлайн-через-нс avadhi-anantara-ns stable candidate "avadhi-anantara = deadline after"))
  (entry (time internet-time-sync запитати-інтернет-час — stable missing "Синхронізація часу через інтернет"))

  ;; ── Persistent map (Batch 2) ───────────────────────────────
  (entry (persistent-map map-empty порожня-карта kośa-śūnya stable candidate "kośa = repository/map; śūnya = empty"))
  (entry (persistent-map map-get отримати-з-карти kośa-grahaṇa stable candidate "grahaṇa = taking/getting"))
  (entry (persistent-map map-insert вставити-в-карту kośa-niveśana stable candidate "niveśana = placing in"))
  (entry (persistent-map map-contains? ключ-у-карті? kośa-sambaddha? stable candidate "sambaddha = contained"))
  (entry (persistent-map map->list карта-у-список kośa-śreṇī stable candidate "śreṇī = sequence/list"))

  ;; ── Persistent vector (Batch 2) ─────────────────────────────
  (entry (persistent-vector vec-empty порожній-вектор samūha-śūnya stable candidate "samūha = aggregate; śūnya = empty"))
  (entry (persistent-vector vec-conj додати-до-вектора samūha-yukti stable candidate "yukti = joining"))
  (entry (persistent-vector vec-count розмір-вектора samūha-gaṇana stable candidate "gaṇana = counting"))
  (entry (persistent-vector vec-nth елемент-вектора-за-індексом samūha-kramāṅka stable candidate "kramāṅka = ordinal"))
  (entry (persistent-vector vec->list вектор-у-список samūha-śreṇī stable candidate "śreṇī = sequence/list"))
  (entry (persistent-vector vec-from-list вектор-із-списку śreṇī-samūha stable candidate "śreṇī-samūha = list to aggregate"))

  ;; ── Knowledge / Reasoning (Batch 2) ─────────────────────────
  (entry (knowledge is-fact? факт? jñāna-satya? stable candidate "jñāna = knowledge; satya = truth"))
  (entry (knowledge describe описати varṇana stable candidate "varṇana = description"))
  (entry (knowledge collect-facts-about зібрати-факти-про jñāna-saṅgraha stable candidate "saṅgraha = collection"))
  (entry (knowledge contains-atom? атом-у-списку? aṇu-sambaddha? stable candidate "aṇu = atom; sambaddha = contained"))
  (entry (knowledge forward-in пряме-виведення abhimukha-anumāna stable candidate "abhimukha = forward; anumāna = inference"))
  (entry (knowledge reason-in логічний-висновок anumāna stable candidate "anumāna = inference"))
  (entry (knowledge check-conflict конфлікт? virodha-parīkṣā stable candidate "virodha = conflict; parīkṣā = check"))
  (entry (knowledge module-known? модуль-відомий? — stable missing "Санскритської назви ще немає"))
  (entry (knowledge module-clauses-now поточні-клаузи-модуля — stable missing "Санскритської назви ще немає"))
  (entry (reasoning prove-goal довести-мету siddhi-sādhana stable candidate "siddhi = proof; sādhana = accomplishment"))
  (entry (reasoning prove-goals довести-мети siddhi-sādhana-sarva stable candidate "sarva = all"))
  (entry (reasoning explain-proof пояснити-доведення siddhi-vyākhyā stable candidate "vyākhyā = explanation"))
  (entry (reasoning source-of джерело-доведення siddhi-mūla stable candidate "mūla = root/source"))
  (entry (reasoning provenance походження utpatti stable candidate "utpatti = origin"))
  (entry (reasoning reason міркування tarka stable candidate "tarka = reasoning/logic"))
  (entry (reasoning reason-explain пояснити-міркування tarka-vyākhyā stable candidate "tarka + vyākhyā"))

  ;; ── Unification (Batch 2) ──────────────────────────────────
  (entry (unification unify уніфікувати ekīkaraṇa stable candidate "ekīkaraṇa = unification"))
  (entry (unification logic-var логічна-змінна tarka-cihna stable candidate "tarka = logic; cihna = mark"))
  (entry (unification var? змінна? cihna? stable candidate "cihna = mark/symbol"))
  (entry (unification apply-subst підставити pratyāroha stable candidate "pratyāroha = substitution"))
  (entry (unification walk розіменувати vicāraṇa-gamana stable candidate "vicāraṇa-gamana = investigation-path"))
  (entry (unification occurs-check змінна-зустрічається? parivṛtti-parīkṣā stable candidate "parivṛtti = occurrence; parīkṣā = check"))

  ;; ── Epistemic (Batch 2) ─────────────────────────────────────
  (entry (epistemic claim? твердження? pratyaya? stable candidate "pratyaya = claim/conviction"))
  (entry (epistemic claim-statement зміст-твердження pratyaya-vākya stable candidate "vākya = statement"))
  (entry (epistemic claim-review стан-розгляду-твердження pratyaya-parīkṣā stable candidate "parīkṣā = review/check"))
  (entry (epistemic evidence? доказ? pramāṇa? stable candidate "pramāṇa = evidence/proof"))
  (entry (epistemic evidence-method метод-доказу pramāṇa-vidhi stable candidate "vidhi = method"))
  (entry (epistemic evidence-outcome результат-доказу pramāṇa-phala stable candidate "phala = result"))
  (entry (epistemic observation? спостереження? pratyakṣa? stable candidate "pratyakṣa = direct perception"))
  (entry (epistemic observation-statement зміст-спостереження pratyakṣa-vākya stable candidate "vākya = statement"))
  (entry (epistemic intent? намір? saṅkalpa? stable candidate "saṅkalpa = intention"))
  (entry (epistemic intent-goal мета-наміру saṅkalpa-lakṣya stable candidate "lakṣya = goal/target"))
  (entry (epistemic supporting-evidence підтримувальний-доказ sahāya-pramāṇa stable candidate "sahāya = supporting"))

  ;; ── Other ─────────────────────────────────────────────────
  (entry (other identity без-змін svabhāva stable candidate "Повертає аргумент без зміни"))
  (entry (other gensym генерувати-символ nāman-nirmāṇa stable candidate "nāman-nirmāṇa = name generation"))
  (entry (other and та — stable missing "Логічна кон'юнкція"))
  (entry (other or або — stable missing "Логічна диз'юнкція"))
  (entry (other let нехай — stable missing "Форма локального зв'язування"))
  (entry (other let* нехай* — stable missing "Послідовне локальне зв'язування"))
  (entry (other -> -> — compatibility-only compatibility-only "Макрос послідовного передавання значення"))
  (entry (other ->> ->> — compatibility-only compatibility-only "Макрос послідовного передавання останнім аргументом"))
  (entry (other json-parse — — compatibility-only compatibility-only "Назва зовнішнього формату"))
  (entry (other sha256-hex — — compatibility-only compatibility-only "Назва алгоритму"))

  ;; ── Summary statistics ─────────────────────────────────────
  (summary
    (total-eligible 161)
    (stable-uk 140)
    (candidate-uk 0)
    (missing-uk 0)
    (compatibility-uk 21)
    (stable-sa 36)
    (candidate-sa 88)
    (missing-sa 16)
    (compatibility-sa 21)
    (usc-uk-percent "100.0%")
    (usc-sa-percent "77.0%")
    (notes "Selected Ukrainian surface complete: 140 stable of 140 translation-eligible names; 21 compatibility-only names are explicitly outside the translation denominator. SA: 124 surface names (36 stable + 88 candidate). Remaining SA gaps: defmacro, lambda, define, min-list, max-list, numeric-buffer?, vector-set!, utc-from-unix, unix-time-observation->utc, internet-time-sync, module-known?, module-clauses-now, and, or, let, let*.")))

