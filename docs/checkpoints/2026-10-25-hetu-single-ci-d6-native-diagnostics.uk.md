# Hetu (हेतु) — SENS D1–D12+: єдиний CI та точні незакриті причини · 25.10.2026

## Сфера й рішення

Дякую Vinyāsa за попередній SENS JUXT та Sūtradhāra за реєстр
фізичних свідків. У цьому ході змінено **тільки CI-механізм**.
Семантика SENS, координати D1–D11, числовий D12+, Rust/Zig evaluator
і нативні трійки не змінювалися.

Коміти цього ходу:
- `5a9b7ce155aba97445a6fd2f26800e7f1e033d8f` — `host-debt0.yml`
  залишено тільки для ручної діагностики, без додаткових push/PR.
- `e996f78a674fe15a08b3b3e94878db0edab6f086` — чинні
  `ensure-host-debt0.sh` і два тести `language_stays_in_sens` перенесено
  до центрального `.github/workflows/ci.yml`. Тест
  `test_domain_function_reuse_rule` у центральному CI вже існував;
  не дублюємо його.

Першопричина за GitHub run `40144142376`, job `121021798342`:
`SENS_CI_BUDGET_FAIL host-debt0.yml: додатковий автоматичний тригер
['pull_request', 'push']`.
Відсутність єдиного автоматичного workflow була **конкретним**
порушенням власницької політики запусків.

## Перевірений результат

Для SHA `e996f78a674fe15a08b3b3e94878db0edab6f086`,
CI run `40145013879`, спостережені завершення:
- step 3 «Один автоматичний CI — тільки поточний main»: SUCCESS;
- step 4 «Чинний SENS захист — host debt та незмінність мови»: SUCCESS;
- step 5 «Rust CLI — рання перевірка синтаксису REPL»: SUCCESS.

Увесь CI на момент перевірки ще виконувався; **не** переносити
часткове SUCCESS на всі SENS-мовні закони чи реліз.

## Важливі незалежні мовні невизначеності

1. **D11 JUXT:** два неправильні виклики
   `підтвердити-набір-одномісних-функцій` замість чинного SENS
   `підтвердити-правильний-набір-функцій` уже виправив інший агент
   у `0749722028872f81a3b854a0e2ce59e30bdaa027`; жодного
   дублюючого коміту не робити. Старий CI run `40144142376`
   повідомляв `d11-clojure-juxt-positive` як unknown Text7 binding;
   після виправлення потрібен НОВИЙ нативний свідок на чинному SHA.
2. **D6:000001 LENGTH-ONTO:** старий native run `40144142376`
   відтворив `cdr expects a non-empty list` для
   `tests/semantic/d6-length-onto-d1-root-negative.lisp` і
   `tests/semantic/d6-length-onto-late-d1-tail-negative.lisp`.
   Нормативне очікування обох свідків — `car expects a non-empty list`
   ще до арифметики. Реальна різниця **CAR проти CDR**, а не невідомий
   загальний `Type`. Джерела SENS:
   `lib/core4.lisp` та `lib/core4-parts/core4-language.lisp`,
   обидва визначають `довжина-до` через D3 `атом?` і D3 `решта`.
   Не підміняти очікуваний CAR на CDR заради зеленого CI; треба
   відтворити і виправити семантичний порядок у SENS, та після цього
   фізично перемайнити Core4.
3. **Core4 фізична проєкція:** у цьому ж CI
   `SENS_CORE4_PHYSICAL_DRIFT`: `lib/core4.sens` не збігається зі
   свіжим mint. Це окремий транспортний борг, не доказ хибності SENS.
4. **F6 producer/consumer:** Rust-механічний інтеграційний
   `producer_records_are_reconstructed_by_the_physical_f6_consumer`
   мав FAILED. Діагностувати окремо, не переносити на D6 закон.
5. **D8 мутант кванторів:** старі CI спостереження мають RED
   `d8-quantifier-composition-mutant`; на main з'явилися пізніші
   виправлення мутанта. Перевірити на новому SHA, не запускати вдруге
   старі червоні workflow.

## Наступний Swarm-таргет

1. На свіжому `main` прочитати `git status --short`, SHA і
   оригінальні SENS DEFINE; уникнути паралельної зміни чужого файлу.
2. Зібрати нативні `sens` і `sens-trit` та запустити
   `bash scripts/prove-lisp-semantic-t5m.sh target/debug/sens
   target/debug/sens-trit /tmp/sens-proof-hetu`, фіксуючи
   позитивний/негативний свідок, stderr, SHA та фізичний carrier.
   Виконання без справжнього SENS не є семантичним PASS.
3. Для D6 `довжина-до` першочергово відновити пріоритет D3 CAR Type
   над CDR Type у двох негативних випадках засобами SENS.
   Продовжити позитивний/мутант для D6:000000, D6:000001;
   тільки після нього D6:000010, D6:000011.
4. Відновити Core4 та JUXT фізичні трійки канонічним Zig/T5M, перевірити
   `.lisp ↔ .sens ↔ бітовий вигляд` і source-matched виконання на
   **одному** SHA; не конструювати фальшиві байти вручну.
5. D1/D2 є доменами істини/структури, D7 — текст, D12+ — числа.
   Викличні D3–D11 визначати за ратифікованим законом і санскритською
   проєкцією; координата без свідка не дорівнює runtime PASS.
6. Не оголошувати реліз GO до повного атестаційного SHA й рішення
   власника.

`SENS_SOURCE=N/A: лише механізм CI`
`NATIVE_SENS_POSITIVE=NOT_VERIFIED`
`NATIVE_SENS_NEGATIVE=NOT_VERIFIED`
`RELEASE=NO-GO`

---
Deutsch: Die doppelten automatischen CI-Trigger wurden entfernt.
Der zentrale Workflow führt die bestehenden Schutzprüfungen aus.
D6 CAR/CDR-Diagnostik und Native-T5M-Parität bleiben offen.

English: Removed duplicate automatic CI triggers while retaining the
existing safeguards in the central workflow. D6 CAR-versus-CDR
semantics and physical T5M parity still require native evidence.
