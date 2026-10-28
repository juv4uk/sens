//! Арена комірок і триколірний колектор сміття (Дейкстра/Стіл) над чинним
//! `Rc`-`Value`.
//!
//! Це ОКРЕМИЙ модуль. Він не замінює `Value::Pair(Rc<PairNode>)` і не чіпає
//! наявне подання `Value`: арена стоїть **поверх** нього. Комірка арени `Cell`
//! має ту саму форму, що й `PairNode` (голова/хвіст), але її ребра — це
//! дескриптори-`u32` (`Edge::Cell`) або листові значення `Value`
//! (`Edge::Atom`), а не `Rc`-володіння. Саме ця непрямість (дескриптор
//! замість `Rc`) і уможливлює вигрібання недосяжних комірок: `Rc` не дає
//! звільнити комірку, поки на неї хтось указує, а дескриптор — дає. Тому
//! `Value::Pair` лишається незмінним, а збирання живе в цьому модулі.
//!
//! Алгоритм — **точний перенос доведеного закону збирача з `lib/core1.lisp`**
//! (триколірне інкрементальне маркування Дейкстри/Стіла). Жодного нового
//! алгоритму тут не вигадано; перенесено саме ці функції:
//!
//! * `ядро1-триколірний-крок`            → [`Arena::tricolor_step`]
//! * `ядро1-триколірний-до-кінця`        → [`Arena::tricolor_to_end`]
//! * `ядро1-затемнення-при-записі`       → [`Arena::darken_on_write`]
//! * `ядро1-позначити-все`               → [`Arena::mark_from_roots`]
//! * `ядро1-зібрати-досяжне`             → [`Arena::reachable`]
//! * `ядро1-зібрати-непозначене`         → [`Arena::garbage`]
//! * `ядро1-вільні-комірки`              → [`Arena::all_cells`]
//! * `ядро1-розділити-за-позначками`     → [`Arena::partition`]
//! * `ядро1-повернути-память`            → [`Arena::collect`]
//! * `ядро1-знайти-комірку-для-памяті`   → [`Arena::cell`]
//!
//! Модель комірки в `core1` — `(ім'я ліве праве)`, де `()` означає відсутнє
//! ребро. Тут `ім'я` — це сам дескриптор комірки, `ліве`/`праве` — це
//! [`Cell::head`] / [`Cell::tail`], а `()` — [`Edge::None`]. Вузол, чиє ребро
//! веде на атом (а не на комірку), **не чорніє** — це не об'єкт (див.
//! [`Edge::Atom`]).
//!
//! Стан триколірного рушія явний, як і в моделі: **сірі** — робочий список
//! [`Arena::tricolor_step`], **чорні** — вектор `bool` (позначені = досяжні),
//! **білі** — обчислюються різницею (не зберігаються), тож непозначене
//! тотожне сміттю.
#![allow(dead_code)] // Арена ще не під'єднана до виконавця: це окремий,
                     // перевірений тестами етап. Дозвіл знімемо, коли колектор
                     // стане чинним у `eval`.

use crate::{PairNode, Value};
use std::rc::Rc;

/// Дескриптор комірки в арені. Це `ім'я` комірки з моделі `core1`.
pub(crate) type CellRef = u32;

/// Зворотна карта «адреса `Rc<PairNode>` → (слабкий власник, дескриптор
/// комірки)» — міст від чинного `Value` до комірки арени.
///
/// Значення — саме [`std::rc::Weak`], а не голий `CellRef`: слабкий власник
/// тримає алокацію `Rc<PairNode>` живучою, тож її адреса не перевикористовується,
/// доки запис існує. Це закриває дефект, коли звільнена адреса `Rc` збігалася з
/// новою парою і `cons` зшивав ребро на чужу комірку.
pub(crate) type ArenaHandles = std::collections::HashMap<usize, (std::rc::Weak<PairNode>, CellRef)>;

/// Відсутнє ребро (`()` у моделі `core1`). Ніколи не індексує живу комірку;
/// [`Arena::cell`] на ньому завжди дає `None`.
pub(crate) const NO_CELL: CellRef = CellRef::MAX;

