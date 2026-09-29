# Двійкові ширини 3/4/5/6 — evidence для SENS #1738

Статус: дослідницький доказ, не призначення семантики.
Задача: juv4uk/sens#1738.
База вимірювання: SENS `7024e057`; живу координацію повторно перевірено на `43fc887f`.

## Межа влади

Поточні призначені ширини не змінюються:
- результат предиката: 1 біт;
- control/default structure: 2 біти;
- код Text: 7 біт (UPC-7);
- ідентичність Function: рівно 8 біт;
- Number: точне двійкове значення змінної ширини.

Простори 3, 4, 5 і 6 біт відкриті й можуть використовуватися, коли фіксована ширина прибирає більше складності, ніж додає. Сама кардинальність backend enum не створює значення SENS.

## Метод

Evidence поєднує:
- точну runtime-інспекцію resolved closures після звичайних Core2/Core3/Core4 loader-ів;
- структурне сканування всіх поточних `lib/**/*.lisp`;
- інспекцію поточного SENS FASL/wire;
- кардинальності поточних CML IR/machine enum;
- наявні контракти compiler-authority та error vocabulary.

Тимчасові probe-тести запускалися в ізольованому worktree й не є production-кодом.
## Вимірювання lexical coordinates

Точний runtime resolver probe:
- Core2: 6 унікальних closures, 12 `Local` refs, max depth 0, max slot 1;
- Core4: 78 унікальних closures, 404 refs, max depth 0, max slot 3;
- Core3: 81 унікальний closure, 410 refs, max depth 0, max slot 3.

Повний структурний корпус `lib/**/*.lisp`:
- 1430 lambda-форм;
- максимальна вкладеність lambda: 3;
- максимальна кількість параметрів: 9;
- приблизно 6917 lexical references.

Спостережений lexical depth:
`0=6868, 1=43, 2=6`.

Спостережений slot index:
`0=4455, 1=1903, 2=455, 3=77, 4=14, 5=10, 6=1, 7=1, 8=1`.

Покриття прямої короткої форми після уточнення розподілу depth/slot:
- Lex4 = depth1 | slot3: 6910/6917 = 99.8988%;
- Lex5 = depth2 | slot3: 6916/6917 = 99.9855%;
- Lex6 = depth2 | slot4: 6917/6917 = 100%.

Жодна fixed short form не може стати мовним лімітом вкладеності чи арності. Потрібна fail-closed довга форма довільної ширини.
## Факти transport

Поточний wire кодує малий `Local` як:
`TAG_LOCAL byte + depth varint byte + index varint byte` = 24 біти.

У справді bit-packed canonical stream гіпотетичний плоский Type3 давав би:
- Type3 + Lex4: 2 + 3 + 4 = 9 біт;
- Type3 + Lex5: 10 біт;
- Type3 + Lex6: 11 біт.

Це порівняння не переноситься без змін на byte-aligned cache.

Важлива корекція: поточний `gen-fasl` snapshot-ить raw parse output. `ExprKind::Local` виникає пізніше під час closure resolution, тому поточний Core4 FASL не отримує прямої економії від lexical coordinate.

Поточний wire уже механічно використовує обмежені кардинальності:
- `0x00..0x3f`: малі цілі 0..63;
- `0x40..0x4f`: довжини коротких списків 0..15.

Це evidence на користь компактного transport, але не дозвіл створювати другу семантику Number.

## Domain3: flat/per-element форма відкинута, block-scoped форма лишається гіпотезою

Поточний Control2 використовує `11`, після якого йде 2-бітний selector для Function, Number, Text або extension.

### Flat / per-element Type3

Плоский 3-бітний selector для кожного payload додає один selector bit до кожного наявного Function/Number/Text payload.

Для мінімального nested Type2 extension:
- primary payload платить 2 selector bits;
- extended lexical payload платить 4 selector bits;
- flat Type3 платить 3 selector bits для обох.

Отже flat Type3 додає 1 біт кожному primary payload і економить 1 біт кожному lexical payload. По щільності він виграє лише коли `lexical_count > primary_payload_count`.

Повний scan бібліотеки знайшов приблизно 17 527 точних Function8 token проти приблизно 6 917 lexical refs. Навіть якщо повністю ігнорувати Number/Text, нижня межа програшу flat Type3 становить:

