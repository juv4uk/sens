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
(00001001 rūpa abs)
; alpatara = least (alpa + -tara comparative)
(00001001 alpatara min)
; brhattara = greatest (bṛhat + -tara comparative)
(00001001 brhattara max)
; avasiṣṭa = remainder (ava-śiṣ; ≠ śeṣa CDR)
(00001001 avasiṣṭa mod)
; bhāga = quotient (result of division)
(00001001 bhāga quotient)
; mūla = square root
(00001001 mūla sqrt)
; sakalamūla = integer square root
(00001001 sakalamūla isqrt)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Comparisons (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; ADR-007/008 / 1014–1016: hīna?, adhika? and sama? are ratified
; stable peers installed directly by the runtime with UK and symbolic names.
; na-adhika = not-greater (compound)
(00001001 na-adhika? <=)
; na-hīna = not-lesser (compound)
(00001001 na-hīna? >=)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Predicates (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; na = not (universal negation)
(00001001 na not)
; tulya = structurally equal (≠ abheda eq, sama =)
(00001001 tulya? equal?)
; nāman = symbol/name (Pāṇini 1.1.62)
(00001001 nāman? symbol?)
; śabda = string/text
(00001001 śabda-hīna? string<?)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Lists (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; śreṇī = ordered sequence
(00001001 śreṇī list)
; pramāṇa = measure/quantity
(00001001 pramāṇa length)
; saṅkalana = collection (≠ saṃyuj CONS)
(00001001 saṅkalana append)
; viloma = reverse order
(00001001 viloma reverse)
; kramāṅka = ordinal number (candidate)
(00001001 kramāṅka nth)
; sambaddha = included/bound (candidate)
(00001001 sambaddha? member?)
; saṃbandha = relation/connection
(00001001 saṃbandha assoc)
; dvandva = pair (Pāṇini 2.2.29-34)
(00001001 dvandva pair)
; ordinals — safe: return element, not sublist
(00001001 dvitīya second)
(00001001 tṛtīya third)
(00001001 caturtha fourth)
(00001001 pañcama fifth)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Higher-order (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; āvartana = repeated application (candidate — no direct traditional source)
(00001001 āvartana map)
; kalpana = selection/postulation (Mīmāṃsā)
(00001001 kalpana filter)
; saṅgraha = comprehension/collection
(00001001 saṅgraha reduce)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Strings (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; śabdasaṃyoga = joining of words (≠ saṃyuj CONS)
(00001001 śabdasaṃyoga string-append)
(00001001 śabdapramāṇa string-length)
; śūnya = empty/void
(00001001 śūnya? string-empty?)
; pūrva = preceding (≠ ādi CAR)
(00001001 pūrva? string-prefix?)
(00001001 śabdasambaddha? string-contains?)
; prathamavarṇa = first letter (≠ ādi CAR)
(00001001 prathamavarṇa string-first)
; śeṣavarṇa = rest of letters (≠ śeṣa CDR)
(00001001 śeṣavarṇa string-rest)
; cheda = cut/slice
(00001001 cheda string-slice)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Other (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; svabhāva = own nature/identity (≠ svarūpa QUOTE)
(00001001 svabhāva identity)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — I/O (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; mudraṇa = impression/printing
(00001001 mudraṇa print)
; darśana = showing/display
(00001001 darśana princ)
; pāṭhana = reading
(00001001 pāṭhana read)
(00001001 pāṭhana-sarva read-all)
; likhana = writing
(00001001 likhana write-to-string)
; vicāraṇa = deliberation/evaluation
(00001001 vicāraṇa eval)
; āśraya = substrate/environment
(00001001 āśraya env)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Vectors (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; samūha = collection/aggregate
(00001001 samūha vector)
(00001001 samūha-nirmāṇa make-vector)
(00001001 samūha-pramāṇa vector-length)
(00001001 samūha-āvartana vector-ref)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Conversions (status: candidate)
;; ═══════════════════════════════════════════════════════════════

(00001001 nāman-śabda symbol->string)
(00001001 śabda-nāman string->symbol)
(00001001 varṇa-śabda codepoint->string)
(00001001 śabda-varṇa string->codepoint)
; saṅkhyā-śabda = number-to-word
(00001001 saṅkhyā-śabda number->string)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Time (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; kāla = time
(00001001 kāla-adya utc-now)
(00001001 kāla-unix unix-time-now)
(00001001 kāla-mono mono-ns)
(00001001 kāla-mono-ms mono-ms)
(00001001 kāla-millisecondāni milliseconds-from-nanoseconds)
; deśa-kāla = timezone
(00001001 deśa-kāla-nāma timezone-name)
(00001001 deśa-kāla-jñāna timezone-detect)
(00001001 deśa-kāla-śeṣa timezone-offset-seconds)
;avadhi = deadline
(00001001 avadhi-gatā? deadline-reached?)
(00001001 avadhi-gatā-kadā? deadline-reached-at?)
(00001001 avadhi-nirmāṇa deadline-from)
(00001001 avadhi-anantara-ns deadline-after-ns)
(00001001 atīta-ns elapsed-ns)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Persistent map (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; kośa = repository/map
(00001001 kośa-śūnya map-empty)
(00001001 kośa-grahaṇa map-get)
(00001001 kośa-niveśana map-insert)
(00001001 kośa-sambaddha? map-contains?)
(00001001 kośa-śreṇī map->list)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Persistent vector (status: candidate)
;; ═══════════════════════════════════════════════════════════════

(00001001 samūha-śūnya vec-empty)
(00001001 samūha-yukti vec-conj)
(00001001 samūha-gaṇana vec-count)
(00001001 samūha-kramāṅka vec-nth)
(00001001 samūha-śreṇī vec->list)
(00001001 śreṇī-samūha vec-from-list)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Knowledge/Reasoning (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; jñāna = knowledge
(00001001 jñāna-satya? is-fact?)
(00001001 varṇana describe)
(00001001 jñāna-saṅgraha collect-facts-about)
(00001001 aṇu-sambaddha? contains-atom?)
; abhimukha = forward
(00001001 abhimukha-anumāna forward-in)
; anumāna = inference
(00001001 anumāna reason-in)
(00001001 virodha-parīkṣā check-conflict)
; pramāṇa-siddhi = proof
(00001001 siddhi-sādhana prove-goal)
(00001001 siddhi-sādhana-sarva prove-goals)
(00001001 siddhi-vyākhyā explain-proof)
(00001001 siddhi-mūla source-of)
(00001001 utpatti provenance)
(00001001 tarka reason)
(00001001 tarka-vyākhyā reason-explain)

; Unification
(00001001 ekīkaraṇa unify)
(00001001 tarka-cihna logic-var)
(00001001 cihna? var?)
(00001001 pratyāroha apply-subst)
(00001001 vicāraṇa-gamana walk)
(00001001 parivṛtti-parīkṣā occurs-check)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Epistemic (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; pratyaya = claim/conviction
(00001001 pratyaya? claim?)
(00001001 pratyaya-vākya claim-statement)
(00001001 pratyaya-parīkṣā claim-review)
; pramāṇa = evidence
(00001001 pramāṇa? evidence?)
(00001001 pramāṇa-vidhi evidence-method)
(00001001 pramāṇa-phala evidence-outcome)
; pratyakṣa = observation
(00001001 pratyakṣa? observation?)
(00001001 pratyakṣa-vākya observation-statement)
; saṅkalpa = intent
(00001001 saṅkalpa? intent?)
(00001001 saṅkalpa-lakṣya intent-goal)
(00001001 sahāya-pramāṇa supporting-evidence)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Missing SA fill (status: candidate)
;; ═══════════════════════════════════════════════════════════════

; nāman-nirmāṇa = name generation
(00001001 nāman-nirmāṇa gensym)