use crate::arena::{Arena, ArenaHandles, CellRef, Edge};
use crate::{DomainIdentity, Value};
use std::{
    cell::RefCell,
    collections::{hash_map::Entry, HashMap},
    path::PathBuf,
    rc::Rc,
};

/// Session-wide print transcript plus a consumer cursor, so hot hosts
/// (REPL, LSP, swarm TCP) can take only the lines appended since their
/// last read instead of re-cloning the whole history per evaluation.
///
/// The transcript is no longer a separate `Rc` inside every `Environment`:
/// it now lives in the shared session state (`SessionState`), so each
/// environment carries only its lexical frame and that one session handle.
/// `cap` is an opt-in ceiling on retained lines for long sessions; `None`
/// keeps the historical unbounded behaviour bit-for-bit.
#[derive(Debug, Default)]
pub struct Transcript {
    lines: Vec<String>,
    taken: usize,
    cap: Option<usize>,
}

impl Transcript {
    fn push(&mut self, line: String) {
        if let Some(cap) = self.cap {
            if cap == 0 {
                return;
            }
            if self.lines.len() >= cap {
                // Rotation: the oldest line is evicted and the consumer
                // cursor shifts with it, so `output_take_new` still returns
                // exactly the lines the consumer has not seen yet.
                self.lines.remove(0);
                self.taken = self.taken.saturating_sub(1);
            }
        }
        self.lines.push(line);
    }

    fn snapshot(&self) -> Vec<String> {
        self.lines.clone()
    }

    fn take_new(&mut self) -> Vec<String> {
        let new = self.lines[self.taken..].to_vec();
        self.taken = self.lines.len();
        new
    }
}

/// Dropping a deeply nested `Environment` chain (thousands of `let`/currying
/// levels) would otherwise recurse through `Rc<RefCell<Frame>>`'s default
/// `Drop` one stack frame per level and could overflow the stack. `Environment`
/// has its own `Drop` below (mirroring `Value::Pair`'s iterative Drop in
/// `value.rs`) that walks the parent chain with an explicit worklist instead,
/// so this is fixed, not just documented as a live risk.
///
/// Layout is `(frame, _, session_state)`. The middle slot used to hold a
/// per-environment `Rc<RefCell<Transcript>>`; the transcript now belongs to the
/// shared `SessionState`, so the slot is a zero-sized placeholder that keeps the
/// historical field order without adding any per-environment weight.
#[derive(Clone, Debug)]
pub struct Environment(Rc<RefCell<Frame>>, (), Rc<RefCell<SessionState>>);

#[derive(Debug)]
struct Frame {
    /// Кадр виклику замикання: параметри лежать у масиві `slots` за номером,
    /// імена — у `slot_names` (той самий порядок), тож пошук за іменем теж
    /// їх бачить. `None` — звичайний кадр без слотів (корінь, `child`).
    slot_names: Option<Rc<[Rc<str>]>>,
    slots: Box<[Value]>,
    /// Тіло цього виклику не може додати нове ім'я в кадр (без `def`, `eval`,
    /// макросів і можливостей хоста) — розв'язувач може дивитися крізь нього.
    pure: bool,
    values: HashMap<Rc<str>, Value>,
    parent: Option<Environment>,
}

impl Frame {
    fn empty(parent: Option<Environment>) -> Self {
        Frame {
            slot_names: None,
            slots: Box::new([]),
            pure: false,
            values: HashMap::new(),
            parent,
        }
    }

    fn slot_index(&self, name: &str) -> Option<usize> {
        self.slot_names
            .as_ref()?
            .iter()
            .position(|slot| **slot == *name)
    }
}

/// Opt-in resource/capability limits for one session, shared across every
/// lexical child. `None` remains the trusted native profile: unrestricted for
/// that dimension once the host capability layer is installed. Embeddings can
/// opt into narrower policies without changing language semantics.
/// Mechanically selected language Core profile.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CoreProfile {
    Core1,
    Core2,
    Core3,
    Core4,
}

/// Підлога порогу високої позначки для `arena_handles`. Карта обслуговується
/// (прибираються мертві записи), щойно її довжина сягає поточного порогу;
/// після прибирання поріг вертається до цієї підлоги, доки живий набір її не
/// переросте.
const ARENA_HANDLES_HWM_FLOOR: usize = 2048;

/// Shared session state: the opt-in resource/capability limits plus the print
/// transcript, allocated once per session and shared by every lexical child.
#[derive(Debug)]
struct SessionState {
    selected_core_profile: Option<CoreProfile>,
    cons_limit: Option<usize>,
    cons_count: usize,
    /// Remaining evaluator dispatches; None is the trusted local profile.
    eval_steps_remaining: Option<usize>,
    /// Опт-ін перемикач арени для `cons`. Коли ввімкнено, єдина точка
    /// алокації `cons_values` виділяє комірку в `arena` і читає значення
    /// назад крізь арену. Вимкнено — подання `Value::Pair(Rc<PairNode>)`
    /// незмінне, як і вся решта виконавця.
    arena_enabled: bool,
    /// Арена комірок, що обслуговує шов `cons_values` за увімкненого
    /// перемикача. Порожня, доки перемикач вимкнено.
    arena: Arena,
    /// Відповідність «адреса `Rc<PairNode>` → (слабкий власник, дескриптор
    /// комірки)» для значень, відновлених із арени. Слабкий власник
    /// ([`std::rc::Weak`]) тримає САМУ алокацію `Rc<PairNode>` живучою, тож
    /// її адреса не може бути перевикористана, поки запис існує. Без цього
    /// звільнена адреса `Rc` збігалася б із новою парою, і `cons` зшивав би
    /// ребро на чужу (застарілу) комірку — саме це й ламало bootstrap FASL.
    /// Сам `Value` при цьому не змінюється.
    arena_handles: ArenaHandles,
    /// Високий поріг для періодичного прибирання мертвих записів у
    /// `arena_handles`, щоб карта не росла назавжди.
    arena_handles_hwm: usize,
    numeric_bit_limit: Option<usize>,
    /// Exact program-name policy. `None` = unrestricted, `Some([])` = deny all.
    process_allowlist: Option<Vec<String>>,
    /// None for trusted CLI; Some([]) denies every host mechanism.
    host_capability_allowlist: Option<Vec<String>>,
    /// Filesystem roots are stored as caller-supplied paths. The host layer,
    /// not the language core, owns canonicalization/symlink enforcement.
    fs_read_roots: Option<Vec<PathBuf>>,
    fs_write_roots: Option<Vec<PathBuf>>,
    /// (host-or-bind-address, first-port, last-port), inclusive.
    tcp_connect_allowlist: Option<Vec<(String, u16, u16)>>,
    tcp_listen_allowlist: Option<Vec<(String, u16, u16)>>,
    /// Canonical language-owned bindings keyed by exact semantic domain.
    /// Equal payloads in different D1-D9 domains remain distinct HashMap keys.
    /// Residency alone never inserts a mechanism slot.
    domain_code_slots: HashMap<DomainIdentity, Value>,
    /// Результати завершених bootstrap-запусків за точним доменним ключем.
    /// Це стан завантажувача, не реєстр значень чи допуску функцій SENS.
    bootstrap_results: HashMap<DomainIdentity, Value>,
    /// Historical exact-eight compatibility slots. These are intentionally
    /// separate storage so a legacy byte can never collide with a canonical
    /// domain identity merely from its packed payload.
    legacy_code_slots: HashMap<crate::CoreDomainIdentity, Value>,
    /// Сесійний транскрипт друку. Живе тут, у спільному стані сесії, а не
    /// окремим `Rc` у кожному `Environment`.
    transcript: Transcript,
}

