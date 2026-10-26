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

#[cfg(test)]
mod tests {
    use super::*;

    fn sorted(mut cells: Vec<CellRef>) -> Vec<CellRef> {
        cells.sort_unstable();
        cells
    }

    /// ПОЗИТИВНИЙ СВІДОК: недосяжний ЦИКЛ збирається.
    ///
    /// Досяжний ланцюг `root -> n1` лишається, а окремий цикл `c1 -> c2 -> c1`,
    /// до якого корінь не веде, визначається як сміття й вигрібається.
    #[test]
    fn unreachable_cycle_is_collected() {
        let mut arena = Arena::new();
        let n1 = arena.alloc(); // 0
        let root = arena.alloc_with(Edge::Cell(n1), Edge::None); // 1
        let c1 = arena.alloc(); // 2
        let c2 = arena.alloc(); // 3
        assert!(arena.write(c1, Edge::Cell(c2), Edge::None));
        assert!(arena.write(c2, Edge::Cell(c1), Edge::None));

        // Позначення з єдиного кореня бачить ланцюг, але не цикл.
        assert_eq!(sorted(arena.reachable(&[root])), vec![n1, root]);
        assert_eq!(sorted(arena.garbage(&[root])), vec![c1, c2]);

        let (live, dead) = arena.partition(&[root]);
        assert_eq!(sorted(live), vec![n1, root]);
        assert_eq!(sorted(dead), vec![c1, c2]);

        // `ядро1-повернути-память`: цикл вигрібено фізично.
        let swept = arena.collect(&[root]);
        assert_eq!(sorted(swept), vec![c1, c2]);
        assert!(arena.cell(c1).is_none(), "c1 мусив бути вигрібений");
        assert!(arena.cell(c2).is_none(), "c2 мусив бути вигрібений");
        // Досяжне лишилося живим.
        assert!(arena.cell(root).is_some());
        assert!(arena.cell(n1).is_some());
        assert_eq!(sorted(arena.reachable(&[root])), vec![n1, root]);

        // Звільнений слот повторно виділяється (арена, а не витік).
        let recycled = arena.alloc();
        assert!(recycled == c1 || recycled == c2);
    }

    /// НЕГАТИВНИЙ СВІДОК: досяжне лишається.
    ///
    /// Зокрема **досяжний цикл** (`root -> r1 -> r2 -> r1`) не збирається: це
    /// доводить, що колектор не «вигрібає будь-який цикл», а саме недосяжне.
    #[test]
    fn reachable_graph_survives() {
        let mut arena = Arena::new();
        let leaf = arena.alloc(); // 0
        let r1 = arena.alloc(); // 1
        let r2 = arena.alloc(); // 2
        let root = arena.alloc(); // 3
        assert!(arena.write(leaf, Edge::None, Edge::None));
        assert!(arena.write(r1, Edge::Cell(leaf), Edge::Cell(r2)));
        assert!(arena.write(r2, Edge::Cell(r1), Edge::None)); // цикл r1 <-> r2
        assert!(arena.write(root, Edge::Cell(r1), Edge::None));

        assert_eq!(sorted(arena.reachable(&[root])), vec![leaf, r1, r2, root]);
        assert!(arena.garbage(&[root]).is_empty());

        let swept = arena.collect(&[root]);
        assert!(swept.is_empty(), "досяжне не можна збирати");
        for cell in [leaf, r1, r2, root] {
            assert!(arena.cell(cell).is_some(), "досяжна комірка мусить жити");
        }
    }

    /// `ядро1-вільні-комірки`: без коренів усе — сміття.
    #[test]
    fn no_roots_means_every_cell_is_garbage() {
        let mut arena = Arena::new();
        let a = arena.alloc();
        let b = arena.alloc_with(Edge::Cell(a), Edge::None);
        assert_eq!(sorted(arena.all_cells()), vec![a, b]);
        assert_eq!(sorted(arena.garbage(&[])), vec![a, b]);
        assert!(arena.reachable(&[]).is_empty());
    }

