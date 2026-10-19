; LEGACY_MIGRATION_DEBT #5605 / owner prohibition #5789: old #d1:0/#d1:1
; are NOT permitted literals in current SENS source. Never add/copy new ones.
; These pre-existing tokens are quarantined for the historical parse() reader.
; Retire with a positional D1 loader, positive/negative native SENS witnesses
; and exact Zig T5 round-trip; no blind substitution with numeric 0/1.
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

(визначити *working-memory* (як-є ()))

(визначити ствердити-факт!
  (make-macro
    (функція (факт)
      (список (як-є визначити) (як-є *working-memory*) (список (як-є сполучити) факт (як-є *working-memory*))))))

; Tries to unify a rule's pattern against a single fact. On success,
; returns the rule's template with the resulting bindings substituted in
; — the new fact this rule application would produce. On failure, returns
; `'no-match` rather than `'()` — an empty list would be ambiguous with a
; template that legitimately evaluates to `()`.
; Мовні зв'язування: правило/факт → шаблон/зразок → зв'язування.
; Стан середовища та маркер невдачі no-match не змінюються.
(визначити fire-rule
  (функція (правило факт)
    ((функція (шаблон зразок)
       ((функція (зв'язування)
          (за-умовою
            ((підстановка-позначає-невдачу? зв'язування)
             (як-є no-match))
            (так (застосувати-підстановка зразок зв'язування))))
        (уніфікувати шаблон факт (як-є ()))))
     (перше правило)
     (друге правило))))

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
(визначити fire-rule-on-facts
  (функція (правило факти)
    (за-умовою
      ((атом? факти) (як-є ()))
      (так
       ((функція (результат)
          (за-умовою
            ; Складений факт — успішний результат; D3 EQ приймає тільки атоми.
            ((хибне? (атом? результат))
             (сполучити
               результат
               (запустити-правило-на-факти правило (решта факти))))
            ; Лише атомарний маркер невдачі пропускаємо.
            ((тотожне? результат (як-є no-match))
             (запустити-правило-на-факти правило (решта факти)))
            (так
             (сполучити
               результат
               (запустити-правило-на-факти правило (решта факти))))))
        (запустити-правило правило (перше факти)))))))
; Convenience wrapper reading the current global working memory rather than
; requiring the caller to pass it explicitly.
(визначити fire-rule-on-working-memory
  (функція (правило-для-робочої-памяті)
    (запустити-правило-на-факти правило-для-робочої-памяті *working-memory*)))

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
(визначити fire-rules-on-facts
  (функція (правила-для-фактів факти-для-правил)
    (за-умовою
      
      ((атом? правила-для-фактів)  (як-є ()))
      (так (приєднати (запустити-правило-на-факти (перше правила-для-фактів) факти-для-правил)
                  (запустити-правила-на-факти (решта правила-для-фактів) факти-для-правил))))))

(визначити fire-rules-on-working-memory
  (функція (правила-робочої-памяті)
    (запустити-правила-на-факти правила-робочої-памяті *working-memory*)))

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

; Structural membership is a derived SENS law over fact data.
; Unlike historical D5 MEMBER, it must not call CAR on an empty list,
; nor require an unadmitted D8 EQUAL mechanism for compound facts.
(визначити факт-наявний?
  (функція (факт-для-пошуку память-для-пошуку)
    (за-умовою
      ((порожній? память-для-пошуку) ні)
      ((unify-equal? факт-для-пошуку (перше память-для-пошуку)) так)
      (так (факт-наявний? факт-для-пошуку (решта память-для-пошуку))))))

(визначити додати-нові
  (функція (нові-факти наявні-факти)
    (за-умовою
      ((атом? нові-факти) наявні-факти)
      ((факт-наявний? (перше нові-факти) наявні-факти)
       (додати-нові (решта нові-факти) наявні-факти))
      (так
       (додати-нові
         (решта нові-факти)
         (сполучити (перше нові-факти) наявні-факти))))))

(визначити запустити
  (функція (правила факти)
    ((функція (злиті-факти)
       (за-умовою
         ((unify-equal? (довжина злиті-факти) (довжина факти)) факти)
         (так (запустити правила злиті-факти))))
     (додати-нові (запустити-правила-на-факти правила факти) факти))))

(визначити ствердити-факти!
  (make-macro
    (функція (факти)
      (список (як-є визначити) (як-є *working-memory*) (список (як-є додати-нові) факти (як-є *working-memory*))))))

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
(визначити retract-fact
  (функція (факт-для-вилучення факти-перед-вилученням)
    (за-умовою
      
      ((атом? факти-перед-вилученням)  (як-є ()))
      ((unify-equal? факт-для-вилучення (перше факти-перед-вилученням)) (решта факти-перед-вилученням))
      (так (сполучити (перше факти-перед-вилученням) (відкликати-факт факт-для-вилучення (решта факти-перед-вилученням)))))))

(визначити retract-fact!
  (make-macro
    (функція (fact)
      (список (як-є визначити) (як-є *working-memory*) (список (як-є відкликати-факт) fact (як-є *working-memory*))))))

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
(визначити make-justified
  (функція (факт-із-підставами підстави-факту)
    (сполучити факт-із-підставами підстави-факту)))

(визначити fact-of (функція (запис-обґрунтування) (перше запис-обґрунтування)))
(визначити supports-of (функція (запис-обґрунтування) (решта запис-обґрунтування)))
(визначити axiom (функція (аксіоматичний-факт) (створити-обґрунтований аксіоматичний-факт (як-є ()))))

(визначити map-fact-of
  (функція (записи-обґрунтувань)
    (за-умовою
      
      ((атом? записи-обґрунтувань)  (як-є ()))
      (так (сполучити (факт-від (перше записи-обґрунтувань)) (мапа-факт-від (решта записи-обґрунтувань)))))))

; Same `fire-rule` as Step 1, but wraps a successful result with the
; single supporting fact that produced it.
(визначити fire-rule-tms
  (функція (правило факт)
    ((функція (результат)
       (за-умовою
         ; Успішний складений факт не порівнюється атомарним D3 EQ.
         ((хибне? (атом? результат))
          (створити-обґрунтований результат (список факт)))
         ((тотожне? результат (як-є no-match)) (як-є no-match))
         (так (створити-обґрунтований результат (список факт)))))
     (запустити-правило правило факт))))

(визначити fire-rule-on-facts-tms
  (функція (правило факти)
    (за-умовою
      ((атом? факти) (як-є ()))
      (так
       ((функція (результат)
          (за-умовою
            ; Лише атомарний no-match пропускаємо; складена пара — доказ.
            ((атом? результат)
             (запустити-правило-на-факти-система-істини правило (решта факти)))
            (так
             (сполучити
               результат
               (запустити-правило-на-факти-система-істини правило (решта факти))))))
        (запустити-правило-система-істини правило (перше факти)))))))

(визначити fire-rules-on-facts-tms
  (функція (rules facts)
    (за-умовою
      
      ((атом? rules)  (як-є ()))
      (так (приєднати (запустити-правило-на-факти-система-істини (перше rules) facts)
                  (запустити-правила-на-факти-система-істини (решта rules) facts))))))

(визначити justified-member?
  (функція (fact entries)
    (за-умовою
      
      ((атом? entries)  (як-є ()))
      ((unify-equal? fact (факт-від (перше entries))) так)
      (так (обґрунтований-член? fact (решта entries))))))

(визначити add-new-justified
  (функція (new-entries entries)
    (за-умовою
      
      ((атом? new-entries)  entries)
      ((обґрунтований-член? (факт-від (перше new-entries)) entries)
       (додати-нові-обґрунтований (решта new-entries) entries))
      (так (додати-нові-обґрунтований (решта new-entries) (сполучити (перше new-entries) entries))))))

; The fixpoint loop over justified facts, mirroring `run` from Step 4.
(визначити run-tms
  (функція (rules entries)
    ((функція (new-entries) ((функція (merged) (за-умовою
          ((unify-equal? (довжина merged) (довжина entries))  entries)
          (так (запустити-система-істини rules merged)))) (додати-нові-обґрунтований new-entries entries))) (запустити-правила-на-факти-система-істини rules (мапа-факт-від entries)))))

(визначити *justified-memory* (як-є ()))

(визначити assert-fact-tms!
  (make-macro
    (функція (fact)
      (список (як-є визначити) (як-є *justified-memory*) (список (як-є додати-нові-обґрунтований) (список (як-є список) (список (як-є аксіома) fact)) (як-є *justified-memory*))))))

(визначити run-tms!
  (make-macro
    (функція (rules)
      (список (як-є визначити) (як-є *justified-memory*) (список (як-є запустити-система-істини) rules (як-є *justified-memory*))))))

(визначити remove-justified
  (функція (fact entries)
    (за-умовою
      
      ((атом? entries)  (як-є ()))
      ((unify-equal? fact (факт-від (перше entries))) (видалити-обґрунтований fact (решта entries)))
      (так (сполучити (перше entries) (видалити-обґрунтований fact (решта entries)))))))

(визначити dependents-of
  (функція (fact entries)
    (за-умовою
      
      ((атом? entries)  (як-є ()))
      ((значення-у-списку? fact (підтримки-від (перше entries)))
       (сполучити (факт-від (перше entries)) (залежні-від fact (решта entries))))
      (так (залежні-від fact (решта entries))))))

; Retracts `fact`, then recursively retracts everything that named it in
; their support set — the cascade truth maintenance is for.
(визначити retract-fact-tms
  (функція (fact entries)
    (відкликати-факти-система-істини (залежні-від fact entries) (видалити-обґрунтований fact entries))))

(визначити retract-facts-tms
  (функція (facts entries)
    (за-умовою
      
      ((атом? facts)  entries)
      (так (відкликати-факти-система-істини (решта facts) (відкликати-факт-система-істини (перше facts) entries))))))

(визначити retract-fact-tms!
  (make-macro
    (функція (fact)
      (список (як-є визначити) (як-є *justified-memory*) (список (як-є відкликати-факт-система-істини) fact (як-є *justified-memory*))))))

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
(визначити justifications-of (функція (entry) (решта entry)))

(визначити fire-rule-jtms
  (функція (rule fact)
    ((функція (result) (за-умовою
        ((хибне? (атом? result)) (за-умовою
           ((тотожне? result (як-є no-match)) (як-є no-match))
           (так (список result (список fact)))))
        ((атом? result)  (за-умовою
           ((тотожне? result (як-є no-match)) (як-є no-match))
           (так (список result (список fact)))))
        (так (список result (список fact))))) (запустити-правило rule fact))))

(визначити fire-rule-on-facts-jtms
  (функція (rule facts)
    (за-умовою
      
      ((атом? facts)  (як-є ()))
      (так ((функція (result) (за-умовою
             ((хибне? (атом? result)) (запустити-правило-на-факти-система-обґрунтувань rule (решта facts)))
             ((атом? result)  (запустити-правило-на-факти-система-обґрунтувань rule (решта facts)))
             (так (сполучити result (запустити-правило-на-факти-система-обґрунтувань rule (решта facts)))))) (запустити-правило-система-обґрунтувань rule (перше facts)))))))

(визначити fire-rules-on-facts-jtms
  (функція (rules facts)
    (за-умовою
      
      ((атом? rules)  (як-є ()))
      (так (приєднати (запустити-правило-на-факти-система-обґрунтувань (перше rules) facts)
                  (запустити-правила-на-факти-система-обґрунтувань (решта rules) facts))))))

(визначити find-entry
  (функція (fact entries)
    (за-умовою
      
      ((атом? entries)  (як-є ()))
      ((unify-equal? fact (факт-від (перше entries))) (перше entries))
      (так (find-entry fact (решта entries))))))

(визначити remove-entry-jtms
  (функція (fact entries)
    (за-умовою
      
      ((атом? entries)  (як-є ()))
      ((unify-equal? fact (факт-від (перше entries))) (видалити-запис-система-обґрунтувань fact (решта entries)))
      (так (сполучити (перше entries) (видалити-запис-система-обґрунтувань fact (решта entries)))))))

; Folds one new `(fact justification)` pair into `entries`: a brand-new
; fact gets a fresh entry; a fact already present gets `justification`
; added to its list only if not already there (so re-deriving the same way
; twice is a no-op, needed for `run-jtms`'s fixpoint check to terminate).
(визначити add-justification
  (функція (fact justification entries)
    ((функція (existing) (за-умовою
        ((хибне? (атом? existing)) (сполучити (список fact justification) entries))
        ((атом? existing)  (сполучити (список fact justification) entries))
        ((значення-у-списку? justification (обґрунтування-від existing)) entries)
        (так (сполучити (сполучити fact (сполучити justification (обґрунтування-від existing)))
                 (видалити-запис-система-обґрунтувань fact entries))))) (find-entry fact entries))))

(визначити add-new-entries-jtms
  (функція (new-entries entries)
    (за-умовою
      
      ((атом? new-entries)  entries)
      (так (додати-нові-записи-система-обґрунтувань
           (решта new-entries)
           (додати-обґрунтування (факт-від (перше new-entries)) (друге (перше new-entries)) entries))))))

; The fixpoint loop. Compares the merged result to the input with `equal?`
; rather than a length/count check (Step 4's `run` compares lengths) —
; `add-justification` can grow an *existing* entry's justification list
; without changing the entry count, so counting entries alone would miss
; real progress and stop too early.
(визначити run-jtms
  (функція (rules entries)
    ((функція (merged) (за-умовою
        ((unify-equal? merged entries) entries)
        (так (запустити-система-обґрунтувань rules merged)))) (додати-нові-записи-система-обґрунтувань (запустити-правила-на-факти-система-обґрунтувань rules (мапа-факт-від entries)) entries))))

(визначити *jtms-memory* (як-є ()))

(визначити assert-fact-jtms!
  (make-macro
    (функція (fact)
      (список (як-є визначити) (як-є *jtms-memory*) (список (як-є додати-обґрунтування) fact (список (як-є як-є) (як-є ())) (як-є *jtms-memory*))))))

(визначити run-jtms!
  (make-macro
    (функція (rules)
      (список (як-є визначити) (як-є *jtms-memory*) (список (як-є запустити-система-обґрунтувань) rules (як-є *jtms-memory*))))))

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
(визначити jtms-state-subst (функція (state) (перше state)))
(визначити jtms-state-used (функція (state) (решта state)))
(визначити jtms-make-state (функція (bindings used) (сполучити bindings used)))

(визначити match-plain-condition-jtms
  (функція (condition facts state)
    (за-умовою
      
      ((атом? facts)  (як-є ()))
      (так ((функція (s) (за-умовою
             ((підстановка-позначає-невдачу? s) (зіставити-звичайну-умову-з-фактами-система-обґрунтувань condition (решта facts) state))
             (так (сполучити (система-обґрунтувань-створити-стан s (сполучити (перше facts) (отримати-використані-факти-зі-стану-система-обґрунтувань state)))
                       (зіставити-звичайну-умову-з-фактами-система-обґрунтувань condition (решта facts) state))))) (уніфікувати condition (перше facts) (отримати-підстановку-зі-стану-система-обґрунтувань state)))))))

(визначити match-or-condition-jtms
  (функція (alternatives facts state)
    (за-умовою
      
      ((атом? alternatives)  (як-є ()))
      (так (приєднати (зіставити-одну-умову-правила-система-обґрунтувань (перше alternatives) facts state)
                  (зіставити-диз'юнкцію-з-фактами-система-обґрунтувань (решта alternatives) facts state))))))

(визначити match-one-condition-jtms
  (функція (condition facts state)
    (за-умовою
      ((умова-має-форму-заперечення? condition)
       (за-умовою
         ((хибне? (атом? (зіставити-умову-із-набором-фактів (друге condition) facts (отримати-підстановку-зі-стану-система-обґрунтувань state)))) (список state))
         ((атом? (зіставити-умову-із-набором-фактів (друге condition) facts (отримати-підстановку-зі-стану-система-обґрунтувань state)))  (список state))
         ))
      ((умова-має-форму-диз'юнкції? condition) (зіставити-диз'юнкцію-з-фактами-система-обґрунтувань (решта condition) facts state))
      ((умова-має-форму-кон'юнкції? condition) (зіставити-умови-система-обґрунтувань (решта condition) facts state))
      ((умова-має-тестову-форму? condition)
       (за-умовою
         ((обчислити (застосувати-підстановка (друге condition) (отримати-підстановку-зі-стану-система-обґрунтувань state))) (список state))
         ))
      (так (зіставити-звичайну-умову-з-фактами-система-обґрунтувань condition facts state)))))

(визначити match-conditions-jtms
  (функція (conditions facts state)
    (потік-виконання-кон'юнкція conditions state
      (функція (condition s) (зіставити-одну-умову-правила-система-обґрунтувань condition facts s)))))

(визначити map-apply-head-jtms
  (функція (head states)
    (за-умовою
      
      ((атом? states)  (як-є ()))
      (так (сполучити (список (застосувати-підстановка head (отримати-підстановку-зі-стану-система-обґрунтувань (перше states))) (отримати-використані-факти-зі-стану-система-обґрунтувань (перше states)))
                (map-apply-head-jtms head (решта states)))))))

(визначити fire-rule-jtms-multi
  (функція (rule facts)
    (map-apply-head-jtms (перше rule) (зіставити-умови-система-обґрунтувань (решта rule) facts (система-обґрунтувань-створити-стан (як-є ()) (як-є ()))))))

(визначити fire-rules-jtms-multi
  (функція (rules facts)
    (за-умовою
      
      ((атом? rules)  (як-є ()))
      (так (приєднати (запустити-правило-система-обґрунтувань-мульти (перше rules) facts)
                  (запустити-правила-система-обґрунтувань-мульти (решта rules) facts))))))

(визначити run-jtms-multi
  (функція (rules entries)
    ((функція (merged) (за-умовою
        ((unify-equal? merged entries) entries)
        (так (запустити-система-обґрунтувань-мульти rules merged)))) (додати-нові-записи-система-обґрунтувань (запустити-правила-система-обґрунтувань-мульти rules (мапа-факт-від entries)) entries))))

(визначити run-jtms-multi!
  (make-macro
    (функція (rules)
      (список (як-є визначити) (як-є *jtms-memory*) (список (як-є запустити-система-обґрунтувань-мульти) rules (як-є *jtms-memory*))))))

(визначити prune-justifications
  (функція (fact justifications)
    (за-умовою
      
      ((атом? justifications)  (як-є ()))
      ((значення-у-списку? fact (перше justifications)) (обрізати-обґрунтування fact (решта justifications)))
      (так (сполучити (перше justifications) (обрізати-обґрунтування fact (решта justifications)))))))

(визначити prune-entry
  (функція (fact entry)
    (сполучити (факт-від entry) (обрізати-обґрунтування fact (обґрунтування-від entry)))))

(визначити prune-all-entries
  (функція (fact entries)
    (за-умовою
      
      ((атом? entries)  (як-є ()))
      (так (сполучити (обрізати-запис fact (перше entries)) (обрізати-всі-записи fact (решта entries)))))))

(визначити unsupported-facts
  (функція (entries)
    (за-умовою
      
      ((атом? entries)  (як-є ()))
      ((хибне? (атом? (обґрунтування-від (перше entries)))) (сполучити (факт-від (перше entries)) (непідтримані-факти (решта entries))))
      ((атом? (обґрунтування-від (перше entries)))  (сполучити (факт-від (перше entries)) (непідтримані-факти (решта entries))))
      (так (непідтримані-факти (решта entries))))))

(визначити drop-unsupported
  (функція (entries)
    (за-умовою
      
      ((атом? entries)  (як-є ()))
      ((хибне? (атом? (обґрунтування-від (перше entries)))) (відкинути-непідтримані (решта entries)))
      ((атом? (обґрунтування-від (перше entries)))  (відкинути-непідтримані (решта entries)))
      (так (сполучити (перше entries) (відкинути-непідтримані (решта entries)))))))

; Removes `fact`'s own entry outright, then prunes every justification-set
; elsewhere that named it. Any entry left with zero justification-sets has
; lost all support and cascade-retracts in turn — recursively, the same way
; Step 5b's single-justification cascade works, just checking "any
; justification left" instead of "any support left".
(визначити retract-fact-jtms
  (функція (fact entries)
    ((функція (pruned) ((функція (newly-unsupported remaining) (за-умовою
          
          ((атом? newly-unsupported)  remaining)
          (так (відкликати-факти-система-обґрунтувань newly-unsupported remaining)))) (непідтримані-факти pruned) (відкинути-непідтримані pruned))) (обрізати-всі-записи fact (видалити-запис-система-обґрунтувань fact entries)))))

(визначити retract-facts-jtms
  (функція (facts entries)
    (за-умовою
      
      ((атом? facts)  entries)
      (так (відкликати-факти-система-обґрунтувань (решта facts) (відкликати-факт-система-обґрунтувань (перше facts) entries))))))

(визначити retract-fact-jtms!
  (make-macro
    (функція (fact)
      (список (як-є визначити) (як-є *jtms-memory*) (список (як-є відкликати-факт-система-обґрунтувань) fact (як-є *jtms-memory*))))))

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
(визначити match-condition-against-facts
  (функція (condition facts bindings)
    (за-умовою
      
      ((атом? facts)  (як-є ()))
      (так ((функція (s) (за-умовою
             ((підстановка-позначає-невдачу? s) (зіставити-умову-із-набором-фактів condition (решта facts) bindings))
             (так (сполучити s (зіставити-умову-із-набором-фактів condition (решта facts) bindings))))) (уніфікувати condition (перше facts) bindings))))))

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
; A negated condition is an exact D1 predicate, never the list (1).
; Both tags are atoms; a compound head is not a negation operator.
(визначити condition-is-not?
  (функція (condition)
    (за-умовою
      ((атом? condition) ні)
      ((хибне? (атом? (перше condition))) ні)
      ((тотожне? (перше condition) (як-є not?)) так)
      ((тотожне? (перше condition) (як-є not)) так)
      (так ні))))

; Negation-as-failure: keep the original substitution only if no fact
; matches the inner condition; a match must produce zero candidates.
(визначити match-negated-condition
  (функція (inner-pattern facts bindings)
    (за-умовою
      ((атом? (зіставити-умову-із-набором-фактів inner-pattern facts bindings))
       (список bindings))
      (так (як-є ())))))

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
(визначити condition-is-or?
  (функція (condition)
    (за-умовою
      
      ((атом? condition)  (як-є ()))
      ((хибне? (атом? (перше condition))) (тотожне? (перше condition) (як-є or)))
      ((атом? (перше condition))  (тотожне? (перше condition) (як-є or)))
      )))

(визначити match-or-condition
  (функція (alternatives facts bindings)
    (за-умовою
      
      ((атом? alternatives)  (як-є ()))
      (так (приєднати (зіставити-одну-умову-правила (перше alternatives) facts bindings)
                  (зіставити-умову-логічного-або (решта alternatives) facts bindings))))))

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
(визначити condition-is-and?
  (функція (condition)
    (за-умовою
      
      ((атом? condition)  (як-є ()))
      ((хибне? (атом? (перше condition))) (тотожне? (перше condition) (як-є and)))
      ((атом? (перше condition))  (тотожне? (перше condition) (як-є and)))
      )))

(визначити match-and-condition
  (функція (sub-conditions facts bindings)
    (зіставити-умови sub-conditions facts bindings)))

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
(визначити condition-is-test?
  (функція (condition)
    (за-умовою
      
      ((атом? condition)  (як-є ()))
      ((хибне? (атом? (перше condition))) (тотожне? (перше condition) (як-є test)))
      ((атом? (перше condition))  (тотожне? (перше condition) (як-є test)))
      )))

(визначити match-test-condition
  (функція (expression bindings)
    (нехай-похідне ((result (обчислити (застосувати-підстановка expression bindings))))
      ; E1 (#216): under exact-Q a false comparison answers 0, and 0 is
      ; truthy -- the pre-exact-Q two-part `(cond (result (list subst)) (t ()))`
      ; treated a falsy test as a success. A test condition is falsy when its
      ; evaluation returns () or the exact-Q 0 answer; equal?-driven clauses
      ; keep this faithful for structural truth values too (t, (structural-
      ; relation same/distinct)) without feeding comparison results to cond
      ; as numeric clauses.
      (за-умовою
        ((unify-equal? result (як-є ())) 
         (як-є ()))
        ((хибне? (unify-equal? result (як-є ())))
         (за-умовою
           ((unify-equal? result 0) 
            (як-є ()))
           ((хибне? (unify-equal? result 0))
            (список bindings))))))))

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
(визначити condition-is-exists?
  (функція (condition)
    (за-умовою
      
      ((атом? condition)  (як-є ()))
      ((хибне? (атом? (перше condition))) (тотожне? (перше condition) (як-є exists)))
      ((атом? (перше condition))  (тотожне? (перше condition) (як-є exists)))
      )))

(визначити match-exists-condition
  (функція (sub-conditions facts bindings)
    (за-умовою
      
      ((атом? (зіставити-умови sub-conditions facts bindings))  (як-є ()))
      (так (список bindings)))))

(визначити condition-is-forall?
  (функція (condition)
    (за-умовою
      
      ((атом? condition)  (як-є ()))
      ((хибне? (атом? (перше condition))) (тотожне? (перше condition) (як-є forall)))
      ((атом? (перше condition))  (тотожне? (перше condition) (як-є forall)))
      )))

(визначити forall-every-candidate-satisfies?
  (функція (candidates rest-conditions facts)
    (за-умовою
      
      ((атом? candidates)  так)
      
      ((атом? (зіставити-умови rest-conditions facts (перше candidates)))  (як-є ()))
      (так (кожен-кандидат-задовольняє-умову? (решта candidates) rest-conditions facts)))))

(визначити match-forall-condition
  (функція (first-condition rest-conditions facts bindings)
    (за-умовою
      ((кожен-кандидат-задовольняє-умову?
         (зіставити-одну-умову-правила first-condition facts bindings) rest-conditions facts)
       (список bindings))
      )))

(визначити match-one-condition
  (функція (condition facts bindings)
    (за-умовою
      ((умова-має-форму-заперечення? condition) (зіставити-заперечену-умову-правила (друге condition) facts bindings))
      ((умова-має-форму-диз'юнкції? condition) (зіставити-умову-логічного-або (решта condition) facts bindings))
      ((умова-має-форму-кон'юнкції? condition) (зіставити-умову-кон'юнкції (решта condition) facts bindings))
      ((умова-має-тестову-форму? condition) (зіставити-тестову-умову (друге condition) bindings))
      ((умова-має-квантор-існування? condition) (зіставити-умову-існування (решта condition) facts bindings))
      ((умова-має-загальний-квантор? condition)
       (зіставити-умову-для-всіх-кандидатів (друге condition) (решта (решта condition)) facts bindings))
      (так (зіставити-умову-із-набором-фактів condition facts bindings)))))

; Built directly on `thread-conjunction` (lib/unify.lisp) — the same
; conjunction-walking kernel `lib/reason.lisp`'s `prove-goals` threads a
; richer `(subst proofs)` state through. Here `try-one` is
; `match-one-condition`: for one condition, either match it against every
; fact in the explicit list, or (for `not`) check that its inner pattern
; matches none of them — rather than recursively searching further rules.
(визначити match-conditions
  (функція (conditions facts bindings)
    (потік-виконання-кон'юнкція conditions bindings
      (функція (condition s) (зіставити-одну-умову-правила condition facts s)))))

(визначити map-apply-head
  (функція (head substs)
    (за-умовою
      
      ((атом? substs)  (як-є ()))
      (так (сполучити (застосувати-підстановка head (перше substs)) (map-apply-head head (решта substs)))))))

; Fires a `(head cond1 cond2 ...)` rule against a fact list: finds every
; substitution satisfying the whole condition conjunction, and returns one
; derived `head` per substitution found (possibly the same fact more than
; once, if several substitutions produce it — downstream dedup via
; `append-new`/`member?` already handles that, same as Steps 1-5).
(визначити fire-rule-multi
  (функція (rule facts)
    (за-умовою
      ((атом? (решта rule))
       (map-apply-head (перше rule) (список (як-є ()))))
      ((хибне? (атом? (решта rule)))
       (map-apply-head (перше rule) (зіставити-умови (решта rule) facts (як-є ())))))))

(визначити fire-rules-multi
  (функція (rules facts)
    (за-умовою
      ((атом? rules) (як-є ()))
      ((хибне? (атом? rules))
       (приєднати (застосувати-одне-правило-до-всіх-збігів (перше rules) facts)
                 (застосувати-правила-до-всіх-збігів (решта rules) facts))))))

(визначити виконати-багатоваріантне-виведення
  (функція (правила факти)
    ((функція (об'єднані) (за-умовою
        ((unify-equal? (довжина об'єднані) (довжина факти)) факти)
        (так (виконати-багатоваріантне-виведення правила об'єднані))))
      (додати-нові (застосувати-правила-до-всіх-збігів правила факти) факти))))

; Історичне зовнішнє ім'я — те саме мовне замикання.
(визначити run-multi виконати-багатоваріантне-виведення)

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити додати-обґрунтування add-justification)
(визначити додати-нові-записи-система-обґрунтувань add-new-entries-jtms)
(визначити додати-нові-обґрунтований add-new-justified)
(визначити умова-має-форму-кон'юнкції? condition-is-and?)
(визначити умова-має-квантор-існування? condition-is-exists?)
(визначити умова-має-загальний-квантор? condition-is-forall?)
(визначити умова-має-форму-заперечення? condition-is-not?)
(визначити умова-має-форму-диз'юнкції? condition-is-or?)
(визначити умова-має-тестову-форму? condition-is-test?)
(визначити залежні-від dependents-of)
(визначити відкинути-непідтримані drop-unsupported)
(визначити факт-від fact-of)
(визначити запустити-правило-система-обґрунтувань fire-rule-jtms)
(визначити запустити-правило-система-обґрунтувань-мульти fire-rule-jtms-multi)
(визначити застосувати-одне-правило-до-всіх-збігів fire-rule-multi)
(визначити запустити-правило-на-факти-система-обґрунтувань fire-rule-on-facts-jtms)
(визначити запустити-правило-на-факти-система-істини fire-rule-on-facts-tms)
(визначити запустити-правило-система-істини fire-rule-tms)
(визначити запустити-правила-система-обґрунтувань-мульти fire-rules-jtms-multi)
(визначити застосувати-правила-до-всіх-збігів fire-rules-multi)
(визначити запустити-правила-на-факти-система-обґрунтувань fire-rules-on-facts-jtms)
(визначити запустити-правила-на-факти-система-істини fire-rules-on-facts-tms)
(визначити кожен-кандидат-задовольняє-умову? forall-every-candidate-satisfies?)
(визначити система-обґрунтувань-створити-стан jtms-make-state)
(визначити отримати-підстановку-зі-стану-система-обґрунтувань jtms-state-subst)
(визначити отримати-використані-факти-зі-стану-система-обґрунтувань jtms-state-used)
(визначити обґрунтування-від justifications-of)
(визначити обґрунтований-член? justified-member?)
(визначити створити-обґрунтований make-justified)
(визначити мапа-факт-від map-fact-of)
(визначити зіставити-умову-кон'юнкції match-and-condition)
(визначити зіставити-умову-із-набором-фактів match-condition-against-facts)
(визначити зіставити-умови match-conditions)
(визначити зіставити-умови-система-обґрунтувань match-conditions-jtms)
(визначити зіставити-умову-існування match-exists-condition)
(визначити зіставити-умову-для-всіх-кандидатів match-forall-condition)
(визначити зіставити-заперечену-умову-правила match-negated-condition)
(визначити зіставити-одну-умову-правила match-one-condition)
(визначити зіставити-одну-умову-правила-система-обґрунтувань match-one-condition-jtms)
(визначити зіставити-умову-логічного-або match-or-condition)
(визначити зіставити-диз'юнкцію-з-фактами-система-обґрунтувань match-or-condition-jtms)
(визначити зіставити-звичайну-умову-з-фактами-система-обґрунтувань match-plain-condition-jtms)
(визначити зіставити-тестову-умову match-test-condition)
(визначити обрізати-обґрунтування prune-justifications)
(визначити видалити-запис-система-обґрунтувань remove-entry-jtms)
(визначити видалити-обґрунтований remove-justified)
(визначити відкликати-факт-система-обґрунтувань retract-fact-jtms)
(визначити відкликати-факт-система-істини retract-fact-tms)
(визначити відкликати-факти-система-обґрунтувань retract-facts-jtms)
(визначити відкликати-факти-система-істини retract-facts-tms)
(визначити підтримки-від supports-of)

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити потік-виконання-кон'юнкція thread-conjunction)

; D9-аліаси нижче потребують уже визначених локальних українських замикань.
; Ніколи не пов'язувати ім'я з невизначеним символом до його DEFINE.
; D9 Ukrainian projections of existing TMS/JTMS language-owned functions.
; Source: lib/forward.lisp and knowledge/d9-final-semantic-fill-v1.json.
; Preserve exact ratified coordinates; no new D9 native opcode.
; D9:010100111
(визначити відкликати-факт-tms відкликати-факт-система-істини)
; D9:001101100
(визначити відкликати-факти-tms відкликати-факти-система-істини)
; D9:001100010
(визначити додати-нові-записи-jtms додати-нові-записи-система-обґрунтувань)
; D9:010101101
(визначити непідтримані-факти unsupported-facts)
; D9:010111001
(визначити відкликати-факт-jtms відкликати-факт-система-обґрунтувань)
; D9:001011010
(визначити відкликати-факти-jtms відкликати-факти-система-обґрунтувань)
; D9:010000011
(визначити обрізати-запис prune-entry)
; D9:010100011
(визначити обрізати-всі-записи prune-all-entries)

; Відповідність точним D9-словам визначена в lib/domains/d9.lisp.
; Ці проєкції повторно використовують наявні SENS-функції, не створюють
; механізмів Zig/Rust або права на прямий виклик D9-бітів.
; Прямий висновок — SENS DEFINE поверх уже наявних функцій
; D9:101001000
(визначити запустити-правило fire-rule)
; D9:010110000
(визначити запустити-правило-на-факти fire-rule-on-facts)
; D9:001011101
(визначити запустити-правило-на-робоча-пам'ять fire-rule-on-working-memory)
; D9:010101010
(визначити запустити-правила-на-факти fire-rules-on-facts)
; D9:001001100
(визначити запустити-правила-на-робоча-пам'ять fire-rules-on-working-memory)
; D9:010001011
; D9:001001000
(визначити відкликати-факт retract-fact)
; Точні повні D9 `укр` і наявні SENS-замикання. Цитовані макросні голови
; повинні мати виконуване мовне зв'язування до першого виклику макросу.
; D9:001111011 AXIOM — (факт . порожній список).
(визначити аксіома axiom)
; D9:001101000 RUN-TMS
(визначити запустити-система-істини run-tms)
; D9:010000100 RUN-JTMS
(визначити запустити-система-обґрунтувань run-jtms)
; D9:010110010 RUN-JTMS-MULTI
(визначити запустити-система-обґрунтувань-мульти run-jtms-multi)

; TMS — SENS DEFINE поверх уже наявних функцій
; D9:010011111
(визначити запустити-правило-tms запустити-правило-система-істини)
; D9:010110101
(визначити запустити-правило-на-факти-tms запустити-правило-на-факти-система-істини)
; D9:101000010
(визначити запустити-правила-на-факти-tms запустити-правила-на-факти-система-істини)
; D9:001101000
(визначити запустити-tms run-tms)
; JTMS — SENS DEFINE поверх уже наявних функцій
; D9:101001001
(визначити запустити-правило-jtms запустити-правило-система-обґрунтувань)
; D9:001111110
(визначити запустити-правило-на-факти-jtms запустити-правило-на-факти-система-обґрунтувань)
; D9:001001110
(визначити запустити-правила-на-факти-jtms запустити-правила-на-факти-система-обґрунтувань)
; D9:001101110
(визначити видалити-запис-jtms видалити-запис-система-обґрунтувань)
; D9:010000100
(визначити запустити-jtms run-jtms)
; D9:010000101
(визначити запустити-правило-jtms-мульти запустити-правило-система-обґрунтувань-мульти)
; D9:001001111
(визначити запустити-правила-jtms-мульти запустити-правила-система-обґрунтувань-мульти)
; D9:010110010
(визначити запустити-jtms-мульти run-jtms-multi)


