# D10 — CLOS roots stacked after historical primary batch

Дата: 2026-10-09. Координація: #4013, #4463, #4867.

Перша серія #4866: 625→627; друга CLOS серія: 627→630 (+3). Це SELECTED-RESEARCH (не ратифікація): 256 law-forced, 374 unplaced, 394 remaining, 0 ratified, 0 T5 authorizations.

| Семантика | Спостережуваний закон | Першоджерело |
| --- | --- | --- |
| SLOT-BOUNDP | existing unbound ≠ bound NIL; D8 BOUNDP стосується змінної-символу | https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_slot-boundp.html |
| SLOT-MAKUNBOUND | скидати binding слоту, не видаляти слот і не замінювати NIL; instance identity зберігається | https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_slot-makunbound.html |
| REMOVE-METHOD | прибрати тільки один метод з generic; відсутній метод без помилки | https://www.lispworks.com/documentation/HyperSpec/Body/f_rm_met.htm |

Позитивні свідки, фальсифікатори, українські поверхні та первинне provenance зберігаються в 3 канонічних research rows, що спираються на вже злиті #4842 і #4843.

Історичний proof: 625-row Git blob 73dd518469f972c55411e004b70b054ba8b3ec86, #4866 627-row 5a8cf8e81edecf9ffdeb313152c0e146f4df80bb, ця stacked 630-row a55f307c27f17091795d75ebfcd7d051547d80bc.
Файл knowledge/d10-selection-transition-history.json дозволяє відновити попередні Git blob SHA без зміни старих значень. Скрипт scripts/check_d10_selection_transition_history.py --self-test перевіряє 8 фальсифікаторів. Незалежну SENS/CLOS runtime-parity НЕ стверджено.

Це stacked PR проти гілки #4866; після злиття predecessor потрібний replay/rebase на live main. Не переносити D2 control в D10; всі три candidate coordinate=null, ratified=false та pending-owner-review.
