; A forward-chaining rule engine (CLIPS-style: working memory of facts +
; pattern/action rules), the other half of classic symbolic AI from
; `lib/reason.lisp`'s backward-chaining (Prolog-style) engine. Grown natively
; in my-lisp instead of embedding the actual CLIPS C library, the same
; choice this project makes everywhere: reuse the existing kernel
; (`unify`/`apply-subst` from `lib/unify.lisp`) rather than adding a new
; dependency or a new Rust primitive.
;
; Step 1 (deliberately small, by explicit agreement before writing this):
; one working-memory list, and firing exactly *one* rule against exactly
; *one* fact. No agenda, no fixpoint loop over the whole working memory, no
; retract, no truth maintenance — those are later steps, each to be agreed
; on before starting, same as every other step in this project.
;
; A rule is `(pattern template)`: `pattern` may contain `(var name)` logic
; variables (see `lib/unify.lisp`); `template` is the new fact to produce,
; typically reusing those same variables so `fire-rule` can substitute in
; whatever `pattern` bound them to.
;
; Рушій forward-chaining (у стилі CLIPS: working memory фактів + правила
; шаблон/дія) — інша половина класичного символьного AI, ніж
; backward-chaining (Prolog-подібний) рушій у `lib/reason.lisp`. Вирощений
; нативно в my-lisp замість вбудовування самої C-бібліотеки CLIPS — той
; самий вибір, що й скрізь у проєкті: перевикористати наявне ядро
; (`unify`/`apply-subst` з `lib/unify.lisp`), а не додавати нову залежність чи
; новий Rust-примітив.
;
; Крок 1 (свідомо маленький, за явною домовленістю перед написанням): один
; список working memory, і застосування рівно *одного* правила до рівно
; *одного* факту. Без agenda, без fixpoint-циклу по всій working memory,
; без retract, без truth maintenance — це пізніші кроки, кожен узгоджується
; окремо перед стартом, як і решта кроків цього проєкту.
;
; Правило — це `(pattern template)`: `pattern` може містити логічні змінні
; `(var name)` (див. `lib/unify.lisp`); `template` — новий факт, зазвичай з
; тими самими змінними, щоб `fire-rule` міг підставити те, що `pattern`
; зв'язав.
;
; Eine Forward-Chaining-Regel-Engine (im CLIPS-Stil: Working Memory aus
; Fakten + Muster-/Aktionsregeln) — die andere Hälfte klassischer
; symbolischer KI neben der Backward-Chaining-Engine (Prolog-artig) in
; `lib/reason.lisp`. Nativ in my-lisp gewachsen statt die eigentliche
; CLIPS-C-Bibliothek einzubetten — dieselbe Wahl, die dieses Projekt überall
; trifft: den vorhandenen Kern wiederverwenden (`unify`/`apply-subst` aus
; `lib/unify.lisp`) statt eine neue Abhängigkeit oder ein neues Rust-Primitiv
; hinzuzufügen.
;
; Schritt 1 (bewusst klein, nach ausdrücklicher Absprache vor dem
; Schreiben): eine Working-Memory-Liste, und genau *eine* Regel auf genau
; *einen* Fakt angewendet. Keine Agenda, keine Fixpunkt-Schleife über die
; gesamte Working Memory, kein Retract, keine Truth Maintenance — das sind
; spätere Schritte, jeder einzeln vor Beginn abzustimmen, wie jeder andere
; Schritt in diesem Projekt.
;
; Eine Regel ist `(pattern template)`: `pattern` kann Logikvariablen
; `(var name)` enthalten (siehe `lib/unify.lisp`); `template` ist der neue zu
; erzeugende Fakt, typischerweise mit denselben Variablen, damit
; `fire-rule` einsetzen kann, woran `pattern` sie gebunden hat.

(00001001 *working-memory* (00000001 ()))

(00001010 assert-fact! (fact)
  (00100111 (00000001 def) (00000001 *working-memory*) (00100111 (00000001 00000100) fact (00000001 *working-memory*))))

; Tries to unify a rule's pattern against a single fact. On success,
; returns the rule's template with the resulting bindings substituted in
; — the new fact this rule application would produce. On failure, returns
; `'no-match` rather than `'()` — an empty list would be ambiguous with a
; template that legitimately evaluates to `()`.
(00001001 fire-rule
  (00001000 (rule fact)
    (10011100 ((pattern (00000101 rule))
          (template (00101111 rule)))
      (10011100 ((bindings (10000111 pattern fact (00000001 ()))))
        (00000111
          ((failed-subst? bindings) (00000001 no-match))
          (t (10001010 template bindings)))))))

; Step 2: apply one rule to every fact in a list, collecting the new facts
; it produces. Still just one rule (not the whole rule set) and still no
; assertion back into `*working-memory*` or fixpoint looping — this stays a
; pure function over an explicit fact list, same shape as `count-usage-list`
; in `lib/reason.lisp`. `no-match` results are silently dropped, same as a
; failed match dropping out of `prove-goal`'s search in the backward-chaining
; engine.
;
; Крок 2: застосувати одне правило до кожного факту в списку, зібравши нові
; факти, які воно породжує. Досі лише одне правило (не весь набір правил) і
; досі без запису назад у `*working-memory*` чи fixpoint-циклу — це чиста
; функція над явним списком фактів, той самий підхід, що й `count-usage-list`
; у `lib/reason.lisp`. Результати `no-match` мовчки відкидаються, так само як
; невдале зіставлення випадає з пошуку `prove-goal` у backward-chaining рушії.
;
; Schritt 2: eine Regel auf jeden Fakt einer Liste anwenden und die dabei
; erzeugten neuen Fakten sammeln. Immer noch nur eine Regel (nicht das ganze
; Regelwerk) und immer noch keine Rückschreibung in `*working-memory*` oder
; Fixpunkt-Schleife — dies bleibt eine reine Funktion über eine explizite
; Faktenliste, dieselbe Form wie `count-usage-list` in `lib/reason.lisp`.
; `no-match`-Ergebnisse werden stillschweigend verworfen, genau wie ein
; fehlgeschlagener Abgleich aus der Suche von `prove-goal` in der
; Backward-Chaining-Engine herausfällt.
; Guards the `eq` with `(atom result)` first, same pattern as `var?` in
; lib/unify.lisp: `result` is `'no-match` (an atom) on failure, but on success
; it's whatever `template` was — which may itself be a compound list (e.g.
; `(has-mass earth)`) — and `eq` errors on non-atom arguments instead of
; just correctly answering "not the no-match atom".
(00001001 fire-rule-on-facts
  (00001000 (rule facts)
    (00000111
      ((00000010 facts) () (00000001 ()))
      ((00000010 facts)  (00000001 ()))
      (t (10011100 ((result (fire-rule rule (00000101 facts))))
           (00000111
             ((00000010 result) () (00000111
                ((00000011 result (00000001 no-match)) (fire-rule-on-facts rule (00000110 facts)))
                (t (00000100 result (fire-rule-on-facts rule (00000110 facts))))))
             ((00000010 result)  (00000111
                ((00000011 result (00000001 no-match)) (fire-rule-on-facts rule (00000110 facts)))
                (t (00000100 result (fire-rule-on-facts rule (00000110 facts))))))
             (t (00000100 result (fire-rule-on-facts rule (00000110 facts))))))))))

; Convenience wrapper reading the current global working memory rather than
; requiring the caller to pass it explicitly.
(00001001 fire-rule-on-working-memory
  (00001000 (rule)
    (fire-rule-on-facts rule *working-memory*)))

; Step 3: apply every rule in a rule set to a fact list (still a single
; pass — no fixpoint loop yet, so a fact produced by one rule isn't itself
; matched against other rules within this same call). `append`-based, the
; same fan-out shape `prove-goal` in lib/reason.lisp uses to try every rule
; against a goal.
;
; Крок 3: застосувати кожне правило з набору правил до списку фактів (досі
; один прохід — без fixpoint-циклу, тож факт, породжений одним правилом, у
; межах цього ж виклику не зіставляється з іншими правилами). Побудовано
; через `append`, той самий розгалужувальний паттерн, що й `prove-goal` у
; lib/reason.lisp для перебору всіх правил проти цілі.
;
; Schritt 3: jede Regel eines Regelwerks auf eine Faktenliste anwenden
; (immer noch ein einzelner Durchlauf — noch keine Fixpunkt-Schleife, ein
; von einer Regel erzeugter Fakt wird innerhalb desselben Aufrufs also nicht
; selbst mit anderen Regeln abgeglichen). Auf `append` aufgebaut, dieselbe
; Fan-out-Form, die `prove-goal` in lib/reason.lisp nutzt, um jede Regel gegen
; ein Ziel zu versuchen.
(00001001 fire-rules-on-facts
  (00001000 (rules facts)
    (00000111
      ((00000010 rules) () (00000001 ()))
      ((00000010 rules)  (00000001 ()))
      (t (00101001 (fire-rule-on-facts (00000101 rules) facts)
                  (fire-rules-on-facts (00000110 rules) facts))))))

(00001001 fire-rules-on-working-memory
  (00001000 (rules)
    (fire-rules-on-facts rules *working-memory*)))