```text
17 527 - 6 917 = 10 610 bits ~= 1326 bytes
```

Тому **flat/per-element Domain3 відкинутий як compression-кандидат** на поточному corpus. Для Text7 він був би ще гіршим: `Domain3 + char7` на кожен символ додає 3 біти до кожних 7 біт тексту.

### Block-scoped Domain3

Окрема, ще не спростована гіпотеза — Domain3 як **відкривач типізованої області**, а не тег кожного елемента:

```text
11 + Domain3 -> open typed region
raw Function8 / Text7 / Number elements inside the region
Control2 closes or changes the region
```

У такій формі один discriminator амортизується на весь блок. Це може:
- прибрати повторні host/FASL/wire enum tags;
- дати prefix-decodable typed region;
- не обкладати Text7 +43% податком на кожен символ.

Головний acceptance/falsifier для block-scoped форми:
**два незалежні substrates повинні декодувати один stream однаково, не ділячись host enums або implementation code.**

Block-scoped Domain3 ще нічого не заробив автоматично. Його треба порівняти з Type2 + extension за:
- загальними bits на реальному corpus;
- кількістю decoder states/branches;
- fail-closed malformed-region behavior;
- proof burden;
- explicit region termination / nesting law.

Якщо цього виграшу немає, 3 біти лишаються вільними.

## Lex4/Lex5/Lex6: точні break-even межі

Початковий Lex4=`depth2|slot2` виявився неоптимальним: corpus має дуже малу lexical depth, тому симетричний split марнує короткий простір.

Краща проста форма без таблиці:

```text
Lex4 = depth1 | slot3
Lex5 = depth2 | slot3
Lex6 = depth2 | slot4
```

Поточний corpus:
- Lex4(1+3): 6910 direct refs, 7 escapes (6 через depth=2, 1 через slot=8);
- Lex5(2+3): 6916 direct refs, 1 escape;
- Lex6(2+4): 6917 direct refs, 0 escapes.

Для coordinate-only порівняння спільні type/framing bits скорочуються. Нехай `C` — повна кількість coordinate bits для одного long-form escaped reference.

```text
Lex4 = 6910*4 + 7*C
Lex5 = 6916*5 + 1*C
Lex6 = 6917*6
```

Звідси:
- Lex4 < Lex5, якщо `C < ~1156.7 bits`;
- Lex4 < Lex6, якщо `C < ~1980.3 bits`;
- Lex5 < Lex6, якщо `C < 6922 bits`.

Будь-яка практична довга форма binary lexical coordinate очікувано значно менша за ці межі. Тому **raw density дуже сильно підтримує Lex4(1+3)**. Lex5 купує майже повну відсутність escape, а Lex6 — нуль current escape і найпростіший прямий шлях.

Це не призначає Lex4: тепер вирішальним стає реальний branch/decoder/proof cost семи long-form випадків.

## Error4: відкинути як canonical semantic domain за замовчуванням

Історично Rust `ErrorKind` мав 10 named categories, що технічно вміщаються у 4 біти. Але #1755/#1749 змінили саму основу питання: Rust error vocabulary більше не є semantic authority, а implementation failures не доведені як закритий мовний всесвіт.

Тому кардинальність старого enum — **не аргумент за Error4**.

Ризик fixed Error4:
- заморозити випадковий набір implementation failures у language semantics;
- повторити саме ту помилку authority, яку #1755 щойно стер;
- змусити майбутні substrates або брехати через старі коди, або ламати fixed domain.

Додатковий evidence: `UnsatisfiedConditional` уже є transition debt старого three-part COND і зникає разом із новою 2-part foundation law. Отже навіть історична кардинальність нестабільна.

Поточний verdict:
- **canonical Error4 semantic domain: reject-by-default**;
- private backend/error tags можуть мати 3/4/5/6 біт як mechanism packing;
- 1–2 окремі framing/result distinctions можуть колись заробити коротку форму лише через незалежний Lisp-owned contract;
- Rust enum ordinal/order ніколи не стає SENS identity.

Щоб повернути Error4 як semantic candidate, потрібен новий незалежний доказ, що мова справді має закритий, стабільний, implementation-independent error algebra. Поточних доказів немає.

## CML / machine evidence

