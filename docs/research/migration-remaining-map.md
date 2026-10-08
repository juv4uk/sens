# Карта залишку міграції lib/ — блокер → рішення

**Знімок мігратора:** 2026-10-08 · **Джерело:** канонічний `scripts/migrate-three-pass.py --source-era legacy`
**Обсяг:** `lib/**/*.lisp` = 128 файлів · **матеріально підготовлено 1** (`lib/machine/block.lisp`, candidate only) · **блоковано 127**

## Головний висновок

Блокери — це **не «мова не двійкова»**, а **шість названих класів**. Один із них домінує:

| # | Клас | Файлів у цьому знімку | Що потрібно | Власник / lane |
|---|---|---:|---|---|
| 1 | **Іменовані форми** (`word 2/4: got '<name>'`) | **67** | Text7-фреймінг top-level імен + розв'язок локальних (`Local(depth,index)`) | #3910, теперішній replay #4799 |
| 2 | Декларативні `name/N` схеми | 35 | класифікація є; потрібне owner-рішення для виключень | #4460 |
| 3 | D2 structural control | 9 | закон D2-фреймінгу / контекстної ролі | #3910 |
| 4 | SID8 unmapped `00001010` | 7 | ратифікований міст або точний BLOCK | #2953 |
| 5 | SID8 unmapped `00000000` | 3 | ратифікований міст або точний BLOCK | #2953 |
| 6 | empty/unsupported + misc | 4 | окремі source-specific докази | owner triage |

**Важливо:** класи перекриваються. 67 — оцінка потенційно уражених файлів у конкретному snapshot, **не** 67 доведених міграцій і не гарантований приріст після одного merge. Після кожного спільного закону треба повторно прогнати канонічний мігратор на поточному `main`.

## Найбільший важіль

Text7-контекст і lexical/global binding є найбільшим повторно використовуваним вузлом. Історичний candidate на #4749 дав байт-ідентичний packed T5 sample, але фізичний candidate сам по собі не проходить статус original executable admission. Не публікувати cohort лише за збігом bytes.

## Оновлення координації — 2026-10-09

Старий список «змержити один із #4776/#4777/#4779/#4780/#4781/#4782» **застарів як інструкція**. Поточний критичний ланцюг:

1. **Text7 / binder:** #4780 позначено superseded; використовувати єдиний clean current-main replay **#4799**. D2 лишається єдиним власником структури; W7-звичайні/quoted дані не можна переінтерпретувати як Symbol. Потрібні focused positive + negative тести й зелений CI.
2. **Core4 bootstrap:** #4789 — єдиний lane для opt-in `eval-core4` через вже наявний Lisp-owned Core library. Не створювати окремий Rust LIST/APPEND dispatcher. Перевіряти саме поточний head, бо попередні червоні запуски включали stale/truncated CLI parent та відсутню залежність `text7_binding_key`.
3. **CLI falsifier:** #4797 — additive integration tests, stacked on #4789. Перед інтерпретацією тестового результату перебазувати на виправлений parent і спершу довести `cargo build -p sens-cli --bin sens-trit`; stale-base compile errors не є доказом D2 grammar failure.
4. **Original-source proof:** #4774 — proof vehicle, а не завершена міграція. Source Git blob залишається `lib/machine/block.lisp@200201b741787c4e144ad4194848acf51d7b439e`. Генерувати packed T5 у тимчасовій теці, читати його Rust D2 reader, запускати через explicit Core4 і звірити всі **9/9 тих самих observable cases** з independent historical oracle.
5. **Admission:** після 9/9 над справжніми physical bytes створити/перевірити canonical українську `.lisp`, packed `.sens`, extensionless spaced-bit view, source/typed/physical digests і strict source-specific admission receipt. Лише тоді змінювати original-migration counter з 0 на 1.

### Чесний облік

Останній перевірений глобальний snapshot у координації: **503 `.lisp`, 13 physical `.sens` + 13 views, 490 unpaired, 211 DATA/archive, 279 active-or-unknown; 0 повністю сертифікованих historical executable physical migrations.** У `lib/` матеріально підготовлений `machine-block` не є admitted executable migration. Fixtures, views, source-only AST changes, mappings, staged physical bytes і green infrastructure tests рахуються окремо.

**Чому цифра мала:** не через відсутність конвертера. Не завершена повна однакова-самість між незмінним джерелом, фактичним фізичним T5, current runtime, independent 9-case oracle і трьома canonical projections. `open`, кілька успішних викликів або text-source parity не замінюють цього доказу.

## D10: паралельний research, не обхід міграції

На останньому прямому читанні `knowledge/d10-fill-v1-state.json` та `knowledge/d10-v1-semantic-inventory.json`: **625/1024 selected, 399 remaining, 256 law-forced, 369 unplaced, 0 ratified**. #4798 (+23) вже включено; #4800’s 8 Flavors/restart proposals — поза selected inventory, поки owner-review не вирішить інакше.

Кандидатні напрями з найкращим шансом на незалежну універсальну поведінку, лише research/HOLD до dedup та owner review:

- **Witness-carrying evidence query** (`lib/epistemic.lisp`): повертає той самий evidence record, а не лише Boolean. Перевірити identity, відсутність/неоднозначність свідчення й помилкову relation. Hold, якщо це лише package wrapper.
- **Persistent vector laws** (`lib/persistent-vector.lisp`): type-distinct empty, однозначна відсутність для `nth`, immutable append-at-end, round-trip до/зі списку. Перевірити D1 NO vs D3 NIL; `from-list`/`to-list` спершу вважати derivable, AVL rotation/height — mechanism-only.
- **Typed reasoning outcomes** (`lib/narrate.lisp`): не зливати PROVED/UNKNOWN/DISPUTED/BLOCKED/INVALID в NIL/false. Dedup обов'язковий проти #4798 meta-eval/reason candidates; presentation-only adapters тримати поза resident inventory.
- **Measurement/unit** (`lib/quantity.lisp`, `lib/si.lisp`) та **translation/equivalence** (`lib/translation.lisp`): harvesting робити за behavior clusters, а не просто рахувати кожен DEFINE як нову семантику.

Для кожної ідеї фіксувати donor blob SHA + line, exact observable law, preconditions, positive/negative falsifiers, D1–D9 + selected-D10 dedup, relation class, substrate-independent ownership, potentially affected source paths, `unblock_fanout`, `expressibility_gap` і `coordinate:null`. Fan-out ранжує роботу, але не доводить семантику. T5, D2 framing/control, Text7 plumbing, Local envelope, Core4 bootstrap, CLI/host APIs **не є D10 candidates**.

## Виконання в правильному порядку

`#4799 GREEN → #4789 GREEN → #4797 replayed GREEN → #4774 9/9 physical OLD↔CURRENT parity → Ukrainian .lisp/.sens/view + digests → first certified 0→1`.

Паралельно — D10 source-grounded discovery без координат і без ратифікації агентом. Не рухати release pins і не запускати сліпий batch по 279 active/unknown; спочатку кластеризувати їх за first shared blocker та повторно проганяти census після кожного підтвердженого закону.
