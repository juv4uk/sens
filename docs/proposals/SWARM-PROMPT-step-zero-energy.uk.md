# SWARM-ПРОМПТ · Крок нуль: енергія як вимір

## Завдання

Додати до SENS вимірювання **енергії** поруч із часом. Не новий шар, а другий
екземпляр наявного патерну: у `lib/бенчмарк.lisp` уже зафіксовано
«Годинник (монотонний-мс) — capability; семантика — мова».

## Обсяг: рівно два файли

| файл | дія |
|---|---|
| `crates/*/…/energy_capability.rs` (або наявний модуль capability) | нове: читання powercap sysfs |
| `lib/бенчмарк.lisp` | нове: `енергія-на-форми`, `медіана-енергії`, стан «недоступно» |

**Заборонено:** нові workflow, зміни в `ci.yml`, нові залежності, будь-які
зміни семантики SENS.

## 1. Capability

```
read-energy-uj → (пакет: u64 | недоступно, dram: u64 | недоступно)
```

- `пакет` — з `intel-rapl:0/energy_uj` (або `amd_energy`), **обов'язковий**.
- `dram` — з `intel-rapl:0:1/energy_uj`, **опційний**.
- Стан **«недоступно»** — окреме значення, **не нуль**.

## 2. Три пастки, які capability мусить закрити

### 2.1 Привілей і відсутність

`energy_uj` зазвичай `0400` (root). У контейнерах `/sys/class/powercap`
не монтується. Capability повертає «недоступно» — і бенчмарк це **друкує**.
Мовчазний нуль заборонено: він потрапить у медіану й збреше.

### 2.2 Переповнення

`energy_uj` обертається на `max_energy_range_uj`. Дельта:

```
Δ = (після − до + max) mod max
```

`max_energy_range_uj` читати **з того самого домену**, не з константи.

### 2.3 Домен `dram` не всюди

`intel-rapl:0:1` є не на всіх SKU; на AMD інші імена; на ARM часто нічого.
`dram` = «недоступно» без падіння й без підміни нулем.

## 3. Негативний свідок — ВИПРАВЛЕНО

**Початкова пропозиція «лічильники мусять рости монотонно» — хибна.** RAPL є
**модель**: оцінка оновлюється щомілісекунди й може зменшуватись між
читаннями. А через переповнення (§2.2) монотонність ламається **завжди** на
довгих інтервалах. Такий свідок дасть хибне червоне там, де все правильно.

**Правильний свідок (два твердження):**

1. Сума дельт за N послідовних читань **додатна**.
2. Ця сума **не перевищує** `N · max_energy_range_uj`.

Перше ловить від'ємну арифметику, друге — невраховане переповнення. Обидва
разом перевіряють коректність, не вимагаючи фізично неможливого.

## 4. Розширення `lib/бенчмарк.lisp`

Поруч із наявними `бенч-довжина`, `коротший?`, `вставити-впорядковано`:

- `енергія-на-форми(енергія форми)` → мікроджоулі на 1000 форм;
- `медіана-енергії(список)` — та сама семантика, що медіана часу;
- **пропагація стану «недоступно»** — якщо хоч одне читання недоступне,
  результат «недоступно», а не часткова сума.

## 5. Приймання

- [ ] `read-energy-uj` компілюється й повертає три стани коректно.
- [ ] Негативний свідок (§3) **проходить** на реальних лічильниках.
- [ ] Свідок **падає**, якщо штучно прибрати модульну дельту — тобто він
      справді ловить переповнення.
- [ ] Бенчмарк друкує колонку **Дж/1000 форм** поруч із forms/s.
- [ ] На системі без powercap усе працює й **друкує «недоступно»**.
- [ ] Змінено рівно два файли.

## 6. Чого НЕ робити

- Не підміняти «недоступно» нулем.
- Не вимагати монотонності лічильника.
- Не додавати `dram` як обов'язковий.
- Не чіпати `ci.yml` і не створювати workflow.

## Deutsch

Swarm-Prompt: Energie-Capability mit drei Fallstricken und korrigiertem Zeugen.

## English

Swarm prompt: energy capability with three pitfalls and corrected witness.

## 7. Готовий код — але НЕПЕРЕВІРЕНИЙ