; Step 4: `run` — the fixpoint loop. Repeatedly fires the whole rule set
; against the current fact list, folding newly produced facts (deduplicated
; via `equal?`, since facts are compound terms) into that list, until a pass
; adds nothing new.
;
; `run` is a *pure function* returning the final fact list — it does not
; itself assert into `*working-memory*`. Same reason `count-usage` accumulates
; instead of mutating in lib/reason.lisp: `run` is a `lambda`, and `def` (the
; only mutation my-lisp has) only ever mutates the frame it runs in, so a
; loop body cannot durably update a global one iteration at a time. To sync
; the result back, call `assert-facts!` yourself at the top level:
; `(assert-facts! (run rules *working-memory*))`.
;
; Крок 4: `run` — fixpoint-цикл. Повторно застосовує весь набір правил до
; поточного списку фактів, вкладаючи новоутворені факти (дедуплікація через
; `equal?`, бо факти — складені терми) у цей список, поки прохід не додає
; нічого нового.
;
; `run` — *чиста функція*, що повертає фінальний список фактів — сама вона
; не записує в `*working-memory*`. Та сама причина, що й акумуляція в
; `count-usage` у lib/reason.lisp замість мутації: `run` — це `lambda`, а
; `def` (єдина мутація в my-lisp) мутує лише той фрейм, у якому виконується,
; тож тіло циклу не може стійко оновлювати глобальний стан по одній
; ітерації. Щоб синхронізувати результат назад, виклич `assert-facts!` сам
; на верхньому рівні: `(assert-facts! (run rules *working-memory*))`.
;
; Schritt 4: `run` — die Fixpunkt-Schleife. Wendet wiederholt das ganze
; Regelwerk auf die aktuelle Faktenliste an und faltet neu erzeugte Fakten
; (dedupliziert über `equal?`, da Fakten zusammengesetzte Terme sind) in
; diese Liste ein, bis ein Durchlauf nichts Neues mehr hinzufügt.
;
; `run` ist eine *reine Funktion*, die die endgültige Faktenliste
; zurückgibt — sie schreibt selbst nicht in `*working-memory*`. Derselbe
; Grund wie die Akkumulation in `count-usage` in lib/reason.lisp statt
; Mutation: `run` ist eine `lambda`, und `def` (die einzige Mutation in
; my-lisp) mutiert nur den Frame, in dem es läuft, daher kann der
; Schleifenkörper nicht Schritt für Schritt dauerhaft einen globalen Zustand
; aktualisieren. Um das Ergebnis zurückzusynchronisieren, ruf `assert-facts!`
; selbst auf oberster Ebene auf: `(assert-facts! (run rules *working-memory*))`.

(00001001 append-new
  (00001000 (facts wm)
    (00000111
      ((00000010 facts) () wm)
      ((00000010 facts) (1) wm)
      ((00101100 (00000101 facts) wm) (append-new (00000110 facts) wm))
      (t (append-new (00000110 facts) (00000100 (00000101 facts) wm))))))

(00001001 run
  (00001000 (rules facts)
    (10011100 ((merged (append-new (fire-rules-on-facts rules facts) facts)))
      (00000111
        ((00011100 (00101000 merged) (00101000 facts)) 1 facts)
        (t (run rules merged))))))

(00001010 assert-facts! (facts)
  (00100111 (00000001 def) (00000001 *working-memory*) (00100111 (00000001 append-new) facts (00000001 *working-memory*))))

; Step 5a: plain `retract-fact` — removes one matching fact (compared via
; `equal?`, same as everywhere else facts are compared) from a fact list.
; Deliberately *not* truth maintenance yet: if some other fact was derived
; only from the one being retracted, that derived fact stays behind,
; unsupported and undetected — `run` currently returns a flat fact list
; with no memory of which facts justified which. A real TMS needs facts
; paired with their support set (`(fact . supporting-facts)`), so retracting
; a support can cascade; that's Step 5b, a separate agreed-on step, not
; assumed here.
;
; Крок 5a: простий `retract-fact` — видаляє один відповідний факт
; (порівняння через `equal?`, як і скрізь для фактів) зі списку фактів.
; Свідомо *ще без* truth maintenance: якщо якийсь інший факт був виведений
; лише з того, що зараз видаляється, цей похідний факт лишається — без
; підтримки й непоміченим — `run` зараз повертає плаский список фактів без
; пам'яті про те, які факти обґрунтовували які. Справжній TMS потребує
; фактів у парі з їхнім набором підтримки (`(факт . факти-підтримки)`), щоб
; видалення підтримки могло каскадно поширюватись; це Крок 5b, окремо
; узгоджений крок, тут не мається на увазі.
;
; Schritt 5a: einfaches `retract-fact` — entfernt einen passenden Fakt
; (Vergleich über `equal?`, wie überall sonst bei Fakten) aus einer
; Faktenliste. Bewusst *noch keine* Truth Maintenance: Wurde ein anderer
; Fakt nur aus dem gerade entfernten abgeleitet, bleibt dieser abgeleitete
; Fakt unbemerkt und ohne Unterstützung zurück — `run` liefert derzeit eine
; flache Faktenliste ohne Gedächtnis darüber, welche Fakten welche
; begründet haben. Ein echtes TMS braucht Fakten gepaart mit ihrer
; Unterstützungsmenge (`(fakt . unterstützende-fakten)`), damit das
; Entfernen einer Unterstützung kaskadieren kann; das ist Schritt 5b, ein
; separat abgestimmter Schritt, hier nicht unterstellt.
(00001001 retract-fact
  (00001000 (fact facts)
    (00000111
      ((00000010 facts) () (00000001 ()))
      ((00000010 facts)  (00000001 ()))
      ((00100010 fact (00000101 facts)) (00000110 facts))
      (t (00000100 (00000101 facts) (retract-fact fact (00000110 facts)))))))

(00001010 retract-fact! (fact)
  (00100111 (00000001 def) (00000001 *working-memory*) (00100111 (00000001 retract-fact) fact (00000001 *working-memory*))))

; Step 5b: a real (if minimal) truth maintenance system. A *justified fact*
; is `(fact . supports)`: `supports` is the list of facts a rule consumed to
; derive `fact`, or `()` for a fact asserted as an axiom (nothing backs it
; but the assertion itself). Retracting a fact now cascades: everything
; whose support set names the retracted fact loses its justification and
; gets retracted too, recursively.
;
; Deliberately single-justification: each fact is tracked with the *one*
; support set that first derived it, not every possible way it could be
; derived. If a fact is independently derivable two different ways,
; retracting the tracked support still retracts it, even though another
; justification might have kept it alive in a full JTMS. Documented as a
; known limitation, not hidden — extending to multiple justifications per
; fact is a further step, not assumed here.
;
; Lives alongside the Step 1-5a plain-fact functions rather than replacing
; them: `*justified-memory*` is a separate global from `*working-memory*`,
; so existing callers of `run`/`assert-fact!`/`retract-fact!` are unaffected.
;
; Крок 5b: справжня (хоч і мінімальна) система підтримки істинності. *Факт з
; обґрунтуванням* — це `(факт . підтримка)`: `підтримка` — список фактів,
; які правило спожило, щоб вивести `факт`, або `()` для факту-аксіоми
; (нічого, крім самого твердження). Видалення факту тепер каскадує: усе, у
; чиєму наборі підтримки згадується видалений факт, втрачає обґрунтування й
; теж видаляється, рекурсивно.
;
; Свідомо одне обґрунтування на факт: кожен факт відстежується з *одним*
; набором підтримки, який вивів його першим, не з усіма можливими шляхами
; виведення. Якщо факт можна незалежно вивести двома різними шляхами,
; видалення відстеженої підтримки все одно видалить факт, навіть якщо інше
; обґрунтування могло б зберегти його живим у повному JTMS. Задокументовано
; як відоме обмеження, не приховано — розширення до кількох обґрунтувань на
; факт — окремий подальший крок, тут не мається на увазі.
;
; Існує поряд із функціями Кроку 1-5a для простих фактів, не замінюючи їх:
; `*justified-memory*` — окрема глобальна змінна від `*working-memory*`, тож
; наявні виклики `run`/`assert-fact!`/`retract-fact!` не зачіпаються.
;
; Schritt 5b: ein echtes (wenn auch minimales) Truth-Maintenance-System. Ein
; *begründeter Fakt* ist `(fakt . unterstützung)`: `unterstützung` ist die
; Liste der Fakten, die eine Regel verbraucht hat, um `fakt` abzuleiten,
; oder `()` für einen als Axiom behaupteten Fakt (nichts stützt ihn außer
; der Behauptung selbst). Das Entfernen eines Fakts kaskadiert nun: alles,
; dessen Unterstützungsmenge den entfernten Fakt nennt, verliert seine
; Begründung und wird ebenfalls rekursiv entfernt.
;
; Bewusst nur eine Begründung pro Fakt: jeder Fakt wird mit der *einen*
; Unterstützungsmenge verfolgt, die ihn zuerst abgeleitet hat, nicht mit
; jedem möglichen Ableitungsweg. Lässt sich ein Fakt unabhängig auf zwei
; verschiedenen Wegen ableiten, entfernt das Retract der verfolgten
; Unterstützung ihn trotzdem, selbst wenn eine andere Begründung ihn in
; einem vollständigen JTMS am Leben erhalten hätte. Als bekannte
; Einschränkung dokumentiert, nicht versteckt — die Erweiterung auf mehrere
; Begründungen pro Fakt ist ein weiterer, hier nicht unterstellter Schritt.
;
; Existiert neben den Funktionen für einfache Fakten aus Schritt 1-5a, ohne
; sie zu ersetzen: `*justified-memory*` ist eine von `*working-memory*`
; getrennte globale Variable, sodass bestehende Aufrufer von
; `run`/`assert-fact!`/`retract-fact!` unberührt bleiben.
(00001001 make-justified
  (00001000 (fact supports)
    (00000100 fact supports)))