Поточні кардинальності CML природно збігаються з відкритими ширинами:
- 3 біти: YmmReg=8, XmmReg=8, AluOp=8;
- 4 біти: X86Reg=16, CondCode=16;
- 5 біт: MachineInst=31; PrimOp=18; IR variants=20;
- FPGA protocol errors=14 -> 4 біти.

Сьогодні це compiler/backend facts. Компактний код може лишитися приватним або бути generated projection Lisp-owned machine contract; CML не повинен сам створювати numbering як semantic authority SENS.

## WSM / layout evidence: одна семантика не вимагає однієї tag-width

Незалежний аудит `wsm-my-lisp/docs/parity/machine-contract-audit.uk.md` уже фіксує реальний приклад двох представлень:
- freestanding WSM bootstrap ABI: `TAG_MASK=7`, тобто 3-bit low tags;
- SENS `memory-layout-contract.lisp`: 4-bit nan-boxing tag у bits 31..28.

WSM-аудит класифікує цю різницю як різні **physical representation mechanisms**, а не як semantic drift. Це підтримує правило #1738: корисна 3/4-бітна ширина може лишатися mechanism-private й не потребує нового мовного domain.

Водночас поточна 4-bit tag table в `memory-layout-contract.lisp` містить старі ролі `symbol`, `true`, UTF-8 `string` тощо, які конфліктують із новою binary-only ontology. Тому:
- сам факт зручності 4-bit physical field є evidence;
- старе призначення tag values **не** є кандидатом для механічного перенесення в canonical SENS;
- будь-який новий 4-bit semantic domain потребує власної Lisp-owned authority, а не успадкування старих nan-boxing ordinals.

## Попередня матриця кандидатів

| Ширина | Кандидат | Evidence | Поточна рекомендація |
|---|---|---|---|
| 3 | flat/per-element domain discriminator | +1 selector bit на primary payload; >=10 610 bits програш ще до Number/Text | відкинути як compression-кандидат |
| 3 | block-scoped domain opener | один Domain3 на typed region; raw payload усередині | досліджувати тільки як block/framing grammar; потрібен незалежний cross-substrate decode proof |
| 3 | machine operand classes | кілька CML families мають рівно 8 станів | backend-private, доки не виводиться з upstream machine contract |
| 4 | Lex4 short coordinate | depth1|slot3: 99.8988% direct; 7 escapes; beats Lex5 if long form <~1156.7 bits | найсильніший raw-density кандидат; decoder cost ще виміряти |
| 4 | Error4 semantic domain | historical Rust enum fit 4 bits, але #1755 стер його authority | reject-by-default; лише private packing або окремо ратифіковане framing |
| 4 | FASL/tag families | поточні ExprKind/FASL мають 10 станів | mechanism-only; переоцінити після Symbol/String cleanup |
| 5 | Lex5 short coordinate | 99.9855%; 1 escape; beats Lex6 if long form <6922 bits | майже без escape; компроміс density/simplicity |
| 5 | CML MachineInst/IR | 31/20/18 станів | корисний machine encoding candidate, не автоматично SENS |
| 6 | Lex6 short coordinate | 100% direct; 0 current escapes | найпростіший current decode, але більший raw bit cost |
| 6 | wire small-int capacity | wire вже використовує 64-state range | лишити mechanism-private; не робити другою Number semantics |

## Відкриті питання

1. Block-scoped Domain3: чи один opener на typed region реально спрощує state machine/host-tag removal проти Type2+extension, і як region явно завершується/вкладається.
2. Cross-substrate criterion: два незалежні decoder-и повинні отримувати однаковий stream semantics без спільних host enums/code.
3. CML: чи MachineInst=31 достатньо стабільний для packing, чи це backend-evolving набір.
4. Lexical representation: виміряти branch/decoder/proof cost 7 Lex4(1+3) escapes проти 1 Lex5 escape та 0 Lex6 escapes; raw density уже сильно схиляється до Lex4.
5. Alignment: canonical storage має бути bit-packed, byte-packed, чи треба розділити canonical bits і transport packing.
6. Final outcome: документоване рішення лишити 3/4/5/6 FREE є повноцінним успішним результатом, якщо жодна ширина не видаляє достатньо складності.

## Правило дослідження

Не заповнювати вільну ширину заради симетрії. Призначати її лише тоді, коли fixed-width domain видаляє більший обсяг випадкової складності, і тримати явну межу між мовною семантикою та backend-private packing.
