; Дослідний корпус перекладу із зовнішньої природної мови.
; Його записи — дані свідчень, а не виконуваний код перекладача.
; Структура зберігає протокольні назви полів:
;   (translation-corpus/1
;     (translation-case/1 ID MODULE INPUT PROPOSAL EXPECTED-REVIEW-STATUS
;                         DOWNSTREAM-QUERY EXPECTED-OUTCOME-STATUS)
;     ...)
; Стан not-run означає, що пропозицію не допущено як знання;
; для неї не можна виконувати подальший запит Advice Taker.

(translation-corpus/1
  (translation-case/1
    direct-fact
    corpus
    "Socrates is human."
    (translation/1 candidate clause "Socrates is human." ((human socrates)))
    accepted
    (human socrates)
    proved)

  (translation-case/1
    rule-batch
    corpus
    "Socrates is human. All humans are mortal."
    (translation/1 candidate batch
      "Socrates is human. All humans are mortal."
      (((human socrates))
       ((mortal (var x)) (human (var x)))))
    accepted
    (mortal socrates)
    proved)

  (translation-case/1
    valid-question-without-proof
    corpus
    "Is Plato metallic?"
    (translation/1 candidate query "Is Plato metallic?" (metallic plato))
    accepted
    (metallic plato)
    unknown)

  (translation-case/1
    malformed-semantic-candidate
    corpus
    "Socrates is human."
    (translation/1 candidate clause "Socrates is human." ((human (var))))
    rejected
    ()
    not-run)

  (translation-case/1
    lexical-ambiguity
    corpus
    "Mercury is hot."
    (translation/1 ambiguous clause
      "Mercury is hot."
      (((hot mercury-planet))
       ((hot mercury-element))))
    ambiguous
    ()
    not-run)

  (translation-case/1
    translator-refusal
    corpus
    "Colorless green ideas sleep furiously."
    (translation/1 rejected clause
      "Colorless green ideas sleep furiously."
      unsupported-translation)
    rejected
    ()
    not-run))
