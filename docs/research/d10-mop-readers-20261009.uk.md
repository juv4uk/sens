# D10 — систематичний перепис читачів CLOS MOP

Дата: 2026-10-09. Координація #4898 / #4896. Статус: RESEARCH ONLY.

Першоджерело: https://clos-mop.hexstreamsoft.com/generic-functions-and-methods/ — The Art of the Metaobject Protocol, Chapter 6 (transcription, page updated 2020-05-28). Це не базова норма ANSI Common Lisp HyperSpec.

Опрацьовано рівно 17 назв зі словника: 10 читачів класів та 7 читачів узагальнених функцій. Чотири мають виразні закони для глибокого REVIEW; 13 лишаються HOLD. Жодну назву не внесено до selected D10.

CLASS-PRECEDENCE-LIST: лінеаризація включає клас, його предків без повторів і кінцевий T, а не лише список прямих батьків.
CLASS-DIRECT-SLOTS: лише локально оголошені визначення слотів; не плутати з успадкованими effective class-slots.
GENERIC-FUNCTION-METHODS: множина конкретних method metaobjects, а не applicable-methods для конкретних аргументів.
GENERIC-FUNCTION-ARGUMENT-PRECEDENCE-ORDER: перестановка потрібних параметрів, яка визначає перевагу під час диспетчеризації.

JSON evidence: knowledge/d10-mop-metaobject-reader-census-20261009.json.
Static provenance and 7 adversarial controls: scripts/check_d10_mop_reader_census.py.
Independent actual SBCL donor (15 assertions): tests/oracles/d10_mop_readers_sbcl.lisp.

Це історичне зовнішнє виконання SB-MOP, не виконання двійкової мови SENS. Подальші незалежні свідки CLISP/інших MOP-реалізацій обов'язкові перед можливим PROPOSE.
Обрані D10 резиденти, 10-бітні координати, D1–D9, D2 та .sens залишаються без змін; ratified D10 = 0.
Після готовності #4894/#4895 усі справді незалежні пропозиції мають потрапити в загальний TSV-леджер до semantic SELECT.
