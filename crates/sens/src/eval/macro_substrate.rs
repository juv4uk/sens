use crate::value::Builtin;
use crate::{Environment, ErrorKind, LanguageError, Span, Value};
use std::rc::Rc;

/// Install the narrow bootstrap mechanism that turns an evaluated closure
/// into a macro value. `defmacro` itself remains language-owned in
/// `lib/macro.lisp`; this binding only supplies Closure -> Macro materialization.
pub(crate) fn install(environment: &Environment) {
    // Ratified D5:00011 (not an historical byte) owns this mechanism.
    let identity = crate::semantic_registry::domain_identity_for_surface("макрос")
        .expect("ратифікована голова D5 макрос");
    assert!(
        matches!(identity, crate::CoreDomainIdentity::D5(_)),
        "макрос має належати саме D5"
    );

    let mechanism = Value::Builtin(Rc::new(Builtin {
        name: "макрос",
        func: Rc::new(materialize_macro_value),
    }));
    assert!(
        environment.bind_domain_code_slot_once(identity, mechanism.clone()),
        "єдиний механізм макроса не можна затінювати"
    );

    // Механізм доступний лише за точною D5-ідентичністю «макрос».
}

fn materialize_macro_value(
    arguments: &[Value],
    _environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if arguments.len() != 1 {
        return Err(LanguageError::new(
            ErrorKind::Arity,
            "макрос очікує рівно один аргумент",
            span,
        ));
    }

    match &arguments[0] {
        Value::Closure(closure) => {
            // Новий макрос: розв'язані раніше тіла могли бачити цю назву як виклик.
            super::closures::bump_resolution_epoch();
            Ok(Value::Macro(closure.clone()))
        }
        _ => Err(LanguageError::new(
            ErrorKind::Type,
            "макрос очікує значення-замикання",
            span,
        )),
    }
}