impl Default for SessionState {
    fn default() -> Self {
        SessionState {
            selected_core_profile: None,
            cons_limit: None,
            cons_count: 0,
            eval_steps_remaining: None,
            // Арена — ТИПОВЕ подання `cons`: кожна сесія народжується з
            // увімкненим швом арени. `Rc`-подання `Value` лишається
            // незмінним; арена стоїть поверх нього.
            arena_enabled: true,
            arena: Arena::default(),
            arena_handles: ArenaHandles::new(),
            arena_handles_hwm: ARENA_HANDLES_HWM_FLOOR,
            numeric_bit_limit: None,
            process_allowlist: None,
            host_capability_allowlist: None,
            fs_read_roots: None,
            fs_write_roots: None,
            tcp_connect_allowlist: None,
            tcp_listen_allowlist: None,
            domain_code_slots: HashMap::new(),
            bootstrap_results: HashMap::new(),
            legacy_code_slots: HashMap::new(),
            transcript: Transcript::default(),
        }
    }
}

impl SessionState {
    /// Обмежити зростання `arena_handles` періодичним прибиранням за порогом
    /// високої позначки [`SessionState::arena_handles_hwm`].
    ///
    /// Слабкий власник у кожному записі тримає алокацію `Rc<PairNode>`
    /// живучою, тож записи мертвих пар треба прибирати явно — інакше карта
    /// росла б упродовж усієї довгої сесії. Політика:
    ///
    /// * доки довжина менша за поріг — нічого не робимо (амортизовано дешево);
    /// * щойно довжина сягає порогу — викидаємо записи з мертвим власником;
    /// * поріг піднімаємо лише тоді, коли ЖИВИЙ набір сам його переріс;
    ///   інакше вертаємо до [`ARENA_HANDLES_HWM_FLOOR`].
    ///
    /// Живі записи не викидаються ніколи: викинути живий запис означало б
    /// втратити комірку-опору для ще живої пари, тобто змінити семантику
    /// `cons`. Тому межа — це саме поріг, за яким прибираються мертві, а не
    /// жорстка стеля кількості.
    fn prune_dead_arena_handles(&mut self) {
        if self.arena_handles.len() < self.arena_handles_hwm {
            return;
        }
        self.arena_handles
            .retain(|_, (owner, _)| owner.strong_count() > 0);
        self.arena_handles_hwm = self
            .arena_handles
            .len()
            .saturating_mul(2)
            .max(ARENA_HANDLES_HWM_FLOOR);
    }
}

impl Environment {
    pub fn root() -> Self {
        Self(
            Rc::new(RefCell::new(Frame::empty(None))),
            (),
            Rc::new(RefCell::new(SessionState::default())),
        )
    }

    /// Opts this session into a maximum `cons` allocation count — past it,
    /// `cons` returns `ErrorKind::OutOfMemory` instead of succeeding.
    pub fn with_cons_limit(self, limit: usize) -> Self {
        self.2.borrow_mut().cons_limit = Some(limit);
        self
    }

    /// Opts this session into a bounded print transcript: at most `limit`
    /// lines are retained, evicting oldest-first. `output_take_new` still
    /// returns only the lines the consumer has not seen yet. Without this
    /// call the transcript stays unbounded (the historical behaviour).
    pub fn with_transcript_cap(self, limit: usize) -> Self {
        self.2.borrow_mut().transcript.cap = Some(limit);
        self
    }

    /// Opts this session into a maximum bit width for exact arithmetic
    /// results — past it arithmetic returns `ErrorKind::NumericOverflow`.
    pub fn with_numeric_bit_limit(self, limit: usize) -> Self {
        self.2.borrow_mut().numeric_bit_limit = Some(limit);
        self
    }

    /// Mechanical resource budget for untrusted network sessions.
    /// Activate only AFTER Core4 and other trusted bootstrap libraries load.
    /// Counts include nested and tail-position evaluator dispatches.
    pub fn activate_untrusted_runtime_limits(&self) {
        const CONS_ADDITIONAL: usize = 100_000;
        const EVAL_DISPATCHES: usize = 500_000;
        const NUMERIC_BITS: usize = 4096;
        const PRINT_LINES: usize = 256;

        let mut state = self.2.borrow_mut();
        // Preserve the already-accounted bootstrap allocations: never reset
        // cons_count, or the arena could have unaccounted surviving values.
        state.cons_limit = Some(state.cons_count.saturating_add(CONS_ADDITIONAL));
        state.eval_steps_remaining = Some(EVAL_DISPATCHES);
        state.numeric_bit_limit = Some(NUMERIC_BITS);
        state.transcript.cap = Some(PRINT_LINES);
    }

    /// Mechanism test/embedding hook; no additional SENS function is defined.
    pub fn with_eval_step_budget(self, steps: usize) -> Self {
        self.2.borrow_mut().eval_steps_remaining = Some(steps);
        self
    }

    /// A zero budget is a named failure, not successful SENS evaluation.
    pub(crate) fn consume_eval_step(&self) -> Result<(), ()> {
        let mut state = self.2.borrow_mut();
        if let Some(remaining) = state.eval_steps_remaining.as_mut() {
            if *remaining == 0 {
                return Err(());
            }
            *remaining -= 1;
        }
        Ok(())
    }

    /// Restricts process execution to exact program names.
    pub fn with_process_allowlist(self, programs: Vec<String>) -> Self {
        self.2.borrow_mut().process_allowlist = Some(programs);
        self
    }

    /// Недовірений TCP-сеанс: лише явно названі процеси можуть отримати
    /// host-виклик; файли, сокети, модель і точні island-механізми заборонені.
    pub fn untrusted_tcp(allowed_processes: Vec<String>) -> Self {
        let allowed_host = if allowed_processes.is_empty() {
            Vec::new()
        } else {
            vec![
                "process-run-raw".to_owned(),
                "процес-запустити-сирий".to_owned(),
            ]
        };
        Self::root()
            .with_process_allowlist(allowed_processes)
            .with_host_capability_allowlist(allowed_host)
            .with_fs_read_roots(Vec::new())
            .with_fs_write_roots(Vec::new())
            .with_tcp_connect_allowlist(Vec::new())
            .with_tcp_listen_allowlist(Vec::new())
    }

    /// Host-механізм — не значення та не семантика SENS.
    pub fn with_host_capability_allowlist(self, names: Vec<String>) -> Self {
        self.2.borrow_mut().host_capability_allowlist = Some(names);
        self
    }

