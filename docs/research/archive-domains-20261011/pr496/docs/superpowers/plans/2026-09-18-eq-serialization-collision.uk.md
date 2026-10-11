# План аудиту collision для EQ через серіалізацію

> **Для агентних виконавців:** використовуйте `superpowers:subagent-driven-development` або `superpowers:executing-plans`.

**Мета:** перевірити, чи можна відновити поточну семантику EQ через `write-to-string` і текстове порівняння.

**Архітектура:** постійні зміни лише в research/plan. Живі probes виконуються у NEVER-MERGE child через тимчасовий integration test. Один serialization collision фальсифікує цей маршрут, але не доводить глобальну незвідність EQ.

**Специфікація:** issue #493.

## Обмеження

- Не змінювати production EQ, writer, strings, evaluator, Canon, registry, fixtures або Rust semantics.
- Поточний EQ розрізняє closures за identity.
- Поточний writer рендерить кожну closure як `<lambda>`.
- Text route не має права викликати EQ прямо або через alias.

## Завдання 1

До запуску записати прогноз:
- одна closure, порівняна сама з собою -> EQ same;
- дві окремо створені closures -> EQ distinct;
- обидві окремі closures серіалізуються однаково як `"<lambda>"`;
- отже equality лише через serialized text дає false-positive same.

До виконання статус — `insufficient-evidence`.

## Завдання 2

У verification-only child:
- перевірити EQ same/distinct для closures;
- перевірити однакову серіалізацію різних closures;
- побудувати `text-same?` без EQ: `write-to-string`, два `string<?`, canonical COND проти `()`;
- показати false-positive same для двох EQ-distinct closures;
- контроль: різні звичайні символи мають різний текст і text route їх розрізняє;
- видалити temporary Rust test і виконати `git diff --check`;
- child PR закрити без merge.

## Завдання 3

Після fresh run записати точний PR/run/SHA і test counts.

Якщо collision підтвердиться:
`serialization/text -> EQ = route-falsified-by-serialization-collision`.

Потім research PR проходить exact-head CI + bilingual gate, а bounded result передається в #493/#471/#419.
