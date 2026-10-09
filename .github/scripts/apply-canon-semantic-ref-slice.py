from pathlib import Path
import re


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"missing patch anchor in {path}: {old[:100]!r}")
    p.write_text(text.replace(old, new, 1))


def regex_once(path: str, pattern: str, replacement: str) -> None:
    p = Path(path)
    text = p.read_text()
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"expected exactly one regex match in {path}, got {count}: {pattern[:100]!r}")
    p.write_text(updated)


# 1. Runtime value: semantic identity becomes a first-class value distinct
# from a Rust implementation closure/pointer.
replace_once(
    "crates/my-lisp/src/value.rs",
    """    Closure(Rc<Closure>),
    Macro(Rc<Closure>),
    /// Primitive operation as a first-class value (contract 2.1).
    Builtin(std::rc::Rc<Builtin>),
""",
    """    Closure(Rc<Closure>),
    Macro(Rc<Closure>),
    /// Opaque numeric semantic identity as a first-class callable value.
    ///
    /// This is deliberately not an implementation pointer: a semantic ID
    /// survives replacement of the execution projection (Rust today;
    /// Lisp/CML/WASM/FPGA later). The first vertical slice uses this for
    /// Canon value-primitives; ordinary legacy host builtins remain below
    /// until migrated independently.
    SemanticRef(&'static str),
    /// Legacy host implementation closure as a first-class value (contract 2.1).
    /// This is an implementation projection, never the language identity key.
    Builtin(std::rc::Rc<Builtin>),
""",
)
replace_once(
    "crates/my-lisp/src/value.rs",
    """            (Value::NumericBuffer(left), Value::NumericBuffer(right)) => left == right,
            // Functions have identity: two separately created closures are not equal.
""",
    """            (Value::NumericBuffer(left), Value::NumericBuffer(right)) => left == right,
            // Semantic references compare by the language-owned numeric identity,
            // never by an implementation allocation or diagnostic spelling.
            (Value::SemanticRef(left), Value::SemanticRef(right)) => left == right,
            // Functions have identity: two separately created closures are not equal.
""",
)
replace_once(
    "crates/my-lisp/src/value.rs",
    """    match value {
        Value::Builtin(builtin) => format!(\"#<builtin {}>\", builtin.name),
""",
    """    match value {
        Value::SemanticRef(semantic_id) => format!(\"#<semantic {semantic_id}>\"),
        Value::Builtin(builtin) => format!(\"#<builtin {}>\", builtin.name),
""",
)

# 2. Canon: stop materializing Rc<Builtin>. Canon surface spellings now yield
# the semantic reference itself; invocation resolves ID -> Rust projection.
p = Path("crates/my-lisp/src/eval/canon.rs")
text = p.read_text().replace("use std::{collections::HashMap, rc::Rc};\n", "")
p.write_text(text)
regex_once(
    "crates/my-lisp/src/eval/canon.rs",
    r"fn builtin\(.*?pub\(crate\) fn value_for_surface\(name: &str\) -> Option<Value> \{\n    identity_for_surface\(name\)\.and_then\(value\)\n\}\n",
    r'''fn semantic_id_for_identity(identity: CanonicalIdentity) -> Option<&'static str> {
    CANON
        .iter()
        .find(|entry| entry.identity == identity)
        .and_then(|entry| entry.semantic_id)
}

/// Invoke the current implementation projection for a semantic value.
///
/// The semantic ID is the language identity. This function is only the
/// execution bridge from that identity to today's Rust implementation; a
/// future backend can replace this projection without changing Value identity.
pub(crate) fn invoke_semantic_ref(
    semantic_id: &str,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    let Some(identity) = identity_for_semantic_id(semantic_id) else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            format!("unknown semantic callable identity: {semantic_id}"),
            span,
        ));
    };

    match identity {
        CanonicalIdentity::Atom => {
            exact_args("PRIM_ATOM", args, 1, span)?;
            Ok(Value::truth(args[0].is_atom()))
        }
        CanonicalIdentity::Eq => {
            exact_args("PRIM_EQ", args, 2, span)?;
            eq_values(args[0].clone(), args[1].clone(), span)
        }
        CanonicalIdentity::Cons => {
            exact_args("PRIM_CONS", args, 2, span)?;
            cons_values(args[0].clone(), args[1].clone(), environment, span)
        }
        CanonicalIdentity::Car => {
            exact_args("PRIM_CAR", args, 1, span)?;
            car_value(&args[0], span)
        }
        CanonicalIdentity::Cdr => {
            exact_args("PRIM_CDR", args, 1, span)?;
            cdr_value(&args[0], span)
        }
        CanonicalIdentity::EmptyList | CanonicalIdentity::Quote | CanonicalIdentity::Cond => {
            Err(LanguageError::new(
                ErrorKind::Type,
                format!("semantic identity is not a callable value: {semantic_id}"),
                span,
            ))
        }
    }
}

/// Return the first-class semantic value for a canonical identity. Special
/// forms deliberately have no value representation; they remain syntax-only.
pub(crate) fn value(identity: CanonicalIdentity) -> Option<Value> {
    match identity {
        CanonicalIdentity::EmptyList => Some(Value::Nil),
        CanonicalIdentity::Atom
        | CanonicalIdentity::Eq
        | CanonicalIdentity::Cons
        | CanonicalIdentity::Car
        | CanonicalIdentity::Cdr => semantic_id_for_identity(identity).map(Value::SemanticRef),
        CanonicalIdentity::Quote | CanonicalIdentity::Cond => None,
    }
}

pub(crate) fn value_for_surface(name: &str) -> Option<Value> {
    identity_for_surface(name).and_then(value)
}
''',
)
regex_once(
    "crates/my-lisp/src/eval/canon.rs",
    r'''    #\[test\]\n    fn numeric_canon_identity_uses_the_same_evaluator_meaning\(\) \{.*?\n    \}\n\n    #\[test\]\n    fn three_callable_surfaces_share_one_stable_handle\(\) \{.*?\n    \}\n''',
    r'''    #[test]
    fn numeric_canon_identity_is_the_runtime_value_identity() {
        assert_eq!(
            identity_for_surface(CAR_SEMANTIC_ID),
            Some(CanonicalIdentity::Car)
        );
        let numeric = value_for_surface(CAR_SEMANTIC_ID).expect("numeric Canon identity");
        let human = value_for_surface("car").expect("historical Canon surface");
        assert_eq!(numeric, Value::SemanticRef(CAR_SEMANTIC_ID));
        assert_eq!(human, Value::SemanticRef(CAR_SEMANTIC_ID));
        assert_eq!(numeric, human);
    }

    #[test]
    fn callable_surfaces_materialize_the_same_semantic_reference() {
        let historical = value_for_surface("car").expect("historical Canon value");
        let ukrainian = value_for_surface("перше").expect("Ukrainian Canon value");
        let sanskrit = value_for_surface("ādi").expect("Sanskrit Canon value");
        let symbolic = value_for_surface(":п").expect("symbolic Canon value");
        for value in [&historical, &ukrainian, &sanskrit, &symbolic] {
            assert_eq!(*value, Value::SemanticRef(CAR_SEMANTIC_ID));
        }
    }
''',
)