Нижче — реалізація за точним зразком `clock-mono-raw`
(`crates/sens-host/src/lib.rs:86`): Rust лише читає лічильник і віддає
**точне D96-слово**, жодної семантики всередині.

**Статус: НЕ КОМПІЛЬОВАНО Й НЕ ПРОГНАНО.** У середовищі автора немає ні
`cargo`, ні `/sys/class/powercap`. Тому код **не закомічено** в `crates/` —
він тут як заготовка для виконавця з інструментами. Мержити без `cargo test`
не можна.

```rust

/// Сире спостереження RAPL-лічильника, у мікроджоулях, без семантики в Rust.
///
/// За зразком `clock-mono-raw`: механізм лише ЧИТАЄ лічильник і віддає точне
/// D96-слово. Одиниці, різниця, медіана й «Дж/1000 форм» — тільки функції SENS
/// у `lib/бенчмарк.lisp`. Реєстрація за назвою НЕ допускає прямого D10 виклику.
///
/// Відсутність лічильника — це НЕ нуль: нуль тихо потрапив би в медіану.
/// Тому недоступність повертається як явна мовна відмова.
fn observe_energy_microjoules(
    domain: &'static str,
    arguments: &[(Value, Span)],
    _environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if !arguments.is_empty() {
        return Err(LanguageError::new(
            ErrorKind::Arity,
            format!("{domain} expects exactly zero arguments"),
            span,
        ));
    }
    // Порядок кандидатів: спершу Intel powercap, далі amd_energy.
    let candidates: [&str; 2] = match domain {
        "energy-package-raw" => [
            "/sys/class/powercap/intel-rapl:0/energy_uj",
            "/sys/class/powercap/amd_energy/energy_uj",
        ],
        _ => [
            "/sys/class/powercap/intel-rapl:0:1/energy_uj",
            "/sys/class/powercap/amd_energy/dram_uj",
        ],
    };
    let mut microjoules: Option<u64> = None;
    for path in candidates {
        if let Ok(text) = std::fs::read_to_string(path) {
            if let Ok(value) = text.trim().parse::<u64>() {
                microjoules = Some(value);
                break;
            }
        }
    }
    let Some(microjoules) = microjoules else {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            format!(
                "{domain}: powercap sysfs counter is not readable (root-only, or absent in this container) · {domain}: lichylnyk powercap nedostupnyi · {domain}: powercap-Zähler nicht lesbar"
            ),
            span,
        ));
    };
    const WIDTH: usize = 96;
    let wide = microjoules as u128;
    if wide >= (1u128 << WIDTH) {
        return Err(LanguageError::new(
            ErrorKind::NumericOverflow,
            format!("{domain} observed microjoules exceed D96"),
            span,
        ));
    }
    let bits: Vec<u8> = (0..WIDTH)
        .rev()
        .map(|shift| ((wide >> shift) & 1) as u8)
        .collect();
    let exact = sens::BinaryNumber::from_numeric_domain_bits(WIDTH, &bits)
        .expect("the checked 96-bit energy observation is an exact D96 word");
    Ok(Value::BinaryNumber(exact))
}

/// Той самий патерн, але з фіксованим доменом — бо замикання в реєстрі
/// приймає лише fn-покажчик, а не параметризовану функцію.
fn observe_energy_package_microjoules(
    arguments: &[(Value, Span)],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    observe_energy_microjoules("energy-package-raw", arguments, environment, span)
}

fn observe_energy_dram_microjoules(
    arguments: &[(Value, Span)],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    observe_energy_microjoules("energy-dram-raw", arguments, environment, span)
}

```

Реєстрація — поруч із `clock-mono-raw` у `crates/sens-host/src/lib.rs:791`:

```rust
register_evaluated_capability("energy-package-raw", 0, observe_energy_package_microjoules);
register_evaluated_capability("energy-dram-raw", 0, observe_energy_dram_microjoules);
```

**Що перевірити першим, коли буде `cargo`:**
1. чи збігається сигнатура з `register_evaluated_capability` (у `clock-mono-raw`
   вона `fn(&[(Value, Span)], &Environment, Span) -> Result<Value, LanguageError>`);
2. чи `ErrorKind::InvalidForm` — правильний різновид для «недоступно»;
3. чи шлях `amd_energy/dram_uj` справді такий на AMD (я цього не перевірив).
