# Pramāṇa · захист цитованого SENS-статусу F6 · 25.10.2026

## Суть
Раніше CI `40158590271` на `7f8dbf863edaf12714234f55dfbd663cb1b77b5d`
мав `root reconstruction rejected: 0`. Колега виправив невідповідність
типу очікуваного маркера `accepted`: замість D7-списку гліфів потрібно
нормативне `(як-є accepted)` через D3:001.

Окремий діагностичний коміт `53585e83bbcd5d0365bb8cb69f7f6493f9fb51f3`
зробив реальний SENS reconstruction доступним у повідомленні відмови.

## Наш невідкатний регресійний свідок
У `crates/sens-cli/src/bin/wsm-fs-record-consumer.rs` додаємо тест
`f6_quoted_marker_matches_native_source`, який виконує справжнім
виконавцем SENS дві форми:
1. source `(як-є accepted)`;
2. D3:001 QUOTE з вихідним SENS `ExprKind::Symbol("accepted")`.

Тест порівнює обчислені SENS значення, а не випробовує Python,
Rust-предикат як оракул мови або переписану бізнес-логіку.
Фізична діагностика помилок F6 колег збережена.

## Статус
`NATIVE_F6_QUOTED_MARKER=NOT_VERIFIED_ON_NEW_SHA`.
`F6_END_TO_END=NOT_VERIFIED_ON_NEW_SHA`.
`RELEASE=l0.42.0:NO-GO`.

## Наступному агенту
Виконати один штатний CI на SHA, звірити два F6 інтеграційні
свідки та цей SENS-quote тест. Якщо root усе ще rejected,
діагностувати за точним SENS результатом, не повертати D7
гліфовий список як підміну символа. Продовжити незалежний
аудит D1–D12+ і релізні ворота без ручного rerun RED.
