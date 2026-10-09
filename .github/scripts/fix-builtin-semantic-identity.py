from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"expected patch anchor not found in {path}: {old[:80]!r}")
    p.write_text(text.replace(old, new, 1))


replace_once(
    "crates/my-lisp/src/value.rs",
    """pub struct Builtin {
    pub name: &'static str,
    #[allow(clippy::type_complexity)]
    pub func: std::rc::Rc<
        dyn Fn(&[Value], &crate::Environment, crate::Span) -> Result<Value, crate::LanguageError>,
    >,
}
""",
    """pub struct Builtin {
    pub name: &'static str,
    semantic_id: Option<&'static str>,
    #[allow(clippy::type_complexity)]
    pub func: std::rc::Rc<
        dyn Fn(&[Value], &crate::Environment, crate::Span) -> Result<Value, crate::LanguageError>,
    >,
}

impl Builtin {
    pub(crate) fn local(
        name: &'static str,
        func: std::rc::Rc<
            dyn Fn(&[Value], &crate::Environment, crate::Span) -> Result<Value, crate::LanguageError>,
        >,
    ) -> Self {
        Self {
            name,
            semantic_id: None,
            func,
        }
    }

    pub(crate) fn semantic(
        name: &'static str,
        semantic_id: &'static str,
        func: std::rc::Rc<
            dyn Fn(&[Value], &crate::Environment, crate::Span) -> Result<Value, crate::LanguageError>,
        >,
    ) -> Self {
        assert_eq!(
            crate::semantic_registry::semantic_id_for_surface(semantic_id),
            Some(semantic_id),
            "registered builtin semantic identity must exist in semantic-registry.wsm: {semantic_id}"
        );
        Self {
            name,
            semantic_id: Some(semantic_id),
            func,
        }
    }

    pub fn semantic_id(&self) -> Option<&'static str> {
        self.semantic_id
    }

    fn same_semantic_identity(&self, other: &Self) -> bool {
        matches!(
            (self.semantic_id, other.semantic_id),
            (Some(left), Some(right)) if left == right
        )
    }
}
""",
)

replace_once(
    "crates/my-lisp/src/value.rs",
    """            (Value::NumericBuffer(left), Value::NumericBuffer(right)) => left == right,
            // Functions have identity: two separately created closures are not equal.
""",
    """            (Value::NumericBuffer(left), Value::NumericBuffer(right)) => left == right,
            // Registered builtins are language operations, not allocation handles.
            // Their semantic ID is the identity key; diagnostic/display spelling and
            // `Rc` allocation are implementation details. Unregistered local builtins
            // deliberately have no semantic identity and therefore do not compare equal.
            (Value::Builtin(left), Value::Builtin(right)) => left.same_semantic_identity(right),
            // Functions have identity: two separately created closures are not equal.
""",
)

replace_once(
    "crates/my-lisp/src/value.rs",
    """impl Value {
    pub fn vector(values: impl IntoIterator<Item = Value>) -> Self {
""",
    """impl Value {
    /// Opaque numeric semantic identity for a registered builtin operation.
    /// Human spelling and runtime allocation are intentionally not identity.
    pub fn builtin_semantic_id(&self) -> Option<&'static str> {
        match self {
            Value::Builtin(builtin) => builtin.semantic_id(),
            _ => None,
        }
    }

    /// True only when both values are registered builtins carrying the same
    /// numeric semantic ID. Missing IDs fail closed rather than falling back
    /// to display spelling or pointer equality.
    pub fn same_builtin_semantic_identity(&self, other: &Self) -> bool {
        match (self, other) {
            (Value::Builtin(left), Value::Builtin(right)) => left.same_semantic_identity(right),
            _ => false,
        }
    }

    pub fn vector(values: impl IntoIterator<Item = Value>) -> Self {
""",
)

