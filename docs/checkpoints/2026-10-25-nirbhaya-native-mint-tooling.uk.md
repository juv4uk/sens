# Nirbheeka · canonical mint tooling checkpoint · 25.10.2026

## Першопричина

У scripts/mint-nirbhaya-law-pairs.py назва обіцяла mint, але реалізація лише декодувала архівні *.sens.b64 і *.view.b64 та безумовно перезаписувала відповідні тести-артефакти. Цей шлях не запускав SENS/Zig і міг перетерти пізніше канонічно створені пари. Архівні blobs не є актуальним доказом виконання.

## Запушене виправлення

- Commit 29f8cfbe44c05b536449e9d0ca3d26ef086c8f96 оновлює scripts/mint-nirbhaya-law-pairs.py.
- Тепер джерелом є рівно п'ять поточних .lisp файлів із STEMS. Helper запускає чинний sens --t5m-mint, генерує view через sens-trit view і вимагає sens-trit verify-view для кожної staged-пари.
- Перед публікацією збираються всі п'ять пар у тимчасовому каталозі. Helper записує SHA-256 джерела, повторно перевіряє його після mint і перед публікацією, відхиляє зміну цільового файла стороннім writer-ом та відновлює попередні байти в разі помилки публікації.
- Архівні файли лишаються лише provenance; runtime-helper більше не читає їх. Статус повідомлення спеціально каже native_semantics=NOT_CERTIFIED_BY_MINT: mint/view-парність не є доказом виконання закону.

## Тести й CI

- Commit d4fb96123546d0de81d43ee45721d93a3156b389 додає tests/test_mint_nirbhaya_law_pairs.py: stale archive is ignored, concurrent target write aborts before publishing, source mutation during mint aborts without publishing.
- Commit 922fa05acec3b34b00efb721b99b9fcddd6071fc підключає цей тест до короткого .github/workflows/ci.yml.
- GitHub Combined Status для цих commit SHA повернув порожні arrays. Це не PASS. У цьому ході я не мав локальних sens/sens-trit бінарників, тому не стверджую, що Python unit test або нативний T5M mint фактично пройшли.

## Точний handoff

1. Перевірити завершений CI для актуальної вершини main і підтвердити, що tests.test_mint_nirbhaya_law_pairs пройшов. За будь-якого RED виправляти сам інструмент, не очікування тесту.
2. Після CI виконати helper із нативними target/debug/sens та target/debug/sens-trit; записати source SHA-256, фізичні розміри і фактичні результати view/verify-view.
3. Окремо виконати предметні SENS-закони для п'яти пар з усіма залежностями. Успішний mint сам по собі не означає native SENS semantic PASS.
4. Відновити фізичний F6 producer→consumer доказ на тому самому exact SHA. Історичний invalid-format RED не переносити на новий код автоматично, але й не оголошувати усуненим без нового нативного результату.
5. Після F6 продовжити D6 mechanism-ledger аудит за Contract 12.0, D6:101000 MAP та відсутні D6:000110 MACROEXPAND-1 / D6:000111 MACROEXPAND.

NIRBHAYA_HELPER=REWRITTEN_TO_NATIVE_T5M
MECHANICAL_UNIT_TEST=WIRED_NOT_YET_VERIFIED
NATIVE_SENS_SEMANTICS=NOT_VERIFIED
F6_END_TO_END=NOT_VERIFIED_ON_CURRENT_SHA
D1_D12_PLUS_FULL_AUDIT=INCOMPLETE
RELEASE=NO-GO