    pub(crate) fn is_host_capability_allowed(&self, name: &str) -> bool {
        match &self.2.borrow().host_capability_allowlist {
            None => true,
            Some(names) => names.iter().any(|allowed| allowed == name),
        }
    }

    /// У недовіреному сеансі host-механізми із точними identity не допускаються.
    pub(crate) fn are_exact_host_capabilities_allowed(&self) -> bool {
        self.2.borrow().host_capability_allowlist.is_none()
    }

    /// Restricts host filesystem reads (`read-file`, `read-file-bytes`,
    /// `read-dir`, `load`) to paths under one of these roots. Canonicalization
    /// and symlink checks are deliberately performed by `sens-host`.
    pub fn with_fs_read_roots(self, roots: Vec<PathBuf>) -> Self {
        self.2.borrow_mut().fs_read_roots = Some(roots);
        self
    }

    /// Restricts host filesystem writes (`write-file`, `write-file-bytes`) to
    /// paths under one of these roots.
    pub fn with_fs_write_roots(self, roots: Vec<PathBuf>) -> Self {
        self.2.borrow_mut().fs_write_roots = Some(roots);
        self
    }

    /// Restricts outbound TCP connects to explicit host + inclusive port
    /// ranges. `None` remains unrestricted; an empty list is deny-all.
    pub fn with_tcp_connect_allowlist(self, entries: Vec<(String, u16, u16)>) -> Self {
        self.2.borrow_mut().tcp_connect_allowlist = Some(entries);
        self
    }

    /// Restricts TCP listen/bind operations independently from connect.
    pub fn with_tcp_listen_allowlist(self, entries: Vec<(String, u16, u16)>) -> Self {
        self.2.borrow_mut().tcp_listen_allowlist = Some(entries);
        self
    }

    /// Host-owned canonicalization needs a snapshot of the configured roots;
    /// exposing data does not give the core any filesystem behavior itself.
    pub fn fs_read_roots(&self) -> Option<Vec<PathBuf>> {
        self.2.borrow().fs_read_roots.clone()
    }

    pub fn fs_write_roots(&self) -> Option<Vec<PathBuf>> {
        self.2.borrow().fs_write_roots.clone()
    }

    pub fn is_tcp_connect_allowed(&self, host: &str, port: u16) -> bool {
        match &self.2.borrow().tcp_connect_allowlist {
            Some(entries) => entries.iter().any(|(allowed_host, first, last)| {
                allowed_host == host && *first <= port && port <= *last
            }),
            None => true,
        }
    }

    pub fn is_tcp_listen_allowed(&self, address: &str, port: u16) -> bool {
        match &self.2.borrow().tcp_listen_allowlist {
            Some(entries) => entries.iter().any(|(allowed_address, first, last)| {
                allowed_address == address && *first <= port && port <= *last
            }),
            None => true,
        }
    }

    /// Called by `cons` before allocating; `Err(())` means the configured
    /// limit (if any) is already reached. No-op when unbounded.
    pub(crate) fn try_alloc_cons(&self) -> Result<(), ()> {
        let mut limits = self.2.borrow_mut();
        if let Some(limit) = limits.cons_limit {
            if limits.cons_count >= limit {
                return Err(());
            }
        }
        limits.cons_count += 1;
        Ok(())
    }

    // ── Арена як BACKING-STORE для `cons` (єдина точка — `cons_values`) ────

    /// Опт-ін: зробити арену BACKING-STORE для `cons`. Без цього виклику
    /// єдина точка алокації `cons_values` лишається на `Rc::new(PairNode)`.
    /// Перемикач живе в спільному стані сесії, тож сигнатури виконавця
    /// не змінюються.
    pub fn with_arena_cons(self) -> Self {
        self.2.borrow_mut().arena_enabled = true;
        self
    }

    /// Чи ввімкнено арену для `cons` у цій сесії.
    pub(crate) fn arena_cons_enabled(&self) -> bool {
        self.2.borrow().arena_enabled
    }

    /// Шов алокації `cons`: виділити комірку в арені й **прочитати значення
    /// назад крізь арену**. Ребро на дитину стає `Edge::Cell`, якщо дитина вже
    /// має комірку в арені (за `arena_handles`), інакше — листове `Edge::Atom`.
    /// Це та сама семантика, що й `Value::Pair(Rc::new(PairNode { .. }))`,
    /// лише матеріалізована з комірки арени.
    pub(crate) fn arena_cons(&self, head: Value, tail: Value) -> Value {
        let mut guard = self.2.borrow_mut();
        let state: &mut SessionState = &mut guard;
        // Обмеження зростання карти за порогом високої позначки.
        state.prune_dead_arena_handles();
        let head_edge = arena_edge_for(&state.arena, &state.arena_handles, &head);
        let tail_edge = arena_edge_for(&state.arena, &state.arena_handles, &tail);
        let cell = state.arena.alloc_with(head_edge, tail_edge);
        state
            .arena
            .to_value_registered(cell, &mut state.arena_handles)
    }

    /// Кількість слотів арени (свідок).
    pub fn arena_len(&self) -> usize {
        self.2.borrow().arena.len()
    }

    /// Скільки записів зараз у `arena_handles` (свідок межі зростання).
    pub fn arena_handles_len(&self) -> usize {
        self.2.borrow().arena_handles.len()
    }

    /// Чи має це значення живу комірку-опору в арені.
    pub fn arena_backs(&self, value: &Value) -> bool {
        let state = self.2.borrow();
        match value {
            Value::Pair(node) => match state.arena_handles.get(&(Rc::as_ptr(node) as usize)) {
                Some((owner, cell)) => {
                    owner.strong_count() > 0 && state.arena.cell(*cell).is_some()
                }
                None => false,
            },
            _ => false,
        }
    }

    /// Скільки комірок арени досяжні з цих значень-коренів (свідок).
    pub fn arena_reachable_count(&self, roots: &[Value]) -> usize {
        let state = self.2.borrow();
        let cells = arena_root_cells(&state.arena_handles, roots);
        state.arena.reachable(&cells).len()
    }

    /// Скільки комірок арени недосяжні з цих значень-коренів (сміття).
    pub fn arena_garbage_count(&self, roots: &[Value]) -> usize {
        let state = self.2.borrow();
        let cells = arena_root_cells(&state.arena_handles, roots);
        state.arena.garbage(&cells).len()
    }

    /// Зібрати недосяжне з цих значень-коренів; повертає кількість
    /// вигрібених комірок. Досяжні комірки лишаються живими.
    pub fn arena_collect(&self, roots: &[Value]) -> usize {
        let mut state = self.2.borrow_mut();
        let cells = arena_root_cells(&state.arena_handles, roots);
        state.arena.collect(&cells).len()
    }

    pub(crate) fn numeric_bit_limit(&self) -> Option<usize> {
        self.2.borrow().numeric_bit_limit
    }

    /// Return the explicitly selected Core profile, if a profile loader selected one.
    pub fn selected_core_profile(&self) -> Option<CoreProfile> {
        self.2.borrow().selected_core_profile
    }