(00001001 fact-of (00001000 (entry) (00000101 entry)))
(00001001 supports-of (00001000 (entry) (00000110 entry)))
(00001001 axiom (00001000 (fact) (make-justified fact (00000001 ()))))

(00001001 map-fact-of
  (00001000 (entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries)  (00000001 ()))
      (t (00000100 (fact-of (00000101 entries)) (map-fact-of (00000110 entries)))))))

; Same `fire-rule` as Step 1, but wraps a successful result with the
; single supporting fact that produced it.
(00001001 fire-rule-tms
  (00001000 (rule fact)
    (10011100 ((result (fire-rule rule fact)))
      (00000111
        ((00000010 result) () (00000111
           ((00000011 result (00000001 no-match)) (00000001 no-match))
           (t (make-justified result (00100111 fact)))))
        ((00000010 result)  (00000111
           ((00000011 result (00000001 no-match)) (00000001 no-match))
           (t (make-justified result (00100111 fact)))))
        (t (make-justified result (00100111 fact)))))))

(00001001 fire-rule-on-facts-tms
  (00001000 (rule facts)
    (00000111
      ((00000010 facts) () (00000001 ()))
      ((00000010 facts)  (00000001 ()))
      (t (10011100 ((result (fire-rule-tms rule (00000101 facts))))
           (00000111
             ((00000010 result) () (fire-rule-on-facts-tms rule (00000110 facts)))
             ((00000010 result)  (fire-rule-on-facts-tms rule (00000110 facts)))
             (t (00000100 result (fire-rule-on-facts-tms rule (00000110 facts))))))))))

(00001001 fire-rules-on-facts-tms
  (00001000 (rules facts)
    (00000111
      ((00000010 rules) () (00000001 ()))
      ((00000010 rules)  (00000001 ()))
      (t (00101001 (fire-rule-on-facts-tms (00000101 rules) facts)
                  (fire-rules-on-facts-tms (00000110 rules) facts))))))

(00001001 justified-member?
  (00001000 (fact entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries)  (00000001 ()))
      ((00100010 fact (fact-of (00000101 entries))) t)
      (t (justified-member? fact (00000110 entries))))))

(00001001 add-new-justified
  (00001000 (new-entries entries)
    (00000111
      ((00000010 new-entries) () entries)
      ((00000010 new-entries) (1) entries)
      ((justified-member? (fact-of (00000101 new-entries)) entries)
       (add-new-justified (00000110 new-entries) entries))
      (t (add-new-justified (00000110 new-entries) (00000100 (00000101 new-entries) entries))))))

; The fixpoint loop over justified facts, mirroring `run` from Step 4.
(00001001 run-tms
  (00001000 (rules entries)
    (10011100 ((new-entries (fire-rules-on-facts-tms rules (map-fact-of entries))))
      (10011100 ((merged (add-new-justified new-entries entries)))
        (00000111
          ((00011100 (00101000 merged) (00101000 entries)) 1 entries)
          (t (run-tms rules merged)))))))

(00001001 *justified-memory* (00000001 ()))

(00001010 assert-fact-tms! (fact)
  (00100111 (00000001 def) (00000001 *justified-memory*) (00100111 (00000001 add-new-justified) (00100111 (00000001 list) (00100111 (00000001 axiom) fact)) (00000001 *justified-memory*))))

(00001010 run-tms! (rules)
  (00100111 (00000001 def) (00000001 *justified-memory*) (00100111 (00000001 run-tms) rules (00000001 *justified-memory*))))

(00001001 remove-justified
  (00001000 (fact entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries)  (00000001 ()))
      ((00100010 fact (fact-of (00000101 entries))) (remove-justified fact (00000110 entries)))
      (t (00000100 (00000101 entries) (remove-justified fact (00000110 entries)))))))

(00001001 dependents-of
  (00001000 (fact entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries)  (00000001 ()))
      ((00101100 fact (supports-of (00000101 entries)))
       (00000100 (fact-of (00000101 entries)) (dependents-of fact (00000110 entries))))
      (t (dependents-of fact (00000110 entries))))))

; Retracts `fact`, then recursively retracts everything that named it in
; their support set — the cascade truth maintenance is for.
(00001001 retract-fact-tms
  (00001000 (fact entries)
    (retract-facts-tms (dependents-of fact entries) (remove-justified fact entries))))

(00001001 retract-facts-tms
  (00001000 (facts entries)
    (00000111
      ((00000010 facts) () entries)
      ((00000010 facts) (1) entries)
      (t (retract-facts-tms (00000110 facts) (retract-fact-tms (00000101 facts) entries))))))

(00001010 retract-fact-tms! (fact)
  (00100111 (00000001 def) (00000001 *justified-memory*) (00100111 (00000001 retract-fact-tms) fact (00000001 *justified-memory*))))

; Step 5c: multiple justifications per fact — the limitation Step 5b
; documented and deliberately left open. An entry is now `(fact
; justification-1 justification-2 ...)`: each `justification-N` is its own
; support set (a list of facts), one entry per *independent* way the fact
; has been derived (or asserted as an axiom, with justification `()`).
; Retracting a fact now only removes derivations that actually depended on
; it: pruning drops any justification-set naming the retracted fact from
; every other entry, and only when an entry's justification list becomes
; fully empty does *that* fact cascade-retract too. A fact with a surviving
; independent justification (e.g. also asserted directly, or derivable
; another way) stays.
;
; Separate global (`*jtms-memory*`) from both `*working-memory*` (Step
; 1-5a) and `*justified-memory*` (Step 5b, single-justification) — neither
; earlier layer is touched or replaced.
;
; Крок 5c: множинні обґрунтування на факт — обмеження, задокументоване й
; свідомо залишене відкритим у Кроці 5b. Запис тепер — `(факт
; обґрунтування-1 обґрунтування-2 ...)`: кожне `обґрунтування-N` — власний
; набір підтримки (список фактів), один запис на кожен *незалежний* спосіб
; виведення факту (або аксіому, з обґрунтуванням `()`). Видалення факту
; тепер прибирає лише ті виведення, що справді залежали від нього:
; обрізання відкидає будь-який набір підтримки, що називає видалений факт,
; з кожного іншого запису, і лише коли список обґрунтувань запису стає
; повністю порожнім, *цей* факт теж каскадно видаляється. Факт із живим
; незалежним обґрунтуванням (напр. також заявлений напряму, або виведений
; іншим шляхом) лишається.
;
; Окрема глобальна (`*jtms-memory*`) від `*working-memory*` (Крок 1-5a) і
; `*justified-memory*` (Крок 5b, одне обґрунтування) — жоден з попередніх
; шарів не чіпається й не замінюється.
;
; Schritt 5c: mehrere Begründungen pro Fakt — die in Schritt 5b dokumentierte
; und bewusst offen gelassene Einschränkung. Ein Eintrag ist nun `(fakt
; begründung-1 begründung-2 ...)`: jede `begründung-N` ist eine eigene
; Unterstützungsmenge (eine Faktenliste), ein Eintrag pro *unabhängigem* Weg,
; auf dem der Fakt abgeleitet wurde (oder als Axiom mit Begründung `()`).
; Das Entfernen eines Fakts entfernt nun nur Ableitungen, die tatsächlich
; von ihm abhingen: das Beschneiden verwirft jede Unterstützungsmenge, die
; den entfernten Fakt nennt, aus jedem anderen Eintrag, und nur wenn die
; Begründungsliste eines Eintrags vollständig leer wird, wird *dieser* Fakt
; ebenfalls kaskadierend entfernt. Ein Fakt mit einer überlebenden
; unabhängigen Begründung (z. B. auch direkt behauptet oder anders
; ableitbar) bleibt erhalten.
;
; Separate globale Variable (`*jtms-memory*`) sowohl von `*working-memory*`
; (Schritt 1-5a) als auch von `*justified-memory*` (Schritt 5b, eine
; Begründung) — keine frühere Schicht wird berührt oder ersetzt.
(00001001 justifications-of (00001000 (entry) (00000110 entry)))

