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
(00001001 narrate-fact
  (00001000 (fact)
    (00000111
      ((00011100 (00101000 fact) 2)  (00100111 (00101111 fact) (00000001 is) (00000001 a) (00000101 fact)))
      ((00011100 (00101000 fact) 3)  (00100111 (00101111 fact) (00000101 fact) (00110000 fact)))
      (1 fact))))


(00001001 provenance-goal (00001000 (prov) (00101111 prov)))
(00001001 provenance-source (00001000 (prov) (00101111 (00110000 prov))))
(00001001 provenance-rule (00001000 (prov) (00101111 (00110110 prov))))
(00001001 provenance-derived-from (00001000 (prov) (00101111 (00110010 prov))))

(00001001 narrate-derivation
  (00001000 (derivations)
    (00000111
      
      ((00000010 derivations)  (00000001 ()))
      
      ((00000010 (00000110 derivations))  (narrate-provenance (00000101 derivations)))
      (1 (00101001 (narrate-provenance (00000101 derivations))
                  (00000100 (00000001 and) (narrate-derivation (00000110 derivations))))))))

(00001001 narrate-provenance
  (00001000 (prov)
    (00000111
      ((00000011 (provenance-source prov) (00000001 fact)) (narrate-fact (provenance-rule prov)))
      (1 (00101001 (narrate-fact (provenance-rule prov))
                  (00000100 (00000001 because) (narrate-derivation (provenance-derived-from prov))))))))

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
(00001001 narrate-answer
  (00001000 (goal proof)
    (10011100 ((derivations (provenance-derived-from (10000100 proof))))
      (00000111
        
        ((00000010 derivations)  (narrate-fact goal))
        (1 (00101001 (narrate-fact goal)
                   (00000100 (00000001 because) (narrate-derivation derivations))))))))

; ----------------------------------------------------------------------
; Structured reasoning-outcome presentation (B2)
; ----------------------------------------------------------------------
; Semantic meaning stays in lib/result-status.lisp. These functions only turn a
; canonical outcome into a controlled word/data list for presentation. They
; deliberately keep the status word visible so `unknown`, `disputed`,
; `blocked`, and `invalid` can never collapse back into one "cannot prove"
; sentence.

(00001001 narrate-proved-outcome
  (00001000 (outcome)
    (10011100 ((statement (00101111 outcome))
          (results (00110000 outcome)))
      (00000111
        
        ((00000010 results)  (00100111 (00000001 proved) statement (00000001 without-proof-result)))
        (1
         (00101001
           (00100111 (00000001 proved))
           (narrate-answer statement (00101111 (00000101 results)))))))))

(00001001 narrate-invalid-outcome-shape
  (00001000 (outcome)
    (00100111 (00000001 invalid) (00000001 outcome-shape) outcome)))

(00001001 narrate-outcome-arity?
  (00001000 (outcome expected)
    (00000111
      ((00100001 (result-proper-list? outcome)) (00000001 ()))
      ((00011100 (00101000 outcome) expected)  t)

      (1 (00000001 ())))))

(00001001 narrate-outcome
  (00001000 (outcome)
    (00000111
      
      ((00000010 outcome)  (narrate-invalid-outcome-shape outcome))
      ((00100001 (result-proper-list? outcome))
       (narrate-invalid-outcome-shape outcome))
      ((0100 (00000010 (00000101 outcome)))
       (00100111 (00000001 invalid) (00000001 outcome-tag) (00000101 outcome)))
      ((0100 (00000010 (00000101 outcome)))
       (00100111 (00000001 invalid) (00000001 outcome-tag) (00000101 outcome)))
      ((00100011 (00000101 outcome)) 
       (00100111 (00000001 invalid) (00000001 outcome-tag) (00000101 outcome)))
      ((00000011 (00000101 outcome) (00000001 proved))
       (00000111
         ((narrate-outcome-arity? outcome 3) (narrate-proved-outcome outcome))
         (1 (narrate-invalid-outcome-shape outcome))))
      ((00000011 (00000101 outcome) (00000001 unknown))
       (00000111
         ((narrate-outcome-arity? outcome 2)
          (00100111
            (00000001 unknown)
            (00000001 because)
            (00000001 no-proof-found-for)
            (00101111 outcome)))
         (1 (narrate-invalid-outcome-shape outcome))))
      ((00000011 (00000101 outcome) (00000001 partial))
       (00000111
         ((narrate-outcome-arity? outcome 3)
          (00100111
            (00000001 partial)
            (00000001 value)
            (00101111 outcome)
            (00000001 bound)
            (00110000 outcome)))
         (1 (narrate-invalid-outcome-shape outcome))))
      ((00000011 (00000101 outcome) (00000001 blocked))
       (00000111
         ((narrate-outcome-arity? outcome 2)
          (00100111
            (00000001 blocked)
            (00000001 because)
            (00101111 outcome)))
         (1 (narrate-invalid-outcome-shape outcome))))
      ((00000011 (00000101 outcome) (00000001 disputed))
       (00000111
         ((narrate-outcome-arity? outcome 2)
          (00100111
            (00000001 disputed)
            (00000001 because)
            (00000001 both-sides-have-evidence)
            (00101111 outcome)))
         (1 (narrate-invalid-outcome-shape outcome))))
      ((00000011 (00000101 outcome) (00000001 invalid))
       (00000111
         ((narrate-outcome-arity? outcome 3)
          (00100111
            (00000001 invalid)
            (00000001 because)
            (00101111 outcome)
            (00000001 payload)
            (00110000 outcome)))
         (1 (narrate-invalid-outcome-shape outcome))))
      (1
       (00100111 (00000001 invalid) (00000001 outcome-tag) (00000101 outcome))))))
