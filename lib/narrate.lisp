; The second half of the "text <-> structure" bridge from
; private/lisp-to-knowledge.md §6 — `lib/understand.lisp` goes text-shaped
; word list -> knowledge clause; `narrate` goes the other way, structure ->
; text-shaped word list. Same controlled, non-statistical spirit: fixed
; structural shapes, matched by list length and position, not a real NLP
; model. `narrate-fact` is the exact structural inverse of
; `understand-is`/`understand-relation` — round-tripping a sentence through
; `understand` then `narrate-fact` returns the original words.
;
; `narrate-provenance` explains *why*, walking a `provenance` record
; (lib/reason.lisp) into a word list joined by `because`/`and`. It narrates
; each node's `rule` field, not its `goal` field: a proof-tree node's
; `goal` can still carry unresolved `(var name)` placeholders (see
; `explain-proof` in lib/reason.lisp, which has this same property already —
; not a new limitation introduced here), while `rule` is the concrete
; matched fact for every leaf. Deeper rule applications can still surface
; an unresolved variable if that particular rule's own head wasn't fully
; grounded by the point of derivation; this is documented, not hidden.
;
; Друга половина мосту "text <-> structure" з private/lisp-to-knowledge.md
; §6 — `lib/understand.lisp` йде від списку слів текстової форми до
; знаннєвого clause; `narrate` — у зворотний бік, від структури до списку
; слів текстової форми. Той самий контрольований, нестатистичний дух:
; фіксовані структурні форми, зіставлені за довжиною й позицією списку, не
; справжня NLP-модель. `narrate-fact` — точна структурна обернена функція
; до `understand-is`/`understand-relation`: пропустивши речення через
; `understand`, а потім `narrate-fact`, отримуємо ті самі слова назад.
;
; `narrate-provenance` пояснює *чому*, обходячи запис `provenance`
; (lib/reason.lisp) у список слів, з'єднаний `because`/`and`. Наратує поле
; `rule` кожного вузла, не поле `goal`: `goal` вузла дерева доведення може
; досі нести нерозв'язані плейсхолдери `(var name)` (та сама властивість,
; що вже є в `explain-proof` з lib/reason.lisp — не нове обмеження, введене
; тут), тоді як `rule` — конкретний зіставлений факт для кожного листка.
; Глибші застосування правил усе ще можуть показати нерозв'язану змінну,
; якщо голова саме цього правила не була повністю конкретизована на момент
; виведення; це задокументовано, не приховано.
;
; Die zweite Hälfte der Brücke "Text <-> Struktur" aus
; private/lisp-to-knowledge.md §6 — `lib/understand.lisp` geht von einer
; textförmigen Wortliste zu einem Wissens-Clause; `narrate` geht den
; anderen Weg, von Struktur zu textförmiger Wortliste. Derselbe
; kontrollierte, nicht-statistische Geist: feste strukturelle Formen, nach
; Listenlänge und -position abgeglichen, kein echtes NLP-Modell.
; `narrate-fact` ist die exakte strukturelle Umkehrung von
; `understand-is`/`understand-relation`: ein Satz, der durch `understand`
; und dann `narrate-fact` geschickt wird, liefert dieselben Wörter zurück.
;
; `narrate-provenance` erklärt *warum*, indem es einen `provenance`-Datensatz
; (lib/reason.lisp) in eine mit `because`/`and` verbundene Wortliste
; übersetzt. Es erzählt das `rule`-Feld jedes Knotens, nicht sein
; `goal`-Feld: das `goal` eines Beweisbaum-Knotens kann noch ungelöste
; `(var name)`-Platzhalter tragen (dieselbe Eigenschaft, die `explain-proof`
; in lib/reason.lisp bereits hat — keine hier neu eingeführte Einschränkung),
; während `rule` für jedes Blatt der konkrete abgeglichene Fakt ist.
; Tiefere Regelanwendungen können immer noch eine ungelöste Variable
; zeigen, wenn der Kopf genau dieses Regel zum Zeitpunkt der Ableitung
; nicht vollständig konkretisiert war; dies ist dokumentiert, nicht
; verborgen.
(def narrate-fact
  (lambda (fact)
    (cond
      ((= (length fact) 2) 1 (list (second fact) (quote is) (quote a) (car fact)))
      ((= (length fact) 3) 1 (list (second fact) (car fact) (third fact)))
      (t fact))))


(def provenance-goal (lambda (prov) (second prov)))
(def provenance-source (lambda (prov) (second (third prov))))
(def provenance-rule (lambda (prov) (second (cadddr prov))))
(def provenance-derived-from (lambda (prov) (second (fifth prov))))

(def narrate-derivation
  (lambda (derivations)
    (cond
      ((atom? derivations) () (quote ()))
      ((atom? derivations) (1) (quote ()))
      ((atom? (cdr derivations)) () (narrate-provenance (car derivations)))
      ((atom? (cdr derivations)) (1) (narrate-provenance (car derivations)))
      (t (append (narrate-provenance (car derivations))
                  (cons (quote and) (narrate-derivation (cdr derivations))))))))