    /// Вузол без комірки (атом-ребро) не пропагує обхід — точний закон `core1`.
    #[test]
    fn atom_edge_does_not_propagate() {
        let mut arena = Arena::new();
        let root = arena.alloc_with(Edge::Atom(Value::Bool(true)), Edge::None);
        assert_eq!(arena.reachable(&[root]), vec![root]);
        assert!(arena.garbage(&[root]).is_empty());
    }

    /// Дескриптор без комірки (поза ареною, [`NO_CELL`], вигрібений) — не об'єкт.
    #[test]
    fn dangling_descriptor_is_not_an_object() {
        let mut arena = Arena::new();
        let root = arena.alloc();
        assert!(arena.cell(NO_CELL).is_none());
        assert!(arena.cell(999).is_none());
        // Ребро на дескриптор поза ареною: корінь чорніє, нащадок — ні.
        assert!(arena.write(root, Edge::Cell(999), Edge::None));
        assert_eq!(arena.reachable(&[root]), vec![root]);
        // Після вигрібання досяжного предка дескриптор теж не об'єкт.
        let gone = arena.alloc();
        arena.collect(&[root]);
        assert!(arena.cell(gone).is_none());
    }

    /// `ядро1-затемнення-при-записі`: чорний власник + нове ребро на білого
    /// нащадка сірить його; інакше — ні.
    #[test]
    fn write_barrier_darkens_white_child_of_black_owner() {
        let mut arena = Arena::new();
        let a = arena.alloc(); // 0
        let root = arena.alloc_with(Edge::Cell(a), Edge::None); // 1
        let white = arena.alloc(); // 2
        let white_owner = arena.alloc(); // 3

        let mut grey = vec![root];
        let mut black = arena.white_set();
        // Крок за кроком: після одного кроку чорними є root і a.
        assert!(arena.tricolor_step(&mut grey, &mut black));
        assert!(arena.tricolor_step(&mut grey, &mut black));
        assert!(!arena.tricolor_step(&mut grey, &mut black)); // сірі порожні
        assert!(arena.is_black(root, &black) && arena.is_black(a, &black));

        // Бар'єр: чорний root -> білий white сіриться.
        assert!(arena.darken_on_write(root, Edge::Cell(white), &mut grey, &black));
        assert_eq!(grey, vec![white]);
        // Білий власник не затемнює.
        assert!(!arena.darken_on_write(white_owner, Edge::Cell(white), &mut grey, &black));
        // Уже чорний нащадок — не затемнюється.
        assert!(!arena.darken_on_write(root, Edge::Cell(a), &mut grey, &black));
        // `()` і атом — без затемнення (нема куди сірити).
        assert!(!arena.darken_on_write(root, Edge::None, &mut grey, &black));
        assert!(!arena.darken_on_write(root, Edge::Atom(Value::Nil), &mut grey, &black));

        // Рушій доходить до кінця: затемнений нащадок стає чорним.
        assert!(arena.tricolor_step(&mut grey, &mut black));
        assert!(arena.is_black(white, &black));
    }

    /// Інваріант Дейкстри тримається навіть після вставки під час маркування:
    /// жоден чорний вузол не вказує на білого.
    #[test]
    fn black_never_points_to_white_after_insertion() {
        let mut arena = Arena::new();
        let a = arena.alloc(); // 0
        let root = arena.alloc_with(Edge::Cell(a), Edge::None); // 1
        let inserted = arena.alloc(); // 2
        let mut grey = vec![root];
        let mut black = arena.white_set();
        // Позначити лише корінь.
        assert!(arena.tricolor_step(&mut grey, &mut black));
        // Вставити нове ребро root.tail -> inserted із бар'єром.
        assert!(arena.write(root, Edge::Cell(a), Edge::Cell(inserted)));
        assert!(arena.darken_on_write(root, Edge::Cell(inserted), &mut grey, &black));
        while arena.tricolor_step(&mut grey, &mut black) {}
        // Тепер жодне ребро чорного не веде на білого.
        for index in 0..arena.len() as CellRef {
            if !arena.is_black(index, &black) {
                continue;
            }
            if let Some(slot) = arena.cell(index) {
                for edge in [&slot.head, &slot.tail] {
                    if let Some(child) = edge.as_cell() {
                        assert!(
                            arena.is_black(child, &black),
                            "чорний {index} указує на білого {child}"
                        );
                    }
                }
            }
        }
        assert_eq!(
            sorted(arena.reachable(&[root])),
            sorted(vec![a, root, inserted])
        );
    }