(00001001 fire-rule-jtms
  (00001000 (rule fact)
    (10011100 ((result (fire-rule rule fact)))
      (00000111
        ((00000010 result) () (00000111
           ((00000011 result (00000001 no-match)) (00000001 no-match))
           (t (00100111 result (00100111 fact)))))
        ((00000010 result)  (00000111
           ((00000011 result (00000001 no-match)) (00000001 no-match))
           (t (00100111 result (00100111 fact)))))
        (t (00100111 result (00100111 fact)))))))

(00001001 fire-rule-on-facts-jtms
  (00001000 (rule facts)
    (00000111
      ((00000010 facts) () (00000001 ()))
      ((00000010 facts)  (00000001 ()))
      (t (10011100 ((result (fire-rule-jtms rule (00000101 facts))))
           (00000111
             ((00000010 result) () (fire-rule-on-facts-jtms rule (00000110 facts)))
             ((00000010 result)  (fire-rule-on-facts-jtms rule (00000110 facts)))
             (t (00000100 result (fire-rule-on-facts-jtms rule (00000110 facts))))))))))

(00001001 fire-rules-on-facts-jtms
  (00001000 (rules facts)
    (00000111
      ((00000010 rules) () (00000001 ()))
      ((00000010 rules)  (00000001 ()))
      (t (00101001 (fire-rule-on-facts-jtms (00000101 rules) facts)
                  (fire-rules-on-facts-jtms (00000110 rules) facts))))))

(00001001 find-entry
  (00001000 (fact entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries)  (00000001 ()))
      ((00100010 fact (fact-of (00000101 entries))) (00000101 entries))
      (t (find-entry fact (00000110 entries))))))

(00001001 remove-entry-jtms
  (00001000 (fact entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries)  (00000001 ()))
      ((00100010 fact (fact-of (00000101 entries))) (remove-entry-jtms fact (00000110 entries)))
      (t (00000100 (00000101 entries) (remove-entry-jtms fact (00000110 entries)))))))

; Folds one new `(fact justification)` pair into `entries`: a brand-new
; fact gets a fresh entry; a fact already present gets `justification`
; added to its list only if not already there (so re-deriving the same way
; twice is a no-op, needed for `run-jtms`'s fixpoint check to terminate).
(00001001 add-justification
  (00001000 (fact justification entries)
    (10011100 ((existing (find-entry fact entries)))
      (00000111
        ((00000010 existing) () (00000100 (00100111 fact justification) entries))
        ((00000010 existing)  (00000100 (00100111 fact justification) entries))
        ((00101100 justification (justifications-of existing)) entries)
        (t (00000100 (00000100 fact (00000100 justification (justifications-of existing)))
                 (remove-entry-jtms fact entries)))))))

(00001001 add-new-entries-jtms
  (00001000 (new-entries entries)
    (00000111
      ((00000010 new-entries) () entries)
      ((00000010 new-entries) (1) entries)
      (t (add-new-entries-jtms
           (00000110 new-entries)
           (add-justification (fact-of (00000101 new-entries)) (00101111 (00000101 new-entries)) entries))))))

; The fixpoint loop. Compares the merged result to the input with `equal?`
; rather than a length/count check (Step 4's `run` compares lengths) —
; `add-justification` can grow an *existing* entry's justification list
; without changing the entry count, so counting entries alone would miss
; real progress and stop too early.
(00001001 run-jtms
  (00001000 (rules entries)
    (10011100 ((merged (add-new-entries-jtms (fire-rules-on-facts-jtms rules (map-fact-of entries)) entries)))
      (00000111
        ((00100010 merged entries) entries)
        (t (run-jtms rules merged))))))

(00001001 *jtms-memory* (00000001 ()))

(00001010 assert-fact-jtms! (fact)
  (00100111 (00000001 def) (00000001 *jtms-memory*) (00100111 (00000001 add-justification) fact (00100111 (00000001 quote) (00000001 ())) (00000001 *jtms-memory*))))

(00001010 run-jtms! (rules)
  (00100111 (00000001 def) (00000001 *jtms-memory*) (00100111 (00000001 run-jtms) rules (00000001 *jtms-memory*))))

; Step 14: JTMS grows a multi-condition twin, the same way Step 6 grew
; `fire-rule-multi`/`run-multi` alongside the Step 1-5 single-condition
; layer. Verified before writing this (not guessed): `run-jtms!` with the
; exact `grandparent`/`parent` rule literal used throughout this project
; derived nothing at all — `fire-rule-jtms` was still built on Step 1's
; `fire-rule`, matching exactly one `(pattern template)` condition against
; one fact, with no path to a `(head cond1 cond2 ...)` rule at all, let
; alone one containing `not`/`or`/`and`/`test`.
;
; `match-conditions-jtms` is `thread-conjunction` again, threading a
; richer state — `(subst . used-facts)` instead of a bare substitution —
; the exact same shape shift `lib/reason.lisp`'s `prove-goal-state` makes
; for `(subst proofs)`. A plain condition's match adds the one fact it
; matched to `used-facts`; `not`/`test` add nothing (no positive fact
; supports a negative check or an arbitrary expression); `or` unions each
; alternative's own `used-facts`; `and`/nested nested nested — is just
; `match-conditions-jtms` again, over the sub-conditions, same reuse
; `match-and-condition` already does non-JTMS.
;
; Deliberately additive, not a replacement: `fire-rule-jtms` and the
; single-condition `run-jtms`/`run-jtms!` above are untouched, still valid
; for the Step 1-5 `(pattern template)` rule shape. `run-jtms-multi!` is
; the JTMS entry point for the shared `(head cond1 cond2 ...)` format.
;
; Крок 14: JTMS отримує багатоумовного близнюка, тим самим шляхом, яким
; Крок 6 виростив `fire-rule-multi`/`run-multi` поряд із однофактовим
; шаром Кроків 1-5. Перевірено перед написанням (не здогадано): `run-jtms!`
; із точно тим самим літералом правила `grandparent`/`parent`, який
; використовується по всьому проєкту, не виводив нічого — `fire-rule-jtms`
; досі був побудований на `fire-rule` з Кроку 1, що зіставляє рівно одну
; умову `(pattern template)` з одним фактом, без жодного шляху до правила
; `(head cond1 cond2 ...)`, тим паче з `not`/`or`/`and`/`test`.
;
; `match-conditions-jtms` — знову `thread-conjunction`, що протягує
; багатший стан — `(підстановка . використані-факти)` замість голої
; підстановки — та сама зміна форми, яку `prove-goal-state` у
; `lib/reason.lisp` робить для `(підстановка доведення)`. Зіставлення
; звичайної умови додає той один факт, з яким зіставилось, до
; `використані-факти`; `not`/`test` не додають нічого (жоден позитивний
; факт не підтримує заперечну перевірку чи довільний вираз); `or` об'єднує
; власні `використані-факти` кожної альтернативи; `and` — знову просто
; `match-conditions-jtms` над під-умовами, те саме перевикористання, що
; вже робить не-JTMS `match-and-condition`.
;
; Свідомо адитивно, не заміна: `fire-rule-jtms` і однофактові `run-jtms`/
; `run-jtms!` вище не чіпаються, досі чинні для форми правила `(pattern
; template)` Кроків 1-5. `run-jtms-multi!` — точка входу JTMS для спільного
; формату `(head cond1 cond2 ...)`.
;
; Schritt 14: JTMS erhält einen Mehrbedingungs-Zwilling, genau wie Schritt
; 6 `fire-rule-multi`/`run-multi` neben der Einzelbedingungs-Schicht aus
; Schritt 1-5 wachsen ließ. Vor dem Schreiben verifiziert (nicht geraten):
; `run-jtms!` mit genau demselben `grandparent`/`parent`-Regelliteral, das
; im ganzen Projekt verwendet wird, leitete überhaupt nichts ab —
; `fire-rule-jtms` war noch auf `fire-rule` aus Schritt 1 aufgebaut, das
; genau eine `(pattern template)`-Bedingung gegen einen Fakt abgleicht,
; ganz ohne Weg zu einer `(head cond1 cond2 ...)`-Regel, geschweige denn
; mit `not`/`or`/`and`/`test`.
;
; `match-conditions-jtms` ist wieder `thread-conjunction`, das einen
; reicheren Zustand fädelt — `(substitution . genutzte-fakten)` statt einer
; bloßen Substitution — derselbe Formwechsel, den `prove-goal-state` in
; `lib/reason.lisp` für `(substitution beweise)` macht. Der Abgleich einer
; gewöhnlichen Bedingung fügt den einen gefundenen Fakt zu
; `genutzte-fakten` hinzu; `not`/`test` fügen nichts hinzu; `or` vereinigt
; die eigenen `genutzte-fakten` jeder Alternative; `and` ist wieder einfach
; `match-conditions-jtms` über die Unterbedingungen, dieselbe
; Wiederverwendung, die `match-and-condition` außerhalb von JTMS bereits
; tut.
;
; Bewusst additiv, kein Ersatz: `fire-rule-jtms` und die
; Einzelbedingungs-`run-jtms`/`run-jtms!` oben bleiben unberührt, weiterhin
; gültig für die `(pattern template)`-Regelform aus Schritt 1-5.
; `run-jtms-multi!` ist der JTMS-Einstiegspunkt für das gemeinsame Format
; `(head cond1 cond2 ...)`.
(00001001 jtms-state-subst (00001000 (state) (00000101 state)))
(00001001 jtms-state-used (00001000 (state) (00000110 state)))
(00001001 jtms-make-state (00001000 (bindings used) (00000100 bindings used)))

(00001001 match-plain-condition-jtms
  (00001000 (condition facts state)
    (00000111
      ((00000010 facts) () (00000001 ()))
      ((00000010 facts)  (00000001 ()))
      (t (10011100 ((s (10000111 condition (00000101 facts) (jtms-state-subst state))))
           (00000111
             ((failed-subst? s) (match-plain-condition-jtms condition (00000110 facts) state))
             (t (00000100 (jtms-make-state s (00000100 (00000101 facts) (jtms-state-used state)))
                       (match-plain-condition-jtms condition (00000110 facts) state)))))))))

(00001001 match-or-condition-jtms
  (00001000 (alternatives facts state)
    (00000111
      ((00000010 alternatives) () (00000001 ()))
      ((00000010 alternatives)  (00000001 ()))
      (t (00101001 (match-one-condition-jtms (00000101 alternatives) facts state)
                  (match-or-condition-jtms (00000110 alternatives) facts state))))))

(00001001 match-one-condition-jtms
  (00001000 (condition facts state)
    (00000111
      ((condition-is-not? condition)
       (00000111
         ((00000010 (match-condition-against-facts (00101111 condition) facts (jtms-state-subst state))) () (00100111 state))
         ((00000010 (match-condition-against-facts (00101111 condition) facts (jtms-state-subst state)))  (00100111 state))
         (t (00000001 ()))))
      ((condition-is-or? condition) (match-or-condition-jtms (00000110 condition) facts state))
      ((condition-is-and? condition) (match-conditions-jtms (00000110 condition) facts state))
      ((condition-is-test? condition)
       (00000111
         ((01001101 (10001010 (00101111 condition) (jtms-state-subst state))) (00100111 state))
         (t (00000001 ()))))
      (t (match-plain-condition-jtms condition facts state)))))

(00001001 match-conditions-jtms
  (00001000 (conditions facts state)
    (thread-conjunction conditions state
      (00001000 (condition s) (match-one-condition-jtms condition facts s)))))

(00001001 map-apply-head-jtms
  (00001000 (head states)
    (00000111
      ((00000010 states) () (00000001 ()))
      ((00000010 states)  (00000001 ()))
      (t (00000100 (00100111 (10001010 head (jtms-state-subst (00000101 states))) (jtms-state-used (00000101 states)))
                (map-apply-head-jtms head (00000110 states)))))))

(00001001 fire-rule-jtms-multi
  (00001000 (rule facts)
    (map-apply-head-jtms (00000101 rule) (match-conditions-jtms (00000110 rule) facts (jtms-make-state (00000001 ()) (00000001 ()))))))

(00001001 fire-rules-jtms-multi
  (00001000 (rules facts)
    (00000111
      ((00000010 rules) () (00000001 ()))
      ((00000010 rules)  (00000001 ()))
      (t (00101001 (fire-rule-jtms-multi (00000101 rules) facts)
                  (fire-rules-jtms-multi (00000110 rules) facts))))))

(00001001 run-jtms-multi
  (00001000 (rules entries)
    (10011100 ((merged (add-new-entries-jtms (fire-rules-jtms-multi rules (map-fact-of entries)) entries)))
      (00000111
        ((00100010 merged entries) entries)
        (t (run-jtms-multi rules merged))))))

(00001010 run-jtms-multi! (rules)
  (00100111 (00000001 def) (00000001 *jtms-memory*) (00100111 (00000001 run-jtms-multi) rules (00000001 *jtms-memory*))))

(00001001 prune-justifications
  (00001000 (fact justifications)
    (00000111
      ((00000010 justifications) () (00000001 ()))
      ((00000010 justifications)  (00000001 ()))
      ((00101100 fact (00000101 justifications)) (prune-justifications fact (00000110 justifications)))
      (t (00000100 (00000101 justifications) (prune-justifications fact (00000110 justifications)))))))

(00001001 prune-entry
  (00001000 (fact entry)
    (00000100 (fact-of entry) (prune-justifications fact (justifications-of entry)))))

(00001001 prune-all-entries
  (00001000 (fact entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries)  (00000001 ()))
      (t (00000100 (prune-entry fact (00000101 entries)) (prune-all-entries fact (00000110 entries)))))))

