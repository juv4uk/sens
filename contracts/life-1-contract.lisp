; LIFE-1 — контракт життєвого ланцюга, визначений мовою Lisp.
;
; Контракт установлює незмінні вимоги до явного перенесення
; спостереження одного автономного виконавця на вхід іншого.
; Він не встановлює семантику Prolog, Datalog, CLIPS або Common Lisp.
;
; Зовнішня форма:
;   (life-1-contract-1 ENTRY ...)
;
; Траса LIFE містить дані про походження та причинність,
; а не логічне значення.

(life-1-contract-1
  ((identity . life-trace)
   (owner . sens)
   (kind . provenance-observation)
   (truth-value . forbidden)
   (producer-required . yes)
   (target-required . yes)
   (semantic-id-required . yes))

  ((identity . source-observation)
   (native-domain-preserved . yes)
   (producer-preserved . yes)
   (provenance-preserved . yes)
   (universal-result-normalization . forbidden))

  ((identity . projection)
   (owner . sens)
   (explicit . yes)
   (partial . yes)
   (source-native-result-preserved . yes)
   (semantic-equivalence-assumed . no))

  ((identity . target-invocation)
   (input-origin-recorded . yes)
   (target-native-domain-preserved . yes)
   (semantic-id-meaning-source . sens-registry-and-laws)
   (kernel-reinterpretation . forbidden))

  ((identity . missing-source-kernel)
   (kind . execution-unavailability)
   (legal . yes)
   (changes-semantic-id-meaning . no)
   (changes-registry-numbering . no))

  ((identity . first-vertical-slice)
   (source . prolog)
   (projection . prolog-substitutions-to-datalog-facts)
   (target . datalog)
   (source-result-domain . native-prolog-answer-list)
   (target-result-domain . native-datalog-relation)
   (shared-result-type . forbidden))

  ((identity . liveness)
   (fresh-checkout . required)
   (manual-semantic-patching . forbidden)
   (focused-ci-question . does-life-1-still-live)))
