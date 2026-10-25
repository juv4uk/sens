# Sādhana · D6 LET/LET* · checkpoint 25.10.2026

Дякую Kārya за NTH/MAPLIST, `68de0a00f5b9af28de67999703831749e28da519`. Батьківський SHA цього пакета: `d05a02f06a7ae85f04cc7ebae0ffb1f07ab2f7c9`.

## Статус сходинок
D1:ні ≠ D3:(); D2 — reader; D3 CONS/CAR/CDR/ATOM/EQ; D4 COND/LAMBDA/DEFINE; D5 числові оператори; D7 тільки текст; D12+ — точна математика.
D6:000110 MACROEXPAND-1 (vistāra-rūpa-prasāra-eka) та D6:000111 MACROEXPAND (vistāra-rūpa-prasāra) ратифіковані, але механізми ще MISSING у `knowledge/d6-mechanism-ledger.json`. Загальний macroexpand потребує доступу до реальних макросів у лексичному оточенні. Не замінювати static-dispatch підробкою.
D6:001000 LET (sthānika-bandha), D6:001001 LET* (krama-sthānika-bandha) вже мають SENS DEFINE, але неправильно трактували атомні хвости як D3:().

## Виправлення мовою SENS
`підтвердити-д6-запис-привязки`: приймає лише два поля й непорожнє атомне ім'я. `підтвердити-д6-привязки`: перевіряє увесь хребет, тільки точне `()` завершує структуру. Два початкові проєктори `параметри-привязок` і `значення-привязок` більше не обриваються на довільному атомі. Обидва D6 макроси виконують структурний preflight ПЕРЕД побудовою розгортання. Паралельні та послідовні області видимості не змінено.

## Фізичні випробування
`scripts/prove-lisp-semantic-t5m.sh`: 4 SENS свідки (LET+LET* позитив; зайві поля обох; неправильний D1 хвіст). Статичний баланс дужок SENS PASS. `NATIVE_SENS=NOT_VERIFIED`, `ZIG_T5M=NOT_VERIFIED`, `Core4 physical triples=REQUIRES_REMINT`, `RELEASE=NO-GO`.

## Swarm далі
1. На точному SHA виконати 4 свідки через direct/paired/standalone реальними SENS/Zig/T5M, зберегти diagnostics і SHA256.
2. Нормативно перемінтити Core4 source/physical/view; без вигаданих бітів.
3. Дослідити D6 MACROEXPAND-1 доступ до реального macro environment: одна стадія не обчислює код, а D6 MACROEXPAND — транзитивне завершення з guard циклів; proof позитивні/негативні, lexical shadowing. Не видавати ратифікацію за native mechanism.
4. З'ясувати RED D6 LENGTH/MIN/MAX/NTH/MAPLIST, F6 Rust, D10 callable й D12, не повторювати хибних workflow. Власник вирішує про реліз.
