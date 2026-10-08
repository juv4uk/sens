//! Owner #4449: compiler .lisp stays human-readable Ukrainian, while
//! execution heads become exact D3/D4 AST identities during loading.
//! Never count this as a physical .sens or historic-oracle admission.
use sens::{parse_mixed_exact_domain, ExprKind};

const UK_SOURCE: &str = include_str!("../../../lib/compiler-nucleus.lisp");

#[test]
fn real_compiler_preserves_uk_source_and_lowers_all_definitions_to_exact_heads() {
    // Six definitions wrap the Ukrainian name onto the following line;
    // a line-start-only counter would silently ignore valid D4 DEFINE forms.
    let source_definitions = UK_SOURCE.matches("(визначити").count();
    assert_eq!(source_definitions, 51, "compiler has 51 original callable definitions");
    assert_eq!(UK_SOURCE.matches("(функція").count(), 51);
    assert!(!UK_SOURCE.contains("(0011 "), "the .lisp human projection must not become raw D4");
    assert!(!UK_SOURCE.contains("(0010 "), "the .lisp human projection must not become raw D4");

    let forms = parse_mixed_exact_domain(UK_SOURCE)
        .expect("ratified Ukrainian compiler source must resolve at parse time");
    assert_eq!(forms.len(), source_definitions);
    for (index, expr) in forms.iter().enumerate() {
        let ExprKind::List(definition) = &expr.kind else {
            panic!("definition {index} must remain a D2 list");
        };
        assert_eq!(definition.len(), 3, "definition {index} arity");
        assert!(matches!(&definition[0].kind, ExprKind::DomainIdentity(identity)
            if identity.width() == 4 && identity.packed_bits() == 0b0011),
            "definition {index} must be exact D4 DEFINE");
        let ExprKind::List(lambda) = &definition[2].kind else {
            panic!("definition {index} must contain a lambda");
        };
        assert!(matches!(&lambda[0].kind, ExprKind::DomainIdentity(identity)
            if identity.width() == 4 && identity.packed_bits() == 0b0010),
            "definition {index} must use exact D4 LAMBDA");
        assert!(!matches!(&definition[1].kind, ExprKind::DomainIdentity(_)),
            "definition {index} name is human binding metadata, not a core resident");
    }
}

#[test]
fn source_projection_is_not_a_physical_migration_claim() {
    // D4 function identity is proven *inside the AST*. Without a ratified
    // binder carrier and an independently observed execution oracle there is
    // no authority to claim this source as byte-packed original .sens.
    assert!(UK_SOURCE.contains("(за-умовою"));
    assert!(UK_SOURCE.contains("(сполучити"));
}
