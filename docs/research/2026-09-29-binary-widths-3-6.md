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

Покриття прямої короткої форми:
- Lex4 = depth2 | slot2: 6890/6917 = 99.6097%;
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

## Domain3 проти поточного Type2 baseline

Поточний Control2 використовує `11`, після якого йде 2-бітний selector для Function, Number, Text або extension.

Плоский 3-бітний selector дає 8 класів і простішу плоску таблицю dispatch, але додає один selector bit до кожного наявного Function/Number/Text payload.

Для мінімального nested Type2 extension:
- primary payload платить 2 selector bits;
- extended lexical payload платить 4 selector bits;
- flat Type3 платить 3 selector bits для обох.

Отже Type3 додає 1 біт кожному primary payload і економить 1 біт кожному lexical payload. По щільності він виграє лише коли `lexical_count > primary_payload_count`.

Повний scan бібліотеки знайшов приблизно 17 527 точних Function8 token проти приблизно 6 917 lexical refs. Навіть якщо повністю ігнорувати Number/Text, нижня межа програшу flat Type3 становить:

```text
17 527 - 6 917 = 10 610 bits ~= 1326 bytes
```

Тому Domain3 на поточному корпусі вже **доведено не є виграшем у щільності** проти цього Type2+extension baseline. Його можлива перевага:
- простіший decoder;
- чіткіша ортогональність;
- більше fail-closed reserved classes;
- простіше майбутнє extension/proof structure.

Перед призначенням його треба порівняти з Type2 + nested extension за decoder/proof cost, а не за compression.

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

## Чотирибітний кандидат: error vocabulary

Поточний observable `ErrorKind` має 10 навмисно admitted категорій. Compiler-authority boundary каже, що backend може мати будь-яке приватне представлення помилки, але не може назовні створити нову категорію поза admitted vocabulary.

Десять станів вміщаються у 4 біти.

Це сильніший semantic candidate, ніж просте стискання FASL tags, але спочатку треба повернути authority:
- #1708 переносить semantic/error-domain authority з Rust tests у Lisp-owned contracts/witnesses;
- `UnsatisfiedConditional` належить старому three-part COND і може зникнути;
- ordinal/order Rust enum ніколи не повинен ставати binary identity.

Порядок дослідження: Lisp-owned error vocabulary -> остаточна кардинальність -> оцінка Error4.

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
| 3 | payload/domain discriminator | 8 класів; evaluator head families вміщаються | досліджувати далі; Type2+extension може бути щільнішим |
| 3 | machine operand classes | кілька CML families мають рівно 8 станів | backend-private, доки не виводиться з upstream machine contract |
| 4 | Lex4 short coordinate | depth1|slot3: 99.8988% direct; 7 escapes; beats Lex5 if long form <~1156.7 bits | найсильніший raw-density кандидат; decoder cost ще виміряти |
| 4 | Error4 | 10 поточних admitted observable error classes | сильний кандидат після Lisp authority migration |
| 4 | FASL/tag families | поточні ExprKind/FASL мають 10 станів | mechanism-only; переоцінити після Symbol/String cleanup |
| 5 | Lex5 short coordinate | 99.9855%; 1 escape; beats Lex6 if long form <6922 bits | майже без escape; компроміс density/simplicity |
| 5 | CML MachineInst/IR | 31/20/18 станів | корисний machine encoding candidate, не автоматично SENS |
| 6 | Lex6 short coordinate | 100% direct; 0 current escapes | найпростіший current decode, але більший raw bit cost |
| 6 | wire small-int capacity | wire вже використовує 64-state range | лишити mechanism-private; не робити другою Number semantics |

## Відкриті питання

1. Hardware/FPGA: area/timing/proof burden Type2+extension проти flat Type3; compression уже не є аргументом за Type3 на поточному corpus.
2. CML: чи MachineInst=31 достатньо стабільний для packing, чи це backend-evolving набір.
3. Lexical representation: виміряти branch/decoder/proof cost 7 Lex4(1+3) escapes проти 1 Lex5 escape та 0 Lex6 escapes; raw density уже сильно схиляється до Lex4.
4. Error vocabulary: остаточний Lisp-owned набір категорій після видалення старого COND/error debt.
5. Alignment: canonical storage має бути bit-packed, byte-packed, чи треба розділити canonical bits і transport packing.

## Правило дослідження

Не заповнювати вільну ширину заради симетрії. Призначати її лише тоді, коли fixed-width domain видаляє більший обсяг випадкової складності, і тримати явну межу між мовною семантикою та backend-private packing.
