; Sanskrit surface for canonical primitives and derived core vocabulary.
; संस्कृत-पृष्ठम् — Sanskrit surface layer.
;
; Canon 0+7 names are NOT defined here. The immutable Canon resolver owns the
; ratified Sanskrit spellings directly, before ordinary lexical lookup.
; Everything below Canon remains language-owned aliases over the same semantic
; environment, except identities migrated under ADR-007: those peer spellings
; are installed directly by the runtime and are not defined here.
;
; Principle: one semantic implementation, multiple human surfaces.
;
; Status legend:
;   stable    — ratified against primary sources (Canon 0+7 calibration doc)
;   candidate — proposed in Batch 1 research, pending ratification
;
; Full-profile loading order: macro.lisp → core.lisp → unify.lisp → reason.lisp →
; forward.lisp → knowledge.lisp → persistent-map.lisp → persistent-vector.lisp →
; time.lisp → epistemic.lisp → sa.lisp (this file).

;; ═══════════════════════════════════════════════════════════════
;; Canon 0+7 — owned by immutable resolver (status: stable)
;; ═══════════════════════════════════════════════════════════════

; svarūpa, aṇu, abheda, saṃyuj, ādi, śeṣa, anukrama
; are reserved Canon spellings and are intentionally not ordinary bindings.

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Arithmetic (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; ADR-007/008 / 0104, 1001–1003: yoga, viyoga, guṇana and haraṇa
; are ratified stable peers installed directly by the runtime together with
; Ukrainian and symbolic spellings. None is defined through another surface.
; rūpa = absolute value (candidate — polysemous)
(визначити rūpa abs)
; alpatara = least (alpa + -tara comparative)
(визначити alpatara min)
; brhattara = greatest (bṛhat + -tara comparative)
(визначити brhattara max)
; avasiṣṭa = remainder (ava-śiṣ; ≠ śeṣa CDR)
(визначити avasiṣṭa mod)
; bhāga = quotient (result of division)
(визначити bhāga quotient)
; mūla = square root
(визначити mūla sqrt)
; sakalamūla = integer square root
(визначити sakalamūla isqrt)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Comparisons (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; ADR-007/008 / 1014–1016: hīna?, adhika? and sama? are ratified
; stable peers installed directly by the runtime with UK and symbolic names.
; na-adhika = not-greater (compound)
(визначити na-adhika? <=)
; na-hīna = not-lesser (compound)
(визначити na-hīna? >=)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Predicates (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; na = not (universal negation)
; tulya = structurally equal (≠ abheda eq, sama =)
(визначити tulya? equal?)
; nāman = symbol/name (Pāṇini 1.1.62)
(визначити nāman? symbol?)
; śabda = string/text
(визначити śabda-hīna? string<?)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Lists (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; śreṇī = ordered sequence
(визначити śreṇī list)
; pramāṇa = measure/quantity
(визначити pramāṇa length)
; saṅkalana = collection (≠ saṃyuj CONS)
(визначити saṅkalana append)
; viloma = reverse order
(визначити viloma reverse)
; kramāṅka = ordinal number (candidate)
(визначити kramāṅka nth)
; sambaddha = included/bound (candidate)
(визначити sambaddha? member?)
; saṃbandha = relation/connection
(визначити saṃbandha assoc)
; «dvandva» лишається назвою проєкції у реєстрі поверхонь.
; Тут не створюємо викличний alias: доменна identity сама не дає допуску.
; ordinals — safe: return element, not sublist
(визначити dvitīya second)
(визначити tṛtīya third)
(визначити caturtha fourth)
(визначити pañcama fifth)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Higher-order (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; āvartana = repeated application (candidate — no direct traditional source)
(визначити āvartana map)
; kalpana = selection/postulation (Mīmāṃsā)
(визначити kalpana filter)
; saṅgraha = comprehension/collection
(визначити saṅgraha reduce)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Strings (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; śabdasaṃyoga = joining of words (≠ saṃyuj CONS)
; śūnya = empty/void
; pūrva = preceding (≠ ādi CAR)
; prathamavarṇa = first letter (≠ ādi CAR)
; śeṣavarṇa = rest of letters (≠ śeṣa CDR)
; cheda = cut/slice

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Other (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; svabhāva = own nature/identity (≠ svarūpa QUOTE)
(визначити svabhāva identity)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — I/O (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; mudraṇa = impression/printing
; darśana = showing/display
; pāṭhana = reading
; likhana = writing
; vicāraṇa = deliberation/evaluation
; āśraya = substrate/environment

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Vectors (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; samūha = collection/aggregate

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Conversions (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; saṅkhyā-śabda = number-to-word
(визначити saṅkhyā-śabda number->string)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Time (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; kāla = time
(визначити kāla-adya utc-now)
(визначити kāla-mono-ms mono-ms)
(визначити kāla-millisecondāni milliseconds-from-nanoseconds)
; deśa-kāla = timezone
(визначити deśa-kāla-nāma timezone-name)
(визначити deśa-kāla-jñāna timezone-detect)
(визначити deśa-kāla-śeṣa timezone-offset-seconds)
;avadhi = deadline
(визначити avadhi-gatā? deadline-reached?)
(визначити avadhi-gatā-kadā? deadline-reached-at?)
(визначити avadhi-nirmāṇa deadline-from)
(визначити avadhi-anantara-ns deadline-after-ns)
(визначити atīta-ns elapsed-ns)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Persistent map (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; kośa = repository/map
(визначити kośa-śūnya map-empty)
(визначити kośa-grahaṇa map-get)
(визначити kośa-niveśana map-insert)
(визначити kośa-sambaddha? map-contains?)
(визначити kośa-śreṇī map->list)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Persistent vector (status: candidate)
;; ═══════════════════════════════════════════════════════════════

(визначити samūha-śūnya вектор-порожній)
(визначити samūha-yukti вектор-додати)
(визначити samūha-gaṇana вектор-кількість)
(визначити samūha-kramāṅka вектор-н-тий)
(визначити samūha-śreṇī вектор-список)
(визначити śreṇī-samūha вектор-з-список)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Knowledge/Reasoning (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; jñāna = knowledge
(визначити jñāna-satya? is-fact?)
(визначити varṇana describe)
(визначити jñāna-saṅgraha collect-facts-about)
(визначити aṇu-sambaddha? contains-atom?)
; abhimukha = forward
(визначити abhimukha-anumāna forward-in)
; anumāna = inference
(визначити anumāna reason-in)
(визначити virodha-parīkṣā check-conflict)
; pramāṇa-siddhi = proof
(визначити siddhi-sādhana prove-goal)
(визначити siddhi-sādhana-sarva prove-goals)
(визначити siddhi-vyākhyā explain-proof)
(визначити siddhi-mūla source-of)
(визначити utpatti provenance)
(визначити tarka reason)
(визначити tarka-vyākhyā reason-explain)

; Unification
(визначити ekīkaraṇa unify)
(визначити tarka-cihna logic-var)
(визначити cihna? var?)
(визначити pratyāroha apply-subst)
(визначити vicāraṇa-gamana walk)
(визначити parivṛtti-parīkṣā occurs-check)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Epistemic (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; pratyaya = claim/conviction
(визначити pratyaya? claim?)
(визначити pratyaya-vākya claim-statement)
(визначити pratyaya-parīkṣā claim-review)
; pramāṇa = evidence
(визначити pramāṇa? evidence?)
(визначити pramāṇa-vidhi evidence-method)
(визначити pramāṇa-phala evidence-outcome)
; pratyakṣa = observation
(визначити pratyakṣa? observation?)
(визначити pratyakṣa-vākya observation-statement)
; saṅkalpa = intent
(визначити saṅkalpa? intent?)
(визначити saṅkalpa-lakṣya intent-goal)
(визначити sahāya-pramāṇa supporting-evidence)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Missing SA fill (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; nāman-nirmāṇa = name generation
(визначити nāman-nirmāṇa створити-символ)