    /// Mechanism-only selector. Core meaning remains owned by SENS contracts.
    pub(crate) fn select_core_profile(&self, profile: CoreProfile) {
        self.2.borrow_mut().selected_core_profile = Some(profile);
    }

    /// Native root sessions are unrestricted (`None`). An embedding can set
    /// an exact allowlist; an empty allowlist is an explicit deny-all policy.
    pub fn is_process_allowed(&self, program: &str) -> bool {
        match &self.2.borrow().process_allowlist {
            Some(programs) => programs.iter().any(|allowed| allowed == program),
            None => true,
        }
    }

    /// Чи це кадр верхнього рівня сесії (без lexical parent).
    pub(crate) fn is_root(&self) -> bool {
        self.0.borrow().parent.is_none()
    }

    /// Результат фактично завершеного bootstrap, спільний для кадрів сесії.
    pub(crate) fn completed_bootstrap_result(&self, identity: DomainIdentity) -> Option<Value> {
        self.2.borrow().bootstrap_results.get(&identity).cloned()
    }

    pub(crate) fn complete_bootstrap(&self, identity: DomainIdentity, value: Value) {
        self.2
            .borrow_mut()
            .bootstrap_results
            .insert(identity, value);
    }

    /// Canonical exact-domain language slot.
    pub(crate) fn domain_code_slot(&self, identity: impl Into<DomainIdentity>) -> Option<Value> {
        let identity = identity.into();
        self.2.borrow().domain_code_slots.get(&identity).cloned()
    }

    /// Чи має точна доменна identity зв'язування в цьому середовищі.
    /// Зайнятість не доводить, що прив'язане значення можна викликати.
    /// Whether an exact domain identity has a runtime binding in this environment.
    /// Occupancy alone does not establish that the bound value is callable.
    pub fn has_domain_code_slot(&self, identity: impl Into<DomainIdentity>) -> bool {
        let identity = identity.into();
        self.2.borrow().domain_code_slots.contains_key(&identity)
    }

    /// Binds one concrete mechanism to one already-known exact-domain identity.
    /// Width/residency alone never grants callability.
    pub(crate) fn bind_domain_code_slot_once(
        &self,
        identity: impl Into<DomainIdentity>,
        value: Value,
    ) -> bool {
        let identity = identity.into();
        let mut limits = self.2.borrow_mut();
        // Exact domain identity (width AND payload) is the whole key.
        // Vacant/Occupied prevents a second lookup and forbids overwrites.
        match limits.domain_code_slots.entry(identity) {
            Entry::Vacant(slot) => {
                slot.insert(value);
                true
            }
            Entry::Occupied(_) => false,
        }
    }

    /// Transitional historical exact-eight compatibility lookup.
    ///
    /// Kept under the old method name so this slice does not grow CoreDomainIdentity API
    /// surface. New canonical code uses domain_code_slot.
    pub(crate) fn code_slot(&self, sid: crate::CoreDomainIdentity) -> Option<Value> {
        self.2.borrow().legacy_code_slots.get(&sid).cloned()
    }

    /// Transitional historical exact-eight compatibility binding.
    ///
    /// New canonical code uses bind_domain_code_slot_once.
    pub(crate) fn bind_code_slot_once(&self, sid: crate::CoreDomainIdentity, value: Value) -> bool {
        let mut limits = self.2.borrow_mut();
        // Historical W8 never shares a keyspace with exact D8.
        match limits.legacy_code_slots.entry(sid) {
            Entry::Vacant(slot) => {
                slot.insert(value);
                true
            }
            Entry::Occupied(_) => false,
        }
    }

    /// A child frame is the future lexical boundary captured by a closure. It
    /// shares all session policy/limits (and thus the transcript) with its
    /// parent.
    pub fn child(&self) -> Self {
        Self(
            Rc::new(RefCell::new(Frame::empty(Some(self.clone())))),
            (),
            self.2.clone(),
        )
    }

    /// Кадр виклику замикання: значення параметрів за номером слота.
    pub(crate) fn child_with_slots(
        &self,
        names: Rc<[Rc<str>]>,
        slots: Vec<Value>,
        pure: bool,
    ) -> Self {
        let mut frame = Frame::empty(Some(self.clone()));
        frame.slot_names = Some(names);
        // Slots are immutable after parameter binding: discard unused Vec capacity.
        frame.slots = slots.into_boxed_slice();
        frame.pure = pure;
        Self(Rc::new(RefCell::new(frame)), (), self.2.clone())
    }

    /// Значення `Local(depth, index)`: слот `index` кадру на `depth` кроків вище.
    pub(crate) fn get_local(&self, depth: u32, index: u32) -> Option<Value> {
        let mut frame = Rc::clone(&self.0);
        for _ in 0..depth {
            let parent = frame
                .borrow()
                .parent
                .as_ref()
                .map(|parent| Rc::clone(&parent.0))?;
            frame = parent;
        }
        let current = frame.borrow();
        current.slots.get(index as usize).cloned()
    }

    /// Імена параметрів кадрів, крізь які розв'язувач може бачити: від цього
    /// кадру вгору, доки кадри мають слоти; нечистий кадр — останній (його
    /// тіло може визначити нове ім'я, що затінить глибші).
    pub(crate) fn lexical_slot_scopes(&self) -> Vec<Rc<[Rc<str>]>> {
        let mut scopes = Vec::new();
        let mut frame = Rc::clone(&self.0);
        loop {
            let parent = {
                let current = frame.borrow();
                let Some(names) = &current.slot_names else {
                    break;
                };
                scopes.push(Rc::clone(names));
                if !current.pure {
                    break;
                }
                current.parent.as_ref().map(|parent| Rc::clone(&parent.0))
            };
            match parent {
                Some(parent) => frame = parent,
                None => break,
            }
        }
        scopes
    }

    /// Перепід'єднує лише безпосереднього lexical parent цього frame.
    /// Це host/UI-механізм для стабільного user-frame поверх змінної
    /// програмної поверхні; Lisp-семантику він не розширює.
    /// Відхиляє цикли та parent з іншим станом сесії.
    pub fn reparent(&self, parent: Environment) -> Result<(), &'static str> {
        if !Rc::ptr_eq(&self.2, &parent.2) {
            return Err("new parent must share session state");
        }

        let mut current = Some(parent.clone());
        while let Some(environment) = current {
            if Rc::ptr_eq(&self.0, &environment.0) {
                return Err("reparent would create an environment cycle");
            }
            current = environment.0.borrow().parent.clone();
        }