# 3. Generic invocation: SemanticRef resolves through Canon, while legacy
# Builtin still executes its host projection directly.
replace_once(
    "crates/my-lisp/src/eval/mod.rs",
    """    match function {
        Value::Builtin(builtin) => (builtin.func)(arguments, environment, span),
        Value::Closure(closure) => closures::apply_values(closure.clone(), arguments, span),
""",
    """    match function {
        Value::SemanticRef(semantic_id) => {
            canon::invoke_semantic_ref(semantic_id, arguments, environment, span)
        }
        Value::Builtin(builtin) => (builtin.func)(arguments, environment, span),
        Value::Closure(closure) => closures::apply_values(closure.clone(), arguments, span),
""",
)
replace_once(
    "crates/my-lisp/src/eval/mod.rs",
    """            let function = evaluate(&items[0], environment)?;
            match &function {
                Value::Builtin(builtin) => {
                    let mut values = Vec::with_capacity(arguments.len());
                    for argument in arguments {
                        values.push(evaluate(argument, environment)?);
                    }
                    (builtin.func)(&values, environment, span).map(EvalStep::Value)
                }
""",
    """            let function = evaluate(&items[0], environment)?;
            match &function {
                Value::SemanticRef(semantic_id) => {
                    let mut values = Vec::with_capacity(arguments.len());
                    for argument in arguments {
                        values.push(evaluate(argument, environment)?);
                    }
                    canon::invoke_semantic_ref(semantic_id, &values, environment, span)
                        .map(EvalStep::Value)
                }
                Value::Builtin(builtin) => {
                    let mut values = Vec::with_capacity(arguments.len());
                    for argument in arguments {
                        values.push(evaluate(argument, environment)?);
                    }
                    (builtin.func)(&values, environment, span).map(EvalStep::Value)
                }
""",
)

# 4. Semantic callable values are values, not source syntax.
replace_once(
    "crates/my-lisp/src/eval/closures.rs",
    """        Value::String(val) => ExprKind::String(val.clone()),
        // A builtin is callable but not syntax: it cannot round-trip
""",
    """        Value::String(val) => ExprKind::String(val.clone()),
        Value::SemanticRef(semantic_id) => {
            return Err(LanguageError::new(
                ErrorKind::Type,
                format!(\"a semantic callable ({semantic_id}) is not executable code\"),
                span,
            ));
        }
        // A builtin is callable but not syntax: it cannot round-trip
""",
)