/// Ребро комірки: або дескриптор нащадка-комірки, або листове значення.
///
/// `Atom` — це «вузол без комірки» з закону `core1`: він **не чорніє**, бо не
/// є об'єктом, тож обхід крізь нього не йде (порівняй коментар у `core1`:
/// «Вузол без комірки не чорніє (це не об'єкт)»).
#[derive(Clone, Debug, PartialEq)]
pub(crate) enum Edge {
    /// Ребра немає — `()`.
    None,
    /// Ребро веде до комірки арени з дескриптором `CellRef`.
    Cell(CellRef),
    /// Ребро веде до значення, яке не є коміркою (атом). Не пропагує обхід.
    Atom(Value),
}

impl Edge {
    /// Дескриптор нащадка, якщо ребро веде до комірки.
    pub(crate) fn as_cell(&self) -> Option<CellRef> {
        match self {
            Edge::Cell(cell) => Some(*cell),
            Edge::None | Edge::Atom(_) => None,
        }
    }

    /// Чи це відсутнє ребро (`()`).
    pub(crate) fn is_empty(&self) -> bool {
        matches!(self, Edge::None)
    }
}

/// Комірка арени — форма `PairNode` (голова/хвіст), але ребра — [`Edge`].
///
/// Це єдина відмінність від `PairNode`: ребра адресуються дескрипторами, а не
/// володіють нащадками через `Rc`. Поле `allocated` — це стан комірки в арені
/// (виділена / вже вигрібена), якого в `PairNode` немає.
#[derive(Clone, Debug)]
pub(crate) struct Cell {
    /// Голова (ліве ребро) — відповідник `PairNode::head`.
    pub(crate) head: Edge,
    /// Хвіст (праве ребро) — відповідник `PairNode::tail`.
    pub(crate) tail: Edge,
    /// `true`, доки комірку не вигріб колектор.
    pub(crate) allocated: bool,
}

impl Cell {
    fn empty() -> Self {
        Cell {
            head: Edge::None,
            tail: Edge::None,
            allocated: true,
        }
    }

    fn freed() -> Self {
        Cell {
            head: Edge::None,
            tail: Edge::None,
            allocated: false,
        }
    }
}

/// Арена комірок: `Vec<Cell>` + дескриптори-`u32` та список вільних слотів.
///
/// Арена тримає комірки за індексом-дескриптором; ребра між комірками — це
/// дескриптори, а не `Rc`. Це дає змогу відрізняти **досяжні** комірки від
/// **недосяжних** і фізично звільняти останні, чого `Rc`-граф не дозволяє.
#[derive(Clone, Debug, Default)]
pub(crate) struct Arena {
    cells: Vec<Cell>,
    free: Vec<CellRef>,
}

impl Arena {
    /// Порожня арена.
    pub(crate) fn new() -> Self {
        Arena {
            cells: Vec::new(),
            free: Vec::new(),
        }
    }

    /// Виділити порожню комірку: обидва ребра `()`. Повторно використовує
    /// раніше вигрібені слоти (LIFO), як і належить арені.
    pub(crate) fn alloc(&mut self) -> CellRef {
        if let Some(recycled) = self.free.pop() {
            self.cells[recycled as usize] = Cell::empty();
            recycled
        } else {
            let fresh = self.cells.len() as CellRef;
            self.cells.push(Cell::empty());
            fresh
        }
    }

    /// Виділити комірку з готовими ребрами.
    pub(crate) fn alloc_with(&mut self, head: Edge, tail: Edge) -> CellRef {
        let cell = self.alloc();
        self.write(cell, head, tail);
        cell
    }

    /// Кількість слотів арени (разом із вигрібеними).
    pub(crate) fn len(&self) -> usize {
        self.cells.len()
    }

    /// Чи арена порожня.
    pub(crate) fn is_empty(&self) -> bool {
        self.cells.is_empty()
    }

    /// Жива комірка за дескриптором — відповідник `ядро1-знайти-комірку-для-памяті`.
    ///
    /// `None`, якщо дескриптор поза ареною, дорівнює [`NO_CELL`] або комірку
    /// вже вигрібено. Це і є «вузол без комірки».
    pub(crate) fn cell(&self, cell: CellRef) -> Option<&Cell> {
        self.cells.get(cell as usize).filter(|slot| slot.allocated)
    }

