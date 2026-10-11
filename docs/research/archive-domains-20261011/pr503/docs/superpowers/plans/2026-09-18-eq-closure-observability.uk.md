# План bounded-аудиту спостережуваності closure без EQ

> **Для агентних виконавців:** використовуйте `superpowers:subagent-driven-development` або `superpowers:executing-plans`.

**Мета:** перевірити, чи обмежений нижчий Lisp-базис може розрізнити дві окремо створені, поведінково однакові closures, які поточний EQ розрізняє.

**Архітектура:** постійні зміни лише research/docs. NEVER-MERGE child тимчасово створює integration observer, запускає живий evaluator, видаляє observer і перевіряє diff hygiene.

## Обмеження

- Не змінювати production evaluator, EQ, Canon, registry, fixtures, writer, machine або Rust semantics.
- EQ використовується лише як цільовий witness, не всередині lower contexts.
- Host pointer/address/debug observations заборонені.
- Дозволений висновок лише bounded; не глобальна contextual equivalence і не теорема незвідності.

## Корпус контекстів

Для двох fresh `(lambda (x) x)` перевірити без EQ:
- `atom`;
- application до `radio`, `()`, `42`, dotted pair;
- `eval` pass-through + application;
- `write-to-string`;
- `cons` transport + CAR/CDR + writer;
- canonical COND проти статичного lambda datum;
- однаковий ErrorKind для CAR-on-closure.

Цільовий witness окремо: reused closure -> EQ same; two fresh closures -> EQ distinct.

Якщо всі lower contexts збігаються, записати лише `bounded-indistinguishability-witness`, із явною приміткою, що неперевірений контекст ще може їх розрізнити.

Потім research PR має пройти exact-head CI + bilingual gate, а результат передається в #498/#471/#419.