(00001001 unsupported-facts
  (00001000 (entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries)  (00000001 ()))
      ((00000010 (justifications-of (00000101 entries))) () (00000100 (fact-of (00000101 entries)) (unsupported-facts (00000110 entries))))
      ((00000010 (justifications-of (00000101 entries)))  (00000100 (fact-of (00000101 entries)) (unsupported-facts (00000110 entries))))
      (t (unsupported-facts (00000110 entries))))))

(00001001 drop-unsupported
  (00001000 (entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries)  (00000001 ()))
      ((00000010 (justifications-of (00000101 entries))) () (drop-unsupported (00000110 entries)))
      ((00000010 (justifications-of (00000101 entries)))  (drop-unsupported (00000110 entries)))
      (t (00000100 (00000101 entries) (drop-unsupported (00000110 entries)))))))

; Removes `fact`'s own entry outright, then prunes every justification-set
; elsewhere that named it. Any entry left with zero justification-sets has
; lost all support and cascade-retracts in turn — recursively, the same way
; Step 5b's single-justification cascade works, just checking "any
; justification left" instead of "any support left".
(00001001 retract-fact-jtms
  (00001000 (fact entries)
    (10011100 ((pruned (prune-all-entries fact (remove-entry-jtms fact entries))))
      (10011100 ((newly-unsupported (unsupported-facts pruned))
            (remaining (drop-unsupported pruned)))
        (00000111
          ((00000010 newly-unsupported) () remaining)
          ((00000010 newly-unsupported) (1) remaining)
          (t (retract-facts-jtms newly-unsupported remaining)))))))

(00001001 retract-facts-jtms
  (00001000 (facts entries)
    (00000111
      ((00000010 facts) () entries)
      ((00000010 facts) (1) entries)
      (t (retract-facts-jtms (00000110 facts) (retract-fact-jtms (00000101 facts) entries))))))

(00001010 retract-fact-jtms! (fact)
  (00100111 (00000001 def) (00000001 *jtms-memory*) (00100111 (00000001 retract-fact-jtms) fact (00000001 *jtms-memory*))))