    /// Читати голову (ліве ребро) комірки.
    pub(crate) fn head(&self, cell: CellRef) -> Option<&Edge> {
        self.cell(cell).map(|slot| &slot.head)
    }

    /// Читати хвіст (праве ребро) комірки.
    pub(crate) fn tail(&self, cell: CellRef) -> Option<&Edge> {
        self.cell(cell).map(|slot| &slot.tail)
    }

    /// Записати обидва ребра. `false`, якщо комірки немає (не виділена/вигрібена).
    ///
    /// Це «сирий» запис без бар'єра; для інкрементального маркування вживай
    /// [`Arena::darken_on_write`] разом із ним (див. `ядро1-затемнення-при-записі`).
    pub(crate) fn write(&mut self, cell: CellRef, head: Edge, tail: Edge) -> bool {
        match self.cells.get_mut(cell as usize) {
            Some(slot) if slot.allocated => {
                slot.head = head;
                slot.tail = tail;
                true
            }
            _ => false,
        }
    }

    // ── Триколірне інкрементальне маркування (Дейкстра/Стіл) ────────────────

    /// `ядро1-триколірний-крок`: обробити рівно один сірий вузол.
    ///
    /// Стан — явна пара (сірі, чорні). Крок знімає голову сірих; якщо вузол
    /// уже чорний або не має комірки — лише відкидає його; інакше сірить обох
    /// нащадків **перш ніж** почорнити сам вузол (інваріант Дейкстри «чорний
    /// не вказує на білого»). Повертає `false` лише коли сірих більше немає.
    pub(crate) fn tricolor_step(&self, grey: &mut Vec<CellRef>, black: &mut [bool]) -> bool {
        let Some(link) = grey.pop() else {
            return false; // `(порожній? сірі)`
        };
        // `ядро1-триколірний-за-посиланням`: уже чорний — не скануємо вдруге.
        if self.is_black(link, black) {
            return true;
        }
        // `ядро1-знайти-комірку-для-памяті`: вузол без комірки не чорніє.
        let Some(slot) = self.cell(link) else {
            return true;
        };
        // `ядро1-триколірний-за-записом`: сіримо обидва нащадки, тоді чорнимо.
        if let Edge::Cell(child) = slot.head {
            grey.push(child);
        }
        if let Edge::Cell(child) = slot.tail {
            grey.push(child);
        }
        if let Some(slot) = black.get_mut(link as usize) {
            *slot = true;
        }
        true
    }

    /// `ядро1-триколірний-до-кінця`: вичерпати робочий список сірих до
    /// нерухомої точки. Повертає чорний набір (позначені = досяжні).
    pub(crate) fn tricolor_to_end(&self, grey: Vec<CellRef>, mut black: Vec<bool>) -> Vec<bool> {
        let mut grey = grey;
        while self.tricolor_step(&mut grey, &mut black) {}
        black
    }

    /// Свіжий білий (непозначений) набір під поточний розмір арени.
    pub(crate) fn white_set(&self) -> Vec<bool> {
        vec![false; self.cells.len()]
    }

    /// `ядро1-позначити-все`: корені сіються як початкові сірі, чорних немає.
    /// Повертає чорний набір.
    pub(crate) fn mark_from_roots(&self, roots: &[CellRef]) -> Vec<bool> {
        let black = self.white_set();
        self.tricolor_to_end(roots.to_vec(), black)
    }

    /// `ядро1-затемнення-при-записі` (insertion barrier Дейкстри).
    ///
    /// Якщо **чорний** власник дістає нове ребро на **білий** вузол, нащадка
    /// негайно заносять до сірих; інакше інкрементальне маркування втратило б
    /// досяжний об'єкт. Повертає `true`, якщо затемнено.
    ///
    /// `Edge::Atom`/`Edge::None` не мають дескриптора, тож затемнити їх нема
    /// куди; крок однаково відкинув би їх як «вузол без комірки», тож
    /// підсумковий чорний набір збігається із законом `core1`.
    pub(crate) fn darken_on_write(
        &self,
        owner: CellRef,
        child: Edge,
        grey: &mut Vec<CellRef>,
        black: &[bool],
    ) -> bool {
        let Edge::Cell(child) = child else {
            return false; // `(порожній? нащадок)` — ребра немає
        };
        if self.is_black(child, black) {
            return false; // нащадок уже чорний
        }
        if grey.contains(&child) {
            return false; // нащадок уже сірий
        }
        if !self.is_black(owner, black) {
            return false; // бар'єр потрібен лише для чорного власника
        }
        grey.push(child);
        true
    }