    /// Міст до чинного `Rc`-`Value`: переніс, збирання за коренем, відновлення.
    #[test]
    fn mirrors_existing_rc_value_and_round_trips() {
        let value = Value::list(vec![Value::Bool(true), Value::Bool(false)]);
        let mut arena = Arena::new();
        let Edge::Cell(root) = arena.mirror_value(&value) else {
            panic!("список мусив стати коміркою");
        };
        // Два конси: (true . rest) і (false . ()).
        assert_eq!(arena.len(), 2);
        assert_eq!(sorted(arena.reachable(&[root])), vec![0, 1]);
        assert!(arena.garbage(&[root]).is_empty());

        // Відновлення назад у `Value` дає той самий список.
        assert_eq!(arena.to_value(root), value);

        // Без кореня весь перенесений граф — сміття.
        let swept = arena.collect(&[]);
        assert_eq!(sorted(swept), vec![0, 1]);
        assert!(arena.cell(root).is_none());
        assert!(arena.to_value(root) == Value::Nil);
    }

    /// `mirror_value` не змінює наявний `Value`: початковий `Rc`-`Pair` живий.
    #[test]
    fn mirroring_leaves_the_source_value_intact() {
        let value = Value::list(vec![Value::Bool(true)]);
        let before = value.clone();
        let mut arena = Arena::new();
        let _ = arena.mirror_value(&value);
        arena.collect(&[]);
        assert_eq!(value, before, "перенесення не мусить чіпати джерело");
        assert!(matches!(value, Value::Pair(_)));
    }

    /// ЦИКЛІЧНИЙ ПІДГРАФ (пункт 3): `to_value` **свідомо** розрізає цикл до
    /// [`Value::Nil`] на зворотному ребрі — це задокументований компроміс
    /// (див. доку [`Arena::to_value`]), а не дефект.
    ///
    /// `Rc<PairNode>` має незмінні `head`/`tail`, тож фізично не подає цикл;
    /// коректне подання циклу вимагало б змінити сам `Value`. Тест закріплює
    /// поведінку, щоб її не прийняли за помилку: розрізається рівно зворотне
    /// ребро, а решта ациклічного підграфа відновлюється точно.
    #[test]
    fn cycle_is_cut_to_nil_by_design() {
        let mut arena = Arena::new();
        // Ациклічний лист: (t . ()) — має відновитися точно.
        let leaf = arena.alloc_with(Edge::Atom(Value::Bool(true)), Edge::None); // 0
                                                                                // Цикл a -> b -> a.
        let a = arena.alloc(); // 1
        let b = arena.alloc(); // 2
        assert!(arena.write(a, Edge::Cell(b), Edge::None));
        assert!(arena.write(b, Edge::Cell(a), Edge::None));

        // Ациклічне відновлюється точно, без жодного зайвого `Nil`.
        assert_eq!(arena.to_value(leaf).to_string(), "(t)");

        // З кореня циклу зворотне ребро ріжеться до `Nil`, решта — точна.
        // a = (b . ()); b = (a . ()) -> b стає (Nil . ()) = (()); a = ((()) . ()).
        assert_eq!(arena.to_value(a).to_string(), "((()))");
        // Той самий результат із другого боку циклу: ріжеться саме зворотне
        // ребро, а не «весь цикл цілком».
        assert_eq!(arena.to_value(b).to_string(), "((()))");

        // Зареєстрований шлях (`cons`) поводиться ідентично.
        let mut handles = ArenaHandles::new();
        assert_eq!(
            arena.to_value_registered(a, &mut handles).to_string(),
            "((()))"
        );
    }
}
