# Sūtradhāra · виправлення фізичного маршруту змінених D11-свідків · 2026-10-25

## Точне спостереження
CI коміту `95980202f69071ee2df2d0ebf973bed68a4f2515`
[GitHub Actions #40144213484](https://github.com/juv4uk/sens/actions/runs/40144213484)
завершився failure. Адресний changed-Lisp T5M маршрут перевірив 23
файли, два з них відмовили через `UnknownSymbol` до появи належних
D11 бібліотечних зв'язувань:
- `tests/semantic/d11-clojure-partition-direct-helper-bad-tail-negative.lisp`
- `tests/semantic/d11-clojure-partition-singleton-key-law.lisp`.

Це були **відмови перед завантаженням SENS DEFINE**, а не доведена
неправильність самої D11 семантики. У тому самому CI незалежний великий
мовний гейт повідомив 426/430 PASS і чотири інші RED:
`d6-length-onto-d1-root-type`, `d6-length-onto-late-d1-tail-type`,
`d11-clojure-juxt-positive`, `d8-quantifier-composition-mutant`.
Їх не можна списувати на нашу маршрутизацію чи позначати як PASS.

## Механічне виправлення
У `scripts/execute_changed_lisp_t5m.sh` доповнено точні SENS binding
джерела для позитиву й негативу D11 PARTITION-BY. Негатив проходить
строгу Type-класифікацію з direct / paired / standalone та очікуваним
`car expects a non-empty list`. Для standalone мітимо фізичний T5M
самодостатньої програми, яка включає реальні бібліотечні SENS DEFINE.

Ті самі правила підключені для **двох нових** D11 UNFOLD-RIGHT
негативів з коміту `61c89c5c2312955200e5bfed16ab1e9a3c03e6c5`.
Таким чином ані непідвантажений Text7, ані очікуваний callback CDR Type
не можуть маскувати справжню перевірку структурного D3 CAR Type.

У shell тільки маршрутизація, мітки тестів, класифікація справжніх
помилок, файловий I/O. Усі мовні висновки належать SENS.

## Стан і передача
Нативний CI нового коміту потребує перегляду окремо; у цьому ході
джерела перевірені статично, не виконувалися локальні SENS/Zig/Cargo.
Наявний source/view/carrier drift D11 усе ще потребує mint.
Не повторювати автоматично попередній RED; класифікувати й виправляти.

Наступний агент: довести ці чотири D11 свідки на одній SHA,
виправити чотири названі RED за першопричинами, синхронізувати
D11 фізичні трійки, перейти до D12+ і F6, залишити l0.42.0 NO-GO.

**Deutsch:** Exakte SENS DEFINE-Bindings für die geänderten D11
Zeugen; kein unbekanntes Symbol als bestandener Typnachweis.
**English:** Fix real-SENS bindings and strict negative witness
routing for four changed D11 files. No invented PASS.
