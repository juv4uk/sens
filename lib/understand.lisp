; A controlled-natural-language bridge from a fixed sentence shape to a
; knowledge clause `(head . body)`, in `lib/knowledge.lisp`'s / `lib/reason.lisp`'s
; format — the "text -> structure" half of the Advice Taker vision from
; private/lisp-to-knowledge.md §6, deliberately without a real NLP model.
;
; `understand` takes a *word list*, not a raw string — my-lisp has no string
; primitives (split/char-access), and adding them just to tokenize sentences
; would grow the Rust built-in surface for a feature this project's own
; CLAUDE.md says to avoid growing it for. So `(all planet have mass)` stands
; in for "All planets have mass": the caller has already done tokenization
; and (crucially) picked the exact singular class name the knowledge base
; uses — there is no morphology here (no plural stripping, no verb
; conjugation). This is "controlled" natural language in the strict sense:
; three fixed sentence shapes, matched structurally, not parsed statistically.
; A real free-text `understand` (LLM-backed) is a separate, later step — see
; PLAN.md Крок 9.6, deliberately removed once already for lacking this
; project's usual rigor (tests, trilingual docs, no hidden network calls).
;
; Shapes recognized:
;   (X is a Y)   / (X is an Y) / (X is Y)  -> fact:  ((Y X))
;   (X V Y)                                -> fact:  ((V X Y))
;   (all X have Y)                         -> rule:  ((has (var w) Y) (X (var w)))
;
; Query shapes (via `understand-query`, text -> goal structure -> a query
; `reason` can take):
;   (is X a Y)   / (is X an Y) / (is X Y)  -> goal:  (Y X)
;   (does X V Y)                           -> goal:  (V X Y)
;
; Місток контрольованої природної мови від фіксованої форми речення до
; знаннєвого clause `(head . body)`, у форматі `lib/knowledge.lisp`/`lib/reason.lisp`
; — половина "текст -> структура" бачення Advice Taker з
; private/lisp-to-knowledge.md §6, свідомо без справжньої NLP-моделі.
;
; `understand` приймає *список слів*, не сирий рядок — my-lisp не має
; рядкових примітивів (split/доступ до символів), а додавати їх лише заради
; токенізації речень означало б розширювати поверхню Rust built-in саме
; там, де власний `CLAUDE.md` проєкту просить цього не робити. Тож
; `(all planet have mass)` заміняє "All planets have mass": виклик уже
; токенізований, і (важливо) там уже точна однина назви класу, яку
; використовує база знань — тут немає морфології (без відкидання множини,
; без відмінювання дієслів). Це "контрольована" природна мова в строгому
; сенсі: три фіксовані форми речень, зіставлені структурно, не статистично.
; Справжній `understand` вільного тексту (на LLM) — окремий, пізніший крок —
; див. PLAN.md Крок 9.6, вже раз свідомо видалений за брак звичної для
; проєкту строгості (тестів, трилінгвальної документації, прихованих
; мережевих викликів).
;
; Розпізнавані форми:
;   (X is a Y)   / (X is an Y) / (X is Y)  -> факт:  ((Y X))
;   (X V Y)                                -> факт:  ((V X Y))
;   (all X have Y)                         -> правило: ((has (var w) Y) (X (var w)))
;
; Форми запитання (через `understand-query`, низ -> структура "goals" ->
; структура запиту для `reason`):
;   (is X a Y)   / (is X an Y) / (is X Y)  -> запит:  (Y X)
;   (does X V Y)                           -> запит:  (V X Y)
;
; Eine Brücke kontrollierter natürlicher Sprache von einer festen Satzform zu
; einem Wissens-Clause `(head . body)`, im Format von `lib/knowledge.lisp`/
; `lib/reason.lisp` — die Hälfte "Text -> Struktur" der Advice-Taker-Vision aus
; private/lisp-to-knowledge.md §6, bewusst ohne echtes NLP-Modell.
;
; `understand` nimmt eine *Wortliste*, keinen rohen String entgegen — my-lisp
; hat keine String-Primitive (split/Zeichenzugriff), und sie nur zur
; Tokenisierung von Sätzen hinzuzufügen würde die Rust-Built-in-Oberfläche
; genau dort vergrößern, wo das eigene CLAUDE.md des Projekts davon abrät.
; `(all planet have mass)` steht daher für "All planets have mass": der
; Aufrufer hat die Tokenisierung bereits erledigt und (entscheidend) den
; exakten Singular-Klassennamen gewählt, den die Wissensbasis verwendet —
; hier gibt es keine Morphologie (kein Pluralabbau, keine Verbkonjugation).
; Dies ist "kontrollierte" natürliche Sprache im strengen Sinn: drei feste
; Satzformen, strukturell abgeglichen, nicht statistisch geparst. Ein
; echtes `understand` für Freitext (LLM-gestützt) ist ein separater, späterer
; Schritt — siehe PLAN.md Schritt 9.6, bereits einmal bewusst entfernt wegen
; fehlender Sorgfalt (Tests, trilinguale Doku, versteckte Netzwerkaufrufe).
;
; Erkannte Formen:
;   (X is a Y)   / (X is an Y) / (X is Y)  -> Fakt:   ((Y X))
;   (X V Y)                                -> Fakt:   ((V X Y))
;   (all X have Y)                         -> Regel:  ((has (var w) Y) (X (var w)))
;
; Frageformen (über `understand-query`, Text -> Goal-Struktur -> Anfrage für
; `reason`):
;   (is X a Y)   / (is X an Y) / (is X Y)  -> Anfrage: (Y X)
;   (does X V Y)                           -> Anfrage: (V X Y)

