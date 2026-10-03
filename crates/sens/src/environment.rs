use crate::{CoreDomainIdentity, Value};
use std::{cell::RefCell, collections::HashMap, path::PathBuf, rc::Rc};

/// Dropping a deeply nested `Environment` chain (thousands of `let`/currying
/// levels) would otherwise recurse through `Rc<RefCell<Frame>>`'s default
/// `Drop` one stack frame per level and could overflow the stack. `Environment`
/// has its own `Drop` below (mirroring `Value::Pair`'s iterative Drop in
/// `value.rs`) that walks the parent chain with an explicit worklist instead,
/// so this is fixed, not just documented as a live risk.
/// Session-wide print transcript plus a consumer cursor, so hot hosts
/// (REPL, LSP, swarm TCP) can take only the lines appended since their
/// last read instead of re-cloning the whole history per evaluation.
#[derive(Debug)]
pub struct Transcript {
    lines: Vec<String>,
    taken: usize,
}

#[derive(Clone, Debug)]
pub struct Environment(
    Rc<RefCell<Frame>>,
    Rc<RefCell<Transcript>>,
    Rc<RefCell<Limits>>,
);

#[derive(Debug)]
struct Frame {
    /// Кадр виклику замикання: параметри лежать у масиві `slots` за номером,
    /// імена — у `slot_names` (той самий порядок), тож пошук за іменем теж
    /// їх бачить. `None` — звичайний кадр без слотів (корінь, `child`).
    slot_names: Option<Rc<[Rc<str>]>>,
    slots: Vec<Value>,
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
            slots: Vec::new(),
            pure: false,
            values: HashMap::new(),
            parent,
        }
    }

    fn slot_index(&self, name: &str) -> Option<usize> {
        self.slot_names.as_ref()?.iter().position(|slot| **slot == *name)
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

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub(crate) enum CondClauseMode {
    #[default]
    CurrentMigration,
    Core2LegacyTwoPart,
}

#[derive(Debug, Default)]
struct Limits {
    selected_core_profile: Option<CoreProfile>,
    cond_clause_mode: CondClauseMode,
    cons_limit: Option<usize>,
    cons_count: usize,
    numeric_bit_limit: Option<usize>,
    /// Exact program-name policy. `None` = unrestricted, `Some([])` = deny all.
    process_allowlist: Option<Vec<String>>,
    /// Filesystem roots are stored as caller-supplied paths. The host layer,
    /// not the language core, owns canonicalization/symlink enforcement.
    fs_read_roots: Option<Vec<PathBuf>>,
    fs_write_roots: Option<Vec<PathBuf>>,
    /// (host-or-bind-address, first-port, last-port), inclusive.
    tcp_connect_allowlist: Option<Vec<(String, u16, u16)>>,
    tcp_listen_allowlist: Option<Vec<(String, u16, u16)>>,
    /// #1455: визначення мовою для кодів СЕНС без примітиву Rust. Слот коду
    /// заповнює перше визначення верхнього рівня з назвою з таблиці функцій;
    /// пізніше затінення назви слот не змінює.
    code_slots: HashMap<u8, Value>,
    /// Canonical language-owned definitions keyed by exact domain-qualified
    /// identity. Legacy byte slots stay separate during #2817 migration.
    domain_slots: HashMap<CoreDomainIdentity, Value>,
}

impl Environment {
    pub fn root() -> Self {
        let environment = Self(
            Rc::new(RefCell::new(Frame::empty(None))),
            Rc::new(RefCell::new(Transcript {
                lines: Vec::new(),
                taken: 0,
            })),
            Rc::new(RefCell::new(Limits::default())),
        );
        // `t` is the canonical truth value itself, not a variable that
        // merely holds one: bound to the symbol `t` (self-referential),
        // so `t` evaluates to `Symbol("t")` -- the exact value `eq`/`atom`
        // (Value::truth) already return for true.
        environment.define("t", Value::Symbol(Rc::from("t")));
        environment
    }

    /// Opts this session into a maximum `cons` allocation count — past it,
    /// `cons` returns `ErrorKind::OutOfMemory` instead of succeeding.
    pub fn with_cons_limit(self, limit: usize) -> Self {
        self.2.borrow_mut().cons_limit = Some(limit);
        self
    }

    /// Opts this session into a maximum bit width for exact arithmetic
    /// results — past it arithmetic returns `ErrorKind::NumericOverflow`.
    pub fn with_numeric_bit_limit(self, limit: usize) -> Self {
        self.2.borrow_mut().numeric_bit_limit = Some(limit);
        self
    }

    /// Restricts process execution to exact program names.
    pub fn with_process_allowlist(self, programs: Vec<String>) -> Self {
        self.2.borrow_mut().process_allowlist = Some(programs);
        self
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

    pub(crate) fn set_cond_clause_mode(&self, mode: CondClauseMode) {
        self.2.borrow_mut().cond_clause_mode = mode;
    }

    pub(crate) fn cond_clause_mode(&self) -> CondClauseMode {
        self.2.borrow().cond_clause_mode
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

    /// #1455: визначення мовою, прив'язане до коду СЕНС.
    pub(crate) fn code_slot(&self, sid: crate::Sens8) -> Option<Value> {
        self.2.borrow().code_slots.get(&sid.packed_byte()).cloned()
    }

    /// Прив'язує визначення до коду, лише якщо слот ще порожній.
    pub(crate) fn bind_code_slot_once(&self, sid: crate::Sens8, value: Value) -> bool {
        let mut limits = self.2.borrow_mut();
        if limits.code_slots.contains_key(&sid.packed_byte()) {
            return false;
        }
        limits.code_slots.insert(sid.packed_byte(), value);
        true
    }

    /// Canonical lookup by exact Core domain identity.
    pub fn domain_slot(&self, identity: CoreDomainIdentity) -> Option<Value> {
        self.2.borrow().domain_slots.get(&identity).cloned()
    }

    /// Bind one exact domain-qualified language identity once.
    pub fn bind_domain_slot_once(
        &self,
        identity: CoreDomainIdentity,
        value: Value,
    ) -> bool {
        let mut limits = self.2.borrow_mut();
        if limits.domain_slots.contains_key(&identity) {
            return false;
        }
        limits.domain_slots.insert(identity, value);
        true
    }

    /// A child frame is the future lexical boundary captured by a closure. It
    /// shares transcript and all session policy/limits with its parent.
    pub fn child(&self) -> Self {
        Self(
            Rc::new(RefCell::new(Frame::empty(Some(self.clone())))),
            self.1.clone(),
            self.2.clone(),
        )
    }

    /// Кадр виклику замикання: значення параметрів за номером слота.
    pub(crate) fn child_with_slots(&self, names: Rc<[Rc<str>]>, slots: Vec<Value>, pure: bool) -> Self {
        let mut frame = Frame::empty(Some(self.clone()));
        frame.slot_names = Some(names);
        frame.slots = slots;
        frame.pure = pure;
        Self(Rc::new(RefCell::new(frame)), self.1.clone(), self.2.clone())
    }

    /// Значення `Local(depth, index)`: слот `index` кадру на `depth` кроків вище.
    pub(crate) fn get_local(&self, depth: u32, index: u32) -> Option<Value> {
        let mut frame = Rc::clone(&self.0);
        for _ in 0..depth {
            let parent = frame.borrow().parent.as_ref().map(|parent| Rc::clone(&parent.0))?;
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
                let Some(names) = &current.slot_names else { break };
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
    /// Відхиляє цикли та parent з іншими transcript/limits.
    pub fn reparent(&self, parent: Environment) -> Result<(), &'static str> {
        if !Rc::ptr_eq(&self.1, &parent.1) || !Rc::ptr_eq(&self.2, &parent.2) {
            return Err("new parent must share transcript and limits");
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
        self.1.borrow_mut().lines.push(line);
    }

    pub fn output_snapshot(&self) -> Vec<String> {
        self.1.borrow().lines.clone()
    }

    pub fn output_take_new(&self) -> Vec<String> {
        let mut transcript = self.1.borrow_mut();
        let new = transcript.lines[transcript.taken..].to_vec();
        transcript.taken = transcript.lines.len();
        new
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
            let slots = f.slot_names.iter().flat_map(|names| names.iter().zip(f.slots.iter()));
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

#[derive(Clone, Debug)]
pub struct Session {
    pub environment: Environment,
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
    use super::*;
    use crate::Exactness;

    #[test]
    fn root_predefines_t_as_the_self_evaluating_truth_symbol() {
        let root = Environment::root();
        assert_eq!(root.get("t"), Some(Value::Symbol(Rc::from("t"))));
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
}
