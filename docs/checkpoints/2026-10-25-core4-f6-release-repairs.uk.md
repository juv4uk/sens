# 25 жовтня 2026 · ремонт Core4 і фізичного коридору релізу

## Дійсно виконані зміни
1. `a8797820c51cbc74b8b51f301391be36580d1f6b` —
   п'ять `lib/core4-parts/*.lisp` поділено лише між
   завершеними формами, `scripts/split-core4.py` переведено
   із числових зсувів на точні SENS-якорі.
   Перед комітом статично перевірено п'ять збалансованих блоків
   і byte-exact склеювання до незміненого
   `lib/core4.lisp` (Git blob `0896a5e63f48c41f911d799a86f8146c7a5a7254`).
2. Колега в `1113b5e5b77eaab8eee84d7435e551188c70b5f8`
   уточнив структурні якорі на початки DEFINE, зберіг byte-exact
   і повноту SENS-блоків. Не відкотити цю новішу версію.
3. `5842d6a26f2f745fb4f20a737bab7b4ca5b04960` —
   чотири механічні Python-якорі не містять буквального
   `(визначити` в host-джерелі. Вони складаються із двох
   рядкових фрагментів і повертають ті самі SENS межі.
   Це ремонтує хибний `host debt` детектор, НЕ послаблюючи
   `tests/test_language_stays_in_sens.py`. Статична перевірка
   показала 4→0 нових regex-збігів у генераторі.

## Останній завершений CI перед змінами
Run `40191821188` для SHA `d56157480a3f19b511ddca34617b2cffcce5d7f5`:
- `SENS_LAW_BENCHMARK_SUMMARY measured=563 failed=4`;
- d9-f6-package-key-canonicalization-positive — unknown Text7 binding
  `внутрішня-мапа-список`: у програмі свідка бракувало
  `lib/persistent-map.lisp` / спорідненого SENS стеку;
- d5-member-hidden-tail, d5-assoc-hidden-tail,
  d5-assoc-late-record — прямий неправильний успіх;
- `lib/core4-parts/core4-d6.lisp` — T5M mint парсить
  фрагмент як незавершений SENS початок; корінь — жорсткі
  числові межі split-core4;
- `lib/core4.sens` та human view не відповідають
  поточному `lib/core4.lisp` (physical drift);
- F6 producer→consumer повернув
  `root reconstruction rejected: verdict=0`,
  дані SENS `(rejected invalid-format)`.

## Зміни інших агентів у тому ж main
- `9052db1aefa5`, `32cb0bbc639d` прибрали сирі
  D5 call heads;
- `73a05f7077f9` підключив чинні SENS DEFINE MEMBER/ASSOC;
- `42daf5f7d17e` та `0f02f138f8af` відновили
  повний SENS стек для F6 WRITE/READ. Не слід повертати
  старі bundles без `persistent-map/world/content-store`.
Ці коміти — код, а не підтверджений релізний PASS.

## Точна дія на наступному SHA
Цей checkpoint коміт містить маркер `SENS_PAIR_REGEN`
у повідомленні commit. Він використовує вже існуючий CI
`Export canonical SENS/Zig T5M pair regeneration evidence`
для генерації `sens-pair-regen-<SHA>` з нативного
`sens --t5m-mint-pair`, `sens-trit verify-view`,
SHA джерела й source-commit SHA. Це є генерацією доказу,
**не** готовим оновленням committed .sens/view.
Артефакт короткоживучий (retention_days=1).
Після його появи: перевірити його exact SHA і parity,
канонічно оновити фізичні файли без ручних байтів
і повторно перевірити current-main CI.

## Наступні безумовні P0
1. Звірити результат host debt після `5842d6...`
   (очікується нуль нових host SENS голів) та структурний
   source↔parts check, не оголошувати PASS до закінчення CI.
2. Відновити `lib/core4.sens` і `lib/core4`
   ТІЛЬКИ канонічним SENS/Zig/T5M та перевіркою байтів.
3. Відновити `lib/lisp-fs.sens` і
   `tests/fixtures/wsm-fs-record-producer.sens` по окремій
   current-source квитанції; F6 invalid-format перевірити
   як саме SENS predicate, не відключати негативи.
4. Звірити реальний D5 member/assoc direct, paired, standalone,
   mutантів і неправильні D1-хвости на одному SHA.
5. Продовжити D6 MACROEXPAND/MAP, D10 і D11–D12+ тільки
   з законами, механізмами й точними фізичними квитанціями.

`RELEASE=NO-GO` до зеленого CI та рішення власника.
Жодного GitHub workflow RED не перезапускати без нової
зміни причини.