        self.0.borrow_mut().parent = Some(parent);
        Ok(())
    }

    pub fn print(&self, line: String) {
        self.2.borrow_mut().transcript.push(line);
    }

    pub fn output_snapshot(&self) -> Vec<String> {
        self.2.borrow().transcript.snapshot()
    }

    pub fn output_take_new(&self) -> Vec<String> {
        self.2.borrow_mut().transcript.take_new()
    }

    /// Snapshot of every visible binding, root-first, shadowed names resolved
    /// to their innermost value.
    pub fn snapshot(&self) -> Vec<(Rc<str>, Value)> {
        let mut frames = Vec::new();
        let mut current = Some(self.clone());
        while let Some(env) = current {
            frames.push(env.0.clone());
            current = env.0.borrow().parent.clone();
        }
        let mut out: Vec<(Rc<str>, Value)> = Vec::new();
        for frame in frames.iter().rev() {
            let f = frame.borrow();
            let slots = f
                .slot_names
                .iter()
                .flat_map(|names| names.iter().zip(f.slots.iter()));
            for (name, value) in slots.chain(f.values.iter()) {
                match out.iter_mut().find(|(n, _)| n == name) {
                    Some(slot) => slot.1 = value.clone(),
                    None => out.push((name.clone(), value.clone())),
                }
            }
        }
        out.sort_by(|a, b| a.0.cmp(&b.0));
        out
    }

    pub fn define(&self, name: impl Into<Rc<str>>, value: Value) {
        let name = name.into();
        let mut frame = self.0.borrow_mut();
        match frame.slot_index(&name) {
            Some(index) => frame.slots[index] = value,
            None => {
                frame.values.insert(name, value);
            }
        }
    }

    /// Updates the nearest already-existing lexical binding and never creates one.
    ///
    /// This is the storage mechanism used by the exact D5 SET/SETQ residents.
    /// Semantic authority remains with the D5 domain law; this method only mutates
    /// the selected environment cell after the evaluator has resolved the target.
    pub(crate) fn update_nearest_existing(&self, name: &str, value: Value) -> bool {
        let mut frame = Rc::clone(&self.0);
        loop {
            let parent = {
                let mut current = frame.borrow_mut();
                if let Some(index) = current.slot_index(name) {
                    current.slots[index] = value;
                    return true;
                }
                if let Some(slot) = current.values.get_mut(name) {
                    *slot = value;
                    return true;
                }
                current.parent.as_ref().map(|parent| Rc::clone(&parent.0))
            };
            let Some(next) = parent else {
                return false;
            };
            frame = next;
        }
    }

    pub fn get(&self, name: &str) -> Option<Value> {
        // Walk the frames themselves: cloning an `Environment` per step would
        // run its `Drop` for every step of every lookup.
        let mut frame = Rc::clone(&self.0);
        loop {
            let parent = {
                let current = frame.borrow();
                if let Some(index) = current.slot_index(name) {
                    return Some(current.slots[index].clone());
                }
                if let Some(value) = current.values.get(name) {
                    return Some(value.clone());
                }
                current.parent.as_ref().map(|parent| Rc::clone(&parent.0))
            };
            frame = parent?;
        }
    }
}

impl Drop for Environment {
    fn drop(&mut self) {
        // Only the last owner of a frame frees it. Its parent chain is then
        // released iteratively: each frame that dies gives up its parent
        // before it drops, so no drop recurses through the chain (a deep
        // recursion would overflow the stack). Dropping a shared handle only
        // decrements a reference count and allocates nothing.
        if Rc::strong_count(&self.0) != 1 {
            return;
        }
        let Ok(mut frame) = self.0.try_borrow_mut() else {
            return;
        };
        let mut next = frame.parent.take();
        drop(frame);
        while let Some(environment) = next {
            next = if Rc::strong_count(&environment.0) == 1 {
                environment
                    .0
                    .try_borrow_mut()
                    .ok()
                    .and_then(|mut parent_frame| parent_frame.parent.take())
            } else {
                None
            };
            // `environment` now has no parent, so its own drop is shallow.
            drop(environment);
        }
    }
}

/// Ребро арени для значення-дитини: `Edge::Cell`, якщо дитина вже має ЖИВУ
/// комірку в арені, інакше листове `Edge::Atom` (вузол без комірки не чорніє).
///
/// Запис визнається чинним лише коли слабкий власник ще живий
/// (`strong_count() > 0`) І комірку не вигріб колектор. Завдяки тому, що
/// `Weak` тримає алокацію `Rc` живою, адреса не перевикористовується, тож
/// застарілий запис фізично не може збігтися з новою парою.
fn arena_edge_for(arena: &Arena, handles: &ArenaHandles, value: &Value) -> Edge {
    if let Value::Pair(node) = value {
        if let Some((owner, cell)) = handles.get(&(Rc::as_ptr(node) as usize)) {
            if owner.strong_count() > 0 && arena.cell(*cell).is_some() {
                return Edge::Cell(*cell);
            }
        }
    }
    Edge::Atom(value.clone())
}

/// Дескриптори-корені для значень: беруться лише ті, що мають живу комірку в арені.
fn arena_root_cells(handles: &ArenaHandles, roots: &[Value]) -> Vec<CellRef> {
    roots
        .iter()
        .filter_map(|value| match value {
            Value::Pair(node) => handles
                .get(&(Rc::as_ptr(node) as usize))
                .filter(|(owner, _)| owner.strong_count() > 0)
                .map(|(_, cell)| *cell),
            _ => None,
        })
        .collect()
}

#[derive(Clone, Debug)]
pub struct Session {
    pub environment: Environment,
}

impl Session {
    /// Construct only the mechanical root environment for programs made from
    /// already-admitted exact domain words. No Lisp macro definitions or Core4
    /// library are installed. Opt-in: `Session::default()` retains its
    /// historical macro-loaded embedding contract.
    ///
    /// Use `load_macro_library(&mut session)` before any program requiring
    /// macros, or `load_core_library(&mut session)` for the full Lisp-owned
    /// core bootstrap. This constructor does not invent any domain semantics.
    pub fn bare() -> Self {
        Self {
            environment: Environment::root(),
        }
    }
}

impl Default for Session {
    fn default() -> Self {
        let mut session = Self {
            environment: Environment::root(),
        };
        crate::load_macro_library(&mut session)
            .expect("embedded lib/macro.lisp must bootstrap a default Session");
        session
    }
}

#[cfg(test)]
mod tests {
    #[test]
    fn untrusted_resource_limits_count_only_post_bootstrap_cons_allocations() {
        let env = Environment::root();
        for _ in 0..3 {
            env.try_alloc_cons().expect("bootstrap setup consumes cons");
        }
        env.activate_untrusted_runtime_limits();
        for _ in 0..100_000 {
            env.try_alloc_cons()
                .expect("post-bootstrap budget admitted");
        }
        assert!(
            env.try_alloc_cons().is_err(),
            "network cons allocation must stop"
        );
        let limited = env.2.borrow();
        assert_eq!(limited.numeric_bit_limit, Some(4096));
        assert_eq!(limited.transcript.cap, Some(256));
        assert_eq!(limited.eval_steps_remaining, Some(500_000));
    }

    use super::*;
    use crate::{CoreDomainIdentity, Exactness};

    #[test]
    fn bare_session_keeps_lisp_macro_bootstrap_explicit() {
        let bare = Session::bare();
        let default = Session::default();
        assert!(
            bare.environment.get("defmacro").is_none(),
            "bare domain carrier must not silently load the Lisp macro library"
        );
        assert!(
            default.environment.get("defmacro").is_some(),
            "default Session must continue bootstrapping macro law"
        );
    }

