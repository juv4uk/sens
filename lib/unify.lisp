; A small symbolic-AI primitive: unification, the pattern-matching engine
; underneath backward-chaining/Prolog-style reasoning — the kind of symbolic
; inference McCarthy's 1958 "Advice Taker" proposal was written for, before
; Lisp itself even existed to build it in.
;
; Logic variables are represented as `(var name)` — a two-element list, not
; a bare symbol — because `eq` only accepts atoms, and there is no
; symbol?/numberp? primitive to ask "is this atom a variable by naming
; convention" (see lib/meta-eval.lisp's header comment for the same
; constraint solved a different way). `(var name)` sidesteps it: `var?`
; checks `(eq (car term) 'var)`, always atom-safe; two variables compare by
; `(equal? (second a) (second b))`, comparing their names, which might be
; symbols or structured pairs (like `(x . 3)` when standardizing apart). 
; Construct one with `(logic-var 'x)`.
;
; With occurs-check: unifying `?x` with a term containing `?x` (e.g. `(f ?x)`)
; correctly fails, preventing infinite structures from being generated and
; preserving the engine's stability during complex logic inference.
;
; Невеликий примітив символьного AI: unification — механізм зіставлення з
; шаблоном, що лежить під backward-chaining/Prolog-подібними міркуваннями —
; той самий вид символьного висновування, для якого писалась пропозиція
; "Advice Taker" Маккарті 1958 року, ще до появи самого Lisp, яким її можна
; було б побудувати.
;
; Логічні змінні представлені як `(var name)` — список із двох елементів,
; не голий символ — бо `eq` приймає лише атоми, а примітиву
; symbol?/numberp?, щоб спитати "чи цей атом — змінна за угодою
; іменування", немає (див. header-коментар lib/meta-eval.lisp — те саме
; обмеження, вирішене інакше). `(var name)` обходить це: `var?` перевіряє
; `(eq (car term) 'var)`, завжди безпечно для атомів; дві змінні
; порівнюються через `(equal? (second a) (second b))` — порівняння їхніх
; імен, які можуть бути символами або структурованими парами (як `(x . 3)` 
; при standardizing apart). Створюється через `(logic-var 'x)`.
;
; З occurs-check: унікація `?x` з термом, що містить `?x` (напр. `(f ?x)`)
; коректно відхиляється, що запобігає створенню нескінченних структур і
; зберігає стабільність рушія під час складного логічного висновування.
;
; Ein kleines symbolisches KI-Primitiv: Unifikation — die
; Mustervergleichs-Engine hinter Backward-Chaining-/Prolog-artigem
; Schließen — genau die Art symbolischer Inferenz, für die McCarthys
; "Advice Taker"-Vorschlag von 1958 geschrieben wurde, bevor Lisp selbst
; existierte, um sie zu bauen.
;
; Logikvariablen werden als `(var name)` dargestellt — eine zweielementige
; Liste, kein bloßes Symbol — weil `eq` nur Atome akzeptiert und es kein
; symbol?/numberp?-Primitiv gibt, um zu fragen "ist dieses Atom nach
; Namenskonvention eine Variable" (siehe den Header-Kommentar von
; lib/meta-eval.lisp — dieselbe Einschränkung, anders gelöst). `(var name)`
; umgeht das: `var?` prüft `(eq (car term) 'var)`, immer atomsicher; zwei
; Variablen werden über `(equal? (second a) (second b))` verglichen, dem
; Vergleich ihrer Namen, die Symbole oder strukturierte Paare sein können
; (wie `(x . 3)` beim standardizing apart). Erzeugt wird eine mit `(logic-var 'x)`.
;
; Mit Occurs-Check: Das Unifizieren von `?x` mit einem Term, der `?x`
; enthält (z. B. `(f ?x)`), schlägt korrekt fehl, verhindert die Erzeugung
; unendlicher Strukturen und erhält die Stabilität der Engine bei komplexer
; logischer Inferenz.

(00001011 logic-var
  (00001000 (name)
    (00100111 (00000001 var) name)))

