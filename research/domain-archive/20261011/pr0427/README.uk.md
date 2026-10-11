# Архів PR #427 — класифікація knowledge-артефактів

**Статус: ARCHIVE-ONLY / NEEDS CURRENT-SENS REVIEW.**

Збережено точні файли гілки `feat/383-knowledge-authority-classification`, head SHA `96b7f6a0b963c65752bcff6654aa1bc847bfa8ba`, разом із Git blob SHA для кожного оригіналу. Цей PR класифікував knowledge-артефакти за provenance/scope/role і додавав Lisp-owned live checker до CI. Ідея governance корисна, але старий пакет не переноситься напряму: він походить із старого main/base та потребує звірки шляхів, build/run команд і поточного складу `knowledge/`.

Поточний `docs/semantic-authority-map.md` вже прямо фіксує, що `knowledge/` не є окремим рівнем семантичного авторитету. Не слід дублювати цей текст або вводити другий registry авторитету. Архів залишає неперенесений checker як джерело для #383; якщо його функціональність потрібна, власник має ухвалити рішення у вже наявному #383/#5041, після чого зробити current-main port без нової гілки.

Не активовано жодного старого workflow і не змінювалася мовна семантика.
