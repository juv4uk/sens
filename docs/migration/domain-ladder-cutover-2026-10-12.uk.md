# Перехід SENS до доменної драбини — поточний зріз 12.10.2026

**Статус: часткова реальна міграція в main; НЕ завершено; release NO-GO.** Заборонено створювати нові гілки, трактувати W8 як автоматичний D8, створювати резидентну семантику з бітового збігу або повертати бездоменну арифметику. D1–D10: exact semantic words, D24+: окремі явно кваліфіковані числові значення.

## Виконані заміни поза Rust

- `scripts/research-2077-binary-word-law.py`: замість `to_sens8/from_sens8` — `DomainCoordinate(width,payload)` із явним `declared_width`, перевіркою D1–D10 і негативними тестами переповнення/перекриття доменів. Це механічна координата, не доказ виконуваності.
- `scripts/sid-binary-identity-guard.sh` **видалений**. Його нормативне припущення про єдиний 8-бітний простір не переноситься далі.
- `scripts/check-domain-ladder-identity.py` — нова активна охорона Rust/Python/C/Lisp: точні записи D1–D10 (2/4/8/16/32/64/126/256/512/1024), 2 зарезервовані D7, анти-SID кодові негативні свідки. Сувора область лише перелічених канонічних файлів; історичні донори не оголошуються мігрованими.
- `scripts/test-binary-language-pipeline.sh`, `.github/workflows/ci.yml`, `.github/workflows/ci-hosted.yml` та `knowledge/repo-tooling-inventory.lisp` перейшли на нову охорону.
- Прибрано стару термінологію з низки канонічних Rust модулів та Python бенчмарку доменів, збережено стару історію в research.

## Де ще дійсно залишився старий виконуваний код

| Зріз | Конкретні файли | Стан і безпечна наступна дія |
|---|---|---|
| Восьмибітна runtime-сумісність Rust | `crates/sens/src/sens.rs`, `syntax.rs`, `value.rs`, `parser.rs`, `eval/canon.rs`, `eval/capabilities.rs`, `semantic_registry.rs` | Ще мають carrier/AST/capability API зі старою ідентичністю; потрібен наскрізний перехід reader → AST → evaluator → FASL/physical codec з тестами, а не видалення типу всліпу |
| Host/island межа Rust CLI | `crates/sens-cli/src/island_invoke.rs`; `crates/sens/src/eval/profile_mechanisms_generated.rs`; генератор `scripts/generate-rust-profile-mechanism-routes.lisp` | Старий **10101000 INVOKE** має classification **MECHANISM-HOLD**, `current_target=null` у `knowledge/sens8-current-coverage-v1.json`. Той самий D8 бітовий вміст **10101000 є ROUND**, а не INVOKE. Автоматична заміна за довжиною була б небезпечною помилкою |
| Інші сучасні W8-колізії | `scripts/migrate-sid8-source-batch.py` містить окремі pins для `knowledge/guard-fact-policy.lisp`, `scripts/semantic-authority-guard-enforce.lisp` | Історичні `01001011` READ-ALL та `10100110` READ-FILE відповідають D9, але сучасні D8 координати цих бітів — інші resident laws; D9 residency також не дає автоматичного callable mechanism |
| Lisp bootstrap/джерела | `lib/macro.lisp`, `lib/machine/block.lisp` та інші source cohorts | Точкове перенесення допустиме тільки для однозначного owner-verified successor, із збереженням QUOTE/COND/D1, перевіркою mechanism і нового Core AST. `lib/machine/block.lisp` та `lib/macro.lisp` уже позначені HOLDS у batch-міграторі; цей HOLD не обходити |
| Python migration toolchain | `scripts/sens_source_resolver.py`, `scripts/migrate-three-pass.py`, `scripts/migrate-sid8-source-batch.py` | Тимчасові односпрямовані перетворювачі старого джерела, не runtime authority. Зберегти до завершення конверсії та byte-exact-oracle, після цього видалити разом із перехідною таблицею |
| Історичний C benchmark | `benchmarks/domain1234-dispatch/d34_dispatch.c` | Стара flat-lane лишається незалежним historical baseline; не видавати її за сучасну реалізацію SENS. Канонічні нові входи перевіряє domain-ladder guard |

## Критерій завершення (ще не досягнутий)

1. Жодний активний reader, AST, evaluator, compiler, FASL, codec чи capability не трактує восьмибітну комірку як універсальний semantic ID.
2. Усі executable source cohorts мають явне доменне походження; несумісні механізми отримують **BLOCKED**, а не підставлену функцію D8.
3. D1/D3 логіка, D24+-only арифметика й D7-reserved залишаються чинними, негативні перевірки на неправильні типи не видаляються.
4. Rust, Python, Lisp, C та physical T5 мають незалежні виконувані witnesses одного candidate SHA; жоден архівний test не оголошується production proof.
5. Реліз лише після необхідних зелених воріт. Немає свідчень успішного запуску всіх тестів у цьому зрізі.

Поточний локальний Desktop Commander повідомив про місячний ліміт виконання; GitHub містить зміни, але без підтвердженого green CI не заявляємо виконану міграцію.