    #[test]
    fn bare_session_evaluates_the_same_exact_d1_and_d3_results() {
        for (source, expected_bit) in [
            ("1", Some(true)),
            ("0", Some(false)),
            ("10 001 00 000 01", None),
        ] {
            let program = crate::parse_canonical_binary(source).unwrap();
            let mut bare = Session::bare();
            let mut default = Session::default();
            let left = crate::eval_parsed_expressions(&program, &mut bare).unwrap();
            let right = crate::eval_parsed_expressions(&program, &mut default).unwrap();
            assert_eq!(left.value, right.value);
            assert_eq!(left.value.as_predicate_bit(), expected_bit);
            assert_eq!(left.output, right.output);
        }
    }

    #[test]
    fn domain_code_slots_keep_equal_payloads_distinct() {
        use crate::{Bija3, Bit3, Bit4, CoreD4};

        let env = Environment::root();
        let d3 = CoreDomainIdentity::from(Bija3::from_word(Bit3::new(1).unwrap()));
        let d4 = CoreDomainIdentity::from(CoreD4::from_word(Bit4::new(1).unwrap()));

        assert!(env.bind_domain_code_slot_once(d3, Value::Symbol(Rc::from("d3-one"))));
        assert!(env.bind_domain_code_slot_once(d4, Value::Symbol(Rc::from("d4-one"))));

        assert_eq!(
            env.domain_code_slot(d3),
            Some(Value::Symbol(Rc::from("d3-one")))
        );
        assert_eq!(
            env.domain_code_slot(d4),
            Some(Value::Symbol(Rc::from("d4-one")))
        );
    }

    #[test]
    fn historical_w8_slots_never_alias_ratified_d8_even_with_equal_bits() {
        use crate::{Bit8, CoreD8, CoreDomainIdentity};

        let environment = Environment::root();
        // Construct the historical registry-slot key explicitly. Lifting a
        // W8 source word uses current D8 identity and must not mint a legacy
        // callable mechanism.
        let legacy = CoreDomainIdentity::D8(crate::CoreD8::from_word(
            crate::Bit8::new(0b1010_1000).expect("8-bit source word"),
        ));
        let current = DomainIdentity::D8(CoreD8::from_word(
            Bit8::new(0b1010_1000).expect("точно вісім біт"),
        ));
        let old_value = Value::Symbol(Rc::from("історичне"));
        let new_value = Value::Symbol(Rc::from("доменне"));

        assert!(environment.bind_code_slot_once(legacy, old_value.clone()));
        assert_eq!(environment.code_slot(legacy), Some(old_value.clone()));
        assert_eq!(environment.domain_code_slot(current), None);
        assert!(environment.bind_domain_code_slot_once(current, new_value.clone()));
        assert_eq!(environment.domain_code_slot(current), Some(new_value));
        assert_eq!(environment.code_slot(legacy), Some(old_value));
        assert!(!environment.bind_code_slot_once(legacy, Value::Nil));
        assert!(!environment.bind_domain_code_slot_once(current, Value::Nil));
    }

    /// Exhaustive mechanical stress witness, not 2046 callable functions.
    /// Every (width,payload) is distinct. Current semantic DomainIdentity
    /// covers D1–D9 (1022 keys); D10's 1024 slots remain carrier-only.
    #[test]
    fn all_2046_coordinates_preserve_width_and_both_bind_once_keyspaces() {
        use crate::{
            domain_ladder::DomainCoordinate, BinarySourceWord, Bit1, Bit2, Bit3, Bit4, Bit5, Bit6,
            Bit7, Bit8, Bit9, CoreDomainIdentity,
        };
        use std::collections::HashSet;

        let environment = Environment::root();
        let mut coordinates = HashSet::new();
        let mut examined = 0usize;
        let mut significant_bits = 0usize;
        let mut current_slots = 0usize;

        for width in 1u8..=10 {
            for bits in 0..(1u16 << width) {
                let coordinate =
                    DomainCoordinate::new(width, bits).expect("in-range exact coordinate");
                assert!(
                    coordinates.insert(coordinate),
                    "coordinate collision at D{width}:{bits:010b}"
                );
                assert_eq!(coordinate.width(), width);
                assert_eq!(coordinate.bits(), bits);
                examined += 1;
                significant_bits += usize::from(width);

                // The bounded source fast-path is exact and typed; there is
                // deliberately NO lossy D10 → narrower-carrier coercion.
                let source = match width {
                    1 => Some(BinarySourceWord::W1(Bit1::new(bits as u8).unwrap())),
                    2 => Some(BinarySourceWord::W2(Bit2::new(bits as u8).unwrap())),
                    3 => Some(BinarySourceWord::W3(Bit3::new(bits as u8).unwrap())),
                    4 => Some(BinarySourceWord::W4(Bit4::new(bits as u8).unwrap())),
                    5 => Some(BinarySourceWord::W5(Bit5::new(bits as u8).unwrap())),
                    6 => Some(BinarySourceWord::W6(Bit6::new(bits as u8).unwrap())),
                    7 => Some(BinarySourceWord::W7(Bit7::new(bits as u8).unwrap())),
                    8 => Some(BinarySourceWord::W8(Bit8::new(bits as u8).unwrap())),
                    9 => Some(BinarySourceWord::W9(Bit9::new(bits).unwrap())),
                    10 => None,
                    _ => unreachable!(),
                };
                let Some(source) = source else {
                    assert_eq!(width, 10);
                    // Owner residency is not DomainIdentity callability.
                    assert_eq!(coordinate.owner_residency(), Some(true));
                    continue;
                };
                let identity = DomainIdentity::from_source_word(source);
                assert_eq!(
                    DomainCoordinate::from_domain_identity(identity),
                    coordinate,
                    "lost width on D{width}:{bits:010b}"
                );
                let marker = Value::Symbol(Rc::from(format!("D{width}:{bits}")));
                assert!(
                    environment.bind_domain_code_slot_once(identity, marker.clone()),
                    "unexpected prebound coordinate D{width}:{bits:010b}"
                );
                assert!(
                    !environment.bind_domain_code_slot_once(identity, Value::Nil),
                    "overwrote exact identity D{width}:{bits:010b}"
                );
                assert_eq!(
                    environment.domain_code_slot(identity),
                    Some(marker),
                    "key or payload collision D{width}:{bits:010b}"
                );
                current_slots += 1;
            }
        }
        assert_eq!(examined, 2046);
        assert_eq!(significant_bits, 18_434);
        assert_eq!(coordinates.len(), 2046);
        assert_eq!(current_slots, 1022);

        // Every historical W8 byte has a current D8 coordinate with the
        // same low eight payload bits, but MUST NOT alias the current slot.
        for bits in 0u16..256 {
            let sid = CoreDomainIdentity::D8(crate::CoreD8::from_word(
                crate::Bit8::new(bits as u8).expect("historical registry-slot payload"),
            ));
            let identity = DomainIdentity::from_source_word(crate::BinarySourceWord::W8(
                crate::Bit8::new(bits as u8).unwrap(),
            ));
            let current = environment.domain_code_slot(identity);
            assert_eq!(
                environment.code_slot(sid),
                None,
                "historical W8 silently lifted to D8 at {bits:08b}"
            );
            let historical = Value::Symbol(Rc::from(format!("legacy-W8:{bits}")));
            assert!(environment.bind_code_slot_once(sid, historical.clone()));
            assert!(!environment.bind_code_slot_once(sid, Value::Nil));
            assert_eq!(environment.code_slot(sid), Some(historical));
            assert_eq!(
                environment.domain_code_slot(identity),
                current,
                "historical W8 overwrote current D8 at {bits:08b}"
            );
        }
        assert_eq!(environment.2.borrow().domain_code_slots.len(), 1022);
        assert_eq!(environment.2.borrow().legacy_code_slots.len(), 256);
        assert!(DomainCoordinate::new(10, 1024).is_none());
        assert!(DomainCoordinate::new(11, 0).is_none());
    }

