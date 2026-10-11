# Архів PR #1083 — provenance generated projections

**Статус: ARCHIVE-ONLY / GENERATOR NOT ACTIVE.**

Усі чотири branch-head файли з `agent/1061-projection-provenance`, SHA `69e36652f121fcb6670877fd83b05960fe14739b`, збережено в цьому архіві. PR пропонував реєстр source SHA/target SHA для п'яти згенерованих проєкцій; це корисний механізм відстеження provenance. Водночас він був прив'язаний до старого Canon SID `00001100` з представленням binary 8/u8 та старої генераторної топології.

У чинному main немає однойменного manifest/generator; тому не можна оголосити цей артефакт current authority або активувати старий CI. Порт потребує поточного registry-derived identity, exact source/target byte hashes, перевірки generator, чутливості до drift та negative mutation witness. Джерело лишається в main для #1061/#5041; нову гілку не створено.
