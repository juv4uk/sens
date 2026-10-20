; #791 ATOMSPACE-1 — аудит тотожності, посилань і походження.
;
; Лише дослідницькі дані. OpenCog AtomSpace розглядаємо як
; приклад графових зв'язків та адресованих посилань, а не
; як обов'язкову центральну онтологію для всіх виконавців.
;
; Розглянуті властивості:
; - вузли AtomSpace визначаються парою назви й типу;
; - зв'язки визначаються типом і набором вихідних посилань;
; - запити подаються графовими структурами;
; - легкі значення окремих атомів зберігають змінні метадані;
; - TruthValue та AttentionValue є пов'язаними з атомом значеннями.
;
; Значення рішень у даних:
;   borrow-mechanism — запозичити механізм;
;   adapt-explicitly — пристосувати явно;
;   reject-ontology — відхилити спільну онтологію.

(atomspace-pattern-audit/1
  ((pattern . stable-node-identity)
   (decision . borrow-mechanism)
   (atomspace-evidence . node-identity-by-name-and-type)
   (use-in-my-lisp . stable-observation-and-semantic-references)
   (reason . references-should-not-depend-on-memory-location-or-rendering))

  ((pattern . stable-link-identity)
   (decision . borrow-mechanism)
   (atomspace-evidence . link-identity-by-type-and-outgoing-set)
   (use-in-my-lisp . provenance-edge-identity)
   (reason . relation-between-observations-can-be-addressed-without-copying-results))

  ((pattern . attached-lightweight-values)
   (decision . adapt-explicitly)
   (atomspace-evidence . per-atom-key-value-values)
   (use-in-my-lisp . observation-metadata)
   (reason . lifecycle-status-timestamps-costs-and-capabilities-need-not-be-semantic-graph-nodes))

  ((pattern . query-as-data)
   (decision . borrow-mechanism)
   (atomspace-evidence . query-links-stored-as-graph)
   (use-in-my-lisp . pending-invocation-and-projection-contract-as-data)
   (reason . scheduler-and-bridge-intent-should-be-inspectable-ordinary-data))

  ((pattern . central-atomspace-knowledgebase)
   (decision . reject-ontology)
   (atomspace-evidence . one-typed-hypergraph-knowledge-store)
   (use-in-my-lisp . none)
   (reason . island-native-results-must-not-be-forced-into-one-central-representation))

  ((pattern . universal-truthvalue-attachment)
   (decision . reject-ontology)
   (atomspace-evidence . truth-values-associated-with-atoms)
   (use-in-my-lisp . none)
   (reason . native-observation-count-or-result-is-not-universal-truth))

  ((pattern . universal-attentionvalue-attachment)
   (decision . reject-ontology)
   (atomspace-evidence . attention-values-associated-with-atoms)
   (use-in-my-lisp . scheduler-priority-metadata-only-if-explicit)
   (reason . scheduling-priority-must-not-be-confused-with-semantic-meaning))

  ((experiment . richer-native-result-reference)
   (proposal .
     (observation-ref
       (observation-id stable)
       (producer prolog)
       (semantic-id opaque)
       (native-slot prolog)
       (metadata-ref optional)
       (provenance-parent none)))
   (relation-proposal .
     (provenance-edge
       (type projected-into)
       (from source-observation-ref)
       (via bridge-contract-ref)
       (to target-observation-ref)))
   (implementation-status . proposed))
)