(def narrate-provenance
  (lambda (prov)
    (cond
      ((eq? (provenance-source prov) (quote fact)) (narrate-fact (provenance-rule prov)))
      (t (append (narrate-fact (provenance-rule prov))
                  (cons (quote because) (narrate-derivation (provenance-derived-from prov))))))))

; `narrate-answer` grounds the conclusion with the caller's actual query while
; retaining the proof's real premises. A renamed rule head can contain
; internal `(var (name . depth))` placeholders; the successful ground query
; is the honest user-facing answer, and the proof children remain the honest
; explanation of why it holds.
;
; `narrate-answer` конкретизує висновок фактичним запитом викликача, але
; зберігає справжні передумови доведення. Перейменована голова правила може
; містити внутрішні плейсхолдери `(var (name . depth))`; успішний конкретний
; запит є чесною відповіддю для користувача, а дочірні вузли доведення —
; чесним поясненням, чому вона істинна.
;
; `narrate-answer` konkretisiert die Schlussfolgerung mit der tatsächlichen
; Anfrage des Aufrufers und behält die echten Beweisprämissen bei. Ein
; umbenannter Regelkopf kann interne `(var (name . depth))`-Platzhalter
; enthalten; die erfolgreiche konkrete Anfrage ist die ehrliche Antwort für
; den Benutzer, die Beweiskinder bleiben die ehrliche Begründung dafür.
(def narrate-answer
  (lambda (goal proof)
    (let ((derivations (provenance-derived-from (provenance proof))))
      (cond
        ((atom? derivations) () (narrate-fact goal))
        ((atom? derivations) (1) (narrate-fact goal))
        (t (append (narrate-fact goal)
                   (cons (quote because) (narrate-derivation derivations))))))))

; ----------------------------------------------------------------------
; Structured reasoning-outcome presentation (B2)
; ----------------------------------------------------------------------
; Semantic meaning stays in lib/result-status.lisp. These functions only turn a
; canonical outcome into a controlled word/data list for presentation. They
; deliberately keep the status word visible so `unknown`, `disputed`,
; `blocked`, and `invalid` can never collapse back into one "cannot prove"
; sentence.

(def narrate-proved-outcome
  (lambda (outcome)
    (let ((statement (second outcome))
          (results (third outcome)))
      (cond
        ((atom? results) () (list (quote proved) statement (quote without-proof-result)))
        ((atom? results) (1) (list (quote proved) statement (quote without-proof-result)))
        (t
         (append
           (list (quote proved))
           (narrate-answer statement (second (car results)))))))))

(def narrate-invalid-outcome-shape
  (lambda (outcome)
    (list (quote invalid) (quote outcome-shape) outcome)))

(def narrate-outcome-arity?
  (lambda (outcome expected)
    (cond
      ((not? (result-proper-list? outcome)) (quote ()))
      ((= (length outcome) expected) 1 t)

      (t (quote ())))))

(def narrate-outcome
  (lambda (outcome)
    (cond
      ((atom? outcome) () (narrate-invalid-outcome-shape outcome))
      ((atom? outcome) (1) (narrate-invalid-outcome-shape outcome))
      ((not? (result-proper-list? outcome))
       (narrate-invalid-outcome-shape outcome))
      ((atom? (car outcome)) (0)
       (list (quote invalid) (quote outcome-tag) (car outcome)))
      ((atom? (car outcome)) ()
       (list (quote invalid) (quote outcome-tag) (car outcome)))
      ((symbol? (car outcome)) (class-membership symbol nonmember)
       (list (quote invalid) (quote outcome-tag) (car outcome)))
      ((eq? (car outcome) (quote proved))
       (cond
         ((narrate-outcome-arity? outcome 3) (narrate-proved-outcome outcome))
         (t (narrate-invalid-outcome-shape outcome))))
      ((eq? (car outcome) (quote unknown))
       (cond
         ((narrate-outcome-arity? outcome 2)
          (list
            (quote unknown)
            (quote because)
            (quote no-proof-found-for)
            (second outcome)))
         (t (narrate-invalid-outcome-shape outcome))))
      ((eq? (car outcome) (quote partial))
       (cond
         ((narrate-outcome-arity? outcome 3)
          (list
            (quote partial)
            (quote value)
            (second outcome)
            (quote bound)
            (third outcome)))
         (t (narrate-invalid-outcome-shape outcome))))
      ((eq? (car outcome) (quote blocked))
       (cond
         ((narrate-outcome-arity? outcome 2)
          (list
            (quote blocked)
            (quote because)
            (second outcome)))
         (t (narrate-invalid-outcome-shape outcome))))
      ((eq? (car outcome) (quote disputed))
       (cond
         ((narrate-outcome-arity? outcome 2)
          (list
            (quote disputed)
            (quote because)
            (quote both-sides-have-evidence)
            (second outcome)))
         (t (narrate-invalid-outcome-shape outcome))))
      ((eq? (car outcome) (quote invalid))
       (cond
         ((narrate-outcome-arity? outcome 3)
          (list
            (quote invalid)
            (quote because)
            (second outcome)
            (quote payload)
            (third outcome)))
         (t (narrate-invalid-outcome-shape outcome))))
      (t
       (list (quote invalid) (quote outcome-tag) (car outcome))))))