# 5. Memory-layout boundary: portable primitive payload is the semantic ID,
# while a legacy host Builtin pointer gets an explicitly non-portable tag.
replace_once(
    "crates/my-lisp/src/layout.rs",
    """pub const TAG_NUMERIC_BUFFER: u64 = 13;
""",
    """pub const TAG_NUMERIC_BUFFER: u64 = 13;
/// Host-only legacy builtin implementation pointer. Never portable identity.
pub const TAG_HOST_BUILTIN: u64 = 14;
""",
)
replace_once(
    "crates/my-lisp/src/layout.rs",
    """            // TAG_PRIMITIVE was reserved in the memory-layout contract
            // from day one -- contract 2.1 finally fills it.
            Value::Builtin(b) => {
                let ptr = Rc::as_ptr(b) as u64;
                NanBox(Self::pack_ptr(TAG_PRIMITIVE, ptr))
            }
""",
    """            // Portable primitive identity: the payload is the numeric
            // semantic ID, not an address in this Rust process.
            Value::SemanticRef(semantic_id) => {
                let payload = semantic_id
                    .parse::<u64>()
                    .expect(\"semantic registry IDs must be numeric\");
                assert!(payload <= 0x0FFF_FFFF, \"semantic ID exceeds NaN-box payload\");
                NanBox(MASK_QNAN | (TAG_PRIMITIVE << 28) | payload)
            }
            // Legacy host-only implementation projection. Kept distinct from
            // TAG_PRIMITIVE so a pointer can never masquerade as portable
            // semantic identity at the layout boundary.
            Value::Builtin(b) => {
                let ptr = Rc::as_ptr(b) as u64;
                NanBox(Self::pack_ptr(TAG_HOST_BUILTIN, ptr))
            }
""",
)
p = Path("crates/my-lisp/src/layout.rs")
text = p.read_text()
if "semantic_ref_nanbox_payload_is_the_numeric_identity" not in text:
    text += r'''

#[cfg(test)]
mod semantic_ref_layout_tests {
    use super::*;

    #[test]
    fn semantic_ref_nanbox_payload_is_the_numeric_identity() {
        let bits = NanBox::from_value(&Value::SemanticRef("0005")).0;
        assert_eq!((bits >> 28) & 0xF, TAG_PRIMITIVE);
        assert_eq!(bits & 0x0FFF_FFFF, 5);
    }
}
'''
    p.write_text(text)

# 6. Presentation is intentionally representation-neutral: expose the ID,
# not a Rust diagnostic builtin name.
replace_once(
    "crates/my-lisp/src/presentation.rs",
    """fn render_uk(value: &Value) -> String {
    match value {
        Value::Builtin(builtin) => {
""",
    """fn render_uk(value: &Value) -> String {
    match value {
        Value::SemanticRef(semantic_id) => {
            format!(\"#<семантична-операція {semantic_id}>\")
        }
        Value::Builtin(builtin) => {
""",
)

# 7. Lisp owns the observable semantic proof. Extend the existing generic
# peer-identity acceptance program instead of encoding language truth in Rust.
p = Path("lib/surface/peer-identity-acceptance.my")
text = p.read_text()
text = text.replace(
    """;; Proves that a Ukrainian peer spelling and its English counterpart
;; share exact identity (Rc::ptr_eq for closures/builtins under `eq`),
;; not merely equal behavior through a re-implementation or translation
""",
    """;; Proves that peer spellings share language identity under `eq`, not
;; merely equal behavior through a re-implementation or translation.
;; For Canon callables that identity is the numeric semantic ID; no Rust
;; allocation or pointer is part of the acceptance criterion.
""",
)
anchor = """      ((хибне? (тотожне? найбільше-у-списку max-list)) (як-є помилка-найбільше-у-списку-max-list))
      ((тотожне? 1 1) (як-є успіх)))))
"""
replacement = """      ((хибне? (тотожне? найбільше-у-списку max-list)) (як-є помилка-найбільше-у-списку-max-list))
      ;; Canon callable peers must be identical because they resolve to one
      ;; numeric semantic ID (car/перше/ādi/:п -> 0005), not one Rc pointer.
      ((хибне? (тотожне? car перше)) (як-є помилка-car-перше))
      ((хибне? (тотожне? car ādi)) (як-є помилка-car-adi))
      ((хибне? (тотожне? car :п)) (як-є помилка-car-symbolic))
      ((тотожне? car cdr) (як-є помилка-car-cdr-злилися))
      ((тотожне? 1 1) (як-є успіх)))))
"""
if replacement not in text:
    if anchor not in text:
        raise SystemExit("peer identity acceptance anchor missing")
    text = text.replace(anchor, replacement, 1)
p.write_text(text)

# 8. Record the implemented first slice in the migration map so the research
# document cannot remain stale after the representation actually changes.
p = Path("docs/BUILTIN-IDENTITY-MIGRATION-MAP-2026-09-11.md")
text = p.read_text()
marker = "# `Value::Builtin` identity migration map (research, not implementation)\n"
status = r'''# `Value::Builtin` identity migration map

> **Implementation status — first slice:** Canon value-primitives now use
> `Value::SemanticRef(numeric-id)` and resolve that ID to the current Rust
> implementation at apply time. Ordinary non-Canon `Value::Builtin` values
> remain a legacy implementation projection for later slices. At the NaN-box
> boundary `TAG_PRIMITIVE` carries the numeric semantic ID; legacy host builtin
> pointers use a separate non-portable tag.
'''
if text.startswith(marker):
    text = status + text[len(marker):]
elif not text.startswith("# `Value::Builtin` identity migration map\n"):
    raise SystemExit("migration map heading changed unexpectedly")
p.write_text(text)
