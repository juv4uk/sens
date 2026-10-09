# План bootstrap для скомпільованого Lisp-owned encoder

> **Для агентних виконавців:** використовуйте `superpowers:subagent-driven-development` або `superpowers:executing-plans`.

**Мета:** прибрати залежність генерації x86-64 байтів від evaluator-а, скомпілювавши Lisp-owned encoder і зберігши byte-for-byte parity та семантичну владу Lisp.

**Архітектура:** `lib/machine/encoding/x86-64.lisp` залишається джерелом істини. Спочатку реальний файл запускається через ширший чинний шлях CML `cml x86-elf`, щоб знайти перший фактичний blocker. Окремий `cml-compile x86-elf` навмисно обмежений arithmetic slice і не є шляхом bootstrap encoder-а. CML може додавати механізм компіляції, але не копіювати таблиці opcode/encoding. Фінальний доказ: interpreted encoder дає bytes A, compiled encoder дає bytes B, A == B, обидва фізично виконуються через той самий admitted host mechanism.

**Специфікація:** issue #507 та `docs/superpowers/specs/2026-09-18-native-first-execution-design.uk.md`.

## Обмеження

- Lisp encoder — єдине нормативне джерело encoding.
- CML володіє лише compilation/lowering mechanism.
- Жодної дубльованої нормативної opcode/encoding таблиці в CML.
- Жодного Rust semantic matcher або Rust encoder replacement.
- Cross-repo witnesses завжди pin exact my-lisp + CML commits.
- Unsupported CML construct -> fail closed, не прихований fallback.
- #509 parity і #508 coverage ledger лишаються окремими lane.

## Завдання 1 — whole-file RED

У verification-only child:
- checkout my-lisp;
- checkout CML `d12db3370180c4d155e21a61ab788d63e02010e9`;
- запустити:
  `cd <pinned-cml> && cargo run --bin cml -- x86-elf <absolute-my-lisp>/lib/machine/encoding/x86-64.lisp /tmp/my-lisp-encoder`;
- вимагати non-zero exit;
- записати першу точну compiler diagnostic;
- класифікувати blocker: admission / IR / machine selection / callable ABI / result representation;
- створити CML issue саме під цей blocker.

## Завдання 2 — мінімальна CML capability

Для кожного blocker:
- RED на найменшому encoder-derived slice;
- мінімальний compiler fix;
- жодного копіювання encoder truth у CML;
- whole-file rerun для знаходження наступного blocker.

## Завдання 3 — callable compiled-encoder witness

Сам факт створення standalone ELF недостатній.

Перший compiled encoder operation має бути callable:
- interpreted encoder -> bytes A;
- compiled encoder -> bytes B;
- A == B;
- A і B незалежно проходять closed admission/native execution;
- physical result однаковий.

Почати з `x86-encode-ret` або `x86-encode-mov-r64-imm64`.

## Завдання 4 — native-first integration

Compiled encoder output може споживатися native-first execution без зміни classifier semantics. Interpreted encoder лишається reference/fallback до повного coverage. Тести мають явно показувати `encoder-route compiled|interpreted`; compiled failure не можна маскувати interpreted fallback у доказі compiled success.

## Завдання 5 — gates

Exact-head CML CI, exact-head my-lisp CI+bilingual, byte parity, physical CPU parity, точний звіт у #507/#504.
