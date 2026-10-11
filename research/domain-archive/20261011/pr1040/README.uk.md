# Архів PR #1040 — інвентар GitHub Actions workflow

**Статус: ARCHIVE-ONLY / СТАРИЙ SNAPSHOT.**

Оригінальні чотири файли збережено побайтно з `agent/384-workflow-inventory`, head SHA `cda9060c53a24aed58662068211e457db859259a`. PR фіксував 26 workflow і додавав Lisp-owned registry/checker, але перелік workflow та CI integration відноситься до старішого стану main. Чинний main уже має інші workflow й governance inventories; merge старого 26-workflow snapshot як поточного inventory створив би хибне покриття й міг би пошкодити CI authority.

Архів залишає джерело для перевірки різниць та історичних ролей. Перед активацією потрібно повторно зняти весь актуальний `.github/workflows/`, зберегти однозначні lifecycle/owner/cancellation твердження, перевірити негативні кейси unknown/stale/duplicate і прогнати чинний CI. Не видаляти й не замінювати workflow за старим інвентарем. Нової гілки не створено.
