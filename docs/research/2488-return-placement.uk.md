# #2488 — falsifier placement для RETURN

Статус: лише research.

## Канонічна онтологія

```text
DOMAIN        Core post-D4 placement
BINARY OBJECT координату не допущено
LAW           dynamic exit target/context policy
WITNESS       executable policy square
FALSIFIER     D4 parent tournament
STATUS        hypothesis under executable attack
RELATION      Core-only
```

## Доведений вхід

Historical RETURN уже пережив Phase D як source-level capability:

> передати value до найновішого активного PROG-exit через звичайні межі
> викликів.

Глобально це компілюється в D4 через CPS, але #2468 доводить: така компіляція
переписує call-chain protocol і тому не є локальною D4-деривацією.

## Дві незалежні осі

Ordinary D4 completion:

```text
target  = immediate caller
context = optional
```

Historical RETURN core:

```text
target  = nearest active PROG
context = required; fail if none
```

Executable witness проходить усі чотири комбінації:

```text
                     optional              required
immediate            ordinary              immediate+guard
nearest-PROG         soft dynamic exit     historical RETURN
```

Обидві осі спостережувані незалежно.

Отже ordinary completion -> historical RETURN змінює щонайменше дві незалежні
policy-ознаки.

## Parent tournament

Placement-law вимагає того самого базового semantic operation.

```text
APPLY   callable + values -> invoke callable
EVAL    form -> evaluate form
LAMBDA  parameters/body -> construct closure
COND    predicate/branches -> local branch selection
RETURN  value + active dynamic context -> non-local transfer
```

Жоден D4-кандидат не володіє тим самим base operation.

CPS може представити exit continuation як closure, але representation не робить
LAMBDA семантичним parent. EVAL/APPLY беруть участь у виконанні навколо RETURN,
але участь не є parenthood. COND — локальний branch selector, а не dynamic exit.

## Поточний результат під перевіркою

```text
RETURN-ROOT=RESIDUE
EXACT-DOMAIN=UNRESOLVED
BINARY-COORDINATE=UNALLOCATED
```

Це означає тільки:
- не садити RETURN декоративно під APPLY/EVAL/LAMBDA/COND;
- зберегти capability як незалежно доведений post-D4 root;
- D5/D6 і точну координату відкласти до окремого residue/domain law.

Жодна вільна D5-комірка тут не отримує значення.

## Принцип

**Якщо parent не володіє тим самим operation, implementation adjacency не має
права ставати prefix-law.**
