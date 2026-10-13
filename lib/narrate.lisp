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
; Structural list-shape tests replace D6 LENGTH + D8 EQUAL and naked 2/3.
; All branches return exact D1; list data never acquires numeric truthiness.
(0011 narrate-proper-list?
  (0010 (value)
    (110
      ((010 value)
       (101 value (001 ())))
      ((010 (001 ()))
       (narrate-proper-list? (011 value))))))

(0011 narrate-list-exact-two?
  (0010 (value)
    (110
      ((0100 (narrate-proper-list? value))
       (101 (001 (0)) (001 (1))))
      ((010 value)
       (101 (001 (0)) (001 (1))))
      ((010 (011 value))
       (101 (001 (0)) (001 (1))))
      ((101 (011 (011 value)) (001 ()))
       (010 (001 ())))
      ((010 (001 ()))
       (101 (001 (0)) (001 (1)))))))

(0011 narrate-list-exact-three?
  (0010 (value)
    (110
      ((0100 (narrate-proper-list? value))
       (101 (001 (0)) (001 (1))))
      ((010 value)
       (101 (001 (0)) (001 (1))))
      ((010 (011 value))
       (101 (001 (0)) (001 (1))))
      ((010 (011 (011 value)))
       (101 (001 (0)) (001 (1))))
      ((101 (011 (011 (011 value))) (001 ()))
       (010 (001 ())))
      ((010 (001 ()))
       (101 (001 (0)) (001 (1)))))))

(0011 narrate-fact
  (0010 (fact)
    (110
      ((narrate-list-exact-two? fact)
       (1110 (1001 fact) (001 is) (001 a) (100 fact)))
      ((narrate-list-exact-three? fact)
       (1110 (1001 fact) (100 fact) (10011 fact)))
      ((010 ()) fact))))


(0011 provenance-goal (0010 (prov) (1001 prov)))
(0011 provenance-source (0010 (prov) (1001 (10011 prov))))
(0011 provenance-rule (0010 (prov) (1001 (100111 prov))))
(0011 provenance-derived-from (0010 (prov) (1001 (110110101 prov))))

(0011 narrate-derivation
  (0010 (derivations)
    (110
      
      ((010 derivations)  (001 ()))
      
      ((010 (011 derivations))  (narrate-provenance (100 derivations)))
      ((010 ()) (1111 (narrate-provenance (100 derivations))
                  (111 (001 and) (narrate-derivation (011 derivations))))))))

(0011 narrate-provenance
  (0010 (prov)
    (110
      ((101 (provenance-source prov) (001 fact)) (narrate-fact (provenance-rule prov)))
      ((010 ()) (1111 (narrate-fact (provenance-rule prov))
                  (111 (001 because) (narrate-derivation (provenance-derived-from prov))))))))

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
(0011 narrate-answer
  (0010 (goal proof)
    (001000 ((derivations (provenance-derived-from (101101111 proof))))
      (110
        
        ((010 derivations)  (narrate-fact goal))
        ((010 ()) (1111 (narrate-fact goal)
                   (111 (001 because) (narrate-derivation derivations))))))))

; ----------------------------------------------------------------------
; Structured reasoning-outcome presentation (B2)
; ----------------------------------------------------------------------
; Semantic meaning stays in lib/result-status.lisp. These functions only turn a
; canonical outcome into a controlled word/data list for presentation. They
; deliberately keep the status word visible so `unknown`, `disputed`,
; `blocked`, and `invalid` can never collapse back into one "cannot prove"
; sentence.

(0011 narrate-proved-outcome
  (0010 (outcome)
    (001000 ((statement (1001 outcome))
          (results (10011 outcome)))
      (110
        
        ((010 results)  (1110 (001 proved) statement (001 without-proof-result)))
        ((010 ())
         (1111
           (1110 (001 proved))
           (narrate-answer statement (1001 (100 results)))))))))

(0011 narrate-invalid-outcome-shape
  (0010 (outcome)
    (1110 (001 invalid) (001 outcome-shape) outcome)))

; Arity is a predicate, not a host truth value: each path returns exact D1.
; Keep the length/equality operations at their own exact widths: D6 LENGTH
; (000000), D8 EQUAL (11110111), with no flattening to a historical byte.
; Outcome arities are checked structurally. The requested size is encoded by
; the called predicate, not as an unqualified numeric argument.


(0011 narrate-outcome
  (0010 (outcome)
    (110
      
      ((010 outcome)  (narrate-invalid-outcome-shape outcome))
      ((0100 (result-proper-list? outcome))
       (narrate-invalid-outcome-shape outcome))
      ((0100 (010 (100 outcome)))
       (1110 (001 invalid) (001 outcome-tag) (100 outcome)))
      ((0100 (010 (100 outcome)))
       (1110 (001 invalid) (001 outcome-tag) (100 outcome)))
      ((110101100 (100 outcome)) 
       (1110 (001 invalid) (001 outcome-tag) (100 outcome)))
      ((101 (100 outcome) (001 proved))
       (110
         ((narrate-list-exact-three? outcome) (narrate-proved-outcome outcome))
         ((010 ()) (narrate-invalid-outcome-shape outcome))))
      ((101 (100 outcome) (001 unknown))
       (110
         ((narrate-list-exact-two? outcome)
          (1110
            (001 unknown)
            (001 because)
            (001 no-proof-found-for)
            (1001 outcome)))
         ((010 ()) (narrate-invalid-outcome-shape outcome))))
      ((101 (100 outcome) (001 partial))
       (110
         ((narrate-list-exact-three? outcome)
          (1110
            (001 partial)
            (001 value)
            (1001 outcome)
            (001 bound)
            (10011 outcome)))
         ((010 ()) (narrate-invalid-outcome-shape outcome))))
      ((101 (100 outcome) (001 blocked))
       (110
         ((narrate-list-exact-two? outcome)
          (1110
            (001 blocked)
            (001 because)
            (1001 outcome)))
         ((010 ()) (narrate-invalid-outcome-shape outcome))))
      ((101 (100 outcome) (001 disputed))
       (110
         ((narrate-list-exact-two? outcome)
          (1110
            (001 disputed)
            (001 because)
            (001 both-sides-have-evidence)
            (1001 outcome)))
         ((010 ()) (narrate-invalid-outcome-shape outcome))))
      ((101 (100 outcome) (001 invalid))
       (110
         ((narrate-list-exact-three? outcome)
          (1110
            (001 invalid)
            (001 because)
            (1001 outcome)
            (001 payload)
            (10011 outcome)))
         ((010 ()) (narrate-invalid-outcome-shape outcome))))
      ((010 ())
       (1110 (001 invalid) (001 outcome-tag) (100 outcome))))))