; Guards the `eq` with `(atom (car term))` first: `term` reaching the final
; branch is already known non-atom, but its `car` can itself be a compound
; list (e.g. unifying nested structures recurses into pieces like
; `((var x) bob)`, whose `car` is `(var x)` — a list, not a symbol) — `eq`
; would error on that instead of just correctly answering "not a variable".
; Захищає `eq` спершу через `(atom (car term))`: `term`, що дійшов до
; останньої гілки, вже точно не атом, але його `car` сам може бути
; складеним списком (напр. унікація вкладених структур рекурсує в шматки
; на кшталт `((var x) bob)`, чий `car` — `(var x)`, список, не символ) —
; `eq` впав би на цьому замість просто коректно відповісти "не змінна".
; Sichert das `eq` zuerst mit `(atom (car term))` ab: `term`, das den
; letzten Zweig erreicht, ist bereits bekanntermaßen kein Atom, aber sein
; `car` kann selbst eine zusammengesetzte Liste sein (z. B. rekursiert die
; Unifikation verschachtelter Strukturen in Teile wie `((var x) bob)`,
; dessen `car` `(var x)` ist — eine Liste, kein Symbol) — `eq` würde dabei
; einen Fehler werfen statt einfach korrekt "keine Variable" zu antworten.
(00001011 var?
  (00001000 (term)
    (00000111
      
      ((00000010 term)  (00000001 ()))
      
      ((00000010 (00000101 term))  (00000011 (00000101 term) (00000001 var)))
      )))

; subst is an alist of (name . term) pairs, keyed by the variable's
; name — never by the `(var name)` pair itself. We use `equal?` instead
; of `eq` because names can be structures like `(x . 3)` from renaming.
(00001011 lookup-subst
  (00001000 (variable bindings)
    (00000111
      
      ((00000010 bindings)  variable)
      ((00100010 (00000101 (00000101 bindings)) (00101111 variable)) (00000110 (00000101 bindings)))
      (1 (lookup-subst variable (00000110 bindings))))))

(00001011 extend-subst
  (00001000 (variable term bindings)
    (00000100 (00000100 (00101111 variable) term) bindings)))

; One-level dereference: if `term` is a bound variable, follow exactly one
; binding; anything else (including a still-unbound variable, or a
; compound term) is returned as-is. `unify` and `apply-subst` each do their
; own recursion into compound terms, so `walk` doesn't need to go deeper.
(00001011 walk
  (00001000 (term bindings)
    (00000111
      ((10001001 term) (walk-resolved term (lookup-subst term bindings) bindings))
      (1 term))))

(00001011 walk-resolved
  (00001000 (term resolved bindings)
    (00000111
      ((10001001 resolved)
       (00000111
         ((00100010 (00101111 resolved) (00101111 term)) term)
         (1 (10001011 resolved bindings))))
      (1 resolved))))

; Same guard shape as `var?`: once `subst` gains bindings it's a non-empty
; alist — a list, not an atom — so `(eq subst 'fail)` would itself error
; instead of just correctly answering "no, it's not the fail atom".
; Той самий патерн захисту, що й у `var?`: щойно `subst` отримує зв'язки,
; він стає непорожнім alist — списком, не атомом — тож `(eq subst 'fail)`
; сам би впав замість просто коректно відповісти "ні, це не атом fail".
; Dieselbe Schutzform wie bei `var?`: sobald `subst` Bindungen erhält, ist
; es eine nichtleere Alist — eine Liste, kein Atom — daher würde
; `(eq subst 'fail)` selbst einen Fehler werfen statt einfach korrekt
; "nein, es ist nicht das fail-Atom" zu antworten.
(00001011 unify
  (00001000 (a b bindings)
    (00000111
      ((failed-subst? bindings) (00000001 fail))
      (1 (unify-walked (10001011 a bindings) (10001011 b bindings) bindings)))))

(00001011 failed-subst?
  (00001000 (bindings)
    (00000111
      
      ((00000010 bindings)  (00000011 bindings (00000001 fail)))
      )))

(00001011 unify-walked
  (00001000 (a b bindings)
    (00000111
      ((10001001 a) (unify-var a b bindings))
      ((10001001 b) (unify-var b a bindings))
      
      ((00000010 a)  (00000111 
                                  ((00000010 b)  (00000111 ((00000011 a b) bindings) (1 (00000001 fail)))) (1 (00000001 fail))))
      
      ((00000010 b)  (00000001 fail))
      (1 (10000111 (00000110 a) (00000110 b) (10000111 (00000101 a) (00000101 b) bindings))))))

(00001011 occurs-check?
  (00001000 (variable term bindings)
    (10011100 ((resolved (10001011 term bindings)))
      (00000111
        ((10001001 resolved) (00100010 (00101111 variable) (00101111 resolved)))
        
        ((00000010 resolved)  (00000001 ()))
        (1 (00000111
             ((10001100 variable (00000101 resolved) bindings) t)
             (1 (10001100 variable (00000110 resolved) bindings))))))))

(00001011 occurs-check occurs-check?)

(00001011 unify-var
  (00001000 (variable term bindings)
    (00000111
      ((10001001 term)
       (00000111
         ((00100010 (00101111 variable) (00101111 term)) bindings)
         (1 (extend-subst variable term bindings))))
      ((10001100 variable term bindings) (00000001 fail))
      (1 (extend-subst variable term bindings)))))

