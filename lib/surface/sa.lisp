; Санскритська проєкція канонічних примітивів і похідної лексики ядра.
; संस्कृत-पृष्ठम् — санскритська мовна проєкція.
;
; Canon 0+7 names are NOT defined here. The immutable Canon resolver owns the
; ratified Sanskrit spellings directly, before ordinary lexical lookup.
; Everything below Canon remains language-owned aliases over the same semantic
; environment, except identities migrated under ADR-007: those peer spellings
; are installed directly by the runtime and are not defined here.
;
; Принцип: одна семантична реалізація, кілька людських проєкцій.
;
; Status legend:
;   stable    — ratified against primary sources (Canon 0+7 calibration doc)
;   candidate — proposed in Batch 1 research, pending ratification
;
; Порядок завантаження повного профілю: macro.lisp → core.lisp → unify.lisp → reason.lisp →
; forward.lisp → knowledge.lisp → persistent-map.lisp → persistent-vector.lisp →
; time.lisp → epistemic.lisp → sa.lisp (цей файл).

;; ═══════════════════════════════════════════════════════════════
;; Канон 0+7 — незмінний розв'язувач (стан: stable)
;; ═══════════════════════════════════════════════════════════════

; svarūpa, aṇu, abheda, saṃyuj, ādi, śeṣa, anukrama
; are reserved Canon spellings and are intentionally not ordinary bindings.

;; ═══════════════════════════════════════════════════════════════
;; Добірка 1 — арифметика (стан: candidate)
;; ═══════════════════════════════════════════════════════════════

; ADR-007/008 / 0104, 1001–1003: yoga, viyoga, guṇana and haraṇa
; are ratified stable peers installed directly by the runtime together with
; Ukrainian and symbolic spellings. None is defined through another surface.
; rūpa = absolute value (candidate — polysemous)
(визначити rūpa модуль)
; alpatara = least (alpa + -tara comparative)
(визначити alpatara найменше)
; brhattara = greatest (bṛhat + -tara comparative)
(визначити brhattara найбільше)
; avasiṣṭa = remainder (ava-śiṣ; ≠ śeṣa CDR)
(визначити avasiṣṭa модульна-остача)
; bhāga = quotient (result of division)
(визначити bhāga частка)
; mūla = square root
(визначити mūla корінь)
; sakalamūla = integer square root
(визначити sakalamūla цілий-корінь)

;; ═══════════════════════════════════════════════════════════════
;; Добірка 1 — порівняння (стан: candidate)
;; ═══════════════════════════════════════════════════════════════

; ADR-007/008 / 1014–1016: hīna?, adhika? and sama? are ratified
; stable peers installed directly by the runtime with UK and symbolic names.
; na-adhika = not-greater (compound)
(визначити na-adhika? не-більше?)
; na-hīna = not-lesser (compound)
(визначити na-hīna? не-менше?)

;; ═══════════════════════════════════════════════════════════════
;; Добірка 1 — предикати (стан: candidate)
;; ═══════════════════════════════════════════════════════════════

; na = not (universal negation)
; tulya = structurally equal (≠ abheda eq, sama =)
(визначити tulya? однакові?)
; nāman = symbol/name (Pāṇini 1.1.62)
(визначити nāman? символ?)
; śabda = string/text
(визначити śabda-hīna? текст-передує?)

;; ═══════════════════════════════════════════════════════════════
;; Добірка 1 — списки (стан: candidate)
;; ═══════════════════════════════════════════════════════════════

