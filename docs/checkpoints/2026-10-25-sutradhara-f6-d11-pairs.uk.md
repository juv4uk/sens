# Sūtrādhāra · F6 фізичний drift та D11 LIST= · checkpoint
Дата: 2026-10-25, Europe/Kyiv
Основний репозиторій: https://github.com/juv4uk/sens
Гілка: main

## Що запушено в цьому ході

- [f4590f4](https://github.com/juv4uk/sens/commit/f4590f40ec54cd5fdd560f091de8c78710ca25c1): виправлено хибнопозитивний host-debt scanner. Він сприймав українські SENS-голови в діагностичних рядках Core4 guard як вбудовану мовну логіку. Зміст guard-перевірок збережено; у run [40159882499](https://github.com/juv4uk/sens/actions/runs/40159882499) крок 4, Core4 parity (17) та changed-Lisp route (18) підтверджено success, повний законний крок залишався in_progress.
- [53585e8](https://github.com/juv4uk/sens/commit/53585e83bbcd5d0365bb8cb69f7f6493f9fb51f3): у разі F6 reconstruction rejection додано лише failure-path діагностику фактичного SENS-значення. Вона ще не дала доступного завершеного журналу.
- [907504e](https://github.com/juv4uk/sens/commit/907504ec0fea9cce1a819671d74db1b02f9051bf): додано лише коментар-маркер для штатного mint поточної фізичної пари `lib/lisp-fs.lisp` через SENS/Zig/T5M. Коментар не змінює мовний AST. Run [40160876665](https://github.com/juv4uk/sens/actions/runs/40160876665) був queued на останній перевірці.

## Встановлений F6 root-cause кандидат

- Джерело `lib/lisp-fs.lisp` зараз має blob SHA `64f86964e51d98e6d1ff26b87db1ec598f1ba075`; він містить зміни з коміту `b4e1bff1e18289ed38068251e1ae68eff3413878` (25 жовтня 02:25 UTC) плюс нешкідливий mint-маркер.
- Фізичний `lib/lisp-fs.sens` залишається `7c560c1cdd8c7ddb3de0aa2f6c64a6b985a367c8`, а view `lib/lisp-fs` — `2ee9a1a49acafc52cfdf9e96c618ae2a83bb3150`. Останні зміни обох sidecar-ів походять із `c285e11cf0fa352e63cf62ff6e05d90873bd2f1c` від 24 жовтня 02:28 UTC. Отже, є доведений source/physical age gap понад добу.
- Старий фізичний F6 тест давав `root reconstruction rejected: 0`. Коміт `938a7b2` замінив очікуваний маркер із D7-списку гліфів на source-symbol `accepted`; `348a269` додав test, але він порівнює результат legacy `eval_program("(як-є accepted)")` із вручну побудованим AST. Це ще не сертифікує фізичний T5M шлях.
- Commit `53585e8` додає failure-only друк реальної реконструкції. Run [40160343319](https://github.com/juv4uk/sens/actions/runs/40160343319) мав Rust step failure, але logs endpoint повертав недоступний blob; не робити висновок про фактичне значення без нового журналу.
- Критичне архітектурне застереження: `crates/sens/src/eval/special_forms/core.rs` має тест `quote_keeps_a_d2_framed_w7_run_as_a_structural_list`. Канонічний D2/W7 reader зберігає такий quote datum як structural list D7, не як `Value::Symbol`. Треба звірити саме новий фізичний mint, перш ніж остаточно фіксувати очікуваний тип маркера.

## D11 LIST= — точний artifact і непропушені sidecar blobs

- Поточне джерело `lib/d11-srfi1-list-equality.lisp` SHA `397eac5fb01be476d6b7d14b2a02df68bfebf275`. Джерело співпадає з ним у artifact-run [40159989211](https://github.com/juv4uk/sens/actions/runs/40159989211).
- Canonical mint artifact ID `12585926968`, archive `sens-d11-pair-regen-ffa2458ba467d9233fa025a3ab6c24bdbdae82c3`. Виходи: `.sens` 1919 bytes, view 9596 bytes. Receipt говорить `physical=ZIG_VERIFIED semantic=NOT_CERTIFIED`; це не є підтвердженням законів.
- Raw-виходи звірені за Git SHA та **запушені** у коміті [`11e2e54`](https://github.com/juv4uk/sens/commit/11e2e54253b99d6883b2b244856119d65070b333):
  - `lib/d11-srfi1-list-equality.sens` → `1c30bea705ff4fc81c1bf63acd3e6ba44477447b`
  - `lib/d11-srfi1-list-equality` → `b54811b2452c93061f0482ca95ff4414c2154502`
- Повторне читання з `main` підтвердило обидва blob SHA; source лишився `397eac5fb01be476d6b7d14b2a02df68bfebf275`. CI run [`40161310715`](https://github.com/juv4uk/sens/actions/runs/40161310715) для цього pair commit був `queued` на момент checkpoint. Фізична узгодженість закрита; семантична не сертифікована, бо receipt мінту — `physical=ZIG_VERIFIED semantic=NOT_CERTIFIED`.

## Інші підтверджені зміни на main

- `d11-srfi1-list-equality.lisp`: неправильні atomic tails тепер приводяться до D3 CAR Type; правильний кінець перевіряється D4 `порожній?` замість дублювання D3 EQ. Негативні свідки: improper-left, improper-right, invalid-singleton, invalid-third; не вважати їх зеленими без завершеного run.
- `scripts/check-numeric-domain-ratification.py`: guard підтримує чинний Contract 12.0 як signed-integer authority, має зберігати native execution release gate. D12 numeric range −2048…2047, widening to D24 without wrap; standard CLI/REPL D24-first.
- D9 STRING-APPEND має SENS D1 positive/mutant у фізичному runner; run [40159918382](https://github.com/juv4uk/sens/actions/runs/40159918382) був in_progress, кроки Core4 parity та changed-file push success, law step ще in_progress.
- Паралельна робота вже додала D10 MAP (12 законів плюс мутант), D11 LIST-TABULATE, LSET, ALIST, COUNT, FIND-PRESENCE, FIND-TAIL, LIST-INDEX. Усе це потребує перевірки на одному SHA, не лише commit presence.

## Точні наступні дії

1. Перечитати HEAD і статус run [40160876665](https://github.com/juv4uk/sens/actions/runs/40160876665). Отримати його артефакт і перевірити, що mint-source SHA дорівнює поточному `lib/lisp-fs.lisp`. Після цього синхронізувати обидва physical sidecar-и поточною парою і підтвердити їхні Git SHA на main.
2. Дочекатися доступного F6 stderr із `53585e8` або нового запуску. За фактичним `detail=` розділити `reconstruction rejected` від невідповідного очікуваного carrier; не повертати blind `Symbol`/D7-list заміну.
3. Оновити `lib/d11-srfi1-list-equality.sens` та view лише raw-byte blobs з artifact ID `12585926968`, fast-forward/CAS без `force`; тоді перевірити всі чотири Type свідки та позитивні закони на тому самому HEAD.
4. Перечитати актуальні перевірки D6 uk/ukr, D9 APPEND, D10 MAP, D11 list laws; фіксувати expected/actual і failure ID без пом'якшення gates.
5. Повний release лишається NO-GO. У цьому середовищі реальних субагентів не запускали.

Статус: кілька точкових комітів запушено, але F6 physical pair та D11 LIST= physical pair ще не certified; D1–D12+ повна викличність і повний CI не доведені.
