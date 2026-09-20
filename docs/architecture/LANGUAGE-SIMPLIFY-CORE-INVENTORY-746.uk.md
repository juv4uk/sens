# Архітектурна інвентаризація: Мале чесне ядро та архіпелаг ядер (#746)

**Статус:** Прийнято в межах #746
**Дата:** 2026-09-19
**Батьківські задачі:** #695, #730, ADR-005
**Пов'язані задачі:** #223, #225, #685, #701, #712, #713, #714, #715, #725

---

## 1. Концепція

Після розділення системи на архіпелаг автономних ядер (`Common Lisp`, `Prolog`, `Datalog`, `CLIPS`) мова `my-lisp` зазнає фундаментального якісного спрощення:

```text
my-lisp = мала чесна семантична та координаційна мова
ядра    = автономні острови нативного виконання та міркувань
```

`my-lisp` більше не намагається бути монолітним супер-рушієм, який одночасно містить у собі:
- алгоритм пошуку з поверненням (SLD resolution) Прологу;
- дедуктивне замикання та обчислення нерухомої точки (fixpoint) Даталогу;
- продукційну систему RETE, порядок денний (agenda) та пам'ять фактів CLIPS;
- повну глибину середовища та компілятора Common Lisp.

Замість цього `my-lisp` фокусується на своєму справжньому покликанні:
1. **канон() (`()`)** як основа відсутності / океан мови;
2. **Неперервний 8-бітний реєстр семантичних ідентифікаторів (SID)** (`00000001..10101000`);
3. **Класична ліспова структура даних** (`cons`, `car`, `cdr`, `atom`, `eq`);
4. **Чесне локальне обчислення** виразів і функцій першого класу (`lambda`);
5. **Механічна диспетчеризація та координація** запитів до автономних островів через непрозорі байти (C-ABI / KernelHost / KernelRouter);
6. **Збереження нативних результатів островів** поруч без фальшивої редукції в єдину вигадану онтологію.

---

## 2. Інвентаризація можливостей

Категорії інвентаризації:
- **`KEEP`**: Залишається в канонічному ядрі `my-lisp` як пряма семантична відповідальність.
- **`DERIVE`**: Виводиться мовою Lisp поверх базових примітивів без розширення ядра.
- **`ROUTE-TO-KERNEL`**: Делегується відповідному автономному острову; видаляється дублювання з ядра.
- **`EXPERIMENTAL`**: Дослідницькі конструкції (багатовалентні проєкції, узгодження свідчень).