    // ── Дві вибірки за одним набором позначок ───────────────────────────────

    /// `ядро1-зібрати-досяжне`: позначені (досяжні) комірки у вихідному порядку.
    pub(crate) fn reachable(&self, roots: &[CellRef]) -> Vec<CellRef> {
        let black = self.mark_from_roots(roots);
        self.cells
            .iter()
            .enumerate()
            .filter(|(index, slot)| slot.allocated && self.is_black(*index as CellRef, &black))
            .map(|(index, _)| index as CellRef)
            .collect()
    }

    /// `ядро1-зібрати-непозначене`: комірки, недосяжні з коренів (сміття).
    pub(crate) fn garbage(&self, roots: &[CellRef]) -> Vec<CellRef> {
        let black = self.mark_from_roots(roots);
        self.unmarked(&black)
    }

    /// `ядро1-вільні-комірки`: усі комірки, бо жодної не позначено.
    pub(crate) fn all_cells(&self) -> Vec<CellRef> {
        self.garbage(&[])
    }

    /// `ядро1-розділити-за-позначками`: `(досяжне, недосяжне)` за одним
    /// набором міток. Кожна комірка належить рівно одній частині.
    pub(crate) fn partition(&self, roots: &[CellRef]) -> (Vec<CellRef>, Vec<CellRef>) {
        let black = self.mark_from_roots(roots);
        let mut live = Vec::new();
        let mut dead = Vec::new();
        for (index, slot) in self.cells.iter().enumerate() {
            if !slot.allocated {
                continue;
            }
            if self.is_black(index as CellRef, &black) {
                live.push(index as CellRef);
            } else {
                dead.push(index as CellRef);
            }
        }
        (live, dead)
    }

    /// `ядро1-повернути-память` + фізичне вигрібання: позначити з коренів і
    /// звільнити недосяжні комірки. Повертає дескриптори вигрібених комірок
    /// (вони стають [`Arena::cell`] `None` і годяться під повторне виділення).
    pub(crate) fn collect(&mut self, roots: &[CellRef]) -> Vec<CellRef> {
        let black = self.mark_from_roots(roots);
        let dead = self.unmarked(&black);
        for &cell in &dead {
            if let Some(slot) = self.cells.get_mut(cell as usize) {
                *slot = Cell::freed();
            }
            self.free.push(cell);
        }
        dead
    }

    fn unmarked(&self, black: &[bool]) -> Vec<CellRef> {
        self.cells
            .iter()
            .enumerate()
            .filter(|(index, slot)| slot.allocated && !self.is_black(*index as CellRef, black))
            .map(|(index, _)| index as CellRef)
            .collect()
    }

    fn is_black(&self, cell: CellRef, black: &[bool]) -> bool {
        black.get(cell as usize).copied().unwrap_or(false)
    }

    // ── Міст до чинного `Rc`-`Value` (без змін у самому `Value`) ────────────

    /// Перенести чинний `Rc`-`Value` у комірки арени, **читаючи** `PairNode`
    /// без жодних змін у поданні `Value`.
    ///
    /// Пари стають комірками (`Edge::Cell`), атоми — листовими ребрами
    /// (`Edge::Atom`), бо «вузол без комірки не чорніє (це не об'єкт)».
    /// Повертає ребро на корінь перенесеного графа.
    pub(crate) fn mirror_value(&mut self, value: &Value) -> Edge {
        match value {
            Value::Pair(node) => {
                let head = self.mirror_value(&node.head);
                let tail = self.mirror_value(&node.tail);
                Edge::Cell(self.alloc_with(head, tail))
            }
            leaf => Edge::Atom(leaf.clone()),
        }
    }

