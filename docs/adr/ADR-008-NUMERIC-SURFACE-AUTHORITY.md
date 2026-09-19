# ADR-008 — Numeric surface authority

**Статус:** Accepted  
**Дата:** 2026-09-08

## Рішення

Етап A meaning-first міграції завершено.

`lib/surface/semantic-registry.lisp` є **єдиною машинною authority** для
відповідності між semantic identities та людськими програмними поверхнями.
Semantic identity у цьому реєстрі — непрозорий атом, що складається тільки з
цифр.

```text
                         0101
                           │
              ┌────────────┼────────────┐
              │            │            │
             UK           EN            SA
        відобразити       map       āvartana
```

Жодна людська назва не є ключем іншої людської назви. Це правило machine layer
і воно не змінює project-level політику: **українська є першою мовою проєкту**,
тоді як англійська й санскрит є допоміжними поверхнями.

## Спільна символіка

Пунктуаційна нотація не є людською мовою. Для неї існує окрема surface `sym`.

```text
                         0104
                ┌──────────┼──────────┐
                │          │          │
               UK         SA         sym
             додати      yoga         +

               EN: missing
```

Тому `+`, `-`, `*`, `/`, `<`, `>`, `=` та подібні знаки не можуть бути
зараховані EN лише тому, що історичний bootstrap використовував їх поруч з
англійськими словами. Якщо справжнє людське ім'я певної surface не
ратифіковане, реєстр чесно містить `— missing`.

## Legacy table

`lib/surface/uk-sa-coverage.lisp` зберігається як історичний аудит походження
імен і попередніх статусів. Вона **не є semantic authority** і не може живити:

- REPL introspection;
- surface parity gate;
- drift checker;
- program surface translator;
- документаційний join key.

Нові executable consumers мають читати тільки `semantic-registry.lisp`.

## REPL

`:ім'я` / `:name` показує numeric identity незалежно від того, яким spelling
виконано пошук.

```text
:ім'я map
:ім'я відобразити
:ім'я āvartana
:ім'я 0101
```

усі ведуть до:

```text
identity: 0101
```

Для shared notation:

```text
:ім'я +

identity: 0104
  UK: додати [stable]
  EN: — [missing]
  SA: yoga [stable]
  SYM: + [stable]
```

`(env)` / `(середовище)` залишається сирою lexical introspection і може
показувати історичні host/bootstrap spellings. Це не надає їм semantic
authority.

`core` також не є четвертою людською surface. У surface introspection він
показує numeric machine handles; його runtime environment може залишатися
implementation-oriented.

## Виконуваний gate

Authority закрита не лише текстом ADR. CI виконує три незалежні перевірки:

```bash
python3 scripts/check_semantic_registry.py
./target/release/my-lisp scripts/check-surface-coverage.lisp
python3 scripts/check_trilingual_surface.py
```

Вони доводять, що semantic IDs numeric-only, чиста пунктуація не приписана
людській мові, runtime public names класифіковані через numeric registry, а
status matrix обчислюється з тієї самої authority. Strict workspace CI окремо
перевіряє Rust consumer-и, включно з REPL catalog.

Фінальний REPL evidence також перевіряє саме поточну модель: numeric identity
`0101`, UK `140/140`, EN `131/140` із 9 чесними `missing`, SA
`36 stable + 88 candidate + 16 missing`, і `29/140` одночасно stable у всіх
трьох людських поверхнях. Це вимірювання, а не release-claim.

## Межа цього ADR

Цей ADR закриває **authority та introspection debt**. Він не стверджує, що всі
140+ public values уже мають direct runtime peer binding одного `Rc`/closure.
Це окремі етапи B–D плану runtime topology і потребують executable proof для
кожної мігрованої identity.

Отже не плутаємо:

```text
numeric authority complete        ✅
REPL numeric introspection         ✅
legacy EN key retired             ✅
all runtime peer bindings complete ⏳
full auxiliary-surface parity      ⏳
```

## Supersession

Цей ADR завершує перехідний пункт ADR-007, за яким
`uk-sa-coverage.lisp` тимчасово залишалася authority під час міграції.

В ADR-005 зберігається фундаментальний висновок, що human surface spelling не
може отримати machine-semantic владу лише через історичне походження. Його
legacy-інтерпретація `canonical/EN` колонки більше не є чинною машинною
архітектурою.

> **Machine layer: значення первинне; людська назва не є semantic key.**  
> **Project layer: українська — перша мова проєкту.**

## Runtime peer progress — 2026-09-08

Numeric authority is now consumed by interactive Ukrainian builtin presentation,
so `presentation.rs` no longer reads the legacy EN-shaped audit table. The first
stable symbolic arithmetic/comparison wave is also direct at runtime: identities
`0104`, `1001`–`1003`, and `1014`–`1016` allocate one builtin value each and bind
UK/SA/symbolic spellings directly. The historical builtin display token remains
a diagnostic compatibility token, not semantic identity.
