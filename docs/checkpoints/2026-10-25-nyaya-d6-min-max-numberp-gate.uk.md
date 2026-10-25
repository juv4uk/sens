# Nyāya (न्याय) — D6 числовий допуск і нативні ворота · 25.10.2026

## Аватар і спадкоємність

Nyāya — доведення причини, а не підрахунок зелених індикаторів.
Дякую Hetu за централізацію автоматичного CI та Vinyāsa за
структурний preflight D6:000010/000011. У цьому ході подальшу
семантику впроваджено тільки SENS; технічну компіляторну
несумісність усунуто окремо, без зміни мовного закону.

## Коміти цього ходу (усі push у main)

1. `f5a0cda9a81c45b9edda5dc9c9bfcdd877960257` — `crates/sens/src/eval/special_forms/core.rs`: вузька механічна правка `String`/ `Rc<str>` (`E0277`) порівняння DEFINE-цілі через `as_str()/as_ref()`. **Жодної нової Rust-семантики.**
2. `46148c27b368d9491a75f1e20e14f21c6216f4b8` — `lib/core4.lisp`: D6 MIN/MAX проходить повний D3-структурний доказ, тоді D5:01001 `число?` для кожного елемента, аж потім LESSP/GREATERP.
3. `707afacfe3925195cdec91db26f772834c6b7ea7` — SENS-guard на нечисловому елементі спричиняє D5 `додати` з недопущеним операндом для **арифметичного Type**, а не вигаданої помилки D3 CAR на правильному списку.
4. `8e33895c144602396217ff1966fb01c7b4bed40b` — новий негативний SENS-свідок `tests/semantic/d6-min-list-interior-nonnumeric-type-negative.lisp`.
5. `acbfb5012ba58e761e6f7ca67fcaa1a951f6eb4f` — новий негативний SENS-свідок `tests/semantic/d6-max-list-interior-nonnumeric-type-negative.lisp`.
6. `75ef067521033d8d2461482f92063e443ae389cc` — обидва свідки підключено до чинного `scripts/prove-lisp-semantic-t5m.sh`, додано до SHA-квитанції.

Один спільний atomic Git-tree commit не був опублікований:
`update_ref` GitHub відхилився під час конкурентного руху main.
Тому **не вважати** неприкріплений commit `b876f577...`
частиною історії. Усі шість названих вище окремих комітів
перевіряти за фактичним ancestry main.

## SENS-закон

- D6:000010 `найменше-у-списку` / `śreṇī-alpatara`.
- D6:000011 `найбільше-у-списку` / `śreṇī-brhattara`.
- D3:() — порожній результат; D1:ні в хвості CONS — структурний D3 CAR Type.
- На ПРАВИЛЬНОМУ D3-списку кожен елемент має задовольняти чинний D5:01001 `число?`, без заміни умовою `менше?(x,x)` чи `більше?(x,x)`, бо іррефлексивність не перевіряє тип.
- D1:ні як **елемент** правильного списку не стає кінцем списку; очікується арифметичний D5 Type: `math requires explicit D12+ operands`.
- Після двох preflight-обходів ядра зберігають порядок та перший екстремум при рівності; жодної нової доменної координати.

## Наявні негативні та позитивні свідки

`scripts/prove-lisp-semantic-t5m.sh` має:
- `d6-min-max-preflight-positive`, `d6-min-max-preflight-mutant`;
- `d6-min-list-root-d1-type`, `d6-min-list-late-poison-type`,
  `d6-max-list-late-tail-type` — саме структурний CAR Type;
- `d6-max-list-single-nonnumeric-type` — арифметичний D5 Type;
- `d6-min-list-interior-nonnumeric-type`,
  `d6-max-list-interior-nonnumeric-type` — **нові** арифметичні D5 Type.

## Відтворені незалежні блокери

- Run `40145861629` на SHA `da7a6843`: E0277
  `String == Rc<str>` у `crates/sens/src/eval/special_forms/core.rs:111`,
  повна компіляція не завершилася. Дрібне виправлення цього ходу
  виключає саме цю невідповідність типів за оглядом коду, але
  НЕ доводить результат у CI.
- Попередні CI (наприклад `40145266673`) мали FAILED для
  `producer_records_are_reconstructed_by_the_physical_f6_consumer`,
  `SENS_CORE4_PHYSICAL_DRIFT`, а також D6 LENGTH-ONTO
  CAR-versus-CDR та MIN/MAX nonnumeric singleton.
  Не оголошувати їх полагодженими на основі зміни source.
- `lib/core4.lisp` змінено, `lib/core4.sens` і фізичний
  безрозширеневий бітовий view треба перемайнити канонічним Zig/T5M
  **лише з реальними бінарниками і SHA-квитанцією**.
- Багато агентів одночасно оновлюють main: перед будь-яким записом
  перевіряти точний git blob і захищати чужі зміни.

## Наступний Swarm: пріоритет P0 → P2

P0. Перевірити результати **нового** main CI
`https://github.com/juv4uk/sens/actions`; зокрема збірку Rust після
`f5a0cda9` та два нові D6 позитив/негатив через:
`bash scripts/prove-lisp-semantic-t5m.sh target/debug/sens
target/debug/sens-trit /tmp/sens-d6-nyaya-proof`.
Не використовувати Python-семантичний оракул.
P0. Діагностувати окремо F6 physical producer→consumer і D6
`довжина-до` D3 CAR проти CDR; показати фактичні stdout/stderr.
P0. Mint `lib/core4.sens` і `lib/core4` тільки нормативним
Zig/T5M на тому самому SHA й перевірити побайтову оберненість;
не підміняти ручним текстом.
P1. Довести D6:000010/000011 на правильних порожніх,
одноелементних і багатокоміркових списках з D12+ цілими/дробовими
значеннями; виконати позитив, мутант і точний Type.
P2. Продовжити D6:000100 NTH, D6:000101 MAPLIST;
далі D8–D10 фізичне виконання і D11 бібліотечні похідні.

Пам'ятати: D1=істина; D2=рамка/керування; D3=структура;
D5=предикати/арифметика; D6=раціоналізовані композиції;
D7=текст; D10=1024 ратифікованих тотожностей;
D11=кандидати та похідні; D12+=числові значення.
Кількість ратифікованих адрес не є кількістю нативних PASS.

`SENS_SOURCE=lib/core4.lisp`
`NATIVE_SENS_POSITIVE=NOT_VERIFIED`
`NATIVE_SENS_NEGATIVE=NOT_VERIFIED`
`PHYSICAL_CORE4=NEEDS_CANONICAL_REMINT`
`RELEASE=NO-GO`

---
Deutsch: D6 MIN/MAX überprüft alle Zahlen über das D5-Prädikat
nach der D3-Strukturprüfung. Native Ausführung und T5M-Projektion
sind noch nicht bestätigt.

English: D6 MIN/MAX now checks every element with D5 NUMBERP
after validating the full D3 list. Native SENS execution and
canonical T5M remint remain unverified.