(00001001 strip-article
  (00001000 (words)
    (00000111
      ((00000011 (00000101 words) (00000001 a))
       
       (00000110 words))
      ((00000011 (00000101 words) (00000001 an))
       
       (00000110 words))
      ((0100 (00000011 (00000101 words) (00000001 an)))
       words))))

(00001001 understand-is
  (00001000 (words)
    (10011100 ((subject (00000101 words))
          (after-is (strip-article (00110101 words))))
      (00100111 (00100111 (00000101 after-is) subject)))))

(00001001 understand-relation
  (00001000 (words)
    (00100111 (00100111 (00101111 words) (00000101 words) (00110000 words)))))

(00001001 understand-universal
  (00001000 (words)
    (10011100 ((subject-class (00101111 words))
          (property (00110110 words)))
      (00100111 (00100111 (00000001 has) (00100111 (00000001 var) (00000001 w)) property)
            (00100111 subject-class (00100111 (00000001 var) (00000001 w)))))))

(00001001 understand
  (00001000 (words)
    (00000111
      ((00000011 (00000101 words) (00000001 all))
       
       (understand-universal words))
      ((00000011 (00101111 words) (00000001 is))
       
       (understand-is words))
      ((0100 (00000011 (00101111 words) (00000001 is)))
       (understand-relation words)))))

; `understand-query` is the goal-shaped complement of `understand`: it turns
; a fixed *question* shape into a goal `(head . args)` that `reason` can be
; asked directly — "Is Socrates mortal?" -> `(mortal socrates)`. Unlike
; `understand`, which returns a list of clauses (facts/rules) to add to a
; knowledge base, this returns exactly one goal, the thing you *ask*.
; Controlled, structural, deterministic: no morphology, no network, no LLM.
;
; `understand-query` — доповнення у формі запиту до `understand`: перетворює
; фіксовану *форму запитання* на мету `(head . args)`, яку можна одразу
; поставити `reason` — "Is Socrates mortal?" -> `(mortal socrates)`. На
; відміну від `understand`, який повертає список clause (фактів/правил) для
; додавання до бази знань, цей повертає рівно одну мету — те, про що
; *запитують*. Контрольовано, структурно, детерміновано: без морфології,
; без мережі, без LLM.
;
; `understand-query` ist das Ziel-Gegenstück zu `understand`: es wandelt eine
; feste *Frageform* in ein Ziel `(head . args)` um, das direkt an `reason`
; gestellt werden kann — "Is Socrates mortal?" -> `(mortal socrates)`. Anders
; als `understand`, das eine Liste von Klauseln (Fakten/Regeln) liefert, die
; in die Wissensbasis aufgenommen werden, liefert dies genau ein Ziel — das,
; wonach man *fragt*. Kontrolliert, strukturell, deterministisch: keine
; Morphologie, kein Netz, kein LLM.
(00001001 understand-query-is
  (00001000 (words)
    (10011100 ((subject (00101111 words))
          (after (00110101 words)))
      (00100111 (00000101 (strip-article after)) subject))))

(00001001 understand-query-relation
  (00001000 (words)
    (00100111 (00110000 words) (00101111 words) (00110001 words))))

(00001001 understand-query
  (00001000 (words)
    (00000111
      ((00000011 (00000101 words) (00000001 is))
       
       (understand-query-is words))
      ((00000011 (00000101 words) (00000001 does))
       
       (understand-query-relation words))
      (t (00000001 ())))))
