// GENERATED — DO NOT EDIT BY HAND.
// Identity: lib/domains/d10.lisp; definitions: lib/core4.lisp.
// Binding-only: concrete Core4 closures, never generic D10 callability.
// Checked by: scripts/check-d10-definition-bindings.py

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(super) struct D10DefinitionBinding {
    pub(super) bits: u16,
    pub(super) names: &'static [&'static str],
}

pub(super) const D10_DEFINITION_BINDINGS: &[D10DefinitionBinding] = &[
    D10DefinitionBinding { bits: 0b0000000001, names: &["кількість-результатів", "кількість-результатів-спостереження", "phala-saṃkhyā", "result-count", "RESULT-COUNT"] },
    D10DefinitionBinding { bits: 0b0000000111, names: &["числа-нерівні?", "saṃkhyā-asama", "numeric-not-equal?", "NUMERIC-NOT-EQUAL"] },
    D10DefinitionBinding { bits: 0b0000011000, names: &["список-усіх-значень", "зібрати-всі-повернені-значення-у-список", "bahu-mūlya-sūcī", "multiple-value-list", "MULTIPLE-VALUE-LIST"] },
    D10DefinitionBinding { bits: 0b0000110110, names: &["зріз-вектора", "взяти-напіввідкритий-зріз-вектора", "sadisa-aṃśa", "vector-slice", "VECTOR-SLICE"] },
    D10DefinitionBinding { bits: 0b0001001001, names: &["кожен-задовольняє?", "кожен-кандидат-задовольняє-умову?", "sarveṣām-pratyeka-pratyāśin-saṃtuṣṭa", "forall-every-candidate-satisfies?", "FORALL-EVERY-CANDIDATE-SATISFIES?"] },
    D10DefinitionBinding { bits: 0b0001011001, names: &["асоціація-тотожність", "saṃbandha-eq", "sassq", "SASSQ"] },
    D10DefinitionBinding { bits: 0b0001100010, names: &["входження-тотожність", "sadasyatā-eq", "memq", "MEMQ"] },
    D10DefinitionBinding { bits: 0b0001100101, names: &["пошук-асоціації", "saṃbandha-anveṣaṇa", "sassoc", "SASSOC"] },
    D10DefinitionBinding { bits: 0b0001110011, names: &["сортувати-за-першим", "ādi-kramaṇa", "sortcar", "SORTCAR"] },
    D10DefinitionBinding { bits: 0b0001110110, names: &["створити-твердження", "створити-структуроване-твердження", "nirmāṇa-pratijñā", "make-claim", "MAKE-CLAIM"] },
    D10DefinitionBinding { bits: 0b0001110111, names: &["джерело-спостереження", "отримати-джерело-спостереження", "nirīkṣaṇa-srotas", "observation-source", "OBSERVATION-SOURCE"] },
    D10DefinitionBinding { bits: 0b0001111011, names: &["вимоги-наміру", "отримати-необхідні-можливості-наміру", "saṅkalpa-āvaśyaka", "intent-requires", "INTENT-REQUIRES"] },
    D10DefinitionBinding { bits: 0b0010000101, names: &["створити-намір", "nirmāṇa-saṅkalpa", "make-intent", "MAKE-INTENT"] },
    D10DefinitionBinding { bits: 0b0010000111, names: &["посилання-доказу-на-твердження", "отримати-посилання-доказу-на-твердження", "pramāṇa-pratijñā-saṃdarbha", "evidence-claim-ref", "EVIDENCE-CLAIM-REF"] },
    D10DefinitionBinding { bits: 0b0010001110, names: &["правильний-список-знань?", "правильно-структурований-список-знань?", "jñāna-samyak-sūcī", "knowledge-proper-list?", "KNOWLEDGE-PROPER-LIST?"] },
    D10DefinitionBinding { bits: 0b0010001111, names: &["створити-доказ", "nirmāṇa-pramāṇa", "make-evidence", "MAKE-EVIDENCE"] },
    D10DefinitionBinding { bits: 0b0010010000, names: &["умови-зупинки-наміру", "отримати-умови-зупинки-наміру", "saṅkalpa-virāma-upari", "intent-stop-on", "INTENT-STOP-ON"] },
    D10DefinitionBinding { bits: 0b0010010001, names: &["посилання-на-джерело-доказу", "отримати-посилання-на-джерело-доказу", "pramāṇa-srotas-saṃdarbha", "evidence-source-ref", "EVIDENCE-SOURCE-REF"] },
    D10DefinitionBinding { bits: 0b0010010011, names: &["створити-спостереження", "nirmāṇa-nirīkṣaṇa", "make-observation", "MAKE-OBSERVATION"] },
    D10DefinitionBinding { bits: 0b0010010100, names: &["голова-заперечена?", "голова-твердження-знань-заперечена?", "jñāna-na-śiras", "knowledge-not-head?", "KNOWLEDGE-NOT-HEAD?"] },
    D10DefinitionBinding { bits: 0b0010010110, names: &["правильний-список-результатів?", "результат-є-правильним-списком?", "phala-samyak-sūcī", "result-proper-list?", "RESULT-PROPER-LIST?"] },
    D10DefinitionBinding { bits: 0b0010011010, names: &["продукти-наміру", "отримати-очікувані-результати-наміру", "saṅkalpa-janana", "intent-produces", "INTENT-PRODUCES"] },
    D10DefinitionBinding { bits: 0b0010110000, names: &["статус-перекладу-коректний?", "статус-запису-перекладу-коректний?", "anuvāda-avasthā-yukta", "translation-status-valid?", "TRANSLATION-STATUS-VALID?"] },
    D10DefinitionBinding { bits: 0b0010111000, names: &["вид-перекладу-коректний?", "вид-кандидата-перекладу-коректний?", "anuvāda-jāti-yukta", "translation-kind-valid?", "TRANSLATION-KIND-VALID?"] },
    D10DefinitionBinding { bits: 0b0010111110, names: &["статус-огляду-перекладу-коректний?", "статус-огляду-кандидата-перекладу-коректний?", "anuvāda-samīkṣā-avasthā-yukta", "translation-review-status-valid?", "TRANSLATION-REVIEW-STATUS-VALID?"] },
    D10DefinitionBinding { bits: 0b0011000010, names: &["черга-порожня?", "перевірити-чи-черга-порожня?", "śūnya-krama", "empty-queue?", "EMPTY-QUEUE?"] },
    D10DefinitionBinding { bits: 0b0011001000, names: &["знайти-усі", "anveṣaṇa-sarva", "find-all", "FIND-ALL"] },
    D10DefinitionBinding { bits: 0b0011001001, names: &["відобразити-у", "citraṇa-antaḥ", "map-into", "MAP-INTO"] },
    D10DefinitionBinding { bits: 0b0011001010, names: &["відобразити-й-додати", "citra-saṃyojana", "mappend", "MAPPEND"] },
    D10DefinitionBinding { bits: 0b0011001011, names: &["сортувати-зірочка", "kramaṇa-tārā", "sort*", "SORT*"] },
    D10DefinitionBinding { bits: 0b0011001101, names: &["останній", "antima", "last1", "LAST1"] },
    D10DefinitionBinding { bits: 0b0011001110, names: &["сплющити", "samīkaraṇa", "flatten", "FLATTEN"] },
    D10DefinitionBinding { bits: 0b0011001111, names: &["розділити-за-умовою", "розділити-елементи-за-предикатом", "vibhāga-yadi", "partition-if", "PARTITION-IF"] },
    D10DefinitionBinding { bits: 0b0011010011, names: &["дерево-має-збіг?", "є-листок-дерева-що-задовольняє-предикат?", "anveṣaṇa-yadi-sarvatra", "find-if-anywhere?", "FIND-IF-ANYWHERE"] },
    D10DefinitionBinding { bits: 0b0011010111, names: &["утворити-список", "sūcī-nirmāṇa", "mklist", "MKLIST"] },
    D10DefinitionBinding { bits: 0b0011011000, names: &["знайти-єдиний-вкладений", "єдиний-знайти-якщо-будь-де", "ananya-anveṣaṇa-yadi-sarvatra", "unique-find-if-anywhere", "UNIQUE-FIND-IF-ANYWHERE"] },
    D10DefinitionBinding { bits: 0b0011111100, names: &["відобразити-ключі", "citraṇa-kuñjikāḥ", "map-keys", "MAP-KEYS"] },
    D10DefinitionBinding { bits: 0b0011111110, names: &["відобразити-значення", "citraṇa-mūlyāni", "map-values", "MAP-VALUES"] },
    D10DefinitionBinding { bits: 0b0100001001, names: &["вилучити-ключ-мапи", "відобразити-вилучити-з-мапи", "citraṇa-saṃbandha-apanayana", "map-dissoc", "MAP-DISSOC"] },
    D10DefinitionBinding { bits: 0b0100001100, names: &["список?", "sūcī", "listp?", "LISTP"] },
    D10DefinitionBinding { bits: 0b0100001101, names: &["відобразити-з-пари", "citraṇa-tasmāt-yugalāni", "map-from-pairs", "MAP-FROM-PAIRS"] },
    D10DefinitionBinding { bits: 0b0101100111, names: &["вибрати-визначення-за-іменами", "відібрати-визначення-іменованої-групи", "svīya-varaṇa-paribhāṣāḥ-anusarati-nāmāni", "my-select-defs-by-names", "MY-SELECT-DEFS-BY-NAMES"] },
    D10DefinitionBinding { bits: 0b0101101000, names: &["вилучити-визначення-за-іменами", "вилучити-з-блоку-визначення-заданих-імен", "svīya-apanayana-paribhāṣāḥ-anusarati-nāmāni", "my-remove-defs-by-names", "MY-REMOVE-DEFS-BY-NAMES"] },
];