    #[test]
    fn define_then_get_returns_the_value() {
        let root = Environment::root();
        root.define("x", Value::Number(1.0, Exactness::Exact));
        assert_eq!(root.get("x"), Some(Value::Number(1.0, Exactness::Exact)));
    }

    #[test]
    fn get_on_unknown_name_returns_none() {
        let root = Environment::root();
        assert_eq!(root.get("does-not-exist"), None);
    }

    #[test]
    fn dropping_a_very_deep_environment_chain_does_not_overflow_the_stack() {
        let mut current = Environment::root();
        for _ in 0..300_000 {
            current = current.child();
        }
        drop(current);
    }

    #[test]
    fn child_reads_bindings_from_its_parent() {
        let root = Environment::root();
        root.define("x", Value::Number(1.0, Exactness::Exact));
        let child = root.child();
        assert_eq!(child.get("x"), Some(Value::Number(1.0, Exactness::Exact)));
    }

    #[test]
    fn child_definitions_do_not_leak_into_the_parent() {
        let root = Environment::root();
        let child = root.child();
        child.define("local", Value::Number(2.0, Exactness::Exact));
        assert_eq!(root.get("local"), None);
    }

    #[test]
    fn reparent_changes_only_inherited_bindings_and_keeps_local_bindings() {
        let root = Environment::root();
        let first_parent = root.child();
        first_parent.define("surface", Value::Symbol(Rc::from("first")));
        let user = first_parent.child();
        user.define("mine", Value::Number(7.0, Exactness::Exact));

        let second_parent = root.child();
        second_parent.define("surface", Value::Symbol(Rc::from("second")));
        user.reparent(second_parent).expect("safe sibling reparent");

        assert_eq!(user.get("surface"), Some(Value::Symbol(Rc::from("second"))));
        assert_eq!(user.get("mine"), Some(Value::Number(7.0, Exactness::Exact)));
    }

    #[test]
    fn reparent_rejects_a_cycle() {
        let root = Environment::root();
        let child = root.child();
        assert!(root.reparent(child).is_err());
    }

    #[test]
    fn child_binding_shadows_the_parent_without_mutating_it() {
        let root = Environment::root();
        root.define("x", Value::Number(1.0, Exactness::Exact));
        let child = root.child();
        child.define("x", Value::Number(2.0, Exactness::Exact));
        assert_eq!(child.get("x"), Some(Value::Number(2.0, Exactness::Exact)));
        assert_eq!(root.get("x"), Some(Value::Number(1.0, Exactness::Exact)));
    }

    #[test]
    fn redefining_in_the_same_frame_overwrites_the_previous_value() {
        let root = Environment::root();
        root.define("x", Value::Number(1.0, Exactness::Exact));
        root.define("x", Value::Number(2.0, Exactness::Exact));
        assert_eq!(root.get("x"), Some(Value::Number(2.0, Exactness::Exact)));
    }

    /// Research-only #2402 countermodel.
    ///
    /// This deliberately lives inside the test module so no production SET/SETQ
    /// mechanism or language-visible mutation API is introduced. It walks the
    /// same Environment graph that closures capture and updates the nearest
    /// already-existing binding instead of constructing a shadow.
    fn update_nearest_existing_for_research(
        environment: &Environment,
        name: &str,
        value: Value,
    ) -> bool {
        let mut frame = Rc::clone(&environment.0);

        loop {
            let parent = {
                let mut current = frame.borrow_mut();

                if let Some(index) = current.slot_index(name) {
                    current.slots[index] = value;
                    return true;
                }

                if let Some(existing) = current.values.get_mut(name) {
                    *existing = value;
                    return true;
                }

                current.parent.as_ref().map(|parent| Rc::clone(&parent.0))
            };

            match parent {
                Some(parent) => frame = parent,
                None => return false,
            }
        }
    }

    #[test]
    fn nearest_existing_update_is_observably_different_from_child_define_shadowing() {
        let root = Environment::root();
        root.define("x", Value::Number(1.0, Exactness::Exact));

        // A closure captures exactly an Environment handle. The body is not
        // needed for this lower-bound witness: the observable under test is
        // which captured binding/location the closure would resolve.
        let observer = crate::Closure {
            parameters: Vec::new(),
            rest: None,
            body: Rc::from(Vec::<crate::syntax::Expr>::new()),
            environment: root.clone(),
            slot_names: Rc::from(Vec::<Rc<str>>::new()),
            pure: true,
            resolved: None,
        };

        let child = root.child();
        child.define("x", Value::Number(2.0, Exactness::Exact));

        assert_eq!(
            child.get("x"),
            Some(Value::Number(2.0, Exactness::Exact)),
            "D4 child DEFINE sees its new shadow"
        );
        assert_eq!(
            observer.environment.get("x"),
            Some(Value::Number(1.0, Exactness::Exact)),
            "a closure created before the child shadow still sees the parent location"
        );

        // Independent graph with the same initial shape, but the candidate
        // operation updates the nearest existing location instead of creating
        // a child binding.
        let root = Environment::root();
        root.define("x", Value::Number(1.0, Exactness::Exact));
        let observer = crate::Closure {
            parameters: Vec::new(),
            rest: None,
            body: Rc::from(Vec::<crate::syntax::Expr>::new()),
            environment: root.clone(),
            slot_names: Rc::from(Vec::<Rc<str>>::new()),
            pure: true,
            resolved: None,
        };
        let child = root.child();

        assert!(update_nearest_existing_for_research(
            &child,
            "x",
            Value::Number(2.0, Exactness::Exact)
        ));

        assert_eq!(
            child.get("x"),
            Some(Value::Number(2.0, Exactness::Exact)),
            "the caller sees NEW through inherited lookup"
        );
        assert_eq!(
            observer.environment.get("x"),
            Some(Value::Number(2.0, Exactness::Exact)),
            "the pre-existing closure sees NEW because the same parent location changed"
        );
        assert!(
            !child.0.borrow().values.contains_key("x"),
            "nearest-existing mutation must not create a child shadow"
        );
    }