    /// Відновити `Value` з комірки.
    ///
    /// Для ациклічного підграфа дає точний `Value::Pair`-еквівалент. На
    /// зворотному ребрі (цикл) спиняється й повертає [`Value::Nil`].
    ///
    /// Це **СВІДОМИЙ, задокументований компроміс, а не дефект** (закріплено
    /// тестом `cycle_is_cut_to_nil_by_design`). Причина в чинному поданні
    /// пари: `Rc<PairNode>` з незмінними полями `head`/`tail` — у ньому
    /// фізично немає куди записати зворотне ребро, а коректне подання циклу
    /// вимагало б змінити сам `Value` (позикове подання або слабке ребро).
    /// Доти цикл розрізається саме на зворотному ребрі: решта ациклічного
    /// підграфа відновлюється точно, а місце зворотного ребра стає `Nil`.
    ///
    /// Не приймати це за помилку відновлення: `Nil` тут означає «зворотне
    /// ребро», а не «відсутня комірка».
    pub(crate) fn to_value(&self, root: CellRef) -> Value {
        self.to_value_guarded(root, &mut Vec::new())
    }

    /// Те саме, що [`Arena::to_value`], але кожну відновлену пару ще й
    /// **реєструє** в `handles` (адреса `Rc<PairNode>` → дескриптор комірки).
    ///
    /// Це потрібно зворотному шляху: `cons` віддає значення, відновлене з
    /// арени, а наступний `cons` мусить знати, у якій комірці воно живе, щоб
    /// зшити ребро-`Cell`, а не розсипати весь підграф у листові `Atom`.
    /// Окремого подання арени в самому `Value` для цього не заводимо.
    pub(crate) fn to_value_registered(&self, root: CellRef, handles: &mut ArenaHandles) -> Value {
        self.to_value_registered_guarded(root, &mut Vec::new(), handles)
    }

    fn to_value_registered_guarded(
        &self,
        root: CellRef,
        seen: &mut Vec<CellRef>,
        handles: &mut ArenaHandles,
    ) -> Value {
        if seen.contains(&root) {
            // Зворотне ребро циклу. `Rc<PairNode>` цикл подати не може
            // (незмінні `head`/`tail`), тож це свідомий компроміс — див.
            // доку [`Arena::to_value`].
            return Value::Nil;
        }
        let Some(slot) = self.cell(root) else {
            return Value::Nil;
        };
        seen.push(root);
        let head = self.edge_to_value_registered(&slot.head, seen, handles);
        let tail = self.edge_to_value_registered(&slot.tail, seen, handles);
        seen.pop();
        let node = Rc::new(PairNode { head, tail });
        // Слабкий власник (не сильний!): він лише закріплює адресу `Rc`,
        // щоб вона не перевикористалася під чужу пару, але не подовжує
        // життя самого значення.
        handles.insert(Rc::as_ptr(&node) as usize, (Rc::downgrade(&node), root));
        Value::Pair(node)
    }

    fn edge_to_value_registered(
        &self,
        edge: &Edge,
        seen: &mut Vec<CellRef>,
        handles: &mut ArenaHandles,
    ) -> Value {
        match edge {
            Edge::None => Value::Nil,
            Edge::Atom(value) => value.clone(),
            Edge::Cell(cell) => self.to_value_registered_guarded(*cell, seen, handles),
        }
    }

    fn to_value_guarded(&self, root: CellRef, seen: &mut Vec<CellRef>) -> Value {
        if seen.contains(&root) {
            // Зворотне ребро циклу — свідомий компроміс, див. [`Arena::to_value`].
            return Value::Nil;
        }
        let Some(slot) = self.cell(root) else {
            return Value::Nil;
        };
        seen.push(root);
        let head = self.edge_to_value(&slot.head, seen);
        let tail = self.edge_to_value(&slot.tail, seen);
        seen.pop();
        Value::Pair(Rc::new(PairNode { head, tail }))
    }

    fn edge_to_value(&self, edge: &Edge, seen: &mut Vec<CellRef>) -> Value {
        match edge {
            Edge::None => Value::Nil,
            Edge::Atom(value) => value.clone(),
            Edge::Cell(cell) => self.to_value_guarded(*cell, seen),
        }
    }
}

