; scripts/build-constitution.lisp — regenerate my-lisp-constitution.lisp from
; its real sources of truth, written in sens itself (2026-08-09,
; replacing the old Python version now that both real blockers are gone:
; tests/fixtures/conformance.lisp is native sens data, readable via
; read-file/read-all with no JSON parser needed, and `print` now escapes
; strings correctly, so a plain (print value) call is enough to emit
; correct, re-readable .lisp output — no string-append needed either.
;
; my-lisp-constitution.lisp is a *projection*, not a second source of truth
; — the same pattern lib/knowledge.lisp's *knowledge-journal* uses (one
; append-only log, current state computed on demand), applied here to
; documentation instead of runtime state. Never hand-edit the generated
; file; edit tests/fixtures/conformance.lisp (or this script's own
; PRINCIPLES/AXIOMS text below), then rerun this script:
;
;   cargo run -p sens-cli -- scripts/build-constitution.lisp > my-lisp-constitution.lisp
;
; The CLI always echoes the final expression's value after the print
; transcript (see crates/sens-cli/tests/cli.rs) — this script ends with
; a bare '() for exactly that reason, so the echoed extra line is a
; harmless "()" a reader can skip, not a duplicated fixture.

(0011 fixtures (110101001 (110110111 "tests/fixtures/conformance.lisp")))

(11011011 (111 (001 about) "my-lisp-constitution.lisp — the executable proof of docs/language-core-axioms.md's project principles and axioms (G1-G8 generative, S1-S3 safety). Each fixture is one of the observable claims from tests/fixtures/conformance.lisp, tagged with the tier (1 CORE SEMANTICS, 2 LANGUAGE CONTRACT, 3 ECOSYSTEM CONFORMANCE) and, where one applies, the axiom(s) it is evidence for. Symbolic-reasoning fixtures (tier 3, unify/reason) carry no axiom tag on purpose — they are evidence for project principle 3, not the G/S axiom list."))

(11011011 (111 (001 status) "draft — not yet ratified; will become read-only once ratified"))

(11011011 (111 (001 generated) "This file is GENERATED — do not hand-edit it. It is a projection over tests/fixtures/conformance.lisp (facts and tags in one record) plus this script's own principle/axiom text. Edit tests/fixtures/conformance.lisp or scripts/build-constitution.lisp, then run: cargo run -p sens-cli -- scripts/build-constitution.lisp > my-lisp-constitution.lisp . Written as sens data, not JSON: readable directly via (read-all (read-file \"my-lisp-constitution.lisp\")), no foreign parser needed — the same reason conformance.lisp itself moved off JSON."))

(11011011 (111 (001 self-contained) "principles and axioms below are the canonical one-line statements from docs/language-core-axioms.md, kept here so this file can be read and understood on its own; docs/language-core-axioms.md remains the single source of the full prose rationale, examples, and open questions — not duplicated here, to avoid two sources of truth for the same wording drifting apart"))

(11011011 (111 (001 role-field) "Each fixture may carry a \"role\" of \"constitutive\" — meaning it directly invokes one of McCarthy's seven original primitives (quote, atom, eq, car, cdr, cons, cond), including their documented error paths. A constitutive fixture doesn't just provide evidence that an axiom holds; it's one of the acts that makes the axiom true in the first place — remove the primitive and the axiom becomes false, not just unproven. Every other fixture (role omitted, i.e. \"derived\") demonstrates a consequence built on top of the constitutive primitives — removing it could in principle still leave the axiom provable some other way."))

(11011011 (111 (001 principles-document) "docs/language-core-axioms.md"))
(11011011 (111 (001 tier-map) "docs/conformance-tier-map.md"))