; śreṇī = ordered sequence
(визначити śreṇī список)
; pramāṇa = measure/quantity
(визначити pramāṇa довжина)
; saṅkalana = collection (≠ saṃyuj CONS)
(визначити saṅkalana приєднати)
; viloma = reverse order
(визначити viloma зворот)
; kramāṅka = ordinal number (candidate)
(визначити kramāṅka елемент-списку-за-індексом)
; sambaddha = included/bound (candidate)
(визначити sambaddha? значення-у-списку?)
; saṃbandha = relation/connection
(визначити saṃbandha знайти-за-ключем)
; «dvandva» лишається назвою проєкції у реєстрі поверхонь.
; Тут не створюємо викличний alias: доменна identity сама не дає допуску.
; Порядкові селектори повертають елемент, а не хвіст списку.
(визначити dvitīya друге)
(визначити tṛtīya третє)
(визначити caturtha четверте)
(визначити pañcama п'ятий)

;; ═══════════════════════════════════════════════════════════════
;; Добірка 1 — функції вищого порядку (стан: candidate)
;; ═══════════════════════════════════════════════════════════════

; āvartana = repeated application (candidate — no direct traditional source)
(визначити āvartana відобразити)
; kalpana = selection/postulation (Mīmāṃsā)
(визначити kalpana відсіяти)
; saṅgraha = comprehension/collection
(визначити saṅgraha згорнути)

;; ═══════════════════════════════════════════════════════════════
;; Добірка 1 — рядки (стан: candidate)
;; ═══════════════════════════════════════════════════════════════

; śabdasaṃyoga = joining of words (≠ saṃyuj CONS)
; śūnya = empty/void
; pūrva = preceding (≠ ādi CAR)
; prathamavarṇa = first letter (≠ ādi CAR)
; śeṣavarṇa = rest of letters (≠ śeṣa CDR)
; cheda = cut/slice

;; ═══════════════════════════════════════════════════════════════
;; Добірка 1 — інші (стан: candidate)
;; ═══════════════════════════════════════════════════════════════

; svabhāva = own nature/identity (≠ svarūpa QUOTE)
(визначити svabhāva тотожність)

;; ═══════════════════════════════════════════════════════════════
;; Добірка 2 — введення/виведення (стан: candidate)
;; ═══════════════════════════════════════════════════════════════

; mudraṇa = impression/printing
; darśana = showing/display
; pāṭhana = reading
; likhana = writing
; vicāraṇa = deliberation/evaluation
; āśraya = substrate/environment

;; ═══════════════════════════════════════════════════════════════
;; Добірка 2 — вектори (стан: candidate)
;; ═══════════════════════════════════════════════════════════════

; samūha = collection/aggregate

;; ═══════════════════════════════════════════════════════════════
;; Добірка 2 — перетворення (стан: candidate)
;; ═══════════════════════════════════════════════════════════════

; saṅkhyā-śabda = number-to-word
(визначити saṅkhyā-śabda число-рядок)

;; ═══════════════════════════════════════════════════════════════
;; Добірка 2 — час (стан: candidate)
;; ═══════════════════════════════════════════════════════════════

; kāla = time
(визначити kāla-adya узгоджений-час-зараз)
(визначити kāla-mono-ms монотонний-мс)
(визначити kāla-millisecondāni мілісекунди-з-наносекунди)
; deśa-kāla = timezone
(визначити deśa-kāla-nāma часовий-пояс-ім'я)
(визначити deśa-kāla-jñāna часовий-пояс-визначити)
(визначити deśa-kāla-śeṣa часовий-пояс-зсув-секунди)
;avadhi = deadline
(визначити avadhi-gatā? крайній-час-досягнуто?)
(визначити avadhi-gatā-kadā? крайній-час-досягнуто-у?)
(визначити avadhi-nirmāṇa крайній-час-з)
(визначити avadhi-anantara-ns крайній-час-після-нс)
(визначити atīta-ns минуло-нс)

;; ═══════════════════════════════════════════════════════════════
;; Добірка 2 — незмінна мапа (стан: candidate)
;; ═══════════════════════════════════════════════════════════════

; kośa = repository/map
(визначити kośa-śūnya мапа-порожній)
(визначити kośa-grahaṇa мапа-отримати)
(визначити kośa-niveśana мапа-вставити)
(визначити kośa-sambaddha? мапа-містить?)
(визначити kośa-śreṇī мапа-список)

;; ═══════════════════════════════════════════════════════════════
;; Добірка 2 — незмінний вектор (стан: candidate)
;; ═══════════════════════════════════════════════════════════════

(визначити samūha-śūnya вектор-порожній)
(визначити samūha-yukti вектор-додати)
(визначити samūha-gaṇana вектор-кількість)
(визначити samūha-kramāṅka вектор-н-тий)
(визначити samūha-śreṇī вектор-список)
(визначити śreṇī-samūha вектор-з-список)

;; ═══════════════════════════════════════════════════════════════
;; Добірка 2 — знання й міркування (стан: candidate)
;; ═══════════════════════════════════════════════════════════════

; jñāna = knowledge
(визначити jñāna-satya? є-факт?)
(визначити varṇana описати)
(визначити jñāna-saṅgraha зібрати-факти-про)
(визначити aṇu-sambaddha? містить-атом?)
; abhimukha = forward
(визначити abhimukha-anumāna вперед-у)
; anumāna = inference
(визначити anumāna міркувати-у)
(визначити virodha-parīkṣā перевірити-конфлікт)
; pramāṇa-siddhi = proof
(визначити siddhi-sādhana довести-ціль)
(визначити siddhi-sādhana-sarva довести-цілі)
(визначити siddhi-vyākhyā пояснити-доказ)
(визначити siddhi-mūla джерело-від)
(визначити utpatti походження)
(визначити tarka міркувати)
(визначити tarka-vyākhyā міркувати-пояснити)

; Уніфікація
(визначити ekīkaraṇa уніфікувати)
(визначити tarka-cihna логічна-змінна)
(визначити cihna? змінна?)
(визначити pratyāroha застосувати-підстановка)
(визначити vicāraṇa-gamana пройти)
(визначити parivṛtti-parīkṣā occurs-check)

;; ═══════════════════════════════════════════════════════════════
;; Добірка 2 — епістеміка (стан: candidate)
;; ═══════════════════════════════════════════════════════════════

; pratyaya = claim/conviction
(визначити pratyaya? твердження?)
(визначити pratyaya-vākya твердження-твердження)
(визначити pratyaya-parīkṣā твердження-перевірка)
; pramāṇa = evidence
(визначити pramāṇa? доказ?)
(визначити pramāṇa-vidhi доказ-метод)
(визначити pramāṇa-phala доказ-підсумок)
; pratyakṣa = observation
(визначити pratyakṣa? спостереження?)
(визначити pratyakṣa-vākya спостереження-твердження)
; saṅkalpa = intent
(визначити saṅkalpa? намір?)
(визначити saṅkalpa-lakṣya намір-ціль)
(визначити sahāya-pramāṇa підтверджувальний-доказ)

;; ═══════════════════════════════════════════════════════════════
;; Добірка 2 — доповнення санскритської проєкції (стан: candidate)
;; ═══════════════════════════════════════════════════════════════

; nāman-nirmāṇa = name generation
(визначити nāman-nirmāṇa створити-символ)
