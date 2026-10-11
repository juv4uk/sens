# Архів PR #2774 — D5 OD-005 historical consumers

**Статус: ARCHIVE-ONLY / історичні контрольні артефакти.**

PR #2774 додавав або перейменовував кілька workflow/benchmark-ів, щоб позначити старі D5 selection/closure/fill artefacts як pre-OD005 snapshots. Це важливий provenance-захист: історичні числа не повинні видаватися за чинний D5 contract.

Поточний D5 authority вже є owner-ratified OD-005 map 32/32. Тому старі workflow та baseline guards не зливаються поверх main, а їхній точний diff збережений у `od005-consumer-migration-review.patch`. Поточні gates не видаляються й не замінюються цим stale replay. Для будь-якої живої зміни потрібен окремий нинішній consumer/evidence, не повторне відкриття старої гілки. Нової гілки не створено.
