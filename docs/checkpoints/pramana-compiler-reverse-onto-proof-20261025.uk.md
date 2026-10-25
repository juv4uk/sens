# Pramāṇa · 25.10.2026 · виконувані свідки компіляторного D5/D3 REVERSE-ONTO

## Подяка й точний контекст
Nyāya виправив `компілятор-зворот-до` у `lib/compiler-nucleus.lisp` (коміт `a8c8cfd63712afc38fe9c52f084fcfea34f5b868`). Виправлення забороняє сприймати D1:ні як кінцеве D3:(). У попередньому коміті було два SENS-свідки, однак `scripts/prove-lisp-semantic-t5m.sh` їх не викликав, тому нативна перевірка не була доведена.

## Нова перевірка, без дублювання SENS семантики
Механічний витяг рівно двох DEFINE із чинного `lib/compiler-nucleus.lisp`: `істина-компілятора` та `компілятор-зворот-до`. Якщо DEFINE немає, їх два, або форму не можна однозначно відокремити — runner завершується RED. Окремий SENS закон/мутація/Type перевіряються чинним прямим SENS → Zig/T5M mint/open/verify → SENS paired/standalone runner. Rust/Python не обчислюють результат.

| Свідок | Джерело | Очікування |
| --- | --- | --- |
| compiler-reverse-onto-positive | tests/semantic/compiler-reverse-onto-proper-law.lisp | D1:так |
| compiler-reverse-onto-order-mutant | tests/semantic/compiler-reverse-onto-order-mutant.lisp | D1:ні |
| compiler-reverse-onto-d1-root-type | tests/semantic/compiler-reverse-onto-d1-root-negative.lisp | D3 CAR Type |
| compiler-reverse-onto-improper-tail-type | tests/semantic/compiler-reverse-onto-improper-tail-negative.lisp | D3 CAR Type |

Входи фіксує `compiler-reverse-onto-exact-inputs.sha256`. Загальна бібліотека компілятора не копіюється в тест: витягаються тільки потрібні оригінальні SENS визначення без повторного опису семантики.

## Статус цього коміту
STATIC_SENS_PARENS=PASS; ORIGINAL_DEFINE_UNIQUENESS=PASS; RUNNER_WIRING=PRESENT.
NATIVE_SENS=NOT_VERIFIED; T5M_PAIRED_STANDALONE=NOT_VERIFIED до фактичного CI на цьому SHA.
RELEASE=NO-GO. Незалежний RED: D6 LENGTH-ONTO отримав `cdr expects a non-empty list` замість очікуваного `car expects a non-empty list`; D11 JUXT та D8 quantifier mutant — unknown Text7 binding. Не змінювати очікувану помилку на CDR, щоб штучно «озеленити» тест.

## Наступний Swarm-агент
1. Зчитати точний CI для цього SHA: чотири нові ідентифікатори мають дати нативні D1:1, D1:0, D3 CAR Type, D3 CAR Type. Ніякого PASS на підставі лише SHA або статичних дужок.
2. Якщо виявиться `UnknownSymbol` / `Text7` / `NOT_SUPPORTED`, показати точну першу невиконувану форму, не замінювати її іншою мовою. Обов'язково звірити paired і standalone.
3. Дослідити розходження D6 `довжина-до` між авторитетним SENS Core4 і реальним T5M: доказ лише D3 CAR, не приймати D3 CDR за нього. Відокремити stale фізичну пару від закону й механізму допуску.
4. Далі D10 `список?`, `утворити-список`, `відобразити-й-додати` з Core4 UnknownSymbol; D11 JUXT, D8 mutant та математична драбина D12+.
5. Не призначати нових доменних координат і не оголошувати GO без рішення власника.