p = Path("crates/my-lisp/src/value.rs")
text = p.read_text()
marker = "\nimpl Drop for Value {"
tests = r'''

#[cfg(test)]
mod builtin_semantic_identity_tests {
    use super::*;

    fn function() -> std::rc::Rc<
        dyn Fn(&[Value], &crate::Environment, crate::Span) -> Result<Value, crate::LanguageError>,
    > {
        std::rc::Rc::new(|_arguments, _environment, _span| Ok(Value::Nil))
    }

    #[test]
    fn semantic_identity_survives_distinct_allocations_and_diagnostic_names() {
        let left_builtin =
            std::rc::Rc::new(Builtin::semantic("left-display", "0104", function()));
        let right_builtin =
            std::rc::Rc::new(Builtin::semantic("right-display", "0104", function()));
        assert!(!std::rc::Rc::ptr_eq(&left_builtin, &right_builtin));

        let left = Value::Builtin(left_builtin);
        let right = Value::Builtin(right_builtin);
        assert_eq!(left.builtin_semantic_id(), Some("0104"));
        assert_eq!(right.builtin_semantic_id(), Some("0104"));
        assert!(left.same_builtin_semantic_identity(&right));
        assert_eq!(left, right);
    }

    #[test]
    fn distinct_semantic_ids_never_collapse() {
        let add = Value::Builtin(std::rc::Rc::new(Builtin::semantic(
            "+", "0104", function(),
        )));
        let subtract = Value::Builtin(std::rc::Rc::new(Builtin::semantic(
            "-", "1001", function(),
        )));
        assert!(!add.same_builtin_semantic_identity(&subtract));
        assert_ne!(add, subtract);
    }

    #[test]
    fn local_builtin_without_semantic_id_fails_closed_for_semantic_identity() {
        let shared = std::rc::Rc::new(Builtin::local("local-helper", function()));
        let left = Value::Builtin(shared.clone());
        let right = Value::Builtin(shared);
        assert_eq!(left.builtin_semantic_id(), None);
        assert!(!left.same_builtin_semantic_identity(&right));
        assert_ne!(left, right);
    }

    #[test]
    #[should_panic(expected = "registered builtin semantic identity must exist")]
    fn unknown_semantic_id_is_rejected_at_construction() {
        let _ = Builtin::semantic("ghost", "not-a-semantic-id", function());
    }
}
'''
if "mod builtin_semantic_identity_tests" not in text:
    if marker not in text:
        raise SystemExit("Value Drop anchor missing")
    p.write_text(text.replace(marker, tests + marker, 1))

replace_once(
    "crates/my-lisp/src/eval/builtins.rs",
    """fn builtin(name: &'static str, func: Native) -> Value {
    Value::Builtin(std::rc::Rc::new(crate::value::Builtin { name, func }))
}

fn define_peer_builtin(
    environment: &Environment,
    diagnostic_name: &'static str,
    semantic_id: &str,
    func: Native,
) {
""",
    """fn builtin(name: &'static str, func: Native) -> Value {
    Value::Builtin(std::rc::Rc::new(crate::value::Builtin::local(name, func)))
}

fn semantic_builtin(
    diagnostic_name: &'static str,
    semantic_id: &'static str,
    func: Native,
) -> Value {
    Value::Builtin(std::rc::Rc::new(crate::value::Builtin::semantic(
        diagnostic_name,
        semantic_id,
        func,
    )))
}

fn define_peer_builtin(
    environment: &Environment,
    diagnostic_name: &'static str,
    semantic_id: &'static str,
    func: Native,
) {
""",
)
replace_once(
    "crates/my-lisp/src/eval/builtins.rs",
    """    let value = builtin(diagnostic_name, func);
    for name in names {
""",
    """    let value = semantic_builtin(diagnostic_name, semantic_id, func);
    for name in names {
""",
)

replace_once(
    "crates/my-lisp/src/eval/canon.rs",
    """fn builtin(
    identity: &'static str,
    func: impl Fn(&[Value], &Environment, Span) -> Result<Value, LanguageError> + 'static,
) -> Value {
    Value::Builtin(Rc::new(crate::value::Builtin {
        name: identity,
        func: Rc::new(func),
    }))
}
""",
    """fn builtin(
    identity: &'static str,
    semantic_id: &'static str,
    func: impl Fn(&[Value], &Environment, Span) -> Result<Value, LanguageError> + 'static,
) -> Value {
    Value::Builtin(Rc::new(crate::value::Builtin::semantic(
        identity,
        semantic_id,
        Rc::new(func),
    )))
}
""",
)
canon = Path("crates/my-lisp/src/eval/canon.rs")
text = canon.read_text()
for name, sid in [
    ("PRIM_ATOM", "ATOM_SEMANTIC_ID"),
    ("PRIM_EQ", "EQ_SEMANTIC_ID"),
    ("PRIM_CONS", "CONS_SEMANTIC_ID"),
    ("PRIM_CAR", "CAR_SEMANTIC_ID"),
    ("PRIM_CDR", "CDR_SEMANTIC_ID"),
]:
    old = f'Some(builtin("{name}", |'
    new = f'Some(builtin("{name}", {sid}, |'
    if new not in text:
        if old not in text:
            raise SystemExit(f"Canon builtin anchor missing for {name}")
        text = text.replace(old, new, 1)