| Компонент / Операція | Категорія | Опис | Цільове ядро / Місце |
| :--- | :--- | :--- | :--- |
| **канон() `()`** | `KEEP` | Точка відліку, порожнеча/відсутність, нейтральний термінатор списків | `my-lisp` канон |
| **8-bit SID Registry** | `KEEP` | 168 неперервних 8-бітних байтових ідентифікаторів (`00000001..10101000`) | `semantic_registry.rs` |
| **McCarthy-7 примітиви** | `KEEP` | `quote`, `atom`, `eq`, `car`, `cdr`, `cons`, `cond` | `my-lisp` core |
| **Функції та замикання** | `KEEP` | `lambda`, лексичне середовище, зв'язування аргументів | `environment.rs`, `closures.rs` |
| **Точна арифметика** | `KEEP` | Раціональні числа точної арифметики, цілі довільної розрядності | `bignum.rs`, `arithmetic.rs` |
| **Символи та рядки** | `KEEP` | Незмінні символи, UTF-8 рядки, базовий парсер та принтер | `parser.rs`, `presentation.rs` |
| **Механічні Host Capabilities** | `KEEP` | Виклики ОС через окремий хост (`load`, `read-file`, `kernel-exchange`) | `my-lisp-host`, `wsm-kernel-host` |
| **Допоміжні спискові форми** | `DERIVE` | `cadr`, `caddr`, `list`, `append`, `reverse`, `length` | `lib/core.lisp` |
| **Логічні комбінатори** | `DERIVE` | `not`, `and`, `or` поверх явного розгалуження `cond` | `lib/core.lisp` |
| **Функціональні ітератори** | `DERIVE` | `map`, `filter`, `fold-left`, `fold-right` поверх `lambda` | `lib/core.lisp` |
| **Синтаксичний цукор** | `DERIVE` | `let`, `let*`, `begin`/`progn` через підстановку `lambda` | `lib/macro.lisp` |
| **Уніфікація та SLD-пошук** | `ROUTE-TO-KERNEL` | Пошук з поверненням, змінні з підстановками, 0..N відповідей | **Prolog Island** (`wsm-prolog-kernel`) |
| **Реляційне замикання** | `ROUTE-TO-KERNEL` | Фікспоінт дедуктивних правил, стратифіковане заперечення | **Datalog Island** (`wsm-datalog-kernel`) |
| **Продукційні правила RETE** | `ROUTE-TO-KERNEL` | Робоча пам'ять фактів, активація правил, виконання agenda | **CLIPS Island** (`wsm-clips-kernel`) |
| **ANSI CL середовище** | `ROUTE-TO-KERNEL` | Макроси CL, CLOS, спеціальні змінні, оптимізоване виконання | **Common Lisp Island** (`wsm-common-lisp-kernel`) |
| **Пірамідальна логіка** | `EXPERIMENTAL` | Стара пірамідальна модель переведена з ролі обов'язкового фундаменту в опціональну проєкцію | Demoted from foundational gate to optional projection over island evidence (#748) |
| **Багатовалентні логіки (FDE/4)** | `EXPERIMENTAL` | Belnap-Dunn 4-значна бігратка для розмічених свідчень кількох островів | Bilattice/FOUR projection over contradictory evidence (#219) |
| **Міжострівний консенсус** | `EXPERIMENTAL` | Протоколи кворуму та узгодження результатів кількох ядер | Multi-island quorum and consensus protocols (#702, #703, #705) |

---

## 3. Спрощення дублювання коду

1. **`lib/unify.lisp` та `lib/forward.lisp`:**
   * Історичні монолітні Lisp-прототипи Prolog та CLIPS перестають вважатися канонічним авторитетом виконання.
   * Вони залишаються лише як історичні/навчальні артефакти або легкі спостерігачі (`observer`).
   * Справжнім виконавчим авторитетом для правил і уніфікації стають нативні острови `wsm-prolog-kernel` та `wsm-clips-kernel`.
2. **`lib/reason.lisp` (Пірамідальна логіка):**
   * Вимога, щоб будь-який висновок чи предикат проходив через багаторівневу пірамідальну структуру, скасовується.
   * Математика залишається строгою математикою (#225).
   * Логічні висновки отримуються через прямі запити до Prolog або Datalog.

---

## 4. Демонстрація виконання: мовна координація (#746.5)

Критерій прийняття 5 вимагає:
> «Demonstrate one program that mixes local Lisp evaluation with at least two island calls.»

Це реалізовано у виконуваному свідку:
[`crates/wsm-kernel-host/tests/language_simplify_island_orchestration.rs`](file:///home/agents/GitHub/my-lisp/crates/wsm-kernel-host/tests/language_simplify_island_orchestration.rs)

Програма мовою `my-lisp`:
```lisp
(define pair (lambda (a b) (cons a b)))

(define orchestrate-inquiry
  (lambda (entity)
    ((lambda (req)
       ((lambda (datalog-facts)
          ((lambda (prolog-proof)
             (pair (pair "request" req)
                   (pair (pair "datalog-evidence" datalog-facts)
                         (pair (pair "prolog-evidence" prolog-proof)
                               ()))))
           (island-exchange "prolog" entity)))
        (island-exchange "datalog" entity)))
     (pair "query-target" entity))))

(orchestrate-inquiry "person(alice)")
```

### Що доводить цей свідок:
1. **Локальні обчислення Lisp:** Створення пар (`pair`/`cons`), зв'язування змінних через чистий `lambda`, робота зі структурами даних без залучення ядер.
2. **Два виклики островів:** Запит до **Datalog** (дедуктивне відношення) та до **Prolog** (уніфікація/підстановки) через механічний кордон `island-exchange`.
3. **Чесна композиція:** Обидва нативні результати залишаються непрозорими рядками/байтами й об'єднуються у звичайний Lisp-список без схлопування в єдину штучну онтологію.
4. **Чистота авторитету:** Жоден біт семантичного авторитету не перемістився в Rust або ядро. Rust керує лише життєвим циклом (`KernelHost`/`KernelRouter`) і байтовим транспортом.

---

## 5. Докази валідації

- `cargo test -p wsm-kernel-host` — 4/4 PASS (включаючи `language_simplify_island_orchestration`).
- `cargo test -p my-lisp --test authority_guard_contract` — 3/3 PASS.
- `cargo test -p xtask --test license_policy` — 3/3 PASS.
- `tests/authority-inventory.tsv` та `tests/authority-inventory.lisp` — зареєстровано як `observer`.