; Fully resolves every variable in `term` (recursively, through chained
; bindings and into nested lists) against `subst` — what you call once
; unification succeeds, to read out a readable answer instead of raw
; `(var ...)` markers and substitution internals.
(00001011 apply-subst
  (00001000 (term bindings)
    (apply-subst-walked (10001011 term bindings) bindings)))

(00001011 apply-subst-walked
  (00001000 (term bindings)
    (00000111
      
      ((00000010 term)  term)
      (1 (00000100 (10001010 (00000101 term) bindings) (10001010 (00000110 term) bindings))))))

; The shared kernel behind proving/matching a *conjunction* of conditions:
; process one condition at a time, threading a `state` value (usually a
; substitution, or something built around one) through the rest via
; `try-one` — a caller-supplied strategy for "how do I satisfy a single
; condition from this state". Every combination `try-one` returns for the
; first condition branches into its own attempt at the remaining ones,
; collecting every fully-successful final state.
;
; Both `lib/reason.lisp`'s backward-chaining (proving each condition by
; recursively searching rules, threading `(subst . proof-so-far)`) and
; `lib/forward.lisp`'s forward-chaining (matching each condition against an
; explicit fact list, threading a bare substitution) do exactly this shape
; of search — one written from goals outward, the other from facts inward.
; `thread-conjunction` is the piece they share; `try-one` is the only part
; that differs, kept as a plain function argument rather than duplicated
; conjunction-walking logic in each file.
;
; Спільне ядро доведення/зіставлення *кон'юнкції* умов: обробляє одну умову
; за раз, протягуючи значення `state` (зазвичай підстановку, або щось
; побудоване навколо неї) крізь решту через `try-one` — надану викликачем
; стратегію "як задовольнити одну умову з цього стану". Кожна комбінація,
; яку `try-one` повертає для першої умови, розгалужується у власну спробу
; для решти, збираючи всі повністю успішні фінальні стани.
;
; І backward-chaining `lib/reason.lisp` (доведення кожної умови рекурсивним
; пошуком по правилах, протягування `(підстановка . доведення-досі)`), і
; forward-chaining `lib/forward.lisp` (зіставлення кожної умови з явним
; списком фактів, протягування голої підстановки) роблять точно таку саму
; форму пошуку — один написаний від цілей назовні, інший від фактів
; усередину. `thread-conjunction` — та частина, яку вони ділять; `try-one`
; — єдине, що відрізняється, передане звичайним аргументом-функцією, а не
; продубльоване як логіка обходу кон'юнкції в кожному файлі.
;
; Der gemeinsame Kern hinter dem Beweisen/Abgleichen einer *Konjunktion*
; von Bedingungen: verarbeitet eine Bedingung nach der anderen und fädelt
; einen `state`-Wert (meist eine Substitution oder etwas darum Gebautes)
; durch die restlichen mittels `try-one` — einer vom Aufrufer bereitgestellten
; Strategie für "wie erfülle ich eine einzelne Bedingung aus diesem Zustand".
; Jede Kombination, die `try-one` für die erste Bedingung liefert, verzweigt
; in einen eigenen Versuch für die restlichen und sammelt alle vollständig
; erfolgreichen Endzustände.
;
; Sowohl das Backward-Chaining von `lib/reason.lisp` (Beweisen jeder Bedingung
; durch rekursive Regelsuche, Fädeln von `(substitution . beweis-bisher)`)
; als auch das Forward-Chaining von `lib/forward.lisp` (Abgleich jeder
; Bedingung gegen eine explizite Faktenliste, Fädeln einer bloßen
; Substitution) folgen genau dieser Suchform — eine von Zielen nach außen
; geschrieben, die andere von Fakten nach innen. `thread-conjunction` ist
; der Teil, den sie teilen; `try-one` ist das Einzige, das sich
; unterscheidet, als gewöhnliches Funktionsargument übergeben statt als
; duplizierte Konjunktions-Durchlauflogik in jeder Datei.
(00001011 thread-conjunction
  (00001000 (conditions state try-one)
    (00000111
      
      ((00000010 conditions)  (00100111 state))
      (1 (thread-conjunction-branches (00000110 conditions) try-one (try-one (00000101 conditions) state))))))

(00001011 thread-conjunction-branches
  (00001000 (remaining try-one states)
    (00000111
      
      ((00000010 states)  (00000001 ()))
      (1 (00101001 (thread-conjunction remaining (00000101 states) try-one)
                 (thread-conjunction-branches remaining try-one (00000110 states)))))))
