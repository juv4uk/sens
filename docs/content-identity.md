# Content identity · Ідентичність вмісту · Inhaltsidentität

> **Scope note (2026-10-03):** “content identity” тут означає ідентичність **data/content-address protocol** для knowledge/world values. Це не глобальна semantic identity SENS. Поточна загальна онтологія: `binary object + exact semantic domain + admitted law` — див. [`CURRENT.md`](../CURRENT.md).

## Українська

SENS визначає цю **content-address identity** раніше, ніж обирає digest-алгоритм. `knowledge-content-address` повертає канонічне, придатне для зворотного `read` представлення `write-to-string` за незалежними від реалізації правилами з [`canonical-serialization.md`](canonical-serialization.md). Тому рівні структури мають точно однакову адресу в Rust, WASM і майбутній FPGA-реалізації; різні структури мають різний канонічний текст.

`world-content-address` адресує `(world-history journal metadata)`. Журнал уже містить повну впорядковану історію, тому рекурсивне вкладання кожного `parent` лише дублювало б її. Світи з однаковими поточними clauses, але різними tell/retract-історіями навмисно мають різні адреси. Незалежно реконструйовані світи з однаковими журналом і metadata мають одну адресу.

`lib/content-store.lisp` перетворює цю ідентичність на незмінне сховище поверх персистентної AVL-мапи. Повторне додавання рівного вмісту не змінює розмір сховища. World зберігається як address content, а не як живий parent-граф, тому отримане значення лишається data-only і придатним до зворотного читання.

Адреса — точний ключ змінної довжини, не криптографічний hash. Майбутній SHA-256 або апаратний digest може обчислювати `hash(canonical-address)` для компактного транспорту й підписів, але не повинен перевизначати цю content identity; тим більше він не визначає глобальну semantic identity SENS і не входить до evaluator kernel.

## English

SENS defines this **content-address identity** before choosing a digest algorithm. `knowledge-content-address` returns the canonical, read-back-safe `write-to-string` representation of any knowledge value, under the implementation-independent rules in [`canonical-serialization.md`](canonical-serialization.md). Equal structures therefore have exactly the same address across conforming Rust, WASM, and future FPGA implementations; different structures have different canonical text.

`world-content-address` addresses `(world-history journal metadata)`. The journal already contains the complete ordered history, so recursively embedding every `parent` would duplicate the same history many times. Two worlds with equal current clauses but different tell/retract histories intentionally have different addresses. Independently reconstructed worlds with the same journal and metadata have the same address.

`lib/content-store.lisp` turns that identity into an immutable store backed by the persistent AVL map. Putting equal content twice leaves the store size unchanged. A World is stored as its address content rather than its live parent graph, so retrieval remains data-only and read-back-safe.

The address is an exact variable-length key, not a cryptographic hash. A future SHA-256 or hardware digest layer may compute `hash(canonical-address)` for compact transport and signatures, but it must not redefine this content identity, and it cannot define global SENS semantic identity or become part of the evaluator kernel.

## Deutsch

SENS definiert diese **Content-Address-Identität**, bevor ein Digest-Algorithmus gewählt wird. `knowledge-content-address` liefert die kanonische, wieder einlesbare `write-to-string`-Darstellung nach den implementierungsunabhängigen Regeln in [`canonical-serialization.md`](canonical-serialization.md). Gleiche Strukturen haben daher in Rust, WASM und einer zukünftigen FPGA-Implementierung exakt dieselbe Adresse; verschiedene Strukturen verschiedenen kanonischen Text.

`world-content-address` adressiert `(world-history journal metadata)`. Das Journal enthält bereits die vollständige geordnete Geschichte; jeden `parent` rekursiv einzubetten würde sie nur vervielfachen. Welten mit gleichen aktuellen Clauses, aber unterschiedlichen Tell-/Retract-Geschichten haben bewusst verschiedene Adressen. Unabhängig rekonstruierte Welten mit gleichem Journal und gleichen Metadaten haben dieselbe Adresse.

`lib/content-store.lisp` macht aus dieser Identität einen unveränderlichen Store auf der persistenten AVL-Map. Gleiches Material zweimal einzufügen ändert die Store-Größe nicht. Eine World wird als ihr Adressinhalt statt als lebender Eltern-Graph gespeichert; das abgerufene Format bleibt damit datenrein und wieder einlesbar.

Die Adresse ist ein exakter Schlüssel variabler Länge, kein kryptographischer Hash. Eine spätere SHA-256- oder Hardware-Digest-Schicht darf `hash(canonical-address)` für kompakten Transport und Signaturen berechnen, aber weder diese Content-Identität noch die globale SENS-Semantik definieren und auch nicht Teil des Evaluator-Kerns werden.
