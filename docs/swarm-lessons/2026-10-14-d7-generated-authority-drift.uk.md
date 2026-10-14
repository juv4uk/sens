# Мій пропущений D7.authority: правильні біти, застарілий закон у сертифікаті (14.10.2026)

**Хто:** ChatGPT, виконавець вузької D7-міграції через GitHub `juv4uk/sens`.
**Контекст:** `knowledge/domain-width-authority.generated.json`, `scripts/generate-domain-width-certificate.py`, `scripts/check-domain-ladder-identity.py`; координація [#5029](https://github.com/juv4uk/sens/issues/5029#issuecomment-6169293096).

## Що сталося

Я виправив застарілий згенерований сертифікат D1–D9 комітом [`4f04d442`](https://github.com/juv4uk/sens/commit/4f04d442417027d14edf43474232b34dcc93e7c7): переніс `D7.rows` із історичних **126** на чинні **128**, оновив Git blob SHA ратифікованої основи й `lib/domains/d7.lisp`. Перевірив усі 128 точних семибітових координат, але **пропустив поле `domains.D7.authority`**.

Сертифікат лишив `"#3572"` — історичний v1, хоча чинне джерело `knowledge/d1-d9-foundation.json` вже має `"owner-ratified-2026-10-13-keyboard-v2"`. Попередній CI був зеленим, бо не викликав повний генератор сертифіката.

Після моєї наступної правки [`402842b0`](https://github.com/juv4uk/sens/commit/402842b05eeb285ef4c3ff90009e2d12c67aecc5) генератор перевіряє D7 keyboard/v2 через **існуючий** `d7_source_projection.load_current_d7()`. Коміт [`f0f8a0d7`](https://github.com/juv4uk/sens/commit/f0f8a0d706bcc9597313aa396566307af1791fc4) під'єднав його `--check` до вже чинного центрального перевіряльника.

**Вперше точна невідповідність стала видимою:** [центральний CI `38569295997`](https://github.com/juv4uk/sens/actions/runs/38569295997) на `f0f8a0d7` завершився **FAILURE**, в реальному логу:

```text
DOMAIN-LADDER-IDENTITY: BLOCKED: D7_V2_CERTIFICATE_DRIFT
id=d7-v2-exact-surface-identity layer=source-projection
actual='domain width certificate is stale; run python3 scripts/generate-domain-width-certificate.py'
```

Точкове виправлення [`ee41dfef`](https://github.com/juv4uk/sens/commit/ee41dfefbd7f9efb2c71242d4b99b7c4e474a2af) оновило **тільки похідне поле** `D7.authority`. [Центральний CI `38570198874`](https://github.com/juv4uk/sens/actions/runs/38570198874) на тому SHA — **COMPLETED SUCCESS**; чинний доменний закон, його бітність, резидентів і таблиці не переписував.

## Корінь

Моя помилка — **часткове ручне відтворення генерованої проєкції**. Я звіряв `rows` і SHA та зробив висновок, що сертифікат цілком актуальний. Але сертифікат містить також нормативне посилання `domains.D7.authority`, тож правильні 128/128 і Git SHA не гарантують збігу всіх похідних полів. Доки CI не запускав справжній `generate-domain-width-certificate.py --check`, мій неповний розрахунок лишався непоміченим.

## Урок

Для generated-файла не варто «латати три відомі поля» і вважати розбіжність усунутою. Треба відтворити **весь** результат на поточному Git-зрізі та перевірити його командою:

```sh
python3 scripts/generate-domain-width-certificate.py --check
python3 scripts/check-domain-ladder-identity.py --check
```

Якщо `--check` червоний, не послаблювати перевірку. Порівняти генераторну модель із записаною проєкцією, встановити перше відмінне поле, виправити тільки похідний файл, повторити команду та позначити точний commit+CI. Ратифікація залишається за власником, а генератор — механічним свідком, не джерелом нової семантики.

У великому рої перед записом обов'язково заново зчитати blob SHA й CLAIM інших виконавців: зелений результат на *старішому SHA* нічого не доводить про пізніший стан.

## Симптом-маркер

**`D7_V2_CERTIFICATE_DRIFT` або `domain width certificate is stale` за наявності 128/128 і збігу SHA таблиці.** Насамперед перевір `domains.D7.authority` проти чинної ратифікації; не роби висновку, що це «хибний червоний» або пошкоджена клавіатура. Розрізняй невідповідність похідної метаінформації, реальний glyph drift і незалежні CI-помилки.
