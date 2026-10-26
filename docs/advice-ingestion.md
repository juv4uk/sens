# Guarded advice ingestion · Захищене приймання порад · Geschützte Wissensaufnahme

## English

The Advice Taker has two distinct boundaries and neither gives an external
translator semantic authority.

### 1. External translation proposal

An external parser, model or LLM may emit only versioned Lisp data:

```lisp
(переклад-версія-1 кандидат клауза
  "Socrates is human."
  ((людина сократ)))
```

`lib/translation.lisp` owns the review protocol. The translator status is one of
`кандидат`, `неоднозначний`, or `відхилений`; the kind is `клауза`, `пакет`, or
`запит`. `translation-review` validates the protocol shell and then reuses the
existing knowledge validators and `advice-decision` / `advice-all-decision`.
It is pure with respect to the knowledge journal: even an `прийнятий` review
writes nothing.

```lisp
(def proposal
  '(переклад-версія-1 кандидат клауза
     "Socrates is human."
     ((людина сократ))))

(def review (translation-review 'science proposal))
; => (огляд-перекладу-версія-1 прийнятий знання-прийнято ...)

(translation-admission-payload review)
; => ((human socrates))
```

Rejected and ambiguous translations are observations, not knowledge.
`translation-evidence-next` can retain their structured reviews in a
caller-owned evidence journal. A proposal with one alternative cannot claim
`неоднозначний`: ambiguity requires at least two structurally valid alternatives.

### 2. Knowledge admission

`advise` is the data-only write boundary between reviewed candidate data and
the symbolic knowledge journal. It accepts exactly one `lib/reason.lisp` clause,
validates the complete structure (including canonical `(var name)` variables),
checks for an explicitly known opposite, and mutates the journal only on
acceptance. It never treats failure to prove a statement as proof of its
negation.

```lisp
(def review (translation-review 'astronomy proposal))
(advise astronomy (translation-admission-payload review))
```

For several mutually dependent clauses use `advise-all`; the entire non-empty
batch is validated atomically against both current and proposed knowledge.
The journal receives every clause in one update or receives none.

Results remain stable data shapes rather than printed messages:

- `(прийнятий (module name) (knowledge clause-or-clauses))`
- `(відхилений (reason некоректний-модуль|invalid-clause|некоректний-пакет) (input value))`
- `(суперечність (new клауза) (existing opposite) (proof result))`

Explicit negative knowledge uses a head such as `((not (planet pluto)))`.
This is distinct from `(not goal)` inside a rule body, where the reasoning
engine implements negation as failure.

The resulting authority chain is therefore:

```text
external translator
        ↓
(переклад-версія-1 ...)
        ↓
translation-review          Lisp-owned, no write
        ↓
прийнятий knowledge payload?
        ├── no  → structured evidence only
        └── yes → explicit advise / advise-all
                        ↓
                 knowledge journal
                        ↓
                reason-in-observe
                        ↓
                 narrate-outcome
```

The versioned adversarial corpus is
`tests/fixtures/translation-corpus-v1.lisp`; executable boundary tests live in
`crates/my-lisp/tests/translation_boundary.rs`.

## Українська

Advice Taker тепер має **дві окремі брами**, і жодна з них не передає
зовнішньому перекладачу семантичної влади.

### 1. Пропозиція перекладу

Зовнішній parser, модель або LLM може лише запропонувати versioned Lisp-дані:

```lisp
(переклад-версія-1 кандидат клауза
  "Socrates is human."
  ((human socrates)))
```

`lib/translation.lisp` належить Lisp-рівню і вирішує, чи сама пропозиція
структурно коректна. Статус перекладача — `кандидат`, `неоднозначний` або
`відхилений`; вид — `клауза`, `пакет` або `запит`.

`translation-review` не пише у `*knowledge-journal*`. Навіть результат
`прийнятий` означає лише: «цей кандидат пройшов Lisp-перевірку і може бути
переданий до брами знань». Він **ще не є знанням**.

Відхилені та неоднозначні переклади лишаються evidence. Функція
`translation-evidence-next` може додати структурований review до окремого
журналу спостережень. `неоднозначний` вимагає щонайменше двох валідних
альтернатив — одна альтернатива не може маскуватися під неоднозначність.

### 2. Приймання знання

`advise` лишається єдиною data-only брамою запису одного clause у символьний
журнал знань. Вона перевіряє всю структуру, канонічні `(var name)` і явно
відому протилежність, та змінює журнал лише після `прийнятий`.

Для кількох взаємозалежних clause використовується `advise-all`: пакет
перевіряється атомарно разом із чинними й запропонованими знаннями — або
записуються всі clause, або жодного.

Тому повний шлях тепер такий:

```text
зовнішній translator
        ↓
(переклад-версія-1 ...)
        ↓
translation-review          ← рішення Lisp, без запису
        ↓
кандидат допустимий?
        ├── ні  → evidence, не knowledge
        └── так → явний advise / advise-all
                         ↓
                    knowledge
                         ↓
                 reason-in-observe
                         ↓
                  narrate-outcome
```

Неможливість довести твердження не є доказом його заперечення. Явне негативне
знання (`((not (...)))`) також не змішується з negation-as-failure у тілі
правила.

Versioned корпус для руйнівної перевірки цієї межі —
`tests/fixtures/translation-corpus-v1.lisp`; executable tests —
`crates/my-lisp/tests/translation_boundary.rs`.

## Deutsch

Der Advice Taker besitzt jetzt **zwei getrennte Grenzen**; keine davon gibt
einem externen Übersetzer semantische Autorität.

### 1. Übersetzungsvorschlag

Ein externer Parser, ein Modell oder LLM darf nur versionierte Lisp-Daten
vorschlagen:

```lisp
(переклад-версія-1 кандидат клауза
  "Socrates is human."
  ((human socrates)))
```

`lib/translation.lisp` prüft die Protokollform sowie die vorhandenen
Wissensregeln. `translation-review` verändert das Wissensjournal nicht. Auch
ein `прийнятий`-Review bedeutet nur, dass der Kandidat die Lisp-Prüfung bestanden
hat und an die eigentliche Wissensgrenze weitergegeben werden darf.

`неоднозначний` und `відхилений` bleiben strukturierte Evidenz, niemals Wissen.
Mehrdeutigkeit erfordert mindestens zwei gültige Alternativen.

### 2. Wissensaufnahme

`advise` bleibt die data-only Schreibgrenze für eine Clause;
`advise-all` ist die atomare Variante für mehrere voneinander abhängige
Clauses. Struktur, `(var name)`-Variablen und explizite Gegenbeweise werden vor
dem Schreiben geprüft. Ein fehlender Beweis wird nie als Beweis der Negation
behandelt.

Damit lautet die Autoritätskette:

```text
externer Übersetzer
        ↓
versionierte Lisp-Daten
        ↓
translation-review          Lisp besitzt die Entscheidung
        ↓
explizites advise / advise-all
        ↓
Wissensjournal → reason-in-observe → narrate-outcome
```

Der versionierte adversariale Korpus liegt in
`tests/fixtures/translation-corpus-v1.lisp`; die ausführbaren Grenztests in
`crates/my-lisp/tests/translation_boundary.rs`.
