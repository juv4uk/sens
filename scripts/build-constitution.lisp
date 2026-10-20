; Побудова my-lisp-constitution.lisp із чинних першоджерел.
; Сценарій написано мовою СЕНС (2026-08-09), замість колишнього Python.
; Випробування з tests/fixtures/conformance.lisp уже є власними даними
; СЕНС, доступними через читання файла й усіх форм без розбирача JSON.
; Друк правильно екранує рядки: отриманий файл повторно читається
; тим самим читачем. Для цього не потрібне окреме зчеплення рядків.
;
; my-lisp-constitution.lisp — лише похідна проєкція, а не друге джерело
; істини. Такий самий принцип застосовує журнал знань: один журнал,
; а поточний стан обчислюється за потреби. Тут його використано
; для документації, а не для стану виконання.
; Не змінювати породжений файл вручну! Змінюйте вихідні випробування
; або тексти принципів і аксіом нижче, після чого запускайте:
;
;   cargo run -p sens-cli --bin sens -- scripts/build-constitution.lisp > my-lisp-constitution.lisp
;
; Командний виконавець також друкує значення останнього виразу
; (див. crates/sens-cli/tests/cli.rs). Тому сценарій завершується
; порожнім списком: додатковий надрукований () не є ще одним
; випробуванням і безпечно ігнорується читачем.

(визначити фікстури (читати-всі (читати-файл "tests/fixtures/conformance.lisp")))

(друкувати (сполучити (як-є about) "my-lisp-constitution.lisp — the executable proof of docs/language-core-axioms.md's project principles and axioms (G1-G8 generative, S1-S3 safety). Each fixture is one of the observable claims from tests/fixtures/conformance.lisp, tagged with the tier (1 CORE SEMANTICS, 2 LANGUAGE CONTRACT, 3 ECOSYSTEM CONFORMANCE) and, where one applies, the axiom(s) it is evidence for. Symbolic-reasoning fixtures (tier 3, unify/reason) carry no axiom tag on purpose — they are evidence for project principle 3, not the G/S axiom list."))

(друкувати (сполучити (як-є status) "draft — not yet ratified; will become read-only once ratified"))

    (друкувати (сполучити (як-є generated) "This file is GENERATED — do not hand-edit it. It is a projection over tests/fixtures/conformance.lisp (facts and tags in one record) plus this script's own principle/axiom text. Edit tests/fixtures/conformance.lisp or scripts/build-constitution.lisp, then run: cargo run -p sens-cli --bin sens -- scripts/build-constitution.lisp > my-lisp-constitution.lisp . Written as sens data, not JSON: readable directly via (read-all (read-file \"my-lisp-constitution.lisp\")), no foreign parser needed — the same reason conformance.lisp itself moved off JSON."))

(друкувати (сполучити (як-є self-contained) "principles and axioms below are the canonical one-line statements from docs/language-core-axioms.md, kept here so this file can be read and understood on its own; docs/language-core-axioms.md remains the single source of the full prose rationale, examples, and open questions — not duplicated here, to avoid two sources of truth for the same wording drifting apart"))

(друкувати (сполучити (як-є role-field) "Each fixture may carry a \"role\" of \"constitutive\" — meaning it directly invokes one of McCarthy's seven original primitives (quote, atom, eq, car, cdr, cons, cond), including their documented error paths. A constitutive fixture doesn't just provide evidence that an axiom holds; it's one of the acts that makes the axiom true in the first place — remove the primitive and the axiom becomes false, not just unproven. Every other fixture (role omitted, i.e. \"derived\") demonstrates a consequence built on top of the constitutive primitives — removing it could in principle still leave the axiom provable some other way."))

(друкувати (сполучити (як-є principles-document) "docs/language-core-axioms.md"))
(друкувати (сполучити (як-є tier-map) "docs/conformance-tier-map.md"))

