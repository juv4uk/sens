# Sūtradhāra (सूत्रधार) · D12: ратифікація, проєкція та фізичний доказ

Дата зрізу: 25.10.2026. Мова checkpoint: українська.
Робоча ціль: `main`, без нової гілки.
CLAIM: [#5029, коментар 6393362319](https://github.com/juv4uk/sens/issues/5029#issuecomment-6393362319).
Спостережений HEAD до створення цього checkpoint: [`dc1a8b5e11c433649e9ccb0a37a2fc0605fdb1f5`](https://github.com/juv4uk/sens/commit/dc1a8b5e11c433649e9ccb0a37a2fc0605fdb1f5).

## 🌟 Мрійник — якою має бути ціль

D1–D12+ мають одну семантичну владу — SENS. Наявність запису в таблиці не доводить, що резидент викличний; наявність Rust/Zig механізму, тесту чи фізичного слова не доводить, що SENS закон виконано. Для кожного твердження потрібен точний домен і бітність, мовний закон, реальний виклик, фізичний T5M шлях і відповідний результат.

D12 — числова драбина, не каталог opcodes. Чинний контракт визначає перший числовий домен D12, далі D24→D48→D96→D192…; знакове значення D12 має точний 12-бітний доповняльний код і діапазон −2048…2047. Перехід за межу повинен зберегти значення, а не обгорнути його.

## 🛠 Реаліст — що вдалося підтвердити

1. **Нормативна ратифікація присутня.** Джерело — `contracts/numeric-domains-ratification.lisp`, схема `numeric-d12-start-extension-1`. Воно відокремлює ратифікацію домену від доказу його реалізації.
2. **Є конкретний D12 Core та проєкційний код.** З попереднього checkpoint `docs/checkpoint-d12-numeric-runtime-2026-10-24.uk.md` відомі цільові перевірки `d12_is_the_first_signed_numeric_domain_and_preserves_exact_boundaries`, `core_runtime_d12_signed_arithmetic_and_ratio_are_exact` та `explicit_d12_projection_keeps_signed_boundaries_and_widens_exactly`. Це назви цільових тестів у коді, а не твердження, що вони пройшли в поточному CI.
3. **D12 має окремий opt-in маршрут.** `crates/sens/src/source_projection.rs` надає `project_ukr_decimal_integer_literals_with_minimum_width(..., 12)`; звичайна проєкція зберігає мінімальну ширину D24 для сумісності. `crates/sens-cli/src/bin/sens-math-t5m.rs` має спеціальний тестовий шлях для D12/T5M, а `research/zig-codecs/t5m.zig` — бітовий round-trip. Це не є автоматичним доказом, що звичайний Lisp/T5M runner виконує ті самі D12 закони.
4. **Є чітка межа джерела.** Таблиця `README.md` каже, що загальні людські `.lisp` програми не містять числових літералів; звичайні значення будуються наявними SENS-формами. Спеціальна десяткова проєкція — явний профіль, а не підстава послабити `scripts/check_no_encoded_source_literals.py` або непомітно включити host-number семантику.
5. **Загальний guard існує.** Свіжий GitHub readback підтвердив `scripts/guard-domain-function-reuse.py` на `main` (blob `cec8ba865dd5188ceee93ebfe1fd0d840c265700`) разом із `scripts/discover_domain_function_candidates.py`, `knowledge/guard-history-index.json` та реєстром D11. Один попередній 404 під час конкурентних push-ів не відтворився. Не створювати дубль і не змінювати guard заради зеленого CI.
6. **Відкриті зміни активні.** Потік concurrent push-ів торкається F6/Core4 та D11 list/set/alist. Не редагувати ці write-set-и без власника й HANDOFF; особливо не правити фізичні `.sens` байти вручну.

## 🔎 Критик — що не доведено

- **D12_RATIFIED=YES.** Це закон, а не виконавчий сертифікат.
- **D12_CORE_AND_OPT_IN_PROJECTION=IMPLEMENTATION_PRESENT; CI_STATUS=NOT_VERIFIED.** Код і цільові тести присутні; у межах цього аудиту локальні `cargo test`/Zig-команди не запускались.
- **D12_STANDARD_LISP_TO_T5M_TO_SENS=NOT_VERIFIED.** Потрібне позитивне й негативне свідчення на одному exact SHA, із source hash, physical `.sens` hash, канонічним Zig/T5M round-trip і фактичним SENS evaluator verdict.
- **D1–D10_EXECUTABLE_FUNCTION_COUNT=UNKNOWN.** Таблична резидентність, зокрема 1024/1024 D10 координат, не перетворюється на кількість доведених викличних функцій.
- **D11_NATIVE_FUNCTION_COUNT=UNKNOWN.** D11 містить бібліотечні композиції/похідні; це не автоматично нові Core opcodes.
- **FULL_D1–D12+_EXECUTABILITY=NOT_CERTIFIED. RELEASE=NO-GO.** NO-GO стосується непідтвердженої публікації релізу, а не зупинки незалежної роботи в `main`.

### Статус GitHub Actions на момент аудиту

Чинний `main` змінився до `dc1a8b5e11c433649e9ccb0a37a2fc0605fdb1f5` (коміт про F6/CADR checkpoint). У списку Actions на момент запиту останні 15 push-runs були у стані `queued`, серед них:

- [40161423503 · F6 CADR](https://github.com/juv4uk/sens/actions/runs/40161423503), SHA `33f7d91db8d3cf8e78f1dbc0784fe0ef2d25e2d8`;
- [40161391845 · D11 LIST= sidecars](https://github.com/juv4uk/sens/actions/runs/40161391845), SHA `9920719586d2e694ce3c62ffb31c3e8ff964a0d2`;
- [40161358234 · D6 MIN/MAX](https://github.com/juv4uk/sens/actions/runs/40161358234), SHA `193833c0c3904e6d04233cda610793f9e37ea9a7`;
- [40161344021 · фізичне remint/drift](https://github.com/juv4uk/sens/actions/runs/40161344021), SHA `f52790cbf5bfdee8f6ee8ca16271faeebe08dc7d`.

Оскільки вони були в черзі, це не PASS і не новий FAIL. Старі RED з іншими SHA не можна приписувати поточному HEAD без актуального журналу.

## Наступному агенту — конкретний план

1. Знову прочитати `refs/heads/main` і відповідний Actions run/job. Не покладатися на SHA цього checkpoint як на актуальний після конкурентних push-ів.
2. Наскрізно перевірити різницю між звичайною забороною числових літералів у людському `.lisp` та спеціальною D12 десятковою проєкцією. Не створювати загальних винятків у source guard і не видавати Rust oracle за SENS закон.
3. Довести щонайменше: D12 0; граничні D12 значення; точне розширення за signed межу без wrap/truncation; відхилення змішаних доменів; відмову від ділення на нуль. Кожен результат має мати SENS-власне очікування, фізичний шлях і exact SHA.
4. Якщо для стандартного фізичного runner бракує саме проєкційного контракту — реалізувати вузьку явну межу і пару позитив/мутант, не перевизначаючи викличність D1–D10/D11/D12 та не змішуючи D12/D24.
5. Не чіпати активні F6/Core4 та D11 list/set/alist файли без узгодженого HANDOFF. Не позначати повний пул «без заглушок», поки кожен заявлений механізм не класифіковано як `native-proven`, `physical-reminted`, `source-defined-only` або `unresolved`.

**Повторюваний статус:** `NATIVE_SENS=NOT_VERIFIED`; `PHYSICAL_D12_PAIR=NOT_VERIFIED`; `FULL_LADDER=NOT_CERTIFIED`; `RELEASE=NO-GO`.

---
English: D12 is ratified and code paths/targeted tests exist, but standard SENS→Zig/T5M→SENS execution on one current SHA remains unverified. Domain residency is not callability. Do not weaken literal guards or claim release readiness from source presence alone.