(11011011 (1110 (001 principle) 1 "Write about possibilities, not limitations." "Писати про можливості, не про обмеження."))
(11011011 (1110 (001 principle) 2 "Be Lisp in the full sense of the word — homoiconicity and a minimal, closed core that grows the rest of the language from inside itself, not the surface syntax of any one historical dialect." "Бути Lisp-ом у повному розумінні цього слова — гомоіконність і мінімальне, замкнене ядро, що вирощує решту мови зсередини себе, не поверхневий синтаксис якогось одного історичного діалекту."))
(11011011 (1110 (001 principle) 3 "Build the reasoning machine — McCarthy's documented 1958 Advice Taker goal, extended by the author's own hybrid neural/symbolic vision (private/lisp-to-knowledge.md)." "Реалізувати розумну машину — задокументована ціль МакКарті 1958 року (Advice Taker), продовжена власним гібридним нейро-символьним баченням автора (private/lisp-to-knowledge.md)."))
(11011011 (1110 (001 principle) 4 "Cross-platform-ness, or more simply: universality — the falsifiability test for G6/G7; sens commits to real, physically different substrates (Rust, fpga-lisp), not just one implementation asserting conformance." "Кросплатформеність, або простіше — універсальність — тест на фальсифіковність для G6/G7; sens зобов'язується перед реально різними фізичними субстратами (Rust, fpga-lisp), не лише однією реалізацією, що заявляє конформність."))
(11011011 (1110 (001 principle) 5 "Maximum awareness of today's technology, applied to symbolic AI — classical symbolic AI is not a museum piece; modern tooling and modern LLMs (as the fuzzy natural-language interface, not a competitor to the precise symbolic core) are part of building it." "Максимальна обізнаність у сьогоднішніх технологіях, застосована до символьного ШІ — класичний символьний AI не музейний експонат; сучасні інструменти й сучасні LLM (як нечіткий інтерфейс природної мови, не конкурент точному символьному ядру) — частина його побудови."))

(11011011 (1110 (001 axiom) (001 G1) (001 generative) "A value's meaning can be fully defined by observable behavior." "Значення value може бути повністю визначене спостережуваною поведінкою."))
(11011011 (1110 (001 axiom) (001 G2) (001 generative) "Every value can be built from just two things: atoms and pairs." "Кожне значення можна побудувати лише з двох речей: атомів і пар."))
(11011011 (1110 (001 axiom) (001 G3) (001 generative) "Program structure can be inspected, transformed, and built like any other value." "Структуру програми можна оглядати, трансформувати й будувати, як і будь-яке інше значення."))
(11011011 (1110 (001 axiom) (001 G4) (001 generative) "A minimal core can grow an entire language inside itself." "Мінімальне ядро може вирощувати всю мову всередині себе."))
(11011011 (1110 (001 axiom) (001 G5) (001 generative) "Anything expressible within the language can live above the implementation boundary." "Усе, що виразне мовою, може жити над межею реалізації."))
(11011011 (1110 (001 axiom) (001 G6) (001 generative) "Conformance can be defined purely by observable behavior." "Конформність можна визначити суто спостережуваною поведінкою."))
(11011011 (1110 (001 axiom) (001 G7) (001 generative) "The same expression can mean the same thing everywhere." "Той самий вираз може означати те саме всюди."))
(11011011 (1110 (001 axiom) (001 G8) (001 generative) "The absence of any element and the absence of truth can be the same value." "Відсутність будь-якого елемента й відсутність істини можуть бути тим самим значенням."))
(11011011 (1110 (001 axiom) (001 S1) (001 safety) "Never silently turn an exact value into an approximation." "Ніколи мовчки не перетворювати точне значення на наближення."))
(11011011 (1110 (001 axiom) (001 S2) (001 safety) "Never fail silently — every failure is a named, observable outcome." "Ніколи не провалюватись мовчки — кожен провал є названим, спостережуваним результатом."))
(11011011 (1110 (001 axiom) (001 S3) (001 safety) "Never let a resource limit silently redefine an operation's meaning." "Ніколи не дозволяти обмеженню ресурсу мовчки переозначити сенс операції."))

(11011011 (1110 (001 tier) 1 "CORE SEMANTICS — every conforming implementation must have this"))
(11011011 (1110 (001 tier) 2 "LANGUAGE CONTRACT — every conforming implementation must have this"))
(11011011 (1110 (001 tier) 3 "ECOSYSTEM CONFORMANCE — an implementation can be sens without this loaded yet; tests a library, not the language itself"))

(0011 print-fixture
  (0010 (fixture)
    (11011011 (111 (001 fixture) fixture))))

(0011 print-fixtures
  (0010 (remaining)
    (110
      ((010 remaining) (001 ()))
      ((010 (001 ())) ((0010 ()
            (print-fixture (100 remaining))
            (print-fixtures (011 remaining))))))))

(print-fixtures fixtures)

(001 ())