; Step 6: a shared rule language with `lib/reason.lisp`. Steps 1-5c used a
; forward-only `(pattern template)` shape, matched against exactly one
; fact — different from `reason.lisp`'s `(head cond1 cond2 ...)` rules, which
; already read naturally as "conclusion :- conditions" either direction:
; backward-chaining proves `head` by proving every `cond`; forward-chaining
; can just as well fire `head` once every `cond` is already a known fact.
; A rule like `((grandparent (var x) (var y)) (parent (var x) (var z))
; (parent (var z) (var y)))` — the exact literal `reason.rs`'s own tests
; use — now runs unmodified through `run-multi` too.
;
; This needed real matching logic, not just a relabeling: firing a
; multi-condition rule forward means finding a substitution that satisfies
; *every* condition against *some* facts simultaneously (a conjunctive
; join), not matching one pattern against one fact. `match-conditions`
; threads a substitution across the condition list exactly the way
; `prove-goals` in lib/reason.lisp threads one through a rule body — same
; idea, just matching against an explicit fact list instead of recursing
; into further rules.
;
; Deliberately additive: a third plain-fact-list layer (`fire-rule-multi`,
; `fire-rules-multi`, `run-multi`), reusing `member?`/`append-new` from Step
; 4. Doesn't touch or replace the Step 1-5a 2-element-rule layer, nor wire
; into the Step 5b/5c truth-maintenance layers — those stay exactly as they
; were.
;
; Крок 6: спільна мова правил із `lib/reason.lisp`. Кроки 1-5c
; використовували форму `(pattern template)` лише для forward, зіставлену
; рівно з одним фактом — інакше, ніж правила `reason.lisp` `(head cond1
; cond2 ...)`, які й так природно читаються як "висновок :- умови" в обидва
; боки: backward-chaining доводить `head`, доводячи кожен `cond`;
; forward-chaining так само може застосувати `head`, щойно кожен `cond` уже
; відомий факт. Правило на кшталт `((grandparent (var x) (var y)) (parent
; (var x) (var z)) (parent (var z) (var y)))` — точно той самий літерал, що
; й у тестах `reason.rs` — тепер незмінно працює й через `run-multi`.
;
; Це вимагало справжньої логіки зіставлення, не просто перейменування:
; застосувати багатоумовне правило вперед означає знайти підстановку, що
; задовольняє *кожну* умову проти *якихось* фактів одночасно (кон'юнктивне
; з'єднання), не зіставлення одного шаблону з одним фактом.
; `match-conditions` протягує підстановку через список умов так само, як
; `prove-goals` у lib/reason.lisp протягує її через тіло правила — та сама
; ідея, лише зіставлення з явним списком фактів замість рекурсії в подальші
; правила.
;
; Свідомо адитивно: третій шар для плаского списку фактів
; (`fire-rule-multi`, `fire-rules-multi`, `run-multi`), перевикористовує
; `member?`/`append-new` з Кроку 4. Не чіпає й не замінює шар Кроку 1-5a з
; 2-елементними правилами, і не підключається до шарів truth maintenance
; Кроку 5b/5c — вони лишаються точно такими, як були.
;
; Schritt 6: eine gemeinsame Regelsprache mit `lib/reason.lisp`. Schritte
; 1-5c verwendeten eine reine Forward-Form `(pattern template)`, gegen
; genau einen Fakt abgeglichen — anders als `reason.lisp`s Regeln `(head
; cond1 cond2 ...)`, die sich ohnehin natürlich als "Schlussfolgerung :-
; Bedingungen" in beide Richtungen lesen: Backward-Chaining beweist `head`,
; indem es jede `cond` beweist; Forward-Chaining kann `head` ebenso
; auslösen, sobald jede `cond` bereits ein bekannter Fakt ist. Eine Regel
; wie `((grandparent (var x) (var y)) (parent (var x) (var z)) (parent
; (var z) (var y)))` — genau das Literal, das `reason.rs`s eigene Tests
; verwenden — läuft nun unverändert auch durch `run-multi`.
;
; Das erforderte echte Abgleichslogik, keine bloße Umbenennung: eine
; mehrbedingte Regel vorwärts auszulösen bedeutet, eine Substitution zu
; finden, die *jede* Bedingung gleichzeitig gegen *irgendwelche* Fakten
; erfüllt (ein konjunktiver Join), nicht ein Muster gegen einen Fakt
; abzugleichen. `match-conditions` fädelt eine Substitution durch die
; Bedingungsliste genauso, wie `prove-goals` in lib/reason.lisp sie durch
; einen Regelrumpf fädelt — dieselbe Idee, nur gegen eine explizite
; Faktenliste statt Rekursion in weitere Regeln.
;
; Bewusst additiv: eine dritte Schicht für flache Faktenlisten
; (`fire-rule-multi`, `fire-rules-multi`, `run-multi`), die
; `member?`/`append-new` aus Schritt 4 wiederverwendet. Berührt oder
; ersetzt weder die 2-Element-Regel-Schicht aus Schritt 1-5a noch bindet
; sie sich in die Truth-Maintenance-Schichten aus Schritt 5b/5c ein — die
; bleiben genau, wie sie waren.
(00001001 match-condition-against-facts
  (00001000 (condition facts bindings)
    (00000111
      ((00000010 facts) () (00000001 ()))
      ((00000010 facts)  (00000001 ()))
      (t (10011100 ((s (10000111 condition (00000101 facts) bindings)))
           (00000111
             ((failed-subst? s) (match-condition-against-facts condition (00000110 facts) bindings))
             (t (00000100 s (match-condition-against-facts condition (00000110 facts) bindings)))))))))

; Step 7: negation as failure — `(not (pattern))` conditions. This is the
; capability `lib/clips-import.lisp`'s Step 5 flagged as missing and worked
; around by *skipping* any CLIPS rule containing `not` rather than
; importing a rule that would silently never fire. Same idea
; `lib/reason.lisp`'s `prove-goal-state` already uses for backward-chaining:
; a `not` succeeds exactly when its inner pattern *cannot* be matched
; against the current facts (with the current substitution) — no new
; bindings, `subst` passes through unchanged.
;
; Крок 7: negation as failure — умови `(not (шаблон))`. Це та можливість,
; якої не вистачало Кроку 5 `lib/clips-import.lisp`, і яку обходили
; *пропуском* будь-якого CLIPS-правила з `not`, замість імпорту правила,
; що мовчки ніколи б не спрацювало. Та сама ідея, яку `prove-goal-state` у
; `lib/reason.lisp` уже використовує для backward-chaining: `not` успішний
; точно тоді, коли внутрішній шаблон *не вдається* зіставити з поточними
; фактами (з поточною підстановкою) — жодних нових зв'язувань, `subst`
; проходить незмінним.
;
; Schritt 7: Negation als Fehlschlag — `(not (muster))`-Bedingungen. Genau
; die Fähigkeit, die Schritt 5 von `lib/clips-import.lisp` als fehlend
; markierte und durch *Überspringen* jeder CLIPS-Regel mit `not` umging,
; statt eine Regel zu importieren, die still nie feuern würde. Dieselbe
; Idee, die `prove-goal-state` in `lib/reason.lisp` bereits für
; Backward-Chaining nutzt: ein `not` gelingt genau dann, wenn sein inneres
; Muster *nicht* gegen die aktuellen Fakten (mit der aktuellen
; Substitution) abgeglichen werden kann — keine neuen Bindungen, `subst`
; läuft unverändert durch.
(00001001 condition-is-not?
  (00001000 (condition)
    (00000111
      ((00000010 condition) () (00000001 ()))
      ((00000010 condition)  (00000001 ()))
      ((00000010 (00000101 condition)) () (00000111
         ((00000011 (00000101 condition) (00000001 not?)) (00000001 (1)))
         (t (00000011 (00000101 condition) (00000001 not)))))
      ((00000010 (00000101 condition))  (00000111
         ((00000011 (00000101 condition) (00000001 not?)) (00000001 (1)))
         (t (00000011 (00000101 condition) (00000001 not)))))
      (t (00000001 ())))))

(00001001 match-negated-condition
  (00001000 (inner-pattern facts bindings)
    (00000111
      ((00000010 (match-condition-against-facts inner-pattern facts bindings)) () (00100111 bindings))
      ((00000010 (match-condition-against-facts inner-pattern facts bindings))  (00100111 bindings))
      (t (00000001 ())))))

; Step 10: `(or (pattern1) (pattern2) ...)` conditions — verified missing
; before fixing (not guessed), the same way Step 7's `not` gap was found:
; a rule with `(or (cat ?x) (dog ?x))` derived nothing at all, because no
; fact's head is ever the symbol `or`, so `match-condition-against-facts`
; unified the whole `or`-condition literally and always failed — the same
; silent-dead-rule shape `not` had. `or` succeeds with the *union* of
; every alternative's own matches: try each alternative as its own
; condition (recursing through `match-one-condition`, so an alternative
; can itself be a `not` or nested `or`), collecting every substitution any
; of them produce.
;
; Крок 10: умови `(or (шаблон1) (шаблон2) ...)` — перевірено як
; відсутню можливість перед виправленням (не здогадано), так само, як
; знайдено прогалину `not` у Кроці 7: правило з `(or (cat ?x) (dog ?x))`
; не виводило нічого, бо жоден факт ніколи не має головою символ `or`,
; тож `match-condition-against-facts` унікувала всю `or`-умову буквально
; й завжди провалювалась — та сама форма мовчки мертвого правила, що й у
; `not`. `or` успішний з *об'єднанням* збігів кожної альтернативи: кожна
; альтернатива пробується як власна умова (рекурсія через
; `match-one-condition`, тож альтернатива сама може бути `not` чи
; вкладеним `or`), збираючи всі підстановки, які видає будь-яка з них.
;
; Schritt 10: `(or (muster1) (muster2) ...)`-Bedingungen — vor dem Fix
; verifiziert (nicht geraten), genauso wie die `not`-Lücke in Schritt 7
; gefunden wurde: eine Regel mit `(or (cat ?x) (dog ?x))` leitete
; überhaupt nichts ab, weil kein Fakt je das Symbol `or` als Kopf hat,
; sodass `match-condition-against-facts` die ganze `or`-Bedingung wörtlich
; unifizierte und immer fehlschlug — dieselbe Form einer still toten Regel
; wie bei `not`. `or` gelingt mit der *Vereinigung* der Treffer jeder
; Alternative: jede Alternative wird als eigene Bedingung versucht
; (Rekursion über `match-one-condition`, sodass eine Alternative selbst
; ein `not` oder verschachteltes `or` sein kann), gesammelt werden alle
; Substitutionen, die irgendeine davon liefert.
(00001001 condition-is-or?
  (00001000 (condition)
    (00000111
      ((00000010 condition) () (00000001 ()))
      ((00000010 condition)  (00000001 ()))
      ((00000010 (00000101 condition)) () (00000011 (00000101 condition) (00000001 or)))
      ((00000010 (00000101 condition))  (00000011 (00000101 condition) (00000001 or)))
      (t (00000001 ())))))

(00001001 match-or-condition
  (00001000 (alternatives facts bindings)
    (00000111
      ((00000010 alternatives) () (00000001 ()))
      ((00000010 alternatives)  (00000001 ()))
      (t (00101001 (match-one-condition (00000101 alternatives) facts bindings)
                  (match-or-condition (00000110 alternatives) facts bindings))))))

; Step 11: `(and (pattern1) (pattern2) ...)` conditions — the same bug
; class again, found the same way: `(or (and (cat ?x) (small ?x)) (dog
; ?x))` never matched the `and`-branch at all, silently missing every
; animal that was both a cat and small, because no fact's head is ever
; the symbol `and` either. Nested explicitly because top-level conditions
; are already an implicit conjunction (that's what `thread-conjunction`
; already does one level up) — an inner `and` is exactly the same
; operation, just written explicitly, most often to group a compound
; condition inside an `or`. `match-and-condition` is `match-conditions`
; itself, threading the sub-conditions the identical way; not
; reimplemented, just reused under the name the condition-position
; dispatch expects.
;
; Крок 11: умови `(and (шаблон1) (шаблон2) ...)` — той самий клас бага,
; знайдений тим самим методом: `(or (and (cat ?x) (small ?x)) (dog ?x))`
; узагалі не зіставляла гілку `and`, мовчки пропускаючи кожну тварину, що
; одночасно кіт і маленька, бо жоден факт теж ніколи не має головою символ
; `and`. Вкладено явно, бо умови верхнього рівня вже й так неявна
; кон'юнкція (те саме, що `thread-conjunction` уже робить на рівень вище)
; — внутрішній `and` — точно та сама операція, лише записана явно,
; найчастіше щоб згрупувати складену умову всередині `or`.
; `match-and-condition` — це сам `match-conditions`, що протягує
; під-умови так само; не переписано заново, лише перевикористано під
; іменем, якого чекає диспетчеризація за позицією умови.
;
; Schritt 11: `(and (muster1) (muster2) ...)`-Bedingungen — dieselbe
; Bugklasse, gefunden auf demselben Weg: `(or (and (cat ?x) (small ?x))
; (dog ?x))` glich den `and`-Zweig überhaupt nie ab und verwarf
; stillschweigend jedes Tier, das zugleich Katze und klein war, weil auch
; kein Fakt je das Symbol `and` als Kopf hat. Explizit verschachtelt, weil
; Bedingungen der obersten Ebene bereits eine implizite Konjunktion sind
; (genau das, was `thread-conjunction` eine Ebene höher schon tut) — ein
; inneres `and` ist genau dieselbe Operation, nur explizit geschrieben,
; meist um eine zusammengesetzte Bedingung innerhalb eines `or` zu
; gruppieren. `match-and-condition` ist `match-conditions` selbst, das die
; Unterbedingungen identisch fädelt; nicht neu implementiert, nur unter
; dem Namen wiederverwendet, den die Dispatch nach Bedingungsposition
; erwartet.
(00001001 condition-is-and?
  (00001000 (condition)
    (00000111
      ((00000010 condition) () (00000001 ()))
      ((00000010 condition)  (00000001 ()))
      ((00000010 (00000101 condition)) () (00000011 (00000101 condition) (00000001 and)))
      ((00000010 (00000101 condition))  (00000011 (00000101 condition) (00000001 and)))
      (t (00000001 ())))))

(00001001 match-and-condition
  (00001000 (sub-conditions facts bindings)
    (match-conditions sub-conditions facts bindings)))

; Step 12: `(test <expression>)` conditions — the fourth time this same
; bug class turned up (verified before fixing, same as `not`/`or`/`and`):
; `(test (> ?x 5))` matched nothing at all, because — once again — no
; fact's head is ever the symbol `test`. Unlike `not`/`or`/`and`, `test`
; isn't a matching combinator at all: it doesn't compare a pattern against
; facts, it evaluates an arbitrary expression (typically a comparison like
; `>`, already a my-lisp primitive) after substituting in whatever the
; preceding conditions already bound. `apply-subst` (lib/unify.lisp) resolves
; every `(var name)` in the expression against the current `subst`; `eval`
; (the same read/eval-closing primitive `(eval (read ...))` uses
; throughout this project, see lib/reason.lisp's header for the pattern)
; then runs the now-fully-resolved expression as ordinary my-lisp code. A
; truthy result succeeds with `subst` unchanged (no new bindings, same as
; `not`); anything else fails.
;
; Крок 12: умови `(test <вираз>)` — четвертий раз той самий клас бага
; (перевірено перед виправленням, як і `not`/`or`/`and`): `(test (> ?x
; 5))` не зіставляла нічого, бо — знову — жоден факт не має головою символ
; `test`. На відміну від `not`/`or`/`and`, `test` — узагалі не комбінатор
; зіставлення: він не порівнює шаблон з фактами, а обчислює довільний
; вираз (зазвичай порівняння на кшталт `>`, уже наявний примітив my-lisp)
; після підстановки того, що вже зв'язали попередні умови. `apply-subst`
; (lib/unify.lisp) розв'язує кожен `(var name)` у виразі проти поточної
; `subst`; `eval` (той самий примітив, що замикає read/eval цикл, який
; `(eval (read ...))` використовує по всьому проєкту) тоді виконує вже
; повністю розв'язаний вираз як звичайний код my-lisp. Правдивий результат
; успішний з незмінною `subst` (без нових зв'язувань, як і `not`); усе
; інше — провал.
;
; Schritt 12: `(test <ausdruck>)`-Bedingungen — das vierte Mal, dass diese
; Bugklasse auftauchte (vor dem Fix verifiziert, wie bei `not`/`or`/`and`):
; `(test (> ?x 5))` glich überhaupt nichts ab, weil — wieder einmal — kein
; Fakt je das Symbol `test` als Kopf hat. Anders als `not`/`or`/`and` ist
; `test` überhaupt kein Abgleichs-Kombinator: es vergleicht kein Muster
; mit Fakten, sondern wertet einen beliebigen Ausdruck aus (typischerweise
; einen Vergleich wie `>`, bereits ein my-lisp-Primitiv), nachdem
; eingesetzt wurde, was vorherige Bedingungen bereits gebunden haben.
; `apply-subst` (lib/unify.lisp) löst jedes `(var name)` im Ausdruck gegen
; die aktuelle `subst` auf; `eval` (dasselbe Primitiv, das die
; Read/Eval-Schleife schließt) führt dann den nun vollständig aufgelösten
; Ausdruck als gewöhnlichen my-lisp-Code aus. Ein wahrer Wert gelingt mit
; unveränderter `subst` (keine neuen Bindungen, wie bei `not`); alles
; andere schlägt fehl.
(00001001 condition-is-test?
  (00001000 (condition)
    (00000111
      ((00000010 condition) () (00000001 ()))
      ((00000010 condition)  (00000001 ()))
      ((00000010 (00000101 condition)) () (00000011 (00000101 condition) (00000001 test)))
      ((00000010 (00000101 condition))  (00000011 (00000101 condition) (00000001 test)))
      (t (00000001 ())))))

(00001001 match-test-condition
  (00001000 (expression bindings)
    (10011100 ((result (01001101 (10001010 expression bindings))))
      ; E1 (#216): under exact-Q a false comparison answers 0, and 0 is
      ; truthy -- the pre-exact-Q two-part `(cond (result (list subst)) (t ()))`
      ; treated a falsy test as a success. A test condition is falsy when its
      ; evaluation returns () or the exact-Q 0 answer; equal?-driven clauses
      ; keep this faithful for structural truth values too (t, (structural-
      ; relation same/distinct)) without feeding comparison results to cond
      ; as numeric clauses.
      (00000111
        ((00100010 result (00000001 ())) (1)
         (00000001 ()))
        ((00100010 result (00000001 ())) (0)
         (00000111
           ((00100010 result 0) (1)
            (00000001 ()))
           ((00100010 result 0) (0)
            (00100111 bindings))))))))

; Step 15: `(exists <CE>+)`/`(forall <first-CE> <CE>+)` — the same class of
; bug as `not`/`or`/`and`/`test` (Steps 7/10-12), found by importing a
; real external CLIPS file (`tests/fixtures/sudoku-external.clp`, CLIPS's
; own Sudoku solver): `(exists (unsolved))` matched nothing, because no
; fact's head is ever the symbol `exists` — the importer's Step 19 guard
; skips any rule using `exists`/`forall` rather than import one that can
; never fire, exactly the safety net Step 7's `not` guard was before this
; step existed.
;
; `exists` succeeds if its conjunction of sub-conditions matches *at
; least once* against the current facts — but, like `not`, it binds
; nothing back into the outer `subst`: an existence check, not a source
; of new variables. `match-conditions` (already built on
; `thread-conjunction`) does exactly the matching; `match-exists-condition`
; only asks whether that came back non-empty, discarding whichever
; sub-substitution actually satisfied it and returning the *original*
; `subst` unchanged on success.
;
; `forall` looked like it could reuse `exists`/`not`/`and` the same way —
; "no counter-example exists" — but `match-negated-condition` only ever
; matches its inner pattern directly against facts (`match-condition-
; against-facts`), not through `match-one-condition`, so a `not` can't
; actually wrap a compound `and` (verified by a failing debug test before
; settling on this version, not assumed). `forall` is written directly
; instead: gather every substitution `first-condition` produces
; (`match-one-condition`, so it can itself be `not`/`or`/`and`/`exists`),
; then require every one of them to also satisfy `rest-conditions`
; (`match-conditions`, the same conjunction-threader everything else
; here uses) — if even one candidate fails, the whole `forall` fails.
;
; Крок 15: `(exists <CE>+)`/`(forall <перша-CE> <CE>+)` — той самий клас
; бага, що й `not`/`or`/`and`/`test` (Кроки 7/10-12), знайдений при
; імпорті реального зовнішнього CLIPS-файлу (`tests/fixtures/sudoku-external.clp`,
; власний Sudoku-solver CLIPS): `(exists (unsolved))` не збігалася ні з
; чим, бо жоден факт ніколи не має головою символ `exists` — guard Кроку
; 19 в імпортері пропускає будь-яке правило з `exists`/`forall`, замість
; імпортувати те, що ніколи не спрацює — саме та сітка безпеки, якою був
; guard `not` у Кроці 7 до появи цього кроку.
;
; `exists` успішний, якщо його кон'юнкція під-умов збігається
; **хоча б раз** проти поточних фактів — але, як і `not`, не зв'язує
; нічого назад у зовнішню `subst`: це перевірка існування, не джерело
; нових змінних. `match-conditions` (уже побудована на
; `thread-conjunction`) виконує саме це зіставлення; `match-exists-condition`
; лише питає, чи результат непорожній, відкидаючи будь-яку конкретну
; під-підстановку, що задовольнила умову, і повертаючи при успіху
; **незмінну оригінальну** `subst`.
;
; Виглядало, що `forall` можна так само перевикористати через
; `exists`/`not`/`and` — "не існує контрприкладу" — але
; `match-negated-condition` завжди зіставляє свій внутрішній патерн
; напряму з фактами (`match-condition-against-facts`), не через
; `match-one-condition`, тож `not` насправді не може обгорнути складену
; `and` (перевірено провальним debug-тестом перед тим, як зупинитись на
; цій версії, не здогадано). `forall` натомість написана напряму: зібрати
; кожну підстановку, яку дає `first-condition` (`match-one-condition`,
; тож вона сама може бути `not`/`or`/`and`/`exists`), а тоді вимагати,
; щоб кожна з них також задовольняла `rest-conditions` (`match-conditions`,
; той самий кон'юнкт-протягувач, що й скрізь тут) — якщо хоч один
; кандидат провалюється, весь `forall` провалюється.
;
; Schritt 15: `(exists <CE>+)`/`(forall <erste-CE> <CE>+)` — dieselbe
; Bugklasse wie `not`/`or`/`and`/`test` (Schritte 7/10-12), gefunden beim
; Import einer echten externen CLIPS-Datei (`tests/fixtures/sudoku-external.clp`,
; CLIPS' eigener Sudoku-Löser): `(exists (unsolved))` glich nichts ab,
; weil kein Fakt je das Symbol `exists` als Kopf hat — der Guard aus
; Schritt 19 im Importer überspringt jede Regel mit `exists`/`forall`,
; statt eine zu importieren, die nie feuern kann — genau das
; Sicherheitsnetz, das der `not`-Guard vor Schritt 7 war.
;
; `exists` gelingt, wenn seine Konjunktion von Unterbedingungen
; **mindestens einmal** gegen die aktuellen Fakten passt — bindet aber,
; wie `not`, nichts zurück in die äußere `subst`: eine Existenzprüfung,
; keine Quelle neuer Variablen. `match-conditions` (bereits auf
; `thread-conjunction` aufgebaut) übernimmt genau dieses Matching;
; `match-exists-condition` fragt nur, ob das Ergebnis nicht leer war,
; verwirft jede konkrete Unter-Substitution, die es erfüllt hat, und
; gibt bei Erfolg die **unveränderte ursprüngliche** `subst` zurück.
;
; Es sah so aus, als könnte `forall` genauso `exists`/`not`/`and`
; wiederverwenden — "es existiert kein Gegenbeispiel" — aber
; `match-negated-condition` gleicht sein inneres Muster immer direkt
; gegen Fakten ab (`match-condition-against-facts`), nicht über
; `match-one-condition`, sodass ein `not` ein zusammengesetztes `and`
; tatsächlich nicht umschließen kann (durch einen fehlschlagenden
; Debug-Test verifiziert, bevor diese Version feststand, nicht
; angenommen). `forall` ist stattdessen direkt geschrieben: alle
; Substitutionen sammeln, die `first-condition` liefert
; (`match-one-condition`, kann also selbst `not`/`or`/`and`/`exists`
; sein), dann verlangen, dass jede davon auch `rest-conditions` erfüllt
; (`match-conditions`, derselbe Konjunktions-Fädler wie überall hier) —
; scheitert auch nur ein Kandidat, scheitert das ganze `forall`.
(00001001 condition-is-exists?
  (00001000 (condition)
    (00000111
      ((00000010 condition) () (00000001 ()))
      ((00000010 condition)  (00000001 ()))
      ((00000010 (00000101 condition)) () (00000011 (00000101 condition) (00000001 exists)))
      ((00000010 (00000101 condition))  (00000011 (00000101 condition) (00000001 exists)))
      (t (00000001 ())))))

(00001001 match-exists-condition
  (00001000 (sub-conditions facts bindings)
    (00000111
      ((00000010 (match-conditions sub-conditions facts bindings)) () (00000001 ()))
      ((00000010 (match-conditions sub-conditions facts bindings))  (00000001 ()))
      (t (00100111 bindings)))))

(00001001 condition-is-forall?
  (00001000 (condition)
    (00000111
      ((00000010 condition) () (00000001 ()))
      ((00000010 condition)  (00000001 ()))
      ((00000010 (00000101 condition)) () (00000011 (00000101 condition) (00000001 forall)))
      ((00000010 (00000101 condition))  (00000011 (00000101 condition) (00000001 forall)))
      (t (00000001 ())))))

(00001001 forall-every-candidate-satisfies?
  (00001000 (candidates rest-conditions facts)
    (00000111
      ((00000010 candidates) () t)
      ((00000010 candidates) (1) t)
      ((00000010 (match-conditions rest-conditions facts (00000101 candidates))) () (00000001 ()))
      ((00000010 (match-conditions rest-conditions facts (00000101 candidates)))  (00000001 ()))
      (t (forall-every-candidate-satisfies? (00000110 candidates) rest-conditions facts)))))

(00001001 match-forall-condition
  (00001000 (first-condition rest-conditions facts bindings)
    (00000111
      ((forall-every-candidate-satisfies?
         (match-one-condition first-condition facts bindings) rest-conditions facts)
       (00100111 bindings))
      (t (00000001 ())))))

(00001001 match-one-condition
  (00001000 (condition facts bindings)
    (00000111
      ((condition-is-not? condition) (match-negated-condition (00101111 condition) facts bindings))
      ((condition-is-or? condition) (match-or-condition (00000110 condition) facts bindings))
      ((condition-is-and? condition) (match-and-condition (00000110 condition) facts bindings))
      ((condition-is-test? condition) (match-test-condition (00101111 condition) bindings))
      ((condition-is-exists? condition) (match-exists-condition (00000110 condition) facts bindings))
      ((condition-is-forall? condition)
       (match-forall-condition (00101111 condition) (00000110 (00000110 condition)) facts bindings))
      (t (match-condition-against-facts condition facts bindings)))))

; Built directly on `thread-conjunction` (lib/unify.lisp) — the same
; conjunction-walking kernel `lib/reason.lisp`'s `prove-goals` threads a
; richer `(subst proofs)` state through. Here `try-one` is
; `match-one-condition`: for one condition, either match it against every
; fact in the explicit list, or (for `not`) check that its inner pattern
; matches none of them — rather than recursively searching further rules.
(00001001 match-conditions
  (00001000 (conditions facts bindings)
    (thread-conjunction conditions bindings
      (00001000 (condition s) (match-one-condition condition facts s)))))

(00001001 map-apply-head
  (00001000 (head substs)
    (00000111
      ((00000010 substs) () (00000001 ()))
      ((00000010 substs)  (00000001 ()))
      (t (00000100 (10001010 head (00000101 substs)) (map-apply-head head (00000110 substs)))))))

; Fires a `(head cond1 cond2 ...)` rule against a fact list: finds every
; substitution satisfying the whole condition conjunction, and returns one
; derived `head` per substitution found (possibly the same fact more than
; once, if several substitutions produce it — downstream dedup via
; `append-new`/`member?` already handles that, same as Steps 1-5).
(00001001 fire-rule-multi
  (00001000 (rule facts)
    (00000111
      ((00000010 (00000110 rule))
       (map-apply-head (00000101 rule) (00100111 (00000001 ()))))
      ((00000100 (00000010 (00000110 rule)))
       (map-apply-head (00000101 rule) (match-conditions (00000110 rule) facts (00000001 ()))))))))

(00001001 fire-rules-multi
  (00001000 (rules facts)
    (00000111
      ((00000010 rules) (00000001 ()))
      ((00000100 (00000010 rules))
       (00101001 (fire-rule-multi (00000101 rules) facts)
                 (fire-rules-multi (00000110 rules) facts))))))

(00001001 run-multi
  (00001000 (rules facts)
    (10011100 ((merged (append-new (fire-rules-multi rules facts) facts)))
      (00000111
        ((00011100 (00101000 merged) (00101000 facts)) 1 facts)
        (t (run-multi rules merged))))))