(друкувати (список (як-є principle) 1 "Write about possibilities, not limitations." "Писати про можливості, не про обмеження."))
(друкувати (список (як-є principle) 2 "Be Lisp in the full sense of the word — homoiconicity and a minimal, closed core that grows the rest of the language from inside itself, not the surface syntax of any one historical dialect." "Бути Lisp-ом у повному розумінні цього слова — гомоіконність і мінімальне, замкнене ядро, що вирощує решту мови зсередини себе, не поверхневий синтаксис якогось одного історичного діалекту."))
(друкувати (список (як-є principle) 3 "Build the reasoning machine — McCarthy's documented 1958 Advice Taker goal, extended by the author's own hybrid neural/symbolic vision (private/lisp-to-knowledge.md)." "Реалізувати розумну машину — задокументована ціль МакКарті 1958 року (Advice Taker), продовжена власним гібридним нейро-символьним баченням автора (private/lisp-to-knowledge.md)."))
(друкувати (список (як-є principle) 4 "Cross-platform-ness, or more simply: universality — the falsifiability test for G6/G7; sens commits to real, physically different substrates (Rust, fpga-lisp), not just one implementation asserting conformance." "Кросплатформеність, або простіше — універсальність — тест на фальсифіковність для G6/G7; sens зобов'язується перед реально різними фізичними субстратами (Rust, fpga-lisp), не лише однією реалізацією, що заявляє конформність."))
(друкувати (список (як-є principle) 5 "Maximum awareness of today's technology, applied to symbolic AI — classical symbolic AI is not a museum piece; modern tooling and modern LLMs (as the fuzzy natural-language interface, not a competitor to the precise symbolic core) are part of building it." "Максимальна обізнаність у сьогоднішніх технологіях, застосована до символьного ШІ — класичний символьний AI не музейний експонат; сучасні інструменти й сучасні LLM (як нечіткий інтерфейс природної мови, не конкурент точному символьному ядру) — частина його побудови."))

(друкувати (список (як-є axiom) (як-є G1) (як-є generative) "A value's meaning can be fully defined by observable behavior." "Значення value може бути повністю визначене спостережуваною поведінкою."))
(друкувати (список (як-є axiom) (як-є G2) (як-є generative) "Every value can be built from just two things: atoms and pairs." "Кожне значення можна побудувати лише з двох речей: атомів і пар."))
(друкувати (список (як-є axiom) (як-є G3) (як-є generative) "Program structure can be inspected, transformed, and built like any other value." "Структуру програми можна оглядати, трансформувати й будувати, як і будь-яке інше значення."))
(друкувати (список (як-є axiom) (як-є G4) (як-є generative) "A minimal core can grow an entire language inside itself." "Мінімальне ядро може вирощувати всю мову всередині себе."))
(друкувати (список (як-є axiom) (як-є G5) (як-є generative) "Anything expressible within the language can live above the implementation boundary." "Усе, що виразне мовою, може жити над межею реалізації."))
(друкувати (список (як-є axiom) (як-є G6) (як-є generative) "Conformance can be defined purely by observable behavior." "Конформність можна визначити суто спостережуваною поведінкою."))
(друкувати (список (як-є axiom) (як-є G7) (як-є generative) "The same expression can mean the same thing everywhere." "Той самий вираз може означати те саме всюди."))
(друкувати (список (як-є axiom) (як-є G8) (як-є generative) "The absence of any element and the absence of truth can be the same value." "Відсутність будь-якого елемента й відсутність істини можуть бути тим самим значенням."))
(друкувати (список (як-є axiom) (як-є S1) (як-є safety) "Never silently turn an exact value into an approximation." "Ніколи мовчки не перетворювати точне значення на наближення."))
(друкувати (список (як-є axiom) (як-є S2) (як-є safety) "Never fail silently — every failure is a named, observable outcome." "Ніколи не провалюватись мовчки — кожен провал є названим, спостережуваним результатом."))
(друкувати (список (як-є axiom) (як-є S3) (як-є safety) "Never let a resource limit silently redefine an operation's meaning." "Ніколи не дозволяти обмеженню ресурсу мовчки переозначити сенс операції."))

(друкувати (список (як-є tier) 1 "CORE SEMANTICS — every conforming implementation must have this"))
(друкувати (список (як-є tier) 2 "LANGUAGE CONTRACT — every conforming implementation must have this"))
(друкувати (список (як-є tier) 3 "ECOSYSTEM CONFORMANCE — an implementation can be sens without this loaded yet; tests a library, not the language itself"))

(визначити надрукувати-приклад
  (функція (приклад)
    (друкувати (сполучити (як-є fixture) приклад))))

(визначити надрукувати-приклади
  (функція (залишок)
    (за-умовою
      ((атом? залишок) (як-є ()))
      (так ((функція ()
            (надрукувати-приклад (перше залишок))
            (надрукувати-приклади (решта залишок))))))))

(надрукувати-приклади фікстури)

(як-є ())
