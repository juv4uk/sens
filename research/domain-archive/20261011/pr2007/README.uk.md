# Архів PR #2007 — strict PredicateBit/Core4 replay

**Статус: ARCHIVE-ONLY / НЕ ЗЛИВАТИ ВСЮ ГІЛКУ.**

PR #2007 має 23 змінені файли і відтворює старішу runtime-архітектуру з окремим `Value::PredicateBit`, Strict Core4/COND і значними змінами Core/Core4, bridge, authority guards та constitution. Поточний main представляє D1 через `DomainIdentity::D1(PredicateBit)` і має суттєво новіші core/core4 та registry/checker контракти. Wholesale merge створив би другу форму D1 result-identity і ризикував би зламати Contract 11.8.

Повний diff збережено в `predicatebit-core4-replay.patch` разом з маніфестом і цією українською нотаткою. У дифі залишилися два особливо корисні джерельні свідки: string ordering → exact predicate і McCarthy 1960 functions. Вони **не** оголошені активними/green; їх слід перепровести проти чинного runtime у вже наявних #1713/#1810/#5041.

Архів зберігає кожен текстовий hunk гілки в main. PR закривається як archived replay, не як семантично завершений випуск. Нову гілку не створено.
