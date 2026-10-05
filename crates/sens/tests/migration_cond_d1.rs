//! Compatibility-only witness for #220/#3162.
//! Exact D1 must never fall through to generic host truthiness while the
//! historical eight-bit COND route still exists during source migration.

use sens::{eval_program, Session};

#[test]
fn migration_cond_distinguishes_exact_d1_no_from_yes() {
    let source = r#"
        (00000111
          ((тотожне? (00000001 а) (00000001 б)) (00000001 помилка))
          ((тотожне? (00000001 а) (00000001 а)) (00000001 добре)))
    "#;

    let result = eval_program(source, &mut Session::default())
        .expect("migration COND must consume exact D1 before legacy truthiness");

    assert_eq!(result.value.to_string(), "добре");
}
