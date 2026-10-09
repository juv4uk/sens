# D10: перша відібрана серія CLOS semantic roots

Дата: 2026-10-09. Координація: #4013, #4463, #4842, #4843.

Мета — **фактичне розширення дослідницького інвентарю**: 625 → 628, залишок 399 → 396. Це не ратифікація та не T5 чи виконувані інструкції.

| Кандидат | Відмінний спостережуваний закон | Першоджерело |
| --- | --- | --- |
| SLOT-BOUNDP | Unbound existing slot ≠ bound-to-NIL, не те саме що BOUNDP у D8 | [CLHS](https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_slot-boundp.html) |
| SLOT-MAKUNBOUND | Розв'язати лише slot без його видалення або втрати ідентичності instance, запис NIL не еквівалентний | [CLHS](https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_slot-makunbound.html) |
| REMOVE-METHOD | Вилучити один конкретний method object із generic, зберігаючи інші; відсутній method не створює помилки | [CLHS](https://www.lispworks.com/documentation/HyperSpec/Body/f_rm_met.htm) |

## Фальсифіковані позитивні свідки

1. SLOT-BOUNDP: a оголошено без initform => NO; присвоїти a=NIL => YES. Контрприклад: плутати NIL та unbound або неіснуючий slot.
2. SLOT-MAKUNBOUND: a=3,b=4; unbind(a) => slot a залишається, bound(a)=NO, b=4, instance identity збережена. Контрприклад: присвоєння NIL чи видалення слоту.
3. REMOVE-METHOD: generic G має A,B. Remove A залишає B; повторно remove A не сигналізує помилку. Контрприклад: зникнення B чи всього G.

Guard scripts/check_d10_clos_roots_selection.py перевіряє 7 негативних мутацій, provenance, дедуп точних назв D1–D9, 628+ лічильник, власниковий gate і unplaced. Він не підміняє незалежний executable CLOS-vs-SENS runtime oracle.

## Ownership і що відкладено

Синтаксис та transfer/control залишаються у D2. Нові три записи мають coordinate=null, donor_coordinate_authority=NONE, proposal_status=pending-owner-review, ratified_resident=false.
Сусідні SLOT-EXISTS-P, CLASS-OF, FIND-METHOD та CHANGE-CLASS не підвищуються автоматично: потрібні derivability tests. Підтвердження exact-name absence ще не доводить поведінкову незалежність; лише вихідні негативні свідки обґрунтовують дослідницьку selection.

Донори: knowledge/d10-clos-slot-state-historical-review-v1.json (злитий PR #4843) і knowledge/d10-historical-clos-interlisp-residual-review-v1.json (злитий PR #4842).

Будь-яка виконавча реалізація повинна показати такі ж результати на oracle, перш ніж API може бути допущений до фізичної мови.