    #[test]
    fn nearest_existing_update_chooses_the_nearest_location_in_a_deep_chain() {
        let root = Environment::root();
        root.define("x", Value::Number(1.0, Exactness::Exact));

        let middle = root.child();
        middle.define("x", Value::Number(2.0, Exactness::Exact));

        let leaf = middle.child();

        assert!(update_nearest_existing_for_research(
            &leaf,
            "x",
            Value::Number(3.0, Exactness::Exact)
        ));

        assert_eq!(leaf.get("x"), Some(Value::Number(3.0, Exactness::Exact)));
        assert_eq!(
            middle.get("x"),
            Some(Value::Number(3.0, Exactness::Exact)),
            "nearest existing middle location changed"
        );
        assert_eq!(
            root.get("x"),
            Some(Value::Number(1.0, Exactness::Exact)),
            "farther shadowed parent location is untouched"
        );
        assert!(
            !leaf.0.borrow().values.contains_key("x"),
            "no leaf binding is created"
        );
    }

    #[test]
    fn nearest_existing_update_fails_closed_when_no_binding_exists() {
        let root = Environment::root();
        let leaf = root.child().child();

        assert!(!update_nearest_existing_for_research(
            &leaf,
            "missing",
            Value::Number(9.0, Exactness::Exact)
        ));
        assert_eq!(leaf.get("missing"), None);
        assert_eq!(root.get("missing"), None);
    }

    #[test]
    fn host_policies_are_unrestricted_by_default_and_shared_with_children() {
        let root = Environment::root();
        assert!(root.fs_read_roots().is_none());
        assert!(root.fs_write_roots().is_none());
        assert!(root.is_tcp_connect_allowed("example.org", 443));
        assert!(root.is_tcp_listen_allowed("0.0.0.0", 9999));

        let root = root
            .with_fs_read_roots(vec![PathBuf::from("/safe/read")])
            .with_fs_write_roots(vec![PathBuf::from("/safe/write")])
            .with_tcp_connect_allowlist(vec![("127.0.0.1".into(), 8000, 9000)])
            .with_tcp_listen_allowlist(vec![("127.0.0.1".into(), 9999, 9999)]);
        let child = root.child();

        assert_eq!(
            child.fs_read_roots(),
            Some(vec![PathBuf::from("/safe/read")])
        );
        assert_eq!(
            child.fs_write_roots(),
            Some(vec![PathBuf::from("/safe/write")])
        );
        assert!(child.is_tcp_connect_allowed("127.0.0.1", 8080));
        assert!(!child.is_tcp_connect_allowed("example.org", 8080));
        assert!(child.is_tcp_listen_allowed("127.0.0.1", 9999));
        assert!(!child.is_tcp_listen_allowed("0.0.0.0", 9999));
    }

    /// РЕГРЕСІЯ НА ПЕРШОПРИЧИНУ (#5950): `arena_handles` ключується не
    /// голим `Rc::as_ptr`, а парою `(Weak<PairNode>, CellRef)`.
    ///
    /// Дефект, який це ловить: коли карта ключувалася голою адресою
    /// `Rc<PairNode>`, звільнений `Rc` віддавав свою адресу новій, нічим не
    /// пов'язаній парі — і наступний `cons` знаходив у карті застарілий запис
    /// та зшивав ребро на чужу комірку арени (`Edge::Cell`), замість того щоб
    /// лишити ту пару листовим `Edge::Atom`. Слабкий власник тримає саму
    /// алокацію `Rc<PairNode>` живучою, тож її адреса фізично не може бути
    /// перевикористана, доки запис існує.
    ///
    /// Тест **падає** на голому ключі: там `Rc::new` одразу віддає щойно
    /// звільнену адресу, `assert_ne!` про перевикористання не проходить, а
    /// `cons` зшиває хвіст на застарілу комірку (друге твердження).
    #[test]
    fn arena_cons_does_not_adopt_a_foreign_pair_that_reuses_a_freed_address() {
        let environment = Environment::root();
        assert!(
            environment.arena_cons_enabled(),
            "арена — типове подання cons"
        );

        // (1) Пара, народжена крізь шов арени: її адреса зареєстрована в
        //     `arena_handles`.
        let first = environment.arena_cons(Value::Symbol(Rc::from("a")), Value::Nil);
        let freed = match &first {
            Value::Pair(node) => Rc::as_ptr(node) as usize,
            other => panic!("cons мусив дати пару, а дав {other:?}"),
        };
        // (2) Прибрати всі сильні власники. За нового ключа слабкий запис
        //     лишається й закріплює адресу; за голого — адреса звільняється.
        drop(first);

        // Нічого не алокуємо між звільненням і новою парою, щоб на голому
        // ключі алокатор гарантовано повернув ту саму адресу.
        let foreign_head = Value::Symbol(Rc::from("b"));
        let foreign = Rc::new(crate::PairNode {
            head: foreign_head,
            tail: Value::Nil,
        });
        let reused = Rc::as_ptr(&foreign) as usize;

        // (3) `cons` із цією чужою парою як хвостом. За нового ключа вона не
        //     має жодного запису в карті, тож лишається листовим `Atom`.
        let second = environment.arena_cons(
            Value::Symbol(Rc::from("c")),
            Value::Pair(Rc::clone(&foreign)),
        );
        let Value::Pair(second_node) = &second else {
            panic!("cons мусив дати пару");
        };
        let Value::Pair(tail_node) = &second_node.tail else {
            panic!("хвіст мусив бути парою");
        };
        assert!(
            Rc::ptr_eq(tail_node, &foreign),
            "cons зшив ребро на чужий (застарілий) підграф замість листового Atom"
        );
        assert_eq!(second.to_string(), "(c b)");

        // (4) Корінь причини: адресу не перевикористано, бо слабкий власник
        //     тримає стару алокацію живучою.
        assert_ne!(
            reused, freed,
            "слабкий власник мусив закріпити адресу Rc<PairNode>"
        );
    }

    /// ОБМЕЖЕНІСТЬ ЗРОСТАННЯ (пункт 2): за довгої сесії `arena_handles` не
    /// росте безмежно.
    ///
    /// Кожен `cons` реєструє одну пару в карті; тут кожну пару одразу
    /// відпускають, тож записи стають мертвими. Без прибирання за порогом
    /// високої позначки карта переросла б `4 × підлога`; з прибиранням пік
    /// не перевищує підлоги. Живі записи (окремо перевірено) не чіпаються.
    #[test]
    fn arena_handles_stays_bounded_across_a_long_session() {
        let environment = Environment::root();
        let floor = ARENA_HANDLES_HWM_FLOOR;
        let mut peak = 0;
        for _ in 0..(floor * 4) {
            let value = environment.arena_cons(Value::Symbol(Rc::from("x")), Value::Nil);
            drop(value); // запис у карті стає мертвим одразу
            peak = peak.max(environment.arena_handles_len());
        }
        assert!(
            peak <= floor,
            "карта переросла поріг високої позначки: пік {peak} > {floor}"
        );
        assert!(
            environment.arena_handles_len() <= floor,
            "наприкінці сесії карта мусить лишатися обмеженою"
        );
    }
}
