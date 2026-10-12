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
(0011 rūpa abs)
; alpatara = least (alpa + -tara comparative)
(0011 alpatara min)
; brhattara = greatest (bṛhat + -tara comparative)
(0011 brhattara max)
; avasiṣṭa = remainder (ava-śiṣ; ≠ śeṣa CDR)
(0011 avasiṣṭa mod)
; bhāga = quotient (result of division)
(0011 bhāga quotient)
; mūla = square root
(0011 mūla sqrt)
; sakalamūla = integer square root
(0011 sakalamūla isqrt)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Comparisons (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; ADR-007/008 / 1014–1016: hīna?, adhika? and sama? are ratified
; stable peers installed directly by the runtime with UK and symbolic names.
; na-adhika = not-greater (compound)
(0011 na-adhika? <=)
; na-hīna = not-lesser (compound)
(0011 na-hīna? >=)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Predicates (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; na = not (universal negation)
; tulya = structurally equal (≠ abheda eq, sama =)
(0011 tulya? equal?)
; nāman = symbol/name (Pāṇini 1.1.62)
(0011 nāman? symbol?)
; śabda = string/text
(0011 śabda-hīna? string<?)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Lists (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; śreṇī = ordered sequence
(0011 śreṇī list)
; pramāṇa = measure/quantity
(0011 pramāṇa length)
; saṅkalana = collection (≠ saṃyuj CONS)
(0011 saṅkalana append)
; viloma = reverse order
(0011 viloma reverse)
; kramāṅka = ordinal number (candidate)
(0011 kramāṅka nth)
; sambaddha = included/bound (candidate)
(0011 sambaddha? member?)
; saṃbandha = relation/connection
(0011 saṃbandha assoc)
; dvandva = pair (Pāṇini 2.2.29-34)
(0011 dvandva pair)
; ordinals — safe: return element, not sublist
(0011 dvitīya second)
(0011 tṛtīya third)
(0011 caturtha fourth)
(0011 pañcama fifth)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Higher-order (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; āvartana = repeated application (candidate — no direct traditional source)
(0011 āvartana map)
; kalpana = selection/postulation (Mīmāṃsā)
(0011 kalpana filter)
; saṅgraha = comprehension/collection
(0011 saṅgraha reduce)

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
(0011 svabhāva identity)

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
(0011 saṅkhyā-śabda number->string)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Time (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; kāla = time
(0011 kāla-adya utc-now)
(0011 kāla-mono-ms mono-ms)
(0011 kāla-millisecondāni milliseconds-from-nanoseconds)
; deśa-kāla = timezone
(0011 deśa-kāla-nāma timezone-name)
(0011 deśa-kāla-jñāna timezone-detect)
(0011 deśa-kāla-śeṣa timezone-offset-seconds)
;avadhi = deadline
(0011 avadhi-gatā? deadline-reached?)
(0011 avadhi-gatā-kadā? deadline-reached-at?)
(0011 avadhi-nirmāṇa deadline-from)
(0011 avadhi-anantara-ns deadline-after-ns)
(0011 atīta-ns elapsed-ns)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Persistent map (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; kośa = repository/map
(0011 kośa-śūnya map-empty)
(0011 kośa-grahaṇa map-get)
(0011 kośa-niveśana map-insert)
(0011 kośa-sambaddha? map-contains?)
(0011 kośa-śreṇī map->list)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Persistent vector (status: candidate)
;; ═══════════════════════════════════════════════════════════════

(0011 samūha-śūnya vec-empty)
(0011 samūha-yukti vec-conj)
(0011 samūha-gaṇana vec-count)
(0011 samūha-kramāṅka vec-nth)
(0011 samūha-śreṇī vec->list)
(0011 śreṇī-samūha vec-from-list)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Knowledge/Reasoning (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; jñāna = knowledge
(0011 jñāna-satya? is-fact?)
(0011 varṇana describe)
(0011 jñāna-saṅgraha collect-facts-about)
(0011 aṇu-sambaddha? contains-atom?)
; abhimukha = forward
(0011 abhimukha-anumāna forward-in)
; anumāna = inference
(0011 anumāna reason-in)
(0011 virodha-parīkṣā check-conflict)
; pramāṇa-siddhi = proof
(0011 siddhi-sādhana prove-goal)
(0011 siddhi-sādhana-sarva prove-goals)
(0011 siddhi-vyākhyā explain-proof)
(0011 siddhi-mūla source-of)
(0011 utpatti provenance)
(0011 tarka reason)
(0011 tarka-vyākhyā reason-explain)

; Unification
(0011 ekīkaraṇa unify)
(0011 tarka-cihna logic-var)
(0011 cihna? var?)
(0011 pratyāroha apply-subst)
(0011 vicāraṇa-gamana walk)
(0011 parivṛtti-parīkṣā occurs-check)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Epistemic (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; pratyaya = claim/conviction
(0011 pratyaya? claim?)
(0011 pratyaya-vākya claim-statement)
(0011 pratyaya-parīkṣā claim-review)
; pramāṇa = evidence
(0011 pramāṇa? evidence?)
(0011 pramāṇa-vidhi evidence-method)
(0011 pramāṇa-phala evidence-outcome)
; pratyakṣa = observation
(0011 pratyakṣa? observation?)
(0011 pratyakṣa-vākya observation-statement)
; saṅkalpa = intent
(0011 saṅkalpa? intent?)
(0011 saṅkalpa-lakṣya intent-goal)
(0011 sahāya-pramāṇa supporting-evidence)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Missing SA fill (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; nāman-nirmāṇa = name generation
(0011 nāman-nirmāṇa gensym)