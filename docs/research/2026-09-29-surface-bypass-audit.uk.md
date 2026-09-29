# Аудит обходу поверхневого виконання — #1774 slice C

**Агент:** Vyasa (Оксі) | **Дата:** 2026-09-29 | **Коміт:** `dbdf7f7f`

---

## Короткий підсумок

Функція `evaluate_step` у `crates/sens/src/eval/mod.rs` містить **обхід поверхневого виконання** на рядках 179-180:

```rust
if let Some(semantic_id) = semantic_registry::semantic_id_for_surface(symbol) {
    return Ok(EvalStep::Value(Value::Sid(semantic_id)));
}
```

Цей шлях дозволяє **будь-якому дозволеному англійському імені поверхні** (напр., `+`, `-`, `car`, `cdr`, `map`, `filter`, `string-length` тощо) виконуватися безпосередньо через пошук імені, обходячи модель лише-бінарного виконання, де ідентичність після lowering має бути бінарним `Sens8`.

---

## Повна класифікація (10 шляхів)

| # | Шлях | Місце | Класифікація | Обґрунтування |
|---|------|-------|--------------|---------------|
| 1 | `canon::value_for_surface` | `evaluate_step:157` | **host/mechanism** | 7 допущених ValueCall SIDів (`00000010`–`00000110`) |
| 2 | `canon::routed_sid_for_surface` | `evaluate_step:160` | **host/mechanism** | Механічний маршрут поверхня→SID для 7 SIDів |
| 3 | `necessary_forms::identity_for_symbol` | `evaluate_step:169` | **canonical-language** | Незмінні синтаксичні форми: QUOTE/LAMBDA/DEFINE |
| 4 | `environment.get` | `evaluate_step:176` | **canonical-language** | Лексичний пошук зв'язаних змінних |
| **5** | **`semantic_id_for_surface`** | **`evaluate_step:179`** | **transition-debt** | **КРИТИЧНЕ: будь-яке допущене ім'я поверхні → виконуваний `Value::Sid`** |
| 6 | `canon::routed_sid_for_surface` | `dispatch_call:243` | **host/mechanism** | Запасний варіант для голів списків без бінарного SID |
| 7 | `necessary_forms::identity_for_symbol` | `dispatch_call:245` | **canonical-language** | Виявлення QUOTE/LAMBDA/DEFINE за іменем |
| 8 | `necessary_forms::identity_for_semantic_id` | `dispatch_call:246` | **canonical-language** | Те саме за бінарним SID |
| 9 | `capabilities::dispatch_capability` | `dispatch_call:265` | **host/mechanism** | Явний межа host capabilities |
| 10 | `ExprKind::Sid(sid)` як голова | `evaluate_list:223` | **canonical-language** | Прямий бінарний SID, пошук імені відсутній |

---

## Обхід (шлях #5)

```rust
// crates/sens/src/eval/mod.rs:179-180
if let Some(semantic_id) = semantic_registry::semantic_id_for_surface(symbol) {
    return Ok(EvalStep::Value(Value::Sid(semantic_id)));
}
```

- `semantic_id_for_surface` = `admitted_semantic_id_for_surface` (псевдонім у `semantic_registry.rs`)
- Повертає SID для **БУДЬ-ЯКОГО** допущеного імені поверхні в згенерованому реєстрі
- Реєстр містить всі англійські імена: `+`, `-`, `car`, `cdr`, `cons`, `map`, `filter`, `string-length` тощо
- Ефект: голе символ `(+ 1 2)` виконується через пошук імені замість вимоги бінарного SID `(00001100 1 2)`

**Це і є обхід поверхневого виконання** — людські імена безпосередньо стають виконуваними SIDами під час виконання.

---

## Класифікація підсумок

| Класифікація | Шляхи | Дія |
|---|---|---|
| **canonical-language** | 3, 4, 7, 8, 10 | Залишити — ядро семантики мови |
| **host/mechanism** | 1, 2, 6, 9 | Залишити — механічний маршрут / явна межа host |
| **transition-debt** | **5** | **Видалити коли lowering завершено** |

---

## План видалення (C1)

**Ціль:** Видалити рядки 179-180 у `evaluate_step`:

```rust
// ВИДАЛИТИ ЦІ РЯДКИ:
if let Some(semantic_id) = semantic_registry::semantic_id_for_surface(symbol) {
    return Ok(EvalStep::Value(Value::Sid(semantic_id)));
}
```

**Попередня умова:** Весь Lisp-код має нести бінарні SIDи (`00001100` замість `+`). Поточний `main` все ще має англійські імена в джерелах.

**Координація:** Заблоковано на завершенні lowering (#1714). Жодного видалення до завершення lowering.

---

## Тест для документування боргу (провалюється сьогодні)

```rust
#[test]
fn surface_bypass_is_transition_debt() {
    // Цей тест ПРОВАЛЮЄТЬСЯ сьогодні бо (+ 1 2) виконується через пошук імені.
    // Коли C1 зроблено — ПРОЙДЕ (очікується UnknownSymbol помилка).
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    
    let result = eval_program("(+ 1 2)", &mut session);
    
    // Сьогодні: проходить (виконується через пошук імені)
    // Після C1: має бути Err(UnknownSymbol) бо '+' не бінарний SID
    assert!(result.is_ok(), "сьогодні проходе через пошук імені — transition debt");
}
```

---

## Координація

- **Блокує видалення C1:** завершеність lowering #1714 (всі джерела → бінарні SIDи)
- **Жодного видалення коду ще** — цей документ фіксує борг і план
- Координувати з #1714 для графіку C1
- Жодного сумісного шару; видалення-first коли готово

---

## Докази

- Файл: `crates/sens/src/eval/mod.rs` рядки 179-180
- Реєстр: `crates/sens/src/semantic_registry.rs` `semantic_id_for_surface` → `admitted_semantic_id_for_surface`
- Джерело реєстру: `lib/surface/semantic-registry.lisp` (генерується `scripts/generate-rust-semantic-registry.lisp`)
- Бінарна SID authority: `lib/core.lisp`, `lib/function-table.lisp`, `SID_ROUTES` у `canon.rs`