canon.write_text(text)

replace_once(
    "crates/my-lisp/src/eval/macro_substrate.rs",
    """        Value::Builtin(Rc::new(Builtin {
            name: "make-macro",
            func: Rc::new(make_macro_values),
        })),
""",
    """        Value::Builtin(Rc::new(Builtin::local(
            "make-macro",
            Rc::new(make_macro_values),
        ))),
""",
)

replace_once(
    "crates/my-lisp/tests/peer_surface_identity.rs",
    """fn assert_same_builtin(left: &Value, right: &Value) {
    match (left, right) {
        (Value::Builtin(left), Value::Builtin(right)) => assert!(Rc::ptr_eq(left, right)),
        other => panic!("expected two builtin values, got {other:?}"),
    }
}
""",
    """fn assert_same_builtin(semantic_id: &str, left: &Value, right: &Value) {
    assert_eq!(left.builtin_semantic_id(), Some(semantic_id));
    assert_eq!(right.builtin_semantic_id(), Some(semantic_id));
    assert!(left.same_builtin_semantic_identity(right));
    match (left, right) {
        // Allocation sharing is a useful implementation invariant, but not the
        // language-level identity proof; the numeric ID above is authoritative.
        (Value::Builtin(left), Value::Builtin(right)) => assert!(Rc::ptr_eq(left, right)),
        other => panic!("expected two builtin values, got {other:?}"),
    }
}
""",
)
p = Path("crates/my-lisp/tests/peer_surface_identity.rs")
text = p.read_text()
text = text.replace(
    "assert_same_builtin(&uk, &sym);", 'assert_same_builtin("0104", &uk, &sym);'
)
text = text.replace(
    "assert_same_builtin(&sym, &sa);", 'assert_same_builtin("0104", &sym, &sa);'
)
p.write_text(text)

replace_once(
    "crates/my-lisp/tests/runtime_peer_operators.rs",
    """fn assert_same_builtin(left: &Value, right: &Value) {
    match (left, right) {
        (Value::Builtin(left), Value::Builtin(right)) => assert!(
            Rc::ptr_eq(left, right),
            "peer spellings must point to one builtin allocation"
        ),
        other => panic!("expected builtin peer values, got {other:?}"),
    }
}
""",
    """fn assert_same_builtin(semantic_id: &str, left: &Value, right: &Value) {
    assert_eq!(left.builtin_semantic_id(), Some(semantic_id));
    assert_eq!(right.builtin_semantic_id(), Some(semantic_id));
    assert!(left.same_builtin_semantic_identity(right));
    match (left, right) {
        (Value::Builtin(left), Value::Builtin(right)) => assert!(
            Rc::ptr_eq(left, right),
            "peer spellings should still share one implementation allocation"
        ),
        other => panic!("expected builtin peer values, got {other:?}"),
    }
}
""",
)
p = Path("crates/my-lisp/tests/runtime_peer_operators.rs")
text = p.read_text()
text = text.replace(
    "assert_same_builtin(&uk, &sa);", "assert_same_builtin(case.identity, &uk, &sa);"
)
text = text.replace(
    "assert_same_builtin(&sa, &sym);", "assert_same_builtin(case.identity, &sa, &sym);"
)
p.write_text(text)

p = Path("crates/my-lisp/src/eval/canon.rs")
text = p.read_text()
old = """        let numeric = value_for_surface(CAR_SEMANTIC_ID).expect("numeric Canon identity");
        let human = value_for_surface("car").expect("historical Canon surface");
        let (Value::Builtin(numeric), Value::Builtin(human)) = (&numeric, &human) else {
"""
new = """        let numeric = value_for_surface(CAR_SEMANTIC_ID).expect("numeric Canon identity");
        let human = value_for_surface("car").expect("historical Canon surface");
        assert_eq!(numeric.builtin_semantic_id(), Some(CAR_SEMANTIC_ID));
        assert_eq!(human.builtin_semantic_id(), Some(CAR_SEMANTIC_ID));
        assert!(numeric.same_builtin_semantic_identity(&human));
        let (Value::Builtin(numeric), Value::Builtin(human)) = (&numeric, &human) else {
"""
if new not in text:
    if old not in text:
        raise SystemExit("Canon numeric identity test anchor missing")
    text = text.replace(old, new, 1)
