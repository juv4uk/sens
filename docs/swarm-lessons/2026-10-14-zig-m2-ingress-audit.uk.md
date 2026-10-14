# Чому я передчасно оголосив перехід CLI на Zig завершеним (14.10.2026)

**Хто:** виконавець Zig→SENS M2 (`sens-trit`), ця ChatGPT-сесія через GitHub.  
**Контекст:** [#5779](https://github.com/juv4uk/sens/issues/5779), [#5777](https://github.com/juv4uk/sens/issues/5777), фізичний T5/F3C транспорт у `crates/sens-cli/src/bin/sens-trit.rs`.

## Що сталося

Я інтегрував новий симетричний Zig ABI v2 `sens_zig_t5_decode_be3` у звичайне `eval`/`eval-core4`, залишивши семантичне читання за `PhysicalT5Program::from_exact_words`. Це були фактичні коміти [1bf97ee5](https://github.com/juv4uk/sens/commit/1bf97ee50d69a6e42ed7e756964e0dda8396ea60) та [221eb979](https://github.com/juv4uk/sens/commit/221eb9796ec03731968183e763b918189924ecee).

Однак у [першій квитанції M2](https://github.com/juv4uk/sens/issues/5029#issuecomment-6170700881) я **передчасно назвав `eval-f3` переведеним на Zig**. Під час наступного аудиту того самого файла виявив два інші місця: `decode_f3_carrier` та `encode_f3_carrier` за ввімкненого `zig-transport` ще викликали `sens::PhysicalT5Program::decode`, тобто фізичне читання T5 виконувалося напряму в Rust.

Я визнав пропуск у [новому CLAIM](https://github.com/juv4uk/sens/issues/5029#issuecomment-6170753706), перевів обидва місця на Zig `decode_t5_words` → чинний SENS `from_exact_words` одним [точковим комітом 0bb725b9](https://github.com/juv4uk/sens/commit/0bb725b9f1dce6301e9b2e4884d8d70494b07da4) та [опублікував виправлену квитанцію](https://github.com/juv4uk/sens/issues/5029#issuecomment-6170793031).

Автоматичний центральний [CI #38581177293](https://github.com/juv4uk/sens/actions/runs/38581177293) на **точному SHA `0bb725b9...` завершився SUCCESS**; у ньому пройшли Zig-тести, фізичний CLI-свідок і парні T5/F3C перевірки. Це **не** є доказом, що *всі* `open`, `decode`, `verify`, `explain` та інші входи вже використовують Zig, чи що кожна команда охоплена окремим адресним тестом.

## Корінь

Я перевірив основний `eval_t5_bytes_core4`, але недостатньо повно перевірив допоміжні шляхи до й після F3C. Одна правильна центральна функція не означає, що всі команди CLI проходять через неї **без обхідного фізичного декодера**. Формула «M2 виконано» виявилася ширшою за мій фактичний diff.

## Урок

Перед словом **DONE** для маршруту перелічити *всі* входи відповідної команди та їхні helper-виклики. Для кожного зафіксувати фізичний decoder і саме той feature, за якого код компілюється. Окремо перевірити `#[cfg(feature = "zig-transport")]` і `#[cfg(not(feature = "zig-transport"))]`: другий є явно вибраним reference, а не непомітним fallback першого.

Вимагати незалежних свідків: (1) source-audit усіх call-site, (2) точні width/bytes, (3) негативний фізичний тест, (4) реальний CI на SHA. **CI SUCCESS не замінює доказу повноти списку call-site.** Зберігати вузький статус «цей маршрут переведено», не проголошувати system-wide single turnstile.

## Симптом-маркер

У feature-gated Zig-блоці є `zig_transport::validate_t5(...)`, але далі той самий шлях усе ще викликає `sens::decode_ternary_words(...)` чи `PhysicalT5Program::decode(...)` для **фізичного T5**. Це ознака, що Zig лише перевіряє, а Rust фактично декодує, хоча звіт може казати протилежне.

**Межа уроку:** це технічна самокорекція агента, не новий закон чи реєстр SENS. Нормативна семантика лишається за власником і чинним виконуваним SENS.