old = """        let sanskrit = value_for_surface("ādi").expect("Sanskrit Canon value");
        let (Value::Builtin(historical), Value::Builtin(ukrainian), Value::Builtin(sanskrit)) =
"""
new = """        let sanskrit = value_for_surface("ādi").expect("Sanskrit Canon value");
        for value in [&historical, &ukrainian, &sanskrit] {
            assert_eq!(value.builtin_semantic_id(), Some(CAR_SEMANTIC_ID));
            assert!(historical.same_builtin_semantic_identity(value));
        }
        let (Value::Builtin(historical), Value::Builtin(ukrainian), Value::Builtin(sanskrit)) =
"""
if new not in text:
    if old not in text:
        raise SystemExit("Canon peer identity test anchor missing")
    text = text.replace(old, new, 1)
p.write_text(text)

replace_once(
    "crates/my-lisp/tests/uk_surface_equivalence.rs",
    """        // A builtin is an operation handle. Canon EN/UK/SA spellings and
        // ordinary aliases must retain one allocation, not merely similar code.
        (Value::Builtin(left), Value::Builtin(right)) => Rc::ptr_eq(left, right),
""",
    """        // This broad legacy-coverage check keeps allocation sharing as an
        // implementation invariant. Numeric semantic identity is proved separately
        // by the focused Canon/peer-ID tests and must not be inferred from `Rc`.
        (Value::Builtin(left), Value::Builtin(right)) => Rc::ptr_eq(left, right),
""",
)

test = Path("crates/my-lisp/tests/builtin_semantic_identity.rs")
expected = r'''use my_lisp::{eval_program, Session, Value};

fn value(session: &mut Session, source: &str) -> Value {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("{source}: {error:?}"))
        .value
}

fn assert_identity(session: &mut Session, semantic_id: &str, names: &[&str]) {
    let values = names
        .iter()
        .map(|name| value(session, name))
        .collect::<Vec<_>>();
    for item in &values {
        assert_eq!(item.builtin_semantic_id(), Some(semantic_id), "{names:?}");
        assert!(values[0].same_builtin_semantic_identity(item), "{names:?}");
    }
}

#[test]
fn canon_peer_spellings_are_one_numeric_builtin_identity() {
    let mut session = Session::default();
    assert_identity(&mut session, "0005", &["car", "перше", "ādi", ":п"]);
}

#[test]
fn ordinary_peer_spellings_are_one_numeric_builtin_identity() {
    let mut session = Session::default();
    assert_identity(&mut session, "0104", &["+", "додати", "yoga"]);
}

#[test]
fn eq_observes_registered_builtin_semantic_identity_not_spelling() {
    let mut session = Session::default();
    for source in [
        "(eq car перше)",
        "(eq перше ādi)",
        "(eq додати +)",
        "(eq + yoga)",
    ] {
        assert_eq!(value(&mut session, source).to_string(), "t", "{source}");
    }
    assert_eq!(value(&mut session, "(eq + -)").to_string(), "()");
}
'''
if test.exists():
    if test.read_text() != expected:
        raise SystemExit("builtin_semantic_identity.rs exists with unexpected content")
else:
    test.write_text(expected)

replace_once(
    "docs/PLAN-FULL-LANGUAGE-PARITY.md",
    """4. **Одна тотожність — одна реалізація значення.** Для ordinary builtin це
   означає один `Value::Builtin`; для Lisp-defined public value — один
   створений closure/value, до якого прямо прив'язуються всі surface names.
""",
    """4. **Одна тотожність — один numeric semantic ID.** Для ordinary builtin
   усі peer spellings несуть той самий ID. Спільний `Value::Builtin`/`Rc` може
   лишатися корисним implementation invariant, але адреса алокації не є
   мовною тотожністю. Для Lisp-defined public value діє той самий принцип:
   surface names не створюють нової semantic identity.
""",
)
replace_once(
    "docs/PLAN-FULL-LANGUAGE-PARITY.md",
    """**Gate B:** `Rc::ptr_eq` або еквівалентний identity proof для всіх builtin peer
spellings.
""",
    """**Gate B:** усі builtin peer spellings мають той самий numeric semantic ID;
різні ID ніколи не зливаються; відсутній/невідомий ID fail-closed. `Rc::ptr_eq`
дозволений лише як додатковий implementation-sharing check, не як semantic proof.
""",
)
